// src/api/mockApi.js
// Follows the PayGuard AI contract field-for-field with realistic heuristics and latency

let mockHistory = [
  {
    id: 1,
    risk_score: 88,
    risk_level: "HIGH",
    verdict: "Do not proceed",
    signals: [
      { name: "Suspicious TLD", severity: "high", detail: "Domain uses .xyz, commonly abused in phishing scams" },
      { name: "Brand Impersonation", severity: "high", detail: "Domain mimics Paytm (similarity 91%)" },
      { name: "Urgency Keyword", severity: "medium", detail: "URL contains pressure term 'verify'" }
    ],
    explanation: "This link strongly mimics Paytm to steal your credentials or initiate unauthorized payments. The .xyz extension and 'verify' keyword are classic indicators of a fraudulent phishing site.",
    recommended_action: "Do not click or enter credentials. Verify directly through the official Paytm app.",
    analyzed_at: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    type: "url"
  },
  {
    id: 2,
    risk_score: 12,
    risk_level: "LOW",
    verdict: "Safe to proceed",
    signals: [
      { name: "Verified Merchant VPA", severity: "low", detail: "VPA matches recognized retailer handle" },
      { name: "HTTPS Transport", severity: "low", detail: "Secure channel with valid certificate" }
    ],
    explanation: "This QR code points to a verified merchant handle and has a normal retail payment pattern. No deceptive signals detected.",
    recommended_action: "Safe to proceed. Verify the merchant name on your payment app screen before entering UPI PIN.",
    analyzed_at: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    type: "qr"
  },
  {
    id: 3,
    risk_score: 76,
    risk_level: "HIGH",
    verdict: "Do not proceed",
    signals: [
      { name: "Extreme Amount vs Baseline", severity: "high", detail: "Amount ₹49,999 is 15.2x user's baseline average" },
      { name: "Odd-Hour Transaction", severity: "medium", detail: "Transaction initiated during high-risk window (02:14 AM)" },
      { name: "Pressure Keyword", severity: "medium", detail: "Note contains urgency term 'urgent refund'" }
    ],
    explanation: "This transaction shows abnormal activity: an extraordinarily high transfer amount initiated at 2:14 AM to an unknown receiver with an urgency note. This matches common UPI refund fraud.",
    recommended_action: "Stop immediately. Genuine refunds never require you to send money or enter your UPI PIN.",
    analyzed_at: new Date(Date.now() - 1000 * 60 * 90).toISOString(),
    type: "transaction"
  }
];

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const randomLatency = () => Math.floor(Math.random() * (900 - 400 + 1)) + 400;

export async function mockAnalyzeUrl(payload) {
  await sleep(randomLatency());
  const url = (payload?.url || '').trim();
  if (!url) {
    const error = new Error("Empty URL provided");
    error.status = 400;
    error.data = { error: "URL field cannot be empty", code: 400 };
    throw error;
  }

  const lower = url.toLowerCase();
  const signals = [];
  let score = 15;

  if (lower.includes('.xyz') || lower.includes('.top') || lower.includes('.click') || lower.includes('.tk')) {
    signals.push({ name: "Suspicious TLD", severity: "high", detail: "Domain uses high-abuse top-level extension" });
    score += 40;
  }

  if (lower.includes('paytm') || lower.includes('phonepe') || lower.includes('gpay') || lower.includes('sbi') || lower.includes('hdfc')) {
    if (!lower.includes('paytm.com') && !lower.includes('phonepe.com') && !lower.includes('google.com') && !lower.includes('onlinesbi.sbi')) {
      signals.push({ name: "Brand Impersonation", severity: "high", detail: "Domain mimics popular financial brand without official authorization" });
      score += 45;
    }
  }

  if (lower.includes('verify') || lower.includes('kyc') || lower.includes('refund') || lower.includes('urgent') || lower.includes('blocked') || lower.includes('lottery')) {
    signals.push({ name: "Suspicious Keyword", severity: "medium", detail: "URL path or query contains urgent social-engineering keywords" });
    score += 25;
  }

  if (!lower.startsWith('https://')) {
    signals.push({ name: "Insecure Connection", severity: "medium", detail: "Link uses unencrypted HTTP protocol" });
    score += 15;
  }

  score = Math.min(100, Math.max(0, score));

  let risk_level = "LOW";
  let verdict = "Safe to proceed";
  let recommended_action = "Link appears normal. Still check browser address bar before entering credentials.";
  let explanation = "No deceptive indicators or known scam signatures detected on this URL.";

  if (score >= 70) {
    risk_level = "HIGH";
    verdict = "Do not proceed";
    recommended_action = "Do not click or enter credentials. Close this page and report the sender.";
    explanation = "This link exhibits severe phishing indicators including brand impersonation, deceptive domain extensions, or urgent credential-harvesting triggers designed to compromise your accounts.";
  } else if (score >= 40) {
    risk_level = "MEDIUM";
    verdict = "Proceed with caution";
    recommended_action = "Double-check the exact domain name before proceeding or submitting any information.";
    explanation = "This link carries warning signs such as unencrypted traffic or suspicious naming patterns. Proceed with extreme vigilance.";
  }

  if (signals.length === 0) {
    signals.push({ name: "Valid Structure", severity: "low", detail: "Domain structure and HTTPS configuration appear standard" });
  }

  const result = {
    risk_score: score,
    risk_level,
    verdict,
    signals,
    explanation,
    recommended_action,
    analyzed_at: new Date().toISOString(),
    type: "url"
  };

  mockHistory.unshift({ ...result, id: Date.now() });
  return result;
}

export async function mockAnalyzeQr(payload) {
  await sleep(randomLatency());
  const qr = (payload?.qr_payload || '').trim();
  if (!qr) {
    const error = new Error("Empty QR payload provided");
    error.status = 400;
    error.data = { error: "QR payload cannot be empty", code: 400 };
    throw error;
  }

  const signals = [];
  let score = 10;
  const lower = qr.toLowerCase();

  if (lower.startsWith('upi://pay')) {
    const urlObj = new URL(qr);
    const pa = urlObj.searchParams.get('pa') || '';
    const pn = urlObj.searchParams.get('pn') || '';
    const am = parseFloat(urlObj.searchParams.get('am') || '0');
    const cu = urlObj.searchParams.get('cu') || 'INR';

    if (cu !== 'INR') {
      signals.push({ name: "Unusual Currency", severity: "high", detail: `Currency set to ${cu} instead of INR` });
      score += 50;
    }

    if (am >= 25000) {
      signals.push({ name: "Excessive Pre-filled Amount", severity: "high", detail: `Pre-set transfer of ₹${am.toLocaleString('en-IN')} is unusually high for standard QR codes` });
      score += 45;
    } else if (am > 5000) {
      signals.push({ name: "High Pre-filled Amount", severity: "medium", detail: `Pre-set transfer of ₹${am.toLocaleString('en-IN')}` });
      score += 20;
    }

    if (pn && pa && !pa.toLowerCase().includes(pn.split(' ')[0].toLowerCase().slice(0, 4))) {
      signals.push({ name: "Payee Name vs VPA Mismatch", severity: "medium", detail: `Display name '${pn}' diverges from address '${pa}'` });
      score += 25;
    }

    if (lower.includes('collect') || lower.includes('receive') || lower.includes('refund')) {
      signals.push({ name: "Collect Money Trick", severity: "high", detail: "Note tries to trick you into believing scanning will receive money. In UPI, scanning ALWAYS pays money." });
      score += 50;
    }
  } else if (lower.startsWith('http://') || lower.startsWith('https://')) {
    signals.push({ name: "Embedded URL in QR", severity: "medium", detail: "QR contains an external website URL instead of direct UPI payment link" });
    score += 35;
    if (lower.includes('.xyz') || lower.includes('login') || lower.includes('verify')) {
      signals.push({ name: "Suspicious Target Link", severity: "high", detail: "Destination domain has phishing characteristics" });
      score += 45;
    }
  }

  score = Math.min(100, Math.max(0, score));

  let risk_level = "LOW";
  let verdict = "Safe to proceed";
  let recommended_action = "Verify the recipient name shown on your UPI app screen before entering your PIN.";
  let explanation = "Standard payment QR code. Always remember: entering your UPI PIN always deducts money from your account.";

  if (score >= 70) {
    risk_level = "HIGH";
    verdict = "Do not proceed";
    recommended_action = "Do not pay. Never enter your UPI PIN. This request appears fraudulent.";
    explanation = "Severe risk detected! Scammers frequently use modified QR codes with disguised amounts, collect-request deceptions, or malicious redirection links to drain bank accounts.";
  } else if (score >= 40) {
    risk_level = "MEDIUM";
    verdict = "Proceed with caution";
    recommended_action = "Check payee address and amount carefully on your payment confirmation screen.";
    explanation = "This QR code presents caution signals such as name-handle discrepancies or pre-set payment amounts.";
  }

  if (signals.length === 0) {
    signals.push({ name: "Standard Payment Link", severity: "low", detail: "Standard UPI intent structure verified" });
  }

  const result = {
    risk_score: score,
    risk_level,
    verdict,
    signals,
    explanation,
    recommended_action,
    analyzed_at: new Date().toISOString(),
    type: "qr"
  };

  mockHistory.unshift({ ...result, id: Date.now() });
  return result;
}

export async function mockAnalyzeTransaction(payload) {
  await sleep(randomLatency());
  const amount = Number(payload?.amount);
  if (isNaN(amount) || amount <= 0) {
    const error = new Error("Invalid transaction amount");
    error.status = 400;
    error.data = { error: "Transaction amount must be a positive number", code: 400 };
    throw error;
  }

  const signals = [];
  let score = 8;
  const note = (payload?.note || '').toLowerCase();
  const receiver = (payload?.receiver || '').toLowerCase();
  const timestamp = payload?.timestamp ? new Date(payload.timestamp) : new Date();
  const hour = timestamp.getHours();

  if (amount >= 40000) {
    signals.push({ name: "High Amount vs Normal", severity: "high", detail: `Amount ₹${amount.toLocaleString('en-IN')} approaches maximum daily UPI limit` });
    score += 40;
  } else if (amount >= 15000) {
    signals.push({ name: "Elevated Amount", severity: "medium", detail: `Amount ₹${amount.toLocaleString('en-IN')} is significantly above everyday average` });
    score += 25;
  }

  if (hour >= 1 && hour <= 5) {
    signals.push({ name: "Unusual Transaction Hour", severity: "medium", detail: `Initiated at ${hour.toString().padStart(2, '0')}:${timestamp.getMinutes().toString().padStart(2, '0')}, an uncommon time for retail transfers` });
    score += 25;
  }

  if (note.includes('urgent') || note.includes('refund') || note.includes('winner') || note.includes('kyc') || note.includes('lottery')) {
    signals.push({ name: "Psychological Urgency Trigger", severity: "high", detail: `Note contains pressure keywords ('${note}') associated with social engineering` });
    score += 35;
  }

  if (receiver.includes('unknown') || receiver.includes('claim') || receiver.includes('support')) {
    signals.push({ name: "Suspicious Payee Handle", severity: "medium", detail: `Receiver address '${receiver}' contains keywords used in impostor fraud` });
    score += 20;
  }

  score = Math.min(100, Math.max(0, score));

  let risk_level = "LOW";
  let verdict = "Safe to proceed";
  let recommended_action = "Transaction appears consistent with typical user history.";
  let explanation = "Payment parameters match expected baseline profile. No behavioral anomalies detected.";

  if (score >= 70) {
    risk_level = "HIGH";
    verdict = "Do not proceed";
    recommended_action = "Stop payment. Confirm the recipient's identity via a trusted phone call or official channels.";
    explanation = "Severe behavioral anomaly flagged. A combination of unusual timing, extreme transfer value, and urgency keywords strongly suggests active deception or social-engineering coercion.";
  } else if (score >= 40) {
    risk_level = "MEDIUM";
    verdict = "Proceed with caution";
    recommended_action = "Verify why this payment is needed before authorizing with your UPI PIN.";
    explanation = "This transaction deviates from typical behavior patterns. Verify recipient and amount carefully.";
  }

  if (signals.length === 0) {
    signals.push({ name: "Baseline Transaction", severity: "low", detail: "Parameters align with typical user profile" });
  }

  const result = {
    risk_score: score,
    risk_level,
    verdict,
    signals,
    explanation,
    recommended_action,
    analyzed_at: new Date().toISOString(),
    type: "transaction"
  };

  mockHistory.unshift({ ...result, id: Date.now() });
  return result;
}

export async function mockGetHistory(limit = 20, type = null, risk_level = null) {
  await sleep(randomLatency() / 2);
  let list = [...mockHistory];
  if (type) {
    list = list.filter(i => i.type.toLowerCase() === type.toLowerCase());
  }
  if (risk_level) {
    list = list.filter(i => i.risk_level.toUpperCase() === risk_level.toUpperCase());
  }
  return list.slice(0, Number(limit) || 20);
}

export async function mockGetHealth() {
  await sleep(150);
  return { status: "ok" };
}

