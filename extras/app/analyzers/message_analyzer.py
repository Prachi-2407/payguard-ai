import os
import re
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import joblib
from sqlalchemy.orm import Session

from extras.app.config import settings, mask_upi_id, mask_phone_number
from extras.app.schemas.models import (
    MessageAnalyzeResponse,
    ExtractedEntities,
    Signal,
)
from extras.app.analyzers.extraction import (
    extract_all_entities,
    extract_urls,
    extract_upi_ids,
    extract_phone_numbers,
)
from extras.app.services.url_service import analyze_embedded_url
from extras.app.services.risk_engine import blend_message_risk
from extras.app.services.explanation import get_message_explanation
from extras.app.database.repository import get_entity_reputation, log_analysis_event

logger = logging.getLogger(__name__)

# Cached model singleton
_MESSAGE_MODEL = None

def get_message_model():
    """Loads the message classification model pipeline once, caching it in memory."""
    global _MESSAGE_MODEL
    if _MESSAGE_MODEL is not None:
        return _MESSAGE_MODEL

    from pathlib import Path
    base_dir = Path(__file__).resolve().parent.parent.parent
    possible_paths = [
        settings.MODEL_PATH,
        str(base_dir / "ml" / "models" / "message_model.joblib"),
        str(base_dir.parent / settings.MODEL_PATH),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            try:
                _MESSAGE_MODEL = joblib.load(path)
                logger.info(f"Loaded message model pipeline from {path}")
                return _MESSAGE_MODEL
            except Exception as e:
                logger.error(f"Failed to load message model from {path}: {e}")

    # Auto-train if missing
    try:
        from extras.ml.train import train_and_evaluate_message_model
        logger.info("Message model artifact missing; running training pipeline...")
        train_and_evaluate_message_model()
        if os.path.exists(path):
            _MESSAGE_MODEL = joblib.load(path)
            return _MESSAGE_MODEL
    except Exception as e:
        logger.error(f"Auto-training failed: {e}")

    return None

class MessageAnalyzer:
    """Analyzes SMS, WhatsApp, and email messages for financial scam patterns."""

    def __init__(self):
        self.model = get_message_model()

    def _detect_rule_signals(self, text: str) -> Tuple[List[Dict[str, str]], bool]:
        """Detects contextual rule signals and checks for genuine hard negative patterns."""
        signals: List[Dict[str, str]] = []
        text_lower = text.lower()

        # Hard negative signals (genuine bank transaction alerts or official OTP delivery)
        is_hard_negative = False
        genuine_markers = [
            "is your otp for transaction", "debited from a/c", "debited by upi",
            "credited with inr", "received inr", "available balance inr",
            "out for delivery today", "delivery associate:", "valid for 10 mins. do not share",
            "do not share otp with anyone", "if not done by you, sms block"
        ]
        if any(gm in text_lower for gm in genuine_markers):
            # Check that it's NOT asking the user to send their OTP or click a suspicious link
            if not any(req in text_lower for req in ["enter pin to receive", "share otp", "otp batao", ".xyz", ".top", ".buzz", ".site"]):
                is_hard_negative = True

        # 1. Direct Credential Theft (OTP, UPI PIN, CVV, Password)
        cred_keywords = ["enter upi pin", "share otp", "otp batayein", "otp batao", "enter secret pin", "share pin", "enter pin to receive", "atm pin", "cvv"]
        if any(kw in text_lower for kw in cred_keywords):
            signals.append({
                "name": "Direct Credential / PIN Request",
                "severity": "high",
                "detail": "Message prompts the recipient to disclose or enter their secret UPI PIN / OTP to complete a transaction."
            })

        # 2. Account Blocking / Suspension Threats
        blocking_keywords = ["blocked today", "permanently suspended", "account will be blocked", "khata freeze", "khata block", "pan is not linked", "suspended within 24 hours", "deactivated due to"]
        if any(kw in text_lower for kw in blocking_keywords):
            signals.append({
                "name": "Account Suspension / Coercive Threat",
                "severity": "high",
                "detail": "Uses psychological fear of sudden account closure or regulatory action to force hurried compliance."
            })

        # 3. Urgency & Panic Manipulation
        urgency_keywords = ["immediately", "turant", "aaj hi", "urgent", "before midnight", "within 24 hours", "abhi", "expires today", "last day"]
        if any(kw in text_lower for kw in urgency_keywords):
            signals.append({
                "name": "High-Pressure Urgency Language",
                "severity": "medium",
                "detail": "Creates an artificial sense of urgency to rush the victim into acting without independent verification."
            })

        # 4. Lottery / Prize / Reward Bait
        lottery_keywords = ["won lottery", "lucky draw", "kbc lucky", "tata safari", "cash prize of rs", "selected as lucky winner", "crorepati", "iphone 15 pro max won"]
        if any(kw in text_lower for kw in lottery_keywords):
            signals.append({
                "name": "Lottery / Unsolicited Prize Bait",
                "severity": "high",
                "detail": "Lures recipient with non-existent lottery winnings or prizes to solicit advance clearance payments."
            })

        # 5. Upfront Processing / Registration Fee Demand
        fee_keywords = ["processing fee", "registration fee", "file charge", "gst deposit", "stamp verification fee", "advance fee", "file processing charge"]
        if any(kw in text_lower for kw in fee_keywords):
            signals.append({
                "name": "Advance Fee / Deposit Solicitation",
                "severity": "high",
                "detail": "Demands an upfront fee before releasing a prize, refund, or loan disbursement."
            })

        # 6. Deceptive UPI Collect Request
        collect_keywords = ["collect request", "approve request to receive", "approve pending request", "accept collect request", "approve and enter upi pin"]
        if any(kw in text_lower for kw in collect_keywords):
            signals.append({
                "name": "Deceptive UPI Collect Request Trap",
                "severity": "high",
                "detail": "Misleads user into approving a collect request; entering a UPI PIN always debits money rather than receiving it."
            })

        # 7. Pre-Approved Collateral-Free Loan Bait
        loan_keywords = ["zero cibil check", "instant pre-approved loan", "bina kisi document ke loan", "aadhaar card par instant loan", "10 minute me loan", "no salary slip"]
        if any(kw in text_lower for kw in loan_keywords):
            signals.append({
                "name": "Unverified Instant Loan Bait",
                "severity": "high",
                "detail": "Advertises unregulated loans without credit checks, a hallmark of predatory lending and loan extortion scams."
            })

        # 8. Work-From-Home / Part-Time Earning Scam
        job_keywords = [
            "like youtube videos", "liking youtube videos", "liking youtube", "youtube video",
            "rate hotels", "rating hotels", "earn 3,000 to 8,000 daily", "earn 5,000 daily",
            "ghar baithe kamayein", "part-time job", "part time job", "work from home",
            "daily payout to upi"
        ]
        if any(kw in text_lower for kw in job_keywords):
            signals.append({
                "name": "Task-Based Part-Time Job Scam",
                "severity": "high",
                "detail": "Offers unrealistic daily income for trivial social media tasks, commonly followed by prepaid deposit demands."
            })

        # 9. Fake Customer Support Helpline
        support_keywords = ["customer care helpline", "failed transaction refund", "speak to verified support", "sahayata kendra", "grahak seva", "toll-free helpline executive"]
        if any(kw in text_lower for kw in support_keywords):
            signals.append({
                "name": "Impersonated Customer Support Contact",
                "severity": "medium",
                "detail": "Directs user to unofficial personal phone numbers falsely advertised as bank or app customer care."
            })

        # 10. Malicious APK App Installation Prompt
        if ".apk" in text_lower or "download apk" in text_lower or "download loan app" in text_lower:
            signals.append({
                "name": "Direct APK Sideloading Prompt",
                "severity": "high",
                "detail": "Urges user to download an unverified Android APK package from outside the official Google Play Store."
            })

        return signals, is_hard_negative

    async def analyze(
        self,
        message: str,
        source: str = "sms",
        db: Optional[Session] = None,
    ) -> MessageAnalyzeResponse:
        """Performs full end-to-end analysis on message content."""
        if not self.model:
            self.model = get_message_model()

        # 1. Extraction of Entities
        extracted = extract_all_entities(message)
        urls = extracted["urls"]
        upi_ids = extracted["upi_ids"]
        phone_numbers = extracted["phone_numbers"]

        # 2. Rule Signal Detection
        rule_signals, is_hard_negative = self._detect_rule_signals(message)

        # 3. Community Intelligence Checking
        community_signals: List[Dict[str, str]] = []
        if db:
            all_targets = [("url", u) for u in urls] + [("vpa", v) for v in upi_ids] + [("phone", p) for p in phone_numbers]
            for t_type, val in all_targets:
                rep = get_entity_reputation(db, val)
                if rep.reputation == "BAD":
                    masked = mask_upi_id(val) if t_type == "vpa" else (mask_phone_number(val) if t_type == "phone" else val)
                    community_signals.append({
                        "name": "Community Blocklist Match",
                        "severity": "high",
                        "detail": f"Extracted {t_type.upper()} '{masked}' has {rep.report_count} verified community reports and is classified BAD."
                    })
                elif rep.reputation == "SUSPICIOUS":
                    masked = mask_upi_id(val) if t_type == "vpa" else (mask_phone_number(val) if t_type == "phone" else val)
                    community_signals.append({
                        "name": "Community Reputation Warning",
                        "severity": "medium",
                        "detail": f"Extracted {t_type.upper()} '{masked}' was flagged by community members ({rep.report_count} reports)."
                    })

        # 4. Embedded URL Analysis (with 2s timeout & local fallback)
        url_signals: List[Dict[str, str]] = []
        max_url_score = 0
        seen_urls = set()

        for u in urls[:3]:  # Analyze up to top 3 unique links
            if u not in seen_urls:
                seen_urls.add(u)
                url_res = await analyze_embedded_url(u)
                score = url_res.get("risk_score", 0)
                max_url_score = max(max_url_score, score)
                url_signals.extend(url_res.get("signals", []))

        # 5. ML Model Inference
        scam_category = "NONE"
        confidence = 0.5

        if self.model:
            try:
                classes = list(self.model.classes_)
                probas = self.model.predict_proba([message])[0]
                top_idx = int(probas.argmax())
                pred_label = classes[top_idx]
                pred_conf = float(probas[top_idx])

                # If rule signals strongly contradict a 'NONE' prediction, let rule signals guide category
                has_strong_scam_rules = any(s["severity"] == "high" for s in rule_signals)
                if pred_label == "NONE" and has_strong_scam_rules and not is_hard_negative:
                    # Infer appropriate category from triggered rules
                    if any("Credential" in s["name"] for s in rule_signals):
                        scam_category = "KYC_FRAUD" if any("KYC" in s["name"] or "Suspension" in s["name"] for s in rule_signals) else "REFUND_SCAM"
                    elif any("Lottery" in s["name"] for s in rule_signals):
                        scam_category = "LOTTERY"
                    elif any("Collect Request" in s["name"] for s in rule_signals):
                        scam_category = "COLLECT_REQUEST"
                    elif any("Loan" in s["name"] for s in rule_signals):
                        scam_category = "LOAN_SCAM"
                    elif any("Part-Time" in s["name"] for s in rule_signals):
                        scam_category = "JOB_SCAM"
                    else:
                        scam_category = "OTHER"
                    confidence = 0.85
                else:
                    scam_category = pred_label
                    confidence = pred_conf
            except Exception as e:
                logger.error(f"Error during ML inference: {e}")
                scam_category = "OTHER" if (rule_signals and not is_hard_negative) else "NONE"
                confidence = 0.5
        else:
            scam_category = "OTHER" if (rule_signals and not is_hard_negative) else "NONE"
            confidence = 0.7 if rule_signals else 0.9

        # If hard negative is detected, ensure category is NONE unless clear credential theft occurs
        if is_hard_negative and not any(s["severity"] == "high" for s in rule_signals):
            scam_category = "NONE"

        # 6. Central Risk Blending
        risk_score, risk_level, verdict, final_signals = blend_message_risk(
            ml_category=scam_category,
            ml_confidence=confidence,
            rule_signals=rule_signals,
            url_signals=url_signals,
            url_risk_score=max_url_score,
            community_signals=community_signals,
            is_hard_negative=is_hard_negative,
        )

        # 7. Explanation & Recommendation
        explanation, recommended_action = get_message_explanation(scam_category, risk_score)

        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # 8. Audit logging
        if db:
            signal_names = [s.name for s in final_signals]
            log_analysis_event(db, "message", scam_category, risk_level, signal_names)

        response = MessageAnalyzeResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            verdict=verdict,
            signals=final_signals,
            explanation=explanation,
            recommended_action=recommended_action,
            analyzed_at=now_iso,
            type="message",
            extracted=ExtractedEntities(
                urls=urls,
                upi_ids=upi_ids,
                phone_numbers=phone_numbers,
                scam_category=scam_category,
            ),
        )

        return response
