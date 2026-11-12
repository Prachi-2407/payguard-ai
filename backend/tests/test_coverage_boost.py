from unittest.mock import patch, MagicMock
import pytest
from backend.analyzers.url_analyzer import UrlAnalyzer, LiveWhoisProvider, get_url_model
from backend.analyzers.txn_analyzer import TransactionAnalyzer, get_txn_model
from backend.analyzers.qr_analyzer import QrAnalyzer
from backend.core.explainer import explain, generate_template_explanation
from backend.models.api import Signal
from backend.config import settings

def test_url_analyzer_punycode_and_no_scheme():
    analyzer = UrlAnalyzer()
    res = analyzer.analyze("xn--paytm-qoa.com/login")
    assert res["risk_level"] in ["MEDIUM", "HIGH"]
    names = [s.name for s in res["signals"]]
    assert any("Punycode" in n for n in names)

def test_url_analyzer_excessive_subdomains():
    analyzer = UrlAnalyzer()
    res = analyzer.analyze("http://secure.login.verify.update.account.evil.xyz/login")
    assert res["risk_level"] == "HIGH"
    names = [s.name for s in res["signals"]]
    assert any("Subdomains" in n for n in names)

def test_live_whois_provider():
    provider = LiveWhoisProvider()
    age = provider.get_domain_age_days("google.com")
    # In sandbox or without whois installed, it returns None or int safely without crashing
    assert age is None or isinstance(age, int)

def test_txn_analyzer_default_baseline():
    analyzer = TransactionAnalyzer()
    res = analyzer.analyze(
        user_id="completely_new_user_999",
        amount=500.0,
        receiver="merchant@okaxis",
        timestamp_str="2026-11-12T11:00:00Z",
    )
    assert res["risk_level"] == "LOW"
    assert res["type"] == "transaction"

def test_txn_analyzer_velocity_with_db():
    from backend.db.session import SessionLocal
    from backend.models.db import TransactionAudit

    db = SessionLocal()
    try:
        # Insert 4 recent transactions for user u_burst
        now = "2026-11-12T11:00:00"
        for i in range(4):
            txn = TransactionAudit(
                user_id="u_burst",
                amount=100.0,
                receiver=f"store{i}@okaxis",
                timestamp=now,
                channel="upi",
                note="",
                risk_score=10,
            )
            db.add(txn)
        db.commit()

        analyzer = TransactionAnalyzer(db=db)
        res = analyzer.analyze(
            user_id="u_burst",
            amount=50000.0,
            receiver="unknown@ybl",
            timestamp_str=now,
            note="urgent refund",
            db=db,
        )
        assert res["risk_level"] == "HIGH"
        names = [s.name for s in res["signals"]]
        assert any("Velocity" in n for n in names)
    finally:
        db.close()

def test_qr_analyzer_malformed_pa_and_negative_amount():
    analyzer = QrAnalyzer()
    # Missing pa
    res1 = analyzer.analyze("upi://pay?pn=Store&am=100&cu=INR")
    assert any("Malformed UPI" in s.name for s in res1["signals"])

    # Negative amount
    res2 = analyzer.analyze("upi://pay?pa=shop@okaxis&am=-500&cu=INR")
    assert any("Negative Payment Amount" in s.name for s in res2["signals"])

    # Malformed non-numeric amount
    res3 = analyzer.analyze("upi://pay?pa=shop@okaxis&am=abc&cu=INR")
    assert any("Malformed Amount" in s.name for s in res3["signals"])

    # Malformed VPA format without @
    res4 = analyzer.analyze("upi://pay?pa=invalid_vpa&cu=INR")
    assert any("Invalid VPA Format" in s.name for s in res4["signals"])

def test_explainer_llm_flow_and_fallback():
    signals = [Signal(name="Suspicious TLD", severity="high", detail="Uses .xyz domain")]

    # Fallback when LLM disabled
    exp_default = explain("url", "HIGH", signals, 87)
    assert "87/100" in exp_default
    assert "What scammers do here" in exp_default

    # When LLM enabled but mock returns error
    with patch.object(settings, "USE_LLM_EXPLAINER", True), patch.object(settings, "LLM_API_KEY", "test-key"):
        with patch("httpx.Client") as mock_client:
            mock_inst = MagicMock()
            mock_inst.__enter__.return_value = mock_inst
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"choices": [{"message": {"content": "Custom LLM explanation of the scam."}}]}
            mock_inst.post.return_value = mock_resp
            mock_client.return_value = mock_inst

            llm_text = explain("url", "HIGH", signals, 87)
            assert "Custom LLM explanation" in llm_text

        # Exception fallback
        with patch("httpx.Client", side_effect=Exception("API timeout")):
            fallback_text = explain("url", "HIGH", signals, 87)
            assert "87/100" in fallback_text
