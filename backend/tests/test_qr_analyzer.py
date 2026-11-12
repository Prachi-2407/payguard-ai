import pytest
from backend.analyzers.qr_analyzer import QrAnalyzer

@pytest.fixture
def qr_analyzer():
    return QrAnalyzer()

def test_safe_upi_payload_scores_low(qr_analyzer):
    result = qr_analyzer.analyze("upi://pay?pa=shop@okaxis&pn=Ram Store&am=250.00&cu=INR")
    assert result["risk_level"] == "LOW"
    assert result["risk_score"] < 40
    assert result["verdict"] == "Safe to proceed"
    assert result["type"] == "qr"

def test_high_prefilled_amount_alert(qr_analyzer):
    result = qr_analyzer.analyze("upi://pay?pa=shop@okaxis&pn=Electronics Depot&am=75000&cu=INR")
    assert result["risk_level"] == "HIGH"
    signal_names = [s.name for s in result["signals"]]
    assert any("High Pre-filled Amount" in s for s in signal_names)

def test_payee_name_and_vpa_mismatch(qr_analyzer):
    result = qr_analyzer.analyze("upi://pay?pa=attacker982@ybl&pn=Paytm Customer Care&cu=INR")
    assert result["risk_level"] == "HIGH"
    signal_names = [s.name for s in result["signals"]]
    assert any("Mismatch" in s for s in signal_names)

def test_upi_collect_receive_money_scam(qr_analyzer):
    result = qr_analyzer.analyze("upi://pay?pa=refund-desk@okicici&pn=Cashback Reward&am=2000&cu=INR&tn=enter pin to receive cashback")
    assert result["risk_level"] == "HIGH"
    signal_names = [s.name for s in result["signals"]]
    assert any("Collect" in s for s in signal_names)

def test_non_inr_currency_flagged(qr_analyzer):
    result = qr_analyzer.analyze("upi://pay?pa=store@okaxis&pn=Global Store&am=100&cu=USD")
    assert result["risk_level"] == "HIGH"
    signal_names = [s.name for s in result["signals"]]
    assert any("Non-INR Currency" in s for s in signal_names)

def test_embedded_phishing_url_in_qr(qr_analyzer):
    result = qr_analyzer.analyze("https://paytm-secure-login.xyz/verify?id=992")
    assert result["risk_level"] == "HIGH"
    assert result["type"] == "qr"
    signal_names = [s.name for s in result["signals"]]
    assert any("Embedded Web Link" in s for s in signal_names)

def test_benign_plain_text_qr(qr_analyzer):
    result = qr_analyzer.analyze("Welcome to Ram General Store! Thank you for shopping with us.")
    assert result["risk_level"] == "LOW"
    assert result["risk_score"] < 40
