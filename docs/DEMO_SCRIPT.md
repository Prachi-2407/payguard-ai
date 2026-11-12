# PayGuard AI – 3-Minute Live Demo Script

**Theme**: *"Warn users BEFORE they pay. Prevention, not post-fraud detection."*  
**Audience**: Everyday UPI and digital payment users in India receiving suspicious WhatsApp links, fake QR codes, or urgent refund requests.

---

## ⏱️ Minute 0:00 – 0:45: The Problem & Phishing Link Interception

1. **Presenter Narration**:
   > *"In India, over ₹1,000 Crore is lost annually to UPI social-engineering scams. Fraudsters send urgent links on WhatsApp or SMS pretending to be electricity bill updates or bank KYC. PayGuard AI stops this before the user enters their PIN."*

2. **Action**:
   - Navigate to `http://localhost:5173`.
   - On the **Check Link** tab, click the sample:
     `http://paytm-secure-login.xyz/verify?id=123`
   - Click **Analyze Threat**.

3. **What Appears**:
   - An assertive **CRITICAL FRAUD ALERT** modal immediately covers the screen with sound cue:
     - **Risk Score**: 88/100 (HIGH RISK)
     - **Verdict**: *"Do not proceed"*
     - **Explanation**: Plain-English AI explanation identifying the `.xyz` deceptive extension and brand impersonation of Paytm.
     - **Safety Gating**: The user cannot proceed unless they manually check the risk acknowledgement box.
   - Click **Cancel Payment (Recommended)**. The payment is aborted safely.

---

## ⏱️ Minute 0:45 – 1:45: Deceptive QR Code & Collect Request Trap

1. **Presenter Narration**:
   > *"Scammers often send QR codes claiming 'Scan this to receive your cashback or refund'. But in UPI architecture, scanning a QR code and entering your PIN NEVER receives money—it only pays money."*

2. **Action**:
   - Switch to the **Scan QR** tab.
   - Show the pre-decoded interactive target in the demo gallery:
     `upi://pay?pa=refund-agent99@fakebank&pn=VIP Support&am=45000&cu=INR&tn=refund-collect`
   - Click **Send to Scanner** (or scan the image `sample_data/qr/malicious_collect_mismatch_qr.png`).
   - Notice the visual inspection card showing:
     - **Payee Name**: VIP Support
     - **Payee VPA**: `refund-agent99@fakebank` (mismatch flagged!)
     - **Pre-filled Amount**: ₹45,000 (abnormally high!)
     - **Note**: `refund-collect` (social-engineering trigger)
   - Click **Analyze QR Code**.

3. **What Appears**:
   - High-risk prevention modal blocks the user from scanning or authorizing the transaction.
   - Signals highlight: *Collect Money Trick*, *Payee Name vs VPA Mismatch*, *Excessive Pre-filled Amount*.

---

## ⏱️ Minute 1:45 – 2:30: Behavioral Anomaly Detection on Odd-Hour Transactions

1. **Presenter Narration**:
   > *"What if an impostor calls at night urging an immediate refund or lottery fee? PayGuard's behavioral ML engine evaluates isolation forests against user baselines."*

2. **Action**:
   - Switch to the **Check Transaction** tab.
   - Click sample:
     `High Anomaly: ₹49,999 Night Refund Alert` (Amount: ₹49,999, Time: 02:14 AM, Note: "urgent refund").
   - Click **Evaluate Transaction**.

3. **What Appears**:
   - Result Card displays **HIGH RISK (Score: 76/100)**:
     - Flagged for extreme amount vs user baseline (15.2x baseline average).
     - Flagged for high-risk midnight timing (02:14 AM).
     - Flagged for psychological urgency keyword: `"urgent refund"`.
   - **Recommended Action**: *"Stop immediately. Genuine refunds never require you to send money."*

---

## ⏱️ Minute 2:30 – 3:00: History Audit Log, Analytics & Multilingual UX

1. **Action**:
   - Switch to the **History & Insights** tab:
     - Observe the **Risk Level Distribution** bar chart (Clean vs Suspicious vs Dangerous).
     - View the **Timeline Threat Trend** line showing recent test scans.
     - Filter by type (`QR Codes`) or risk level (`HIGH`).
     - Click **View Details** on any past record to open the complete inspection drawer.
   - In the top header:
     - Toggle language to **हिन्दी (Hindi)**: Notice all verdicts, buttons, tabs, and alerts seamlessly render in Hindi for regional accessibility.
     - Toggle **Dark/Light Mode**: Notice clean fintech aesthetics in both modes.

2. **Conclusion**:
   > *"PayGuard AI protects citizens at the moment of payment—stopping cybercrime before the money leaves the account."*

