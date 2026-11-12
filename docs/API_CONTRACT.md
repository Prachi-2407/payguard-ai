# PayGuard AI – Official API Contract

The API contract below is the single source of truth for both Person A (Backend) and Person B (Frontend).

## Base URLs
- **Backend Service**: `http://localhost:8000`
- **Frontend App**: `http://localhost:5173`
- **Interactive Swagger Documentation**: `http://localhost:8000/docs`

---

## Shared Response Format
All three analysis endpoints return the exact same canonical JSON schema:

```json
{
  "risk_score": 87,
  "risk_level": "HIGH",
  "verdict": "Do not proceed",
  "signals": [
    {
      "name": "Suspicious TLD",
      "severity": "high",
      "detail": "Domain uses .xyz, commonly abused in phishing"
    }
  ],
  "explanation": "Plain-English paragraph for non-technical users.",
  "recommended_action": "Do not pay. Verify via a known number.",
  "analyzed_at": "2026-11-12T10:30:00Z",
  "type": "url"
}
```

### Risk Tier Boundaries
- `LOW`: 0 – 39
- `MEDIUM`: 40 – 69
- `HIGH`: 70 – 100

---

## Endpoints

### 1. Analyze URL
- **Method / Route**: `POST /api/analyze/url`
- **Request Body**:
  ```json
  {
    "url": "http://paytm-secure-login.xyz/verify?id=123"
  }
  ```
- **Response**: Shared response format with `"type": "url"`.

### 2. Analyze QR Payload
- **Method / Route**: `POST /api/analyze/qr`
- **Request Body**:
  ```json
  {
    "qr_payload": "upi://pay?pa=shop@okaxis&pn=Ram Store&am=5000&cu=INR"
  }
  ```
- **Note**: QR images are decoded to text on the frontend (e.g. via jsQR); backend inspects the decoded string payload.
- **Response**: Shared response format with `"type": "qr"`.

### 3. Analyze Transaction Behavior
- **Method / Route**: `POST /api/analyze/transaction`
- **Request Body**:
  ```json
  {
    "user_id": "u101",
    "amount": 49999,
    "receiver": "unknown@ybl",
    "timestamp": "2026-11-12T02:14:00",
    "channel": "upi",
    "note": "urgent refund"
  }
  ```
- **Response**: Shared response format with `"type": "transaction"`.

### 4. Scan History
- **Method / Route**: `GET /api/history?limit=20&type=url&risk_level=HIGH`
- **Query Parameters**:
  - `limit` *(int, default: 20)*: Maximum records to return (newest first).
  - `type` *(string, optional)*: Filter by `url`, `qr`, or `transaction`.
  - `risk_level` *(string, optional)*: Filter by `LOW`, `MEDIUM`, or `HIGH`.
- **Response**: Array of scan result objects, identical to the shared response schema plus an integer `"id"`.

### 5. Health Check
- **Method / Route**: `GET /api/health`
- **Response**:
  ```json
  {
    "status": "ok"
  }
  ```

### 6. Standard Error Format
All 4xx validation or client errors return:
```json
{
  "error": "Detailed error message",
  "code": 400
}
```
