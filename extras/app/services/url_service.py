import logging
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import httpx

from extras.app.config import settings

logger = logging.getLogger(__name__)

IP_PATTERN = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d+)?$')

def local_url_heuristics(url: str) -> Dict[str, Any]:
    """Lightweight local fallback URL heuristic analyzer when main backend is offline."""
    signals: List[Dict[str, str]] = []
    risk_score = 15  # baseline benign score

    try:
        parsed = urlparse(url if "://" in url else f"http://{url}")
        host = (parsed.netloc or "").lower().split(":")[0]
        path = (parsed.path or "").lower()
        full_lower = url.lower()

        # 1. IP address host
        if IP_PATTERN.match(host):
            signals.append({
                "name": "Link: IP Address Host",
                "severity": "high",
                "detail": f"URL uses raw IP host ({host}) instead of a trusted domain name."
            })
            risk_score += 45

        # 2. Suspicious TLD check
        tld = host.split(".")[-1] if "." in host else ""
        if tld in settings.SUSPICIOUS_TLDS:
            signals.append({
                "name": "Link: Suspicious TLD",
                "severity": "high",
                "detail": f"Domain uses high-abuse top-level domain '.{tld}'."
            })
            risk_score += 40

        # 3. Phishing / Banking keyword targeting
        sensitive_keywords = ["sbi", "hdfc", "icici", "axis", "paytm", "gpay", "phonepe", "kyc", "verify", "login", "update", "refund"]
        matched_kw = [kw for kw in sensitive_keywords if kw in host or kw in path]
        if matched_kw and not any(legit in host for legit in ["sbi.co.in", "onlinesbi.sbi", "hdfcbank.com", "icicibank.com", "paytm.com", "phonepe.com"]):
            signals.append({
                "name": "Link: Brand/Credential Keyword Spoofing",
                "severity": "high",
                "detail": f"Untrusted link incorporates sensitive banking keywords: {', '.join(matched_kw[:3])}."
            })
            risk_score += 45

        # 4. Long / Obfuscated URL
        if len(url) > 80:
            signals.append({
                "name": "Link: Excessive URL Length",
                "severity": "low",
                "detail": f"URL length is unusually long ({len(url)} chars), a common obfuscation tactic."
            })
            risk_score += 15

        # Fallback signal informing that local heuristics were used
        signals.append({
            "name": "Link: Local Heuristic Fallback",
            "severity": "low",
            "detail": "Main backend was unreachable; assessed via local offline URL heuristics."
        })

    except Exception as e:
        logger.debug(f"Error parsing URL {url} in local heuristics: {e}")
        signals.append({
            "name": "Link: Unparseable URL Format",
            "severity": "medium",
            "detail": "Failed to parse target link structure safely."
        })
        risk_score += 30

    risk_score = min(100, max(0, risk_score))
    return {
        "risk_score": risk_score,
        "signals": signals,
    }

async def analyze_embedded_url(url: str) -> Dict[str, Any]:
    """
    Analyzes an embedded URL by calling the main backend URL analysis endpoint.
    Applies a 2-second timeout and falls back to local heuristics if offline.
    """
    target_endpoint = f"{settings.MAIN_API_URL.rstrip('/')}/api/analyze/url"

    try:
        async with httpx.AsyncClient(timeout=settings.MAIN_API_TIMEOUT_SECONDS) as client:
            resp = await client.post(target_endpoint, json={"url": url})
            if resp.status_code == 200:
                data = resp.json()
                # Prefix imported signals with 'Link: '
                prefixed_signals = []
                for s in data.get("signals", []):
                    name = s.get("name", "Signal")
                    if not name.startswith("Link:"):
                        name = f"Link: {name}"
                    prefixed_signals.append({
                        "name": name,
                        "severity": s.get("severity", "medium"),
                        "detail": s.get("detail", ""),
                    })
                return {
                    "risk_score": data.get("risk_score", 0),
                    "signals": prefixed_signals,
                }
            else:
                logger.warning(
                    f"Main backend returned HTTP {resp.status_code} for URL analysis; using local heuristics."
                )
                return local_url_heuristics(url)
    except (httpx.RequestError, httpx.TimeoutException) as exc:
        logger.info(
            f"Main backend unreachable ({exc.__class__.__name__}); falling back to local URL heuristics."
        )
        return local_url_heuristics(url)
    except Exception as exc:
        logger.warning(f"Unexpected error calling main backend: {exc}; using local heuristics.")
        return local_url_heuristics(url)

