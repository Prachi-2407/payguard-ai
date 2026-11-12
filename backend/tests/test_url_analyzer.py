import pytest
from backend.analyzers.url_analyzer import UrlAnalyzer, MockWhoisProvider

@pytest.fixture
def url_analyzer():
    return UrlAnalyzer()

def test_legitimate_url_scores_low(url_analyzer):
    result = url_analyzer.analyze("https://paytm.com/recharge")
    assert result["risk_level"] == "LOW"
    assert result["risk_score"] < 40
    assert result["verdict"] == "Safe to proceed"
    assert result["type"] == "url"

def test_hard_negative_hyphen_legitimate_url(url_analyzer):
    result = url_analyzer.analyze("https://developer-support.microsoft.com/en-us/help")
    assert result["risk_level"] == "LOW"
    assert result["risk_score"] < 40

def test_suspicious_tld_and_brand_impersonation(url_analyzer):
    result = url_analyzer.analyze("http://paytm-secure-login.xyz/verify?id=123")
    assert result["risk_level"] == "HIGH"
    assert result["risk_score"] >= 70
    assert result["verdict"] == "Do not proceed"
    signal_names = [s.name for s in result["signals"]]
    assert any("Suspicious TLD" in s for s in signal_names)

def test_ip_address_host_detected(url_analyzer):
    result = url_analyzer.analyze("http://192.168.1.105/sbi/netbanking/login.php")
    assert result["risk_level"] == "HIGH"
    signal_names = [s.name for s in result["signals"]]
    assert any("IP Address Host" in s for s in signal_names)

def test_at_symbol_deception(url_analyzer):
    result = url_analyzer.analyze("http://amazon.in@pay-secure-bonus.xyz/redeem")
    assert result["risk_level"] == "HIGH"
    signal_names = [s.name for s in result["signals"]]
    assert any("Deceptive '@' Character" in s for s in signal_names)

def test_open_redirect_and_shortener(url_analyzer):
    result = url_analyzer.analyze("https://bit.ly/3xPaytmKYC?redirect=http://paytm-kyc.xyz")
    assert result["risk_level"] in ["MEDIUM", "HIGH"]
    signal_names = [s.name for s in result["signals"]]
    assert any("URL Shortener" in s for s in signal_names) or any("Redirect Parameter" in s for s in signal_names)

def test_mock_whois_provider():
    mock = MockWhoisProvider()
    assert mock.get_domain_age_days("paytm.com") > 1000
    assert mock.get_domain_age_days("scam-site.xyz") < 35
