import re
import urllib.parse
from typing import Dict, Any, List, Optional
from backend.config import settings
from backend.models.api import Signal
from backend.analyzers.url_analyzer import UrlAnalyzer
from backend.core.risk_engine import blend_risk
from backend.core.explainer import explain

UPI_COLLECT_PATTERNS = [
    "collect", "receive money", "accept money", "claim reward", "enter pin to receive",
    "refund claim", "cashback reward", "win money", "pin to get", "receive cashback"
]

class QrAnalyzer:
    def __init__(self, url_analyzer: Optional[UrlAnalyzer] = None):
        self.url_analyzer = url_analyzer or UrlAnalyzer()

    def analyze(self, qr_payload: str) -> Dict[str, Any]:
        """
        Analyzes a decoded QR code payload string:
        - UPI deep links (upi://pay?...)
        - Embedded HTTP(S) links
        - Plain text / non-payment payloads
        """
        payload = qr_payload.strip()
        signals: List[Signal] = []

        # Case 1: Plain URL payload (e.g. http://... or https://...)
        if payload.startswith(("http://", "https://")):
            url_result = self.url_analyzer.analyze(payload)
            signals = [
                Signal(
                    name="Embedded Web Link in QR",
                    severity="medium",
                    detail="QR code opens an external web link rather than a verified UPI payment window.",
                )
            ] + url_result["signals"]

            # Compute blended score for QR wrapping URL
            risk_score, risk_level, verdict, action = blend_risk(
                signals=signals,
                ml_probability=url_result.get("ml_probability", 0.0),
                scan_type="qr",
            )
            explanation = explain("qr", risk_level, signals, risk_score)
            return {
                "risk_score": risk_score,
                "risk_level": risk_level,
                "verdict": verdict,
                "signals": signals,
                "explanation": explanation,
                "recommended_action": action,
                "type": "qr",
            }

        # Case 2: UPI Deep Link
        if payload.lower().startswith("upi://"):
            return self._analyze_upi_payload(payload)

        # Case 3: Non-UPI and Non-URL (Plain text / WiFi / Contact / Malformed)
        return self._analyze_non_upi_payload(payload)

    def _analyze_upi_payload(self, upi_uri: str) -> Dict[str, Any]:
        signals: List[Signal] = []

        # Parse query params
        parsed = urllib.parse.urlparse(upi_uri)
        params = urllib.parse.parse_qs(parsed.query)

        def get_param(name: str) -> str:
            val = params.get(name, [""])[0]
            return val.strip()

        pa = get_param("pa") # Payee VPA
        pn = get_param("pn") # Payee Name
        am_str = get_param("am") # Amount
        cu = get_param("cu") # Currency
        tn = get_param("tn") # Transaction Note
        mc = get_param("mc") # Merchant Code
        mode = get_param("mode")

        # 1. Missing payee address
        if not pa:
            signals.append(
                Signal(
                    name="Malformed UPI Payload",
                    severity="high",
                    detail="UPI payload is missing the mandatory payee address ('pa').",
                )
            )

        # 2. Currency check
        if cu and cu.upper() != "INR":
            signals.append(
                Signal(
                    name="Non-INR Currency",
                    severity="high",
                    detail=f"UPI requires Indian Rupee ('INR') currency, but found '{cu}'.",
                )
            )

        # 3. Amount checks
        if am_str:
            try:
                am_val = float(am_str)
                if am_val < 0:
                    signals.append(
                        Signal(
                            name="Negative Payment Amount",
                            severity="high",
                            detail=f"Payload contains an invalid negative amount ('{am_val}').",
                        )
                    )
                elif am_val >= 50000.0:
                    signals.append(
                        Signal(
                            name="High Pre-filled Amount",
                            severity="high",
                            detail=f"QR code requests a very large payment of ₹{am_val:,.2f}; high risk for QR tampering.",
                        )
                    )
                elif am_val >= 10000.0:
                    signals.append(
                        Signal(
                            name="Elevated Pre-filled Amount",
                            severity="medium",
                            detail=f"QR code pre-fills an amount of ₹{am_val:,.2f}.",
                        )
                    )
            except ValueError:
                signals.append(
                    Signal(
                        name="Malformed Amount Value",
                        severity="medium",
                        detail=f"Amount parameter '{am_str}' is not a valid numeric value.",
                    )
                )

        # 4. VPA & PSP Handle verification
        if pa:
            if "@" not in pa:
                signals.append(
                    Signal(
                        name="Invalid VPA Format",
                        severity="medium",
                        detail=f"Payee VPA '{pa}' lacks the standard user@bank structure.",
                    )
                )
            else:
                user_part, psp_handle = pa.split("@", 1)
                user_part = user_part.lower()
                psp_handle = psp_handle.lower()

                # Unknown PSP handle
                if psp_handle not in settings.TRUSTED_PSP_HANDLES:
                    signals.append(
                        Signal(
                            name="Unrecognized PSP Handle",
                            severity="medium",
                            detail=f"Payee handle '@{psp_handle}' is not recognized among standard verified NPCI handles.",
                        )
                    )

                # Lookalike / Brand Impersonation in VPA
                for brand in settings.TARGET_BRANDS:
                    if brand in user_part:
                        # Check if it pretends to be support or desk
                        scam_suffixes = ["support", "help", "care", "refund", "kyc", "verify", "official", "desk"]
                        if any(s in user_part for s in scam_suffixes):
                            signals.append(
                                Signal(
                                    name="Impersonated Brand Support VPA",
                                    severity="high",
                                    detail=f"VPA '{pa}' mimics official customer support for '{brand}', a common phishing tactic.",
                                )
                            )
                            break

        # 5. Payee Name vs VPA Mismatch
        if pn and pa and "@" in pa:
            pn_lower = pn.lower()
            pa_user = pa.split("@")[0].lower()

            # Check if name claims official brand entity but VPA is personal/unrelated
            for brand in settings.TARGET_BRANDS:
                if brand in pn_lower and brand not in pa_user:
                    signals.append(
                        Signal(
                            name="Payee Name & VPA Mismatch",
                            severity="high",
                            detail=f"Display name '{pn}' claims brand identity '{brand}' but VPA address '{pa}' does not match.",
                        )
                    )
                    break

        # 6. Collect-Request / Receive-Money Deception
        note_lower = (tn or "").lower()
        if any(pat in note_lower for pat in UPI_COLLECT_PATTERNS) or "collect" in upi_uri.lower():
            signals.append(
                Signal(
                    name="UPI Collect / Receive-Money Scam",
                    severity="high",
                    detail="Note or parameters attempt to disguise a payment as receiving money. Entering your UPI PIN always pays out funds.",
                )
            )

        # 7. Check for embedded URLs in transaction note or parameters
        url_match = re.search(r"https?://[^\s&]+", upi_uri)
        if url_match:
            embedded_url = url_match.group(0)
            url_res = self.url_analyzer.analyze(embedded_url)
            signals.append(
                Signal(
                    name="Embedded Phishing URL in UPI Note",
                    severity="high",
                    detail=f"UPI parameters contain an external URL link ({embedded_url}).",
                )
            )
            signals.extend(url_res["signals"])

        # 8. Community Reports & Reputation Check
        if pa:
            try:
                import httpx
                resp = httpx.get(
                    f"{settings.EXTRAS_API_URL}/api/ext/reputation",
                    params={"value": pa},
                    timeout=2.0
                )
                if resp.status_code == 200:
                    rep_data = resp.json()
                    rep_count = rep_data.get("report_count", 0)
                    if rep_count >= 3:
                        signals.append(
                            Signal(
                                name="Reported by community",
                                severity="high",
                                detail=f"This UPI payee has {rep_count} verified community fraud reports in the threat database.",
                            )
                        )
                    elif rep_count > 0:
                        signals.append(
                            Signal(
                                name="Community Fraud Reports",
                                severity="medium",
                                detail=f"This UPI payee has {rep_count} community report(s) on file.",
                            )
                        )
            except Exception:
                pass

        # Blend signals into final verdict
        risk_score, risk_level, verdict, action = blend_risk(
            signals=signals,
            ml_probability=0.0,
            scan_type="qr",
        )
        explanation = explain("qr", risk_level, signals, risk_score)

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "verdict": verdict,
            "signals": signals,
            "explanation": explanation,
            "recommended_action": action,
            "type": "qr",
        }

    def _analyze_non_upi_payload(self, payload: str) -> Dict[str, Any]:
        """Handles non-UPI, non-HTTP QR payloads (plain text, WiFi, Contacts)."""
        signals: List[Signal] = []
        payload_lower = payload.lower()

        # Check for embedded links in arbitrary text
        url_match = re.search(r"https?://[^\s]+", payload)
        if url_match:
            embedded_url = url_match.group(0)
            url_res = self.url_analyzer.analyze(embedded_url)
            signals.append(
                Signal(
                    name="Web URL Inside QR Payload",
                    severity="medium",
                    detail=f"QR contains an embedded web address: {embedded_url}",
                )
            )
            signals.extend(url_res["signals"])
        else:
            # Check for scam keywords in plain text
            urgent_kws = [kw for kw in settings.SUSPICIOUS_KEYWORDS if kw in payload_lower]
            if len(urgent_kws) >= 2:
                signals.append(
                    Signal(
                        name="Phishing Keywords in QR Text",
                        severity="medium",
                        detail=f"QR text contains urgency/fraud keywords: {', '.join(urgent_kws)}.",
                    )
                )

        risk_score, risk_level, verdict, action = blend_risk(
            signals=signals,
            ml_probability=0.0,
            scan_type="qr",
        )

        if not signals:
            explanation = "This QR code contains non-payment text or contact data. No financial payment will be initiated."
            verdict = "Safe to proceed"
            action = "No payment detected in this QR payload."
        else:
            explanation = explain("qr", risk_level, signals, risk_score)

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "verdict": verdict,
            "signals": signals,
            "explanation": explanation,
            "recommended_action": action,
            "type": "qr",
        }
