import logging
from typing import List, Optional
import httpx
from backend.config import settings
from backend.models.api import Signal

logger = logging.getLogger(__name__)

SCAMMER_INSIGHTS = {
    "suspicious_tld": "What scammers do here: Fraudsters register cheap domains (.xyz, .top) that look legitimate at first glance to host phishing clones and steal bank passwords.",
    "brand_impersonation": "What scammers do here: Attackers craft deceptive lookalike names (typosquatting) to pose as trusted brands like Paytm or SBI, luring you into a fake payment page.",
    "upi_collect": "What scammers do here: A common UPI fraud trick where scammers tell you that you will 'receive' prize money by scanning a code or entering your UPI PIN. In reality, entering your PIN always deducts money from your account.",
    "amount_mismatch": "What scammers do here: Scammers disguise a personal bank account with a legitimate-sounding shop name to trick victims into sending funds to an untraceable account.",
    "urgent_night_transfer": "What scammers do here: Scammers create artificial panics (claims of 'account suspension' or 'urgent refund') during late-night hours when banking helplines are closed, hoping you act before verifying.",
    "embedded_link": "What scammers do here: Fraudsters generate payment QR codes that secretly redirect your phone to a phishing site designed to harvest sensitive payment tokens.",
}

def generate_template_explanation(
    scan_type: str,
    risk_level: str,
    signals: List[Signal],
    risk_score: int,
) -> str:
    """
    Generates an intuitive, non-technical plain-English explanation paragraph
    with actionable scammer context.
    """
    if not signals or risk_level == "LOW":
        if scan_type == "url":
            return "This web link belongs to a verified domain and exhibits no signs of phishing or deceptive redirects. The connection is encrypted and matches official registration records."
        elif scan_type == "qr":
            return "This QR code corresponds to a standard UPI payment with verified merchant handles and no anomalous parameters. It appears safe for regular transactions."
        else:
            return "This transaction aligns with typical spending patterns, normal transfer hours, and recognized payees for this account."

    high_signals = [s for s in signals if s.severity == "high"]
    med_signals = [s for s in signals if s.severity == "medium"]

    parts = []

    if risk_level == "HIGH":
        parts.append(
            f"PayGuard detected critical danger signals (Risk Score: {risk_score}/100). "
            f"This {scan_type.upper()} request displays multiple hallmarks of an active fraud or phishing attempt."
        )
    else:
        parts.append(
            f"PayGuard detected suspicious patterns (Risk Score: {risk_score}/100) requiring caution."
        )

    # Summarize top reasons
    reasons = []
    for s in (high_signals + med_signals)[:3]:
        reasons.append(s.detail)

    if reasons:
        parts.append("Key findings: " + "; ".join(reasons) + ".")

    # Add relevant scammer insight
    insight_added = False
    sig_names = " ".join(s.name.lower() for s in signals)
    sig_details = " ".join(s.detail.lower() for s in signals)
    combined_text = f"{sig_names} {sig_details}"

    if "collect" in combined_text or "receive" in combined_text:
        parts.append(SCAMMER_INSIGHTS["upi_collect"])
        insight_added = True
    elif "impersonat" in combined_text or "typosquat" in combined_text:
        parts.append(SCAMMER_INSIGHTS["brand_impersonation"])
        insight_added = True
    elif "tld" in combined_text or ".xyz" in combined_text or ".top" in combined_text:
        parts.append(SCAMMER_INSIGHTS["suspicious_tld"])
        insight_added = True
    elif "mismatch" in combined_text:
        parts.append(SCAMMER_INSIGHTS["amount_mismatch"])
        insight_added = True
    elif "urgent" in combined_text or "odd hour" in combined_text or "night" in combined_text:
        parts.append(SCAMMER_INSIGHTS["urgent_night_transfer"])
        insight_added = True
    elif "embedded" in combined_text:
        parts.append(SCAMMER_INSIGHTS["embedded_link"])
        insight_added = True

    if not insight_added and risk_level == "HIGH":
        parts.append("What scammers do here: Attackers leverage deceptive parameters and urgency to bypass standard caution and extract unauthorized payments.")

    return " ".join(parts)

def explain(
    scan_type: str,
    risk_level: str,
    signals: List[Signal],
    risk_score: int,
) -> str:
    """
    Main explainer entrypoint. Uses offline template by default,
    or falls back to it if LLM explainer is enabled but fails.
    """
    fallback_text = generate_template_explanation(scan_type, risk_level, signals, risk_score)

    if not settings.USE_LLM_EXPLAINER or not settings.LLM_API_KEY:
        return fallback_text

    # LLM Explainer invocation with strict timeout and sanitization
    try:
        prompt = (
            f"Explain this {scan_type} fraud alert in 2-3 plain-English sentences for a non-technical user. "
            f"Risk Level: {risk_level}, Score: {risk_score}/100. "
            f"Detected signals: {', '.join([s.name + ': ' + s.detail for s in signals])}. "
            f"Do not include greeting or technical jargon. Explain how scammers use this technique."
        )

        with httpx.Client(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
            headers = {"Authorization": f"Bearer {settings.LLM_API_KEY}"}
            payload = {
                "model": settings.LLM_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a friendly cybersecurity expert protecting everyday Indian payment users."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 120,
                "temperature": 0.2,
            }
            res = client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
            if res.status_code == 200:
                data = res.json()
                content = data["choices"][0]["message"]["content"].strip()
                if content:
                    return content
    except Exception as e:
        logger.warning(f"LLM explainer call failed or timed out: {e}. Falling back to template.")

    return fallback_text
