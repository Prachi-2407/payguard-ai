import pytest
from unittest.mock import MagicMock, patch
from extras.app.analyzers.voice_analyzer import VoiceAnalyzer
from extras.app.services.transcription import AudioTranscriptionService

@pytest.fixture
def voice_analyzer():
    return VoiceAnalyzer()

@pytest.fixture
def transcription_service():
    return AudioTranscriptionService()

@pytest.mark.asyncio
async def test_bank_impersonation_voice(voice_analyzer, db_session):
    transcript = "Hello, I am calling from State Bank of India main branch. Your debit card and NetBanking services are expiring today. Please share your OTP to renew."
    res = await voice_analyzer.analyze(transcript, db=db_session)
    assert res.type == "voice"
    assert res.scam_category == "BANK_IMPERSONATION"
    assert res.risk_level == "HIGH"
    assert res.risk_score >= 70
    assert any("Banking Official" in s.name or "OTP" in s.name for s in res.signals)

@pytest.mark.asyncio
async def test_digital_arrest_voice(voice_analyzer, db_session):
    transcript = "You are placed under Digital Arrest by Supreme Court orders. You cannot disconnect this call or switch off your camera. Do not inform family or anyone."
    res = await voice_analyzer.analyze(transcript, db=db_session)
    assert res.scam_category == "DIGITAL_ARREST"
    assert res.risk_level == "HIGH"
    assert any("Digital Arrest" in s.name for s in res.signals)

@pytest.mark.asyncio
async def test_digital_arrest_hinglish_voice(voice_analyzer, db_session):
    transcript = "Aap is waqt Digital Arrest mein hain. Jab tak inquiry complete nahi hoti aap room se bahar nahi jayenge aur camera on rakhein. Security deposit transfer karein."
    res = await voice_analyzer.analyze(transcript, db=db_session)
    assert res.scam_category == "DIGITAL_ARREST"
    assert res.risk_level == "HIGH"

@pytest.mark.asyncio
async def test_otp_theft_voice(voice_analyzer, db_session):
    transcript = "Sir, I have triggered a security token to your mobile number. Please read out the 6-digit OTP so I can cancel the unauthorized debit."
    res = await voice_analyzer.analyze(transcript, db=db_session)
    assert res.scam_category == "OTP_FRAUD"
    assert res.risk_level == "HIGH"

@pytest.mark.asyncio
async def test_remote_access_scam_voice(voice_analyzer, db_session):
    transcript = "Apne phone mein AnyDesk app install kijiye aur jo 9 digit ka code screen par dikh raha hai wo mujhe batayein taaki error theek karein."
    res = await voice_analyzer.analyze(transcript, db=db_session)
    assert res.scam_category == "REMOTE_ACCESS_SCAM"
    assert res.risk_level == "HIGH"

@pytest.mark.asyncio
async def test_hard_negative_delivery_voice(voice_analyzer, db_session):
    transcript = "Hello sir, I am your Amazon delivery agent Manoj. I am standing outside your apartment gate. Please come down to collect your package."
    res = await voice_analyzer.analyze(transcript, db=db_session)
    assert res.scam_category == "NONE"
    assert res.risk_level == "LOW"
    assert res.risk_score <= 39

def test_audio_validation(transcription_service):
    # Invalid extension
    valid, err = transcription_service.validate_audio_file("recording.exe", 1000)
    assert valid is False
    assert "Unsupported audio format" in err

    # Empty file
    valid, err = transcription_service.validate_audio_file("recording.wav", 0)
    assert valid is False
    assert "empty" in err

    # Too large file (>15 MB)
    valid, err = transcription_service.validate_audio_file("recording.wav", 20 * 1024 * 1024)
    assert valid is False
    assert "exceeds maximum" in err

    # Valid WAV
    valid, err = transcription_service.validate_audio_file("test.wav", 1024)
    assert valid is True
    assert err is None

@pytest.mark.asyncio
async def test_mocked_audio_transcription(transcription_service):
    # Mock WhisperModel at the unit-test boundary
    mock_model = MagicMock()
    mock_segment = MagicMock()
    mock_segment.text = "Hello I am calling from bank please share your OTP"
    mock_segment.avg_logprob = -0.2
    mock_info = MagicMock()
    mock_info.language = "en"
    mock_info.duration = 4.5

    mock_model.transcribe.return_value = ([mock_segment], mock_info)

    svc = AudioTranscriptionService(whisper_model=mock_model)
    res = await svc.transcribe_audio(
        audio_bytes=b"RIFFdummydataWAVEfmt ",
        filename="call.wav",
        language="en",
    )
    assert res["transcript"] == "Hello I am calling from bank please share your OTP"
    assert res["language"] == "en"
    assert res["duration_seconds"] == 4.5
    assert res["source"] == "audio"

