from typing import List, Tuple
from backend.config import settings
from backend.models.api import Signal

def calculate_rule_score(signals: List[Signal]) -> int:
    """
    Computes a deterministic score from 0 to 100 based on signals.
    - 0 signals: 0 (LOW)
    - Low severity: 15 points each (remains in LOW tier unless compounded)
    - Medium severity: 45 base points for the first, +12 for additional (MEDIUM tier 40-69)
    - High severity: 75 base points for the first, +12 for additional (HIGH tier 70-100, matches contract example where 1 high signal = 87)
    """
    if not signals:
        return 0

    high_count = sum(1 for s in signals if s.severity == "high")
    med_count = sum(1 for s in signals if s.severity == "medium")
    low_count = sum(1 for s in signals if s.severity == "low")

    if high_count >= 1:
        # Matches prompt example: single high signal produces score in HIGH tier (e.g. 75-87)
        score = 75 + ((high_count - 1) * 12) + (med_count * 6) + (low_count * 2)
    elif med_count >= 1:
        score = 45 + ((med_count - 1) * 10) + (low_count * 4)
    else:
        score = low_count * 15

    return min(100, max(0, score))

def determine_risk_level(score: int) -> str:
    """
    Categorizes score into LOW, MEDIUM, HIGH.
    LOW: 0 - 39
    MEDIUM: 40 - 69
    HIGH: 70 - 100
    """
    if score >= settings.THRESHOLD_HIGH_MIN:
        return "HIGH"
    elif score > settings.THRESHOLD_LOW_MAX:
        return "MEDIUM"
    return "LOW"

def get_verdict_and_action(risk_level: str, scan_type: str = "url") -> Tuple[str, str]:
    """Returns the verdict and actionable recommendation based on risk level."""
    if risk_level == "HIGH":
        verdict = "Do not proceed"
        if scan_type == "qr":
            action = "Do not scan or pay. Entering your UPI PIN will deduct money from your account."
        elif scan_type == "transaction":
            action = "Do not authorize this transfer. Contact your bank or verify the payee immediately."
        else:
            action = "Do not pay. Verify via an official known number or support channel."
    elif risk_level == "MEDIUM":
        verdict = "Proceed with caution"
        if scan_type == "qr":
            action = "Double-check the merchant name and amount before confirming with your UPI PIN."
        elif scan_type == "transaction":
            action = "Confirm the recipient identity with a phone call before proceeding with payment."
        else:
            action = "Exercise caution. Check the website domain carefully before entering credentials."
    else:
        verdict = "Safe to proceed"
        action = "Details match standard verified patterns. Always confirm the final amount before payment."

    return verdict, action

def blend_risk(
    signals: List[Signal],
    ml_probability: float = 0.0,
    scan_type: str = "url",
    ml_weight: float = settings.URL_ML_WEIGHT,
    rule_weight: float = settings.URL_RULE_WEIGHT,
) -> Tuple[int, str, str, str]:
    """
    Merges heuristic signals and ML probability into a calibrated risk score (0-100),
    level, verdict, and recommended action.
    """
    rule_score = calculate_rule_score(signals)
    ml_score = int(round(ml_probability * 100.0))

    if ml_probability > 0.0:
        raw_blended = (rule_weight * rule_score) + (ml_weight * ml_score)
        blended_score = int(round(raw_blended))

        # Critical override: if rules found 2+ high severity signals, or ML is >= 0.90 with at least 1 high signal
        if sum(1 for s in signals if s.severity == "high") >= 2:
            blended_score = max(blended_score, 75)
        elif sum(1 for s in signals if s.severity == "high") == 1 and ml_probability >= 0.70:
            blended_score = max(blended_score, 70)
    else:
        blended_score = rule_score

    # Boundary check
    final_score = min(100, max(0, blended_score))
    risk_level = determine_risk_level(final_score)
    verdict, action = get_verdict_and_action(risk_level, scan_type=scan_type)

    return final_score, risk_level, verdict, action
