import os
import re
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse
import joblib

from backend.config import settings
from backend.models.api import Signal
from backend.ml.features import (
    extract_url_features,
    extract_url_parts,
    compute_levenshtein,
    features_dict_to_vector,
    IP_REGEX,
    tld_extractor,
)
from backend.core.risk_engine import blend_risk
from backend.core.explainer import explain

logger = logging.getLogger(__name__)

# WHOIS Interface and Mock Implementation
class WhoisProvider(ABC):
    @abstractmethod
    def get_domain_age_days(self, domain: str) -> Optional[int]:
        pass

class MockWhoisProvider(WhoisProvider):
    """Deterministic offline WHOIS mock for testing and air-gapped environments."""
    def get_domain_age_days(self, domain: str) -> Optional[int]:
        domain_lower = domain.lower()
        # Established legitimate domains
        if domain_lower in settings.LEGITIMATE_BRAND_DOMAINS or any(
            d in domain_lower for d in ["google.com", "github.com", "wikipedia.org", "apple.com", "microsoft.com", "gov.in"]
        ):
            return 3650 # 10 years

        # Obvious phishing or suspicious markers
        ext = tld_extractor(domain_lower)
        suffix = ext.suffix.lower()
        if suffix in settings.SUSPICIOUS_TLDS or any(k in domain_lower for k in ["verify", "kyc", "refund", "login", "update", "secure"]):
            # Deterministic young age based on domain string hash (5 to 25 days)
            return (abs(hash(domain_lower)) % 20) + 5

        # Other domains
        return (abs(hash(domain_lower)) % 500) + 60

class LiveWhoisProvider(WhoisProvider):
    """Optional live WHOIS lookup provider."""
    def get_domain_age_days(self, domain: str) -> Optional[int]:
        try:
            import whois
            from datetime import datetime, timezone
            w = whois.whois(domain)
            creation_date = w.creation_date
            if isinstance(creation_date, list):
                creation_date = creation_date[0]
            if creation_date:
                now = datetime.now(timezone.utc)
                if creation_date.tzinfo is None:
                    creation_date = creation_date.replace(tzinfo=timezone.utc)
                return max(1, (now - creation_date).days)
        except Exception as e:
            logger.debug(f"Live WHOIS lookup failed for {domain}: {e}")
        return None

def get_whois_provider() -> WhoisProvider:
    if settings.WHOIS_LOOKUP_ENABLED:
        return LiveWhoisProvider()
    return MockWhoisProvider()

# Global cached ML model artifact
_URL_MODEL_ARTIFACT = None

def get_url_model() -> Optional[Dict[str, Any]]:
    """Loads URL ML model once at startup. Falls back or auto-trains if missing, never crashes."""
    global _URL_MODEL_ARTIFACT
    if _URL_MODEL_ARTIFACT is not None:
        return _URL_MODEL_ARTIFACT

    model_path = "backend/ml/url_model.pkl"
    if os.path.exists(model_path):
        try:
            _URL_MODEL_ARTIFACT = joblib.load(model_path)
            logger.info("Loaded URL ML model successfully from %s", model_path)
            return _URL_MODEL_ARTIFACT
        except Exception as e:
            logger.error("Failed to load model from %s: %e", model_path, e)

    # Try auto-training if missing
    try:
        from backend.ml.train import train_and_evaluate
        logger.info("URL model missing; attempting automatic quick training...")
        train_and_evaluate(n_samples_if_missing=2000)
        if os.path.exists(model_path):
            _URL_MODEL_ARTIFACT = joblib.load(model_path)
            return _URL_MODEL_ARTIFACT
    except Exception as e:
        logger.warning("Auto-training ML model failed: %s. Falling back to heuristic rules.", e)

    return None

class UrlAnalyzer:
    def __init__(self, whois_provider: Optional[WhoisProvider] = None):
        self.whois_provider = whois_provider or get_whois_provider()

    def analyze(self, url: str) -> Dict[str, Any]:
        """
        Executes full URL phishing analysis:
        1. Extract lexical, brand, and WHOIS rule signals
        2. Extract ML feature vector and compute model probability
        3. Blend into risk score, risk level, verdict, and explanation
        """
        raw_url = url.strip()
        url_lower = raw_url.lower()
        signals: List[Signal] = []

        # Parse URL
        if not raw_url.startswith(("http://", "https://")):
            parsed = urlparse("http://" + raw_url)
            is_https = False
        else:
            parsed = urlparse(raw_url)
            is_https = parsed.scheme.lower() == "https"

        host, reg_domain, subdomain, path, suffix = extract_url_parts(raw_url)
        extracted = tld_extractor(host)
        main_domain = extracted.domain.lower() if extracted.domain else host

        # 1. Suspicious TLD check
        if suffix in settings.SUSPICIOUS_TLDS:
            signals.append(
                Signal(
                    name="Suspicious TLD",
                    severity="high",
                    detail=f"Domain uses .{suffix}, commonly abused in phishing and scam campaigns.",
                )
            )

        # 2. IP as host check
        if IP_REGEX.match(host):
            signals.append(
                Signal(
                    name="IP Address Host",
                    severity="high",
                    detail=f"Host is a raw numerical IP address ({host}) instead of a trusted registered domain.",
                )
            )

        # 3. Brand Impersonation & Typosquatting
        is_legit_brand_domain = reg_domain in settings.LEGITIMATE_BRAND_DOMAINS

        for brand in settings.TARGET_BRANDS:
            # Typosquatting on main domain
            dist = compute_levenshtein(brand, main_domain)
            # If main domain is not exact brand official domain, but closely resembles it (1 or 2 edits)
            if 0 < dist <= 2 and not is_legit_brand_domain and len(main_domain) >= len(brand):
                signals.append(
                    Signal(
                        name="Brand Impersonation / Typosquatting",
                        severity="high",
                        detail=f"Domain '{main_domain}' closely mimics legitimate brand '{brand}' (Levenshtein distance {dist}).",
                    )
                )
                break
            # Brand appearing in subdomain or path of unrelated domain
            elif (brand in subdomain or brand in path or (brand in main_domain and dist > 0)) and not is_legit_brand_domain:
                signals.append(
                    Signal(
                        name="Brand Keyword in Subdomain/Path",
                        severity="high",
                        detail=f"Brand '{brand}' appears inside subdomain/path of unrelated domain '{reg_domain or host}'.",
                    )
                )
                break

        # 4. Embedded '@' symbol
        if "@" in raw_url:
            signals.append(
                Signal(
                    name="Deceptive '@' Character",
                    severity="high",
                    detail="URL contains an '@' character, frequently used to obscure the true server destination.",
                )
            )

        # 5. Non-HTTPS scheme
        if not is_https:
            signals.append(
                Signal(
                    name="Insecure Protocol (HTTP)",
                    severity="medium",
                    detail="Connection is unencrypted (HTTP), making payment credentials vulnerable to interception.",
                )
            )

        # 6. Punycode / Homograph check
        if "xn--" in host:
            signals.append(
                Signal(
                    name="Punycode Homograph",
                    severity="high",
                    detail="Host uses internationalized punycode ('xn--'), often used to disguise lookalike characters.",
                )
            )

        # 7. URL Shortener check
        if host in settings.URL_SHORTENERS:
            signals.append(
                Signal(
                    name="URL Shortener",
                    severity="medium",
                    detail=f"URL uses shortening service '{host}' which conceals the destination payment endpoint.",
                )
            )

        # 8. Open redirect parameters
        query = parsed.query.lower()
        for param in ["url=", "redirect=", "next=", "dest=", "target=", "r="]:
            if param in query:
                signals.append(
                    Signal(
                        name="Redirect Parameter",
                        severity="medium",
                        detail=f"URL query string contains redirect parameter '{param[:-1]}' pointing to external target.",
                    )
                )
                break

        # 9. Excessive subdomains
        subdomain_count = len(subdomain.split(".")) if subdomain else 0
        if subdomain_count >= 3:
            signals.append(
                Signal(
                    name="Excessive Subdomains",
                    severity="medium",
                    detail=f"Host uses {subdomain_count} nested subdomains, a pattern used to evade domain filters.",
                )
            )

        # 10. Suspicious Phishing Keywords
        found_keywords = [kw for kw in settings.SUSPICIOUS_KEYWORDS if kw in url_lower]
        if len(found_keywords) >= 2:
            signals.append(
                Signal(
                    name="Urgency / Phishing Keywords",
                    severity="high",
                    detail=f"Multiple phishing keywords found: {', '.join(found_keywords[:4])}.",
                )
            )
        elif len(found_keywords) == 1:
            signals.append(
                Signal(
                    name="Suspicious Keyword",
                    severity="medium",
                    detail=f"Contains payment-related keyword: '{found_keywords[0]}'.",
                )
            )

        # 11. Domain Age / WHOIS check
        age_days = self.whois_provider.get_domain_age_days(reg_domain or host)
        if age_days is not None:
            if age_days < 30:
                signals.append(
                    Signal(
                        name="Newly Registered Domain",
                        severity="high",
                        detail=f"Domain registered recently ({age_days} days old); new domains correlate strongly with fraud.",
                    )
                )
            elif age_days < 90:
                signals.append(
                    Signal(
                        name="Young Domain Age",
                        severity="medium",
                        detail=f"Domain is relatively new ({age_days} days old).",
                    )
                )

        # 12. Structural / Lexical anomalies (length, hyphens)
        if len(raw_url) > 100:
            signals.append(
                Signal(
                    name="Unusually Long URL",
                    severity="low",
                    detail=f"URL length ({len(raw_url)} characters) is exceptionally long.",
                )
            )
        if host.count("-") >= 3:
            signals.append(
                Signal(
                    name="Multiple Hyphens in Domain",
                    severity="medium",
                    detail="Hostname contains 3 or more hyphens, often used to concatenate trusted brand tokens.",
                )
            )

        # ML Model Inference
        ml_prob = 0.0
        model_artifact = get_url_model()
        if model_artifact and "model" in model_artifact:
            try:
                features_dict = extract_url_features(raw_url)
                feat_vector = [features_dict_to_vector(features_dict)]
                model = model_artifact["model"]
                probs = model.predict_proba(feat_vector)
                ml_prob = float(probs[0][1])
            except Exception as e:
                logger.warning("ML prediction failed: %s; using rule scores only.", e)

        # Blend rule scores + ML score
        risk_score, risk_level, verdict, action = blend_risk(
            signals=signals,
            ml_probability=ml_prob,
            scan_type="url",
        )

        explanation = explain(
            scan_type="url",
            risk_level=risk_level,
            signals=signals,
            risk_score=risk_score,
        )

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "verdict": verdict,
            "signals": signals,
            "explanation": explanation,
            "recommended_action": action,
            "type": "url",
            "ml_probability": ml_prob,
        }
