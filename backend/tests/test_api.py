import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_analyze_url_contract_shape():
    payload = {"url": "http://paytm-secure-login.xyz/verify?id=123"}
    response = client.post("/api/analyze/url", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "risk_score" in data
    assert isinstance(data["risk_score"], int)
    assert 0 <= data["risk_score"] <= 100

    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert "verdict" in data
    assert isinstance(data["signals"], list)
    for sig in data["signals"]:
        assert "name" in sig
        assert sig["severity"] in ["low", "medium", "high"]
        assert "detail" in sig

    assert "explanation" in data
    assert "recommended_action" in data
    assert "analyzed_at" in data
    assert data["type"] == "url"

def test_analyze_qr_contract_shape():
    payload = {"qr_payload": "upi://pay?pa=shop@okaxis&pn=Ram Store&am=5000&cu=INR"}
    response = client.post("/api/analyze/qr", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "risk_score" in data
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert "verdict" in data
    assert "signals" in data
    assert "explanation" in data
    assert "recommended_action" in data
    assert "analyzed_at" in data
    assert data["type"] == "qr"

def test_analyze_transaction_contract_shape():
    payload = {
        "user_id": "u101",
        "amount": 49999,
        "receiver": "unknown@ybl",
        "timestamp": "2026-11-12T02:14:00",
        "channel": "upi",
        "note": "urgent refund"
    }
    response = client.post("/api/analyze/transaction", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "risk_score" in data
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert "verdict" in data
    assert "signals" in data
    assert "explanation" in data
    assert "recommended_action" in data
    assert "analyzed_at" in data
    assert data["type"] == "transaction"

def test_history_endpoint_contract_and_filters():
    # Hit history
    response = client.get("/api/history?limit=10")
    assert response.status_code == 200
    items = response.json()
    assert isinstance(items, list)
    assert len(items) >= 1

    item = items[0]
    assert "id" in item
    assert "risk_score" in item
    assert "risk_level" in item
    assert "verdict" in item
    assert "signals" in item
    assert "explanation" in item
    assert "recommended_action" in item
    assert "analyzed_at" in item
    assert "type" in item

    # Filter by type
    res_url = client.get("/api/history?type=url")
    assert res_url.status_code == 200
    for it in res_url.json():
        assert it["type"] == "url"

def test_bad_input_returns_contract_error_format():
    # 1. Empty URL
    res = client.post("/api/analyze/url", json={"url": "   "})
    assert res.status_code == 400
    data = res.json()
    assert "error" in data
    assert data["code"] == 400

    # 2. Missing QR payload
    res_qr = client.post("/api/analyze/qr", json={})
    assert res_qr.status_code == 400
    data_qr = res_qr.json()
    assert "error" in data_qr
    assert data_qr["code"] == 400

    # 3. Negative amount in transaction
    res_txn = client.post(
        "/api/analyze/transaction",
        json={
            "user_id": "u101",
            "amount": -500,
            "receiver": "someone@okaxis",
            "timestamp": "2026-11-12T10:00:00",
        },
    )
    assert res_txn.status_code == 400
    data_txn = res_txn.json()
    assert "error" in data_txn
    assert data_txn["code"] == 400

def test_cors_headers():
    res = client.options(
        "/api/analyze/url",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://localhost:5173"
