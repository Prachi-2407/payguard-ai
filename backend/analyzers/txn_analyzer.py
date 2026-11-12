import os
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import numpy as np
from sqlalchemy.orm import Session
import joblib

from backend.config import settings
from backend.models.api import Signal
from backend.ml.train_txn import TXN_FEATURE_NAMES, extract_transaction_features, URGENT_WORDS
from backend.models.db import TransactionAudit
from backend.core.risk_engine import blend_risk
from backend.core.explainer import explain

logger = logging.getLogger(__name__)

_TXN_MODEL_ARTIFACT = None
_USER_BASELINES = None

def get_txn_model() -> Optional[Dict[str, Any]]:
    """Loads transaction IsolationForest model once at startup."""
    global _TXN_MODEL_ARTIFACT
    if _TXN_MODEL_ARTIFACT is not None:
        return _TXN_MODEL_ARTIFACT

    model_path = "backend/ml/txn_model.pkl"
    if os.path.exists(model_path):
        try:
            _TXN_MODEL_ARTIFACT = joblib.load(model_path)
            logger.info("Loaded Transaction IsolationForest model successfully from %s", model_path)
            return _TXN_MODEL_ARTIFACT
        except Exception as e:
            logger.error("Failed to load txn model: %s", e)

    # Auto train if missing
    try:
        from backend.ml.train_txn import train_txn_model
        train_txn_model()
        if os.path.exists(model_path):
            _TXN_MODEL_ARTIFACT = joblib.load(model_path)
            return _TXN_MODEL_ARTIFACT
    except Exception as e:
        logger.warning("Auto-training txn model failed: %s", e)

    return None

def get_user_baselines() -> Dict[str, Any]:
    """Loads stored user baselines or returns defaults."""
    global _USER_BASELINES
    if _USER_BASELINES is not None:
        return _USER_BASELINES

    baseline_path = "backend/ml/txn_baselines.json"
    if os.path.exists(baseline_path):
        try:
            with open(baseline_path, "r") as f:
                _USER_BASELINES = json.load(f)
                return _USER_BASELINES
        except Exception as e:
            logger.error("Failed to load user baselines: %s", e)

    # Defaults
    _USER_BASELINES = {
        "u101": {"avg_amount": 850.0, "std_amount": 450.0, "usual_hours": [9, 22], "daily_limit": 100000.0, "known_receivers": ["grocery@okaxis", "zomato@icici", "friend@ybl"]},
        "u_default": {"avg_amount": 1200.0, "std_amount": 800.0, "usual_hours": [8, 22], "daily_limit": 100000.0, "known_receivers": []},
    }
    return _USER_BASELINES

class TransactionAnalyzer:
    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def analyze(
        self,
        user_id: str,
        amount: float,
        receiver: str,
        timestamp_str: str,
        channel: str = "upi",
        note: Optional[str] = "",
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Analyzes a payment transaction:
        - Compares against user baselines (z-score, known payees, usual hours)
        - Calculates velocity from past transactions
        - Evaluates urgency and round-number signals
        - Scores via IsolationForest anomaly detector
        """
        session = db or self.db
        baselines = get_user_baselines()
        user_profile = baselines.get(user_id, baselines.get("u_default", {
            "avg_amount": 1200.0,
            "std_amount": 800.0,
            "usual_hours": [8, 22],
            "daily_limit": 100000.0,
            "known_receivers": [],
        }))

        # Parse timestamp
        try:
            clean_ts = timestamp_str.replace("Z", "+00:00")
            parsed_dt = datetime.fromisoformat(clean_ts)
            hour = parsed_dt.hour
            minute = parsed_dt.minute
        except Exception:
            parsed_dt = datetime.now(timezone.utc)
            hour = parsed_dt.hour
            minute = parsed_dt.minute

        # Calculate velocity in past 1 hour from DB if available
        velocity_count = 1
        if session:
            try:
                one_hour_ago = (parsed_dt - timedelta(hours=1)).isoformat()
                count = (
                    session.query(TransactionAudit)
                    .filter(
                        TransactionAudit.user_id == user_id,
                        TransactionAudit.timestamp >= one_hour_ago,
                    )
                    .count()
                )
                velocity_count = max(1, count + 1)
            except Exception as e:
                logger.debug("Velocity query failed: %s", e)

        signals: List[Signal] = []

        avg_amt = user_profile.get("avg_amount", 1000.0)
        std_amt = max(user_profile.get("std_amount", 500.0), 1.0)
        daily_lim = user_profile.get("daily_limit", 100000.0)
        known_recvs = [r.lower() for r in user_profile.get("known_receivers", [])]

        z_score = (amount - avg_amt) / std_amt

        # 1. High Amount / Z-Score Spike
        if amount >= 40000.0 or z_score >= 8.0:
            signals.append(
                Signal(
                    name="Extreme Amount Anomaly",
                    severity="high",
                    detail=f"Amount of ₹{amount:,.2f} is an extreme spike vs user average of ₹{avg_amt:,.2f} (z-score: {z_score:.1f}).",
                )
            )
        elif z_score >= 3.0:
            signals.append(
                Signal(
                    name="Unusual Amount Deviation",
                    severity="medium",
                    detail=f"Amount ₹{amount:,.2f} exceeds user's typical payment bounds (z-score: {z_score:.1f}).",
                )
            )

        # 2. Odd Hour Transfer (1 AM - 5 AM)
        if 1 <= hour <= 5:
            signals.append(
                Signal(
                    name="Unusual Night Transfer Hour",
                    severity="medium",
                    detail=f"Transaction initiated at {hour:02d}:{minute:02d} AM, outside normal active hours (8 AM - 10 PM).",
                )
            )

        # 3. New / Unseen Receiver
        if receiver.lower() not in known_recvs:
            signals.append(
                Signal(
                    name="Unrecognized New Payee",
                    severity="medium",
                    detail=f"First-time transfer to recipient '{receiver}' who is not in user's known payees list.",
                )
            )

        # 4. Velocity Spikes
        if velocity_count >= 4:
            signals.append(
                Signal(
                    name="Rapid Transaction Velocity",
                    severity="high",
                    detail=f"Burst velocity of {velocity_count} payments in the last hour, characteristic of account compromise.",
                )
            )

        # 5. Round Number Amount (often requested by scammers)
        if amount >= 5000.0 and amount % 1000 == 0:
            signals.append(
                Signal(
                    name="Large Round Payment Amount",
                    severity="low",
                    detail=f"Payment is an exact round sum (₹{amount:,.2f}), frequently seen in upfront fee scams.",
                )
            )

        # 6. Urgency / Fraud Keywords in Note
        note_lower = (note or "").lower()
        matched_kws = [w for w in URGENT_WORDS if w in note_lower]
        if matched_kws:
            signals.append(
                Signal(
                    name="Urgency Keywords in Note",
                    severity="high",
                    detail=f"Note contains psychological urgency/scam keywords: '{', '.join(matched_kws)}'.",
                )
            )

        # 7. Near or Exceeding Daily Limit
        if amount >= 0.85 * daily_lim:
            signals.append(
                Signal(
                    name="Near Daily Transfer Limit",
                    severity="high",
                    detail=f"Amount (₹{amount:,.2f}) approaches or reaches the daily account limit of ₹{daily_lim:,.2f}.",
                )
            )

        # 8. Community Reputation Check on Receiver
        if receiver:
            try:
                import httpx
                resp = httpx.get(
                    f"{settings.EXTRAS_API_URL}/api/ext/reputation",
                    params={"value": receiver},
                    timeout=2.0
                )
                if resp.status_code == 200:
                    rep_data = resp.json()
                    rep_count = rep_data.get("report_count", 0)
                    if rep_count >= 3:
                        signals.append(
                            Signal(
                                name="Reported by community",
                                severity="high",
                                detail=f"This UPI payee has {rep_count} verified community fraud reports in the threat database.",
                            )
                        )
                    elif rep_count > 0:
                        signals.append(
                            Signal(
                                name="Community Fraud Reports",
                                severity="medium",
                                detail=f"This UPI payee has {rep_count} community report(s) on file.",
                            )
                        )
            except Exception:
                pass

        # IsolationForest Anomaly Score
        ml_prob = 0.0
        model_artifact = get_txn_model()
        if model_artifact and "model" in model_artifact:
            try:
                feats = extract_transaction_features(
                    amount=amount,
                    timestamp_str=timestamp_str,
                    receiver=receiver,
                    note=note or "",
                    user_baseline=user_profile,
                    velocity_count=velocity_count,
                )
                feat_vector = np.array([[feats[n] for n in TXN_FEATURE_NAMES]])
                model = model_artifact["model"]
                # IsolationForest decision_function: higher is normal (>0), lower is anomalous (<0)
                raw_score = float(model.decision_function(feat_vector)[0])
                # Calibrate raw_score to anomaly probability:
                # raw_score ~ 0.15 => prob ~ 0.05 (normal)
                # raw_score ~ -0.15 => prob ~ 0.85 (anomaly)
                ml_prob = max(0.0, min(1.0, 0.5 - (raw_score * 2.5)))
            except Exception as e:
                logger.warning("Transaction IsolationForest prediction failed: %s", e)

        risk_score, risk_level, verdict, action = blend_risk(
            signals=signals,
            ml_probability=ml_prob,
            scan_type="transaction",
            ml_weight=0.30,
            rule_weight=0.70,
        )

        explanation = explain("transaction", risk_level, signals, risk_score)

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "verdict": verdict,
            "signals": signals,
            "explanation": explanation,
            "recommended_action": action,
            "type": "transaction",
            "ml_probability": ml_prob,
        }
