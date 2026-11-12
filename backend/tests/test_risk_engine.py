from backend.core.risk_engine import (
    calculate_rule_score,
    determine_risk_level,
    get_verdict_and_action,
    blend_risk,
)
from backend.models.api import Signal

def test_risk_level_boundaries():
    assert determine_risk_level(0) == "LOW"
    assert determine_risk_level(39) == "LOW"
    assert determine_risk_level(40) == "MEDIUM"
    assert determine_risk_level(69) == "MEDIUM"
    assert determine_risk_level(70) == "HIGH"
    assert determine_risk_level(100) == "HIGH"

def test_verdict_and_action_consistency():
    verdict, action = get_verdict_and_action("HIGH", scan_type="url")
    assert verdict == "Do not proceed"
    assert "Do not pay" in action

    verdict_m, action_m = get_verdict_and_action("MEDIUM", scan_type="url")
    assert verdict_m == "Proceed with caution"

    verdict_l, action_l = get_verdict_and_action("LOW", scan_type="url")
    assert verdict_l == "Safe to proceed"

def test_blend_risk_multi_high_signals():
    signals = [
        Signal(name="Suspicious TLD", severity="high", detail="Phishing TLD"),
        Signal(name="IP Host", severity="high", detail="Raw IP address"),
    ]
    score, level, verdict, action = blend_risk(signals, ml_probability=0.85, scan_type="url")
    assert score >= 70
    assert level == "HIGH"
    assert verdict == "Do not proceed"
