# PayGuard AI – Frontend Application

**PayGuard AI Frontend** is a modern, responsive, trustworthy React 18 application designed to protect everyday UPI and digital payment users in India by warning them **before** they authorize payments.

---

## 🚀 Features

- **Multi-Vector Payment Analysis**:
  - **Check Link**: Detects phishing, brand typosquatting (`.xyz`, `.top`), and deceptive redirects.
  - **Scan QR**: Real-time webcam scanning via `jsQR` and image file upload. Decodes and displays UPI payload parameters before analysis.
  - **Check Transaction**: Evaluates amount anomalies, off-hours transfers (e.g. 2:00 AM), new receivers, and urgency pressure notes.
- **Real-Time Warning Modal (Safety Gating)**:
  - **HIGH Risk**: Full-screen blocking alert modal requiring user confirmation before proceeding, with a prominent "Cancel Payment" primary action, audio cue, and ARIA live region.
  - **MEDIUM Risk**: Amber caution state.
  - **LOW Risk**: Calm green verified state.
- **Shared Circular Gauge Result Card**:
  - 0–100 threat score gauge with dynamic color rendering.
  - Plain-English AI explanation tailored for non-technical users.
  - Actionable recommendation box ("Do not pay. Verify via a known number.").
  - Categorized signals list with severity badges.
  - Copy and native share triggers.
- **History & Threat Insights**:
  - Audit log table with search, type filters, and risk-level filters.
  - Recharts risk distribution bar chart and timeline score trend line.
  - Detail drawer to inspect full historical reports.
- **i18n & Accessibility**:
  - English and Hindi (हिन्दी) dual-language switch.
  - Dark mode and light mode toggle with localStorage persistence.
  - WCAG-AA compliant contrast, keyboard navigation, and ARIA labels.
- **Interactive QR Code Target Gallery**:
  - Pre-rendered test QR codes (safe merchant, high-value collect fraud, phishing link) for testing webcam scanners.

---

## 🛠️ Tech Stack

- **Framework**: React 18, Vite
- **Styling**: Tailwind CSS, Lucide React Icons
- **QR Decoding**: jsQR
- **Data Visualization**: Recharts
- **Testing**: Vitest, React Testing Library, jsdom
- **QR Generation**: QRCode (Node script)

---

## 📦 Setup & Running

### 1. Install Dependencies
```bash
npm install
```

### 2. Generate Sample QR Code Images
Generates high-resolution sample QR code images into `sample_data/qr/`:
```bash
npm run gen:qr
```

### 3. Start Development Server
```bash
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

### 4. Run Tests
```bash
npm test
```

### 5. Production Build
```bash
npm run build
```

---

## 🔄 Switching Between Mock API and Real Backend

By default, the frontend can run fully standalone using an embedded, contract-compliant mock engine (`src/api/mockApi.js`) that simulates realistic network latency (400–900ms) and heuristic threat scoring.

To connect to the live Python FastAPI backend:

1. Open `src/config.js` and set:
   ```javascript
   export const USE_MOCK = false;
   export const API_BASE_URL = 'http://localhost:8000';
   ```
   *Alternatively*, set environment variables in a `.env` file:
   ```env
   VITE_USE_MOCK=false
   VITE_API_BASE_URL=http://localhost:8000
   ```
2. Start the FastAPI backend on port `8000`:
   ```bash
   cd ../backend
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```
3. The frontend `src/api/client.js` will immediately route all requests to the live backend. If the backend is stopped, an `OfflineBanner` automatically informs the user.

---

## 🐳 Docker Deployment

Build and run the frontend via Docker:
```bash
docker build -t payguard-frontend .
docker run -p 5173:5173 payguard-frontend
```

