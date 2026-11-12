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

---

## Addendum: Extras & Intelligence Layer (Person C)

Operates an independent microservice on **port 8001**:
- **Service URL**: `http://localhost:8001`
- **Swagger Documentation**: `http://localhost:8001/docs`

### 1. Analyze Message (SMS / WhatsApp / Email)
- **Method / Route**: `POST /api/ext/analyze/message`
- **Request Body**:
  ```json
  {
    "message": "Dear user your SBI KYC expires today. Update at http://sbi-kyc-update.top/login or account will be blocked",
    "source": "sms"
  }
  ```
  *(Supported sources: `sms`, `whatsapp`, `email`, `other`)*
- **Response**: Same shape as canonical contract with `"type": "message"` and additional `"extracted"` object:
  ```json
  {
    "risk_score": 92,
    "risk_level": "HIGH",
    "verdict": "Do not proceed",
    "signals": [
      {
        "name": "KYC Expiry Urgency Scam",
        "severity": "high",
        "detail": "Message creates false urgency regarding immediate bank KYC expiry or account blocking."
      }
    ],
    "explanation": "Plain-English explanation of detected phishing tactics.",
    "recommended_action": "Do not open any links or provide personal information.",
    "analyzed_at": "2026-11-12T10:30:00Z",
    "type": "message",
    "extracted": {
      "urls": ["http://sbi-kyc-update.top/login"],
      "upi_ids": [],
      "phone_numbers": [],
      "scam_category": "KYC_FRAUD"
    }
  }
  ```
  *(Supported categories: `KYC_FRAUD`, `LOTTERY`, `REFUND_SCAM`, `JOB_SCAM`, `FAKE_CUSTOMER_CARE`, `COLLECT_REQUEST`, `LOAN_SCAM`, `OTHER`, `NONE`)*

### 2. Analyze Voice Call Scam
- **Method / Route**: `POST /api/ext/analyze/voice`
- **Request Formats**:
  - JSON Transcript:
    ```json
    {
      "transcript": "This is CBI officer Sharma. Digital arrest warrant issued. Transfer funds to safe account.",
      "call_duration_seconds": 120,
      "caller_number": "+919876543210"
    }
    ```
  - Audio File Upload (`multipart/form-data`):
    - `audio_file`: binary audio (`.mp3`, `.wav`, `.m4a`, `.ogg`)
    - `caller_number`: optional phone string
- **Response**: Same shape as canonical contract with `"type": "voice"` and `"extracted"` object.

### 3. Submit Community Report
- **Method / Route**: `POST /api/ext/reports`
- **Request Body**:
  ```json
  {
    "target_type": "vpa",
    "value": "fraud@ybl",
    "reason": "Asked me to pay a fee for a refund"
  }
  ```
  *(Supported `target_type`: `url`, `vpa`, `phone`)*
- **Response**:
  ```json
  {
    "status": "recorded",
    "report_count": 3
  }
  ```

### 4. Reputation Lookup
- **Method / Route**: `GET /api/ext/reputation?value=fraud@ybl`
- **Response**:
  ```json
  {
    "value": "fraud@ybl",
    "report_count": 7,
    "reputation": "BAD",
    "last_reported": "2026-11-12T10:30:00Z"
  }
  ```
  *(Reputation levels: `UNKNOWN` [0 reports], `SUSPICIOUS` [1–2 reports], `BAD` [3+ reports])*

### 5. Community Blocklist
- **Method / Route**: `GET /api/ext/blocklist?type=vpa&limit=50`
- **Response**: Array of blocklisted entities with report counts and timestamps.

### 6. Threat Intelligence Statistics
- **Method / Route**: `GET /api/ext/stats`
- **Response**:
  ```json
  {
    "total_reports": 42,
    "by_category": { "vpa": 18, "url": 15, "phone": 9 },
    "top_signals": [
      { "signal": "Reported by community", "count": 24 }
    ],
    "daily_counts": [
      { "date": "2026-11-12", "count": 12 }
    ]
  }
  ```

### 7. Extras Health Check
- **Method / Route**: `GET /api/ext/health`
- **Response**:
  ```json
  {
    "status": "ok"
  }
  ```
