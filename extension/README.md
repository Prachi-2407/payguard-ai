# PayGuard AI – Chrome Browser Extension (Manifest V3)

A lightweight, real-time security extension that protects digital payment and web banking users against phishing links, fraudulent UPI collect traps, and deceptive scam messages.

---

## 🌟 Key Features

1. **Context Menu Inspector ("Check with PayGuard AI")**:
   - Right-click any hyperlink on any web page to inspect destination safety.
   - Select suspicious message text on WhatsApp Web, Gmail, or forums, right-click, and analyze intent via the Message Scam Analyzer.
2. **Interactive Popup UI**:
   - Clean risk gauge (0–100), categorical verdict (`Safe to proceed`, `Proceed with caution`, `Do not proceed`), risk badge, top 3 detected signals, and plain-English actionable recommendations.
3. **Automated WhatsApp Web & Gmail Badging**:
   - Non-invasive content script detects links inside incoming emails (`mail.google.com`) and messages (`web.whatsapp.com`).
   - Injects a small, colored badge (`🛡️ SAFE`, `⚠️ CAUTION`, `🚨 DANGER`) next to visible links without altering message text or interfering with navigation.
4. **10-Minute Threat Cache**:
   - Background service worker caches URL assessments for 10 minutes to eliminate redundant network round-trips.
5. **High-Risk Native Notifications**:
   - Triggers a desktop notification whenever a critical threat (`risk_score >= 70`) is flagged via context menu.
6. **Configurable Endpoints**:
   - An Options page lets users customize both the Main Gateway (`http://localhost:8000`) and the Extras Intelligence Service (`http://localhost:8001`).

---

## 🔒 Permissions & Privacy Practices

PayGuard AI strictly adheres to the principle of least privilege:

| Permission | Purpose |
|------------|---------|
| `contextMenus` | Adds the right-click "Check with PayGuard AI" inspection option. |
| `storage` | Stores user API endpoint preferences and cached assessment results locally. |
| `notifications` | Alerts user when high-risk phishing or scam links are encountered. |
| `activeTab` | Detects current page URL for quick one-click inspection in the popup. |

### Privacy Commitments:
- **Zero Keystroke / Chat Logging**: The extension never reads, stores, or logs chat history, contact lists, or personal correspondence.
- **Link-Only Transmission**: Automated badging transmits *only* the specific target URL string to the inspection engine; no ambient message context or sender information is ever transmitted.
- **Local Heuristics Fallback**: If the backend service is offline, lightweight lexical heuristics run completely inside the local browser without failing.

---

## 🚀 Setup & Load-Unpacked Instructions

1. Open Google Chrome and enter `chrome://extensions/` in the address bar.
2. Toggle on **Developer mode** in the top right corner.
3. Click the **Load unpacked** button.
4. Select the `extension/` directory located inside this repository.
5. The extension icon (🛡️) will now appear in your browser extensions toolbar. Pin it for quick access.

---

## ⚙️ API Configuration

By default, the extension connects to local services:
- **Main Backend Gateway**: `http://localhost:8000`
- **Extras Intelligence Service**: `http://localhost:8001`

To change endpoints:
1. Right-click the PayGuard AI icon in your browser toolbar and choose **Options** (or click the gear ⚙️ icon in the popup).
2. Enter your custom API base URLs and click **Save Settings**.

---

## 🧪 Local Demonstration & Testing

A local HTML playground is provided in `extension/test_page/index.html`:
1. Open Chrome and press `Cmd+O` (or `Ctrl+O`).
2. Open `file:///Users/shreya1/paygaurd/payguard-ai/extension/test_page/index.html`.
3. Test features:
   - Notice the automatic security badges beside legitimate bank links (`https://onlinesbi.sbi`) vs. phishing links (`http://sbi-kyc-update.top/login`).
   - Select the sample scam message text, right-click, and select **"Check with PayGuard AI"**.
   - Open the popup by clicking the extension icon to verify score and top 3 signals.

