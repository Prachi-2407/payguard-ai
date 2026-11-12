from typing import Dict, Any, List, Tuple
from extras.app.schemas.models import Signal
from extras.app.config import settings

def calculate_risk_level(score: int) -> str:
    """Categorizes risk score into LOW, MEDIUM, HIGH matching main contract."""
    if score >= settings.THRESHOLD_HIGH_MIN:
        return "HIGH"
    elif score > settings.THRESHOLD_LOW_MAX:
        return "MEDIUM"
    return "LOW"

def get_verdict(level: str) -> str:
    """Returns human-facing verdict string matching main contract."""
    if level == "HIGH":
        return "Do not proceed"
    elif level == "MEDIUM":
        return "Proceed with caution"
    return "Safe to proceed"

def blend_message_risk(
    ml_category: str,
    ml_confidence: float,
    rule_signals: List[Dict[str, str]],
    url_signals: List[Dict[str, str]],
    url_risk_score: int,
    community_signals: List[Dict[str, str]],
    is_hard_negative: bool = False,
) -> Tuple[int, str, str, List[Signal]]:
    """
    Blends ML probability, rule signals, embedded URL assessment, and community intelligence.
    Returns (risk_score, risk_level, verdict, final_signals_list).
    """
    raw_score = 10.0

    # 1. Base ML Contribution
    if ml_category != "NONE":
        # ML model detects scam intent
        raw_score += ml_confidence * 45.0
    else:
        # Legitimate intent
        raw_score = max(5.0, raw_score - (ml_confidence * 10.0))

    # 2. Rule Signals Contribution
    for s in rule_signals:
        sev = s.get("severity", "low")
        if sev == "high":
            raw_score += 25.0
        elif sev == "medium":
            raw_score += 15.0
        else:
            raw_score += 8.0

    # 3. Embedded URL Contribution
    if url_signals:
        raw_score += (url_risk_score * 0.35)

    # 4. Community Reputation Contribution
    for cs in community_signals:
        sev = cs.get("severity", "low")
        if sev == "high":
            raw_score += 35.0
        elif sev == "medium":
            raw_score += 20.0
        else:
            raw_score += 10.0

    # 5. Hard Negative Context Dampening
    if is_hard_negative and ml_category == "NONE":
        # Strongly legitimate alert (e.g., standard "OTP is valid for 10 min. Do not share")
        raw_score = min(raw_score, 25.0)

    # Critical trigger overriding: direct request for credential theft always escalates to at least HIGH
    has_credential_theft = any(
        "OTP" in s.get("name", "") or "UPI PIN" in s.get("name", "") or "CVV" in s.get("name", "")
        for s in rule_signals
    )
    if has_credential_theft and ml_category != "NONE":
        raw_score = max(raw_score, 78.0)

    # Clamp score to [0, 100]
    final_score = int(round(min(100.0, max(0.0, raw_score))))
    level = calculate_risk_level(final_score)
    verdict = get_verdict(level)

    # Merge all signals
    merged_raw = rule_signals + url_signals + community_signals
    # Deduplicate signals by name
    seen_names = set()
    final_signals: List[Signal] = []
    for s in merged_raw:
        n = s["name"]
        if n not in seen_names:
            seen_names.add(n)
            final_signals.append(
                Signal(name=n, severity=s["severity"], detail=s["detail"])
            )

    return final_score, level, verdict, final_signals

def blend_voice_risk(
    ml_category: str,
    ml_confidence: float,
    rule_signals: List[Dict[str, str]],
    community_signals: List[Dict[str, str]],
    is_hard_negative: bool = False,
) -> Tuple[int, str, str, List[Signal]]:
    """
    Blends voice classifier confidence, voice rule signals, and community intelligence.
    Returns (risk_score, risk_level, verdict, final_signals_list).
    """
    raw_score = 10.0

    if ml_category != "NONE":
        raw_score += ml_confidence * 45.0
    else:
        raw_score = max(5.0, raw_score - (ml_confidence * 10.0))

    for s in rule_signals:
        sev = s.get("severity", "low")
        if sev == "high":
            raw_score += 25.0
        elif sev == "medium":
            raw_score += 15.0
        else:
            raw_score += 8.0

    for cs in community_signals:
        sev = cs.get("severity", "low")
        if sev == "high":
            raw_score += 35.0
        elif sev == "medium":
            raw_score += 20.0

    if is_hard_negative and ml_category == "NONE":
        raw_score = min(raw_score, 25.0)

    # Critical Voice Rules: Digital arrest or explicit credential demand automatically high risk
    has_credential_theft = any(
        "OTP" in s.get("name", "") or "Credential" in s.get("name", "") or "PIN" in s.get("name", "")
        for s in rule_signals
    )
    critical_categories = {"DIGITAL_ARREST", "OTP_FRAUD", "REMOTE_ACCESS_SCAM", "BANK_IMPERSONATION"}
    if has_credential_theft and ml_category != "NONE":
        raw_score = max(raw_score, 82.0)
    elif ml_category in critical_categories and ml_confidence > 0.4:
        raw_score = max(raw_score, 75.0)

    final_score = int(round(min(100.0, max(0.0, raw_score))))
    level = calculate_risk_level(final_score)
    verdict = get_verdict(level)

    merged_raw = rule_signals + community_signals
    seen_names = set()
    final_signals: List[Signal] = []
    for s in merged_raw:
        n = s["name"]
        if n not in seen_names:
            seen_names.add(n)
            final_signals.append(
                Signal(name=n, severity=s["severity"], detail=s["detail"])
            )

    return final_score, level, verdict, final_signals
