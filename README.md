# PayGuard AI – Real-Time Intelligent Payment Fraud Prevention

> **Warn users BEFORE they pay.** PayGuard AI prevents financial fraud before authorization occurs for everyday UPI and digital payment users in India.

## Monorepo Architecture

```
payguard-ai/
├── backend/        # Person A: FastAPI, Scikit-Learn, ML Models, Threat Analyzers
├── frontend/       # Person B: React 18, Vite, Tailwind CSS, jsQR
├── docs/           # Architecture & API Contract specifications
├── sample_data/    # Verified test datasets (urls.json, qr_payloads.json, transactions.json)
└── README.md
```

## Quick Links
- **API Contract**: [`docs/API_CONTRACT.md`](file:///Users/prachi/Desktop/payguardAI/docs/API_CONTRACT.md)
- **Backend Documentation & Setup**: [`backend/README.md`](file:///Users/prachi/Desktop/payguardAI/backend/README.md)
- **Sample Datasets**: [`sample_data/`](file:///Users/prachi/Desktop/payguardAI/sample_data/)

## Quick Start (Backend)
```bash
# Setup virtual environment
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt

# Run tests
PYTHONPATH=. pytest backend/tests/ -v

# Start FastAPI server
PYTHONPATH=. uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API docs: `http://localhost:8000/docs`
