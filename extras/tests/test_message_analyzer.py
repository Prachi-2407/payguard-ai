import pytest
from extras.app.analyzers.message_analyzer import MessageAnalyzer
from extras.app.services.url_service import local_url_heuristics

@pytest.fixture
def analyzer():
    return MessageAnalyzer()

@pytest.mark.asyncio
async def test_kyc_fraud_detection(analyzer, db_session):
    msg = "Dear user your SBI KYC expires today. Update at http://sbi-kyc-update.top/login or account will be blocked"
    res = await analyzer.analyze(msg, source="sms", db=db_session)
    assert res.type == "message"
    assert res.extracted.scam_category == "KYC_FRAUD"
    assert res.risk_level == "HIGH"
    assert res.risk_score >= 70
    assert "http://sbi-kyc-update.top/login" in res.extracted.urls
    assert any("Suspension" in s.name or "Urgency" in s.name for s in res.signals)

@pytest.mark.asyncio
async def test_lottery_scam_detection(analyzer, db_session):
    msg = "Congratulations! You won Rs 25,00,000 in KBC Lucky Draw. Contact WhatsApp +919876543210 to claim prize"
    res = await analyzer.analyze(msg, source="whatsapp", db=db_session)
    assert res.extracted.scam_category == "LOTTERY"
    assert res.risk_level == "HIGH"
    assert "+919876543210" in res.extracted.phone_numbers
    assert any("Lottery" in s.name for s in res.signals)

@pytest.mark.asyncio
async def test_job_scam_detection(analyzer, db_session):
    msg = "Part-time job offer: Earn 5,000 daily by liking YouTube videos and rating hotels. Contact HR on WhatsApp +918765432109"
    res = await analyzer.analyze(msg, source="whatsapp", db=db_session)
    assert res.extracted.scam_category == "JOB_SCAM"
    assert res.risk_level in ("MEDIUM", "HIGH")
    assert "+918765432109" in res.extracted.phone_numbers
    assert any("Part-Time" in s.name for s in res.signals)

@pytest.mark.asyncio
async def test_collect_request_trap(analyzer, db_session):
    msg = "You have received a collect request of Rs 4,999 on PhonePe. Approve request and enter your secret UPI PIN to receive cashback"
    res = await analyzer.analyze(msg, source="sms", db=db_session)
    assert res.extracted.scam_category == "COLLECT_REQUEST"
    assert res.risk_level == "HIGH"
    assert any("Collect Request" in s.name or "PIN" in s.name for s in res.signals)

@pytest.mark.asyncio
async def test_hard_negative_genuine_bank_otp(analyzer, db_session):
    msg = "482910 is your OTP for transaction of INR 1,500.00 at Swiggy using HDFC Bank Card ending 1234. OTP is valid for 10 mins. Do not share with anyone."
    res = await analyzer.analyze(msg, source="sms", db=db_session)
    assert res.extracted.scam_category == "NONE"
    assert res.risk_level == "LOW"
    assert res.risk_score <= 39

@pytest.mark.asyncio
async def test_hard_negative_delivery_notification(analyzer, db_session):
    msg = "Your Amazon package with tracking ID 4819203 is out for delivery today. Delivery agent: Ramesh (+919876501234). Share delivery code 5812 only at doorstep."
    res = await analyzer.analyze(msg, source="sms", db=db_session)
    assert res.extracted.scam_category == "NONE"
    assert res.risk_level == "LOW"

@pytest.mark.asyncio
async def test_local_url_heuristics_fallback():
    url = "http://sbi-secure-update.top/login"
    heuristics = local_url_heuristics(url)
    assert heuristics["risk_score"] >= 70
    signal_names = [s["name"] for s in heuristics["signals"]]
    assert any("Suspicious TLD" in n for n in signal_names)
    assert any("Brand/Credential" in n for n in signal_names)
