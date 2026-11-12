import pytest
from fastapi.testclient import TestClient

def test_health_endpoint(client: TestClient):
    resp = client.get("/api/ext/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

def test_analyze_message_contract_shape(client: TestClient):
    payload = {
        "message": "Dear user your SBI KYC expires today. Update at http://sbi-kyc-update.top/login or account will be blocked",
        "source": "sms"
    }
    resp = client.post("/api/ext/analyze/message", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    # Exact contract keys
    assert "risk_score" in data
    assert "risk_level" in data
    assert "verdict" in data
    assert "signals" in data
    assert "explanation" in data
    assert "recommended_action" in data
    assert "analyzed_at" in data
    assert data["type"] == "message"
    assert "extracted" in data

    # Extracted sub-keys
    extracted = data["extracted"]
    assert "urls" in extracted
    assert "upi_ids" in extracted
    assert "phone_numbers" in extracted
    assert "scam_category" in extracted
    assert extracted["scam_category"] == "KYC_FRAUD"

def test_community_reports_contract(client: TestClient):
    payload = {
        "target_type": "vpa",
        "value": "scam.target@ybl",
        "reason": "Demanded advance payment for lottery"
    }
    resp = client.post("/api/ext/reports", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "report_count" in data
    assert data["status"] in ("recorded", "duplicate_ignored")

def test_reputation_contract(client: TestClient):
    resp = client.get("/api/ext/reputation?value=scam.target@ybl")
    assert resp.status_code == 200
    data = resp.json()
    assert "value" in data
    assert "report_count" in data
    assert "reputation" in data
    assert data["reputation"] in ("BAD", "SUSPICIOUS", "UNKNOWN")

def test_blocklist_contract(client: TestClient):
    resp = client.get("/api/ext/blocklist?type=vpa")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    if data:
        item = data[0]
        assert "value" in item
        assert "type" in item
        assert "report_count" in item
        assert "first_reported" in item
        assert "last_reported" in item

def test_stats_contract(client: TestClient):
    resp = client.get("/api/ext/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_reports" in data
    assert "by_category" in data
    assert "top_signals" in data
    assert "daily_counts" in data

def test_voice_transcript_contract_shape(client: TestClient):
    payload = {
        "transcript": "Hello I am calling from State Bank of India. Your account will be blocked. Share your OTP now.",
        "language": "en"
    }
    resp = client.post("/api/ext/analyze/voice", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "voice"
    assert "risk_score" in data
    assert "risk_level" in data
    assert "transcript" in data
    assert "scam_category" in data
    assert "transcription_metadata" in data
    assert data["transcription_metadata"]["source"] == "transcript"

def test_voice_audio_upload_endpoint(client: TestClient):
    from unittest.mock import patch
    with patch("extras.app.api.voice.transcription_service.transcribe_audio") as mock_transcribe:
        async def _mock_transcribe(*args, **kwargs):
            return {
                "transcript": "Hello calling from State Bank of India please share your OTP",
                "language": "en",
                "duration_seconds": 3.2,
                "confidence": 0.95,
                "source": "audio",
            }
        mock_transcribe.side_effect = _mock_transcribe
        files = {"audio": ("sample.wav", b"RIFFmockaudioWAVE", "audio/wav")}
        resp = client.post("/api/ext/analyze/voice", files=files, data={"language": "en"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "voice"
        assert data["transcription_metadata"]["source"] == "audio"

def test_validation_error_shape(client: TestClient):
    # Blank message should return 400 with { error: "...", code: 400 }
    resp = client.post("/api/ext/analyze/message", json={"message": "   "})
    assert resp.status_code == 400
    data = resp.json()
    assert "error" in data
    assert data["code"] == 400

def test_offline_backend_fallback(client: TestClient):
    # Main backend on 8000 is intentionally offline during this unit test
    # Extras service should gracefully evaluate URL heuristics without crashing
    payload = {
        "message": "Click http://sbi-kyc-verify.top/login to update details",
        "source": "sms"
    }
    resp = client.post("/api/ext/analyze/message", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_level"] in ("MEDIUM", "HIGH")
    assert any("Link:" in s["name"] for s in data["signals"])
