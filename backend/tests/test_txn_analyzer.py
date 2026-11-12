import pytest
from backend.analyzers.txn_analyzer import TransactionAnalyzer

@pytest.fixture
def txn_analyzer():
    return TransactionAnalyzer()

def test_normal_user_transaction_scores_low(txn_analyzer):
    result = txn_analyzer.analyze(
        user_id="u101",
        amount=450.0,
        receiver="grocery@okaxis",
        timestamp_str="2026-11-12T14:30:00",
        channel="upi",
        note="weekly groceries",
    )
    assert result["risk_level"] == "LOW"
    assert result["risk_score"] < 40
    assert result["type"] == "transaction"

def test_extreme_amount_and_odd_night_hour_scores_high(txn_analyzer):
    result = txn_analyzer.analyze(
        user_id="u101",
        amount=49999.0,
        receiver="unknown@ybl",
        timestamp_str="2026-11-12T02:14:00",
        channel="upi",
        note="urgent refund",
    )
    assert result["risk_level"] == "HIGH"
    assert result["risk_score"] >= 70
    signal_names = [s.name for s in result["signals"]]
    assert any("Extreme Amount" in s for s in signal_names)
    assert any("Night Transfer" in s for s in signal_names)
    assert any("Urgency Keywords" in s for s in signal_names)

def test_near_daily_limit_transaction(txn_analyzer):
    result = txn_analyzer.analyze(
        user_id="u101",
        amount=95000.0,
        receiver="scam_desk@axl",
        timestamp_str="2026-11-12T03:45:00",
        channel="upi",
        note="account blocked kyc penalty",
    )
    assert result["risk_level"] == "HIGH"
    signal_names = [s.name for s in result["signals"]]
    assert any("Near Daily Transfer Limit" in s for s in signal_names)
