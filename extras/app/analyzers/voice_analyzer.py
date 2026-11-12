import os
import re
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import joblib
from sqlalchemy.orm import Session

from extras.app.config import settings, mask_upi_id, mask_phone_number
from extras.app.schemas.models import (
    VoiceAnalyzeResponse,
    TranscriptionMetadata,
    Signal,
)
from extras.app.analyzers.extraction import extract_all_entities
from extras.app.services.risk_engine import blend_voice_risk
from extras.app.services.explanation import get_voice_explanation
from extras.app.database.repository import get_entity_reputation, log_analysis_event

logger = logging.getLogger(__name__)

_VOICE_MODEL = None

def get_voice_model():
    """Loads voice classification model pipeline once, caching it in memory."""
    global _VOICE_MODEL
    if _VOICE_MODEL is not None:
        return _VOICE_MODEL

    path = settings.VOICE_MODEL_PATH
    if os.path.exists(path):
        try:
            _VOICE_MODEL = joblib.load(path)
            logger.info(f"Loaded voice model pipeline from {path}")
            return _VOICE_MODEL
        except Exception as e:
            logger.error(f"Failed to load voice model from {path}: {e}")

    # Auto-train if missing
    try:
        from extras.ml.train import train_and_evaluate_voice_model
        logger.info("Voice model artifact missing; running training pipeline...")
        train_and_evaluate_voice_model()
        if os.path.exists(path):
            _VOICE_MODEL = joblib.load(path)
            return _VOICE_MODEL
    except Exception as e:
        logger.error(f"Voice auto-training failed: {e}")

    return None

class VoiceAnalyzer:
    """Analyzes audio recordings or transcripts for spoken social engineering and voice fraud."""

    def __init__(self):
        self.model = get_voice_model()

    def _detect_voice_signals(self, text: str) -> Tuple[List[Dict[str, str]], bool]:
        """Detects contextual voice scam signals and hard negatives in English & Hinglish."""
        signals: List[Dict[str, str]] = []
        text_lower = text.lower()

        # Hard negative check
        is_hard_negative = False
        legit_call_markers = [
            "delivery agent", "standing outside", "gate", "landmark", "confirm my appointment",
            "meeting at", "cafe", "biryani", "cricket", "technician visit for fiber",
            "relationship manager calling to check if you are satisfied with your credit card rewards"
        ]
        if any(m in text_lower for m in legit_call_markers):
            if not any(bad in text_lower for bad in ["share your otp", "otp batao", "digital arrest", "anydesk", "teamviewer"]):
                is_hard_negative = True

        # 1. Digital Arrest Coercion
        digital_arrest_phrases = [
            "digital arrest", "supreme court", "cannot disconnect this call", "camera off",
            "do not inform family", "escrow account", "room se bahar nahi", "video call continuously",
            "swat dispatch", "clearance account"
        ]
        if any(p in text_lower for p in digital_arrest_phrases):
            signals.append({
                "name": "Digital Arrest Extortion Threat",
                "severity": "high",
                "detail": "Caller asserts the victim is under 'Digital Arrest', commanding isolation and camera monitoring to extort money."
            })

        # 2. Police / Government / Law Enforcement Impersonation
        police_phrases = [
            "crime branch", "customs department", "cbi headquarters", "money laundering case",
            "illegal narcotics", "contraband", "parcel seized", "arrest warrant", "fake passports"
        ]
        if any(p in text_lower for p in police_phrases):
            signals.append({
                "name": "Law Enforcement / Police Impersonation",
                "severity": "high",
                "detail": "Caller fabricates criminal charges (drugs, money laundering) claiming to be from Police, CBI, or Customs."
            })

        # 3. Direct Credential & OTP Theft
        cred_phrases = [
            "share your otp", "read out the 6-digit otp", "otp batayein", "otp bataiye",
            "otp batao", "enter upi pin", "secret pin", "cvv", "atm pin", "netbanking password"
        ]
        if any(p in text_lower for p in cred_phrases):
            signals.append({
                "name": "Verbal OTP / PIN / Credential Demands",
                "severity": "high",
                "detail": "Caller directly prompts the victim to speak or transmit an OTP, banking PIN, or CVV code over the phone."
            })

        # 4. Bank / Regulatory Impersonation
        bank_phrases = [
            "calling from state bank", "calling from sbi", "calling from hdfc", "calling from icici",
            "calling from axis", "calling from bank", "sbi main branch", "hdfc head office", "senior manager",
            "icici bank security", "rbi verification cell", "debit card is expiring", "account will be frozen",
            "account will be blocked", "unauthorized international transaction", "kyc expires", "kyc update"
        ]
        if any(p in text_lower for p in bank_phrases):
            signals.append({
                "name": "Banking Official Impersonation",
                "severity": "high",
                "detail": "Caller impersonates bank staff or RBI officials claiming urgent security or KYC lapses."
            })

        # 5. Remote Access / Screen Sharing Software
        remote_phrases = [
            "anydesk", "teamviewer", "quicksupport", "rustdesk", "9-digit code",
            "9 digit code", "download remote", "screen share"
        ]
        if any(p in text_lower for p in remote_phrases):
            signals.append({
                "name": "Remote Desktop Screen-Sharing Request",
                "severity": "high",
                "detail": "Instructs victim to install remote control apps (AnyDesk, TeamViewer) to inspect or manipulate their phone."
            })

        # 6. Fraudulent Investment / Guaranteed Returns
        invest_phrases = [
            "guaranteed 300 percent", "guaranteed profit", "insider stock tips",
            "crypto arbitrage", "100 percent risk free", "daily 15 percent"
        ]
        if any(p in text_lower for p in invest_phrases):
            signals.append({
                "name": "Guaranteed High-Return Investment Bait",
                "severity": "high",
                "detail": "Promises unrealistic risk-free trading or crypto returns, a trademark of high-yield investment fraud."
            })

        # 7. Accidental Transfer / Coercive Payment Demand
        payment_phrases = [
            "accidentally sent", "return my money immediately", "meter will be disconnected",
            "clear the outstanding charge right now"
        ]
        if any(p in text_lower for p in payment_phrases):
            signals.append({
                "name": "Coercive Payment / False Reversal Demand",
                "severity": "high",
                "detail": "Claims money was deposited accidentally or service disconnection is imminent, forcing hasty transfers."
            })

        # 8. High-Pressure Psychological Manipulation
        manipulation_phrases = [
            "kisi ko mat batana", "do not tell anyone", "immediately", "turant payment",
            "aapka account block ho jayega", "within 2 hours"
        ]
        if any(p in text_lower for p in manipulation_phrases):
            signals.append({
                "name": "Psychological Coercion & Secrecy Demands",
                "severity": "medium",
                "detail": "Attempts to isolate the victim and enforce strict urgency to bypass rational checks."
            })

        return signals, is_hard_negative

    async def analyze(
        self,
        transcript: str,
        transcription_meta: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
    ) -> VoiceAnalyzeResponse:
        """Analyzes speech transcript for phone scam vectors."""
        if not self.model:
            self.model = get_voice_model()

        # 1. Extraction of any entities spoken in call
        extracted = extract_all_entities(transcript)
        rule_signals, is_hard_negative = self._detect_voice_signals(transcript)

        # 2. Check community reputation for extracted entities
        community_signals: List[Dict[str, str]] = []
        if db:
            all_targets = [("vpa", v) for v in extracted["upi_ids"]] + [("phone", p) for p in extracted["phone_numbers"]]
            for t_type, val in all_targets:
                rep = get_entity_reputation(db, val)
                if rep.reputation == "BAD":
                    masked = mask_upi_id(val) if t_type == "vpa" else mask_phone_number(val)
                    community_signals.append({
                        "name": "Community Blocklist Match",
                        "severity": "high",
                        "detail": f"Entity '{masked}' mentioned in conversation is verified BAD in community reports ({rep.report_count} reports)."
                    })
                elif rep.reputation == "SUSPICIOUS":
                    masked = mask_upi_id(val) if t_type == "vpa" else mask_phone_number(val)
                    community_signals.append({
                        "name": "Community Reputation Warning",
                        "severity": "medium",
                        "detail": f"Entity '{masked}' was previously reported by community ({rep.report_count} reports)."
                    })

        # 3. ML Model Classification
        scam_category = "NONE"
        confidence = 0.5

        if self.model:
            try:
                classes = list(self.model.classes_)
                probas = self.model.predict_proba([transcript])[0]
                top_idx = int(probas.argmax())
                pred_label = classes[top_idx]
                pred_conf = float(probas[top_idx])

                has_strong_voice_rules = any(s["severity"] == "high" for s in rule_signals)
                if pred_label == "NONE" and has_strong_voice_rules and not is_hard_negative:
                    if any("Digital Arrest" in s["name"] for s in rule_signals):
                        scam_category = "DIGITAL_ARREST"
                    elif any("Police" in s["name"] for s in rule_signals):
                        scam_category = "POLICE_OR_GOVERNMENT_IMPERSONATION"
                    elif any("Credential" in s["name"] for s in rule_signals):
                        scam_category = "OTP_FRAUD"
                    elif any("Banking" in s["name"] for s in rule_signals):
                        scam_category = "BANK_IMPERSONATION"
                    elif any("Remote" in s["name"] for s in rule_signals):
                        scam_category = "REMOTE_ACCESS_SCAM"
                    elif any("Investment" in s["name"] for s in rule_signals):
                        scam_category = "INVESTMENT_SCAM"
                    else:
                        scam_category = "OTHER"
                    confidence = 0.90
                else:
                    scam_category = pred_label
                    confidence = pred_conf
            except Exception as e:
                logger.error(f"Error in voice ML inference: {e}")
                scam_category = "OTHER" if (rule_signals and not is_hard_negative) else "NONE"
                confidence = 0.6
        else:
            scam_category = "OTHER" if (rule_signals and not is_hard_negative) else "NONE"
            confidence = 0.7 if rule_signals else 0.9

        if is_hard_negative and not any(s["severity"] == "high" for s in rule_signals):
            scam_category = "NONE"

        # 4. Central Risk Blending
        risk_score, risk_level, verdict, final_signals = blend_voice_risk(
            ml_category=scam_category,
            ml_confidence=confidence,
            rule_signals=rule_signals,
            community_signals=community_signals,
            is_hard_negative=is_hard_negative,
        )

        # 5. Explanation & Recommendation
        explanation, recommended_action = get_voice_explanation(scam_category, risk_score)
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # 6. Audit logging
        if db:
            signal_names = [s.name for s in final_signals]
            log_analysis_event(db, "voice", scam_category, risk_level, signal_names)

        meta = transcription_meta or {
            "language": "en",
            "duration_seconds": None,
            "confidence": 1.0,
            "source": "transcript",
        }

        response = VoiceAnalyzeResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            verdict=verdict,
            transcript=transcript,
            scam_category=scam_category,
            signals=final_signals,
            explanation=explanation,
            recommended_action=recommended_action,
            analyzed_at=now_iso,
            type="voice",
            transcription_metadata=TranscriptionMetadata(**meta),
        )

        return response
