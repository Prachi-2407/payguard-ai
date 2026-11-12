import re
import math
from typing import Dict, Any, List, Tuple
from urllib.parse import urlparse, parse_qs
import tldextract
from backend.config import settings

# Initialize offline TLDExtract with no network fetching
tld_extractor = tldextract.TLDExtract(suffix_list_urls=None)

FEATURE_NAMES: List[str] = [
    "url_length",
    "host_length",
    "num_dots",
    "num_hyphens",
    "num_digits",
    "digit_ratio",
    "has_at_symbol",
    "is_ip_address",
    "num_subdomains",
    "is_https",
    "has_punycode",
    "is_shortener",
    "has_redirect_param",
    "is_suspicious_tld",
    "brand_similarity_score",
    "brand_in_subdomain_or_path",
    "num_suspicious_keywords",
    "url_entropy",
    "path_depth",
    "query_length",
]

IP_REGEX = re.compile(r"^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)(?::\d+)?$")

def compute_levenshtein(s1: str, s2: str) -> int:
    """Compute the Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return compute_levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def calculate_entropy(text: str) -> float:
    """Compute Shannon entropy of a string."""
    if not text:
        return 0.0
    probabilities = [float(text.count(c)) / len(text) for c in dict.fromkeys(list(text))]
    return -sum(p * math.log2(p) for p in probabilities if p > 0)

def extract_url_parts(url: str) -> Tuple[str, str, str, str, str]:
    """
    Parses URL safely and extracts scheme, host, registered domain, subdomain, path.
    Pre-pends http:// if scheme is missing so urllib parses correctly.
    """
    clean_url = url.strip()
    if not clean_url.startswith(("http://", "https://", "ftp://")):
        parsed = urlparse("http://" + clean_url)
    else:
        parsed = urlparse(clean_url)

    host = parsed.netloc.lower().split(":")[0]
    extracted = tld_extractor(host)
    reg_domain = extracted.top_domain_under_public_suffix.lower() if hasattr(extracted, 'top_domain_under_public_suffix') and extracted.top_domain_under_public_suffix else f"{extracted.domain}.{extracted.suffix}".lower()
    subdomain = extracted.subdomain.lower()
    path = parsed.path.lower()
    suffix = extracted.suffix.lower()

    return host, reg_domain, subdomain, path, suffix

def extract_url_features(url: str) -> Dict[str, Any]:
    """
    Extract a dictionary of numerical features suitable for ML models and heuristics.
    """
    raw_url = url.strip()
    url_lower = raw_url.lower()

    # Normalize parsing
    if not raw_url.startswith(("http://", "https://")):
        parsed = urlparse("http://" + raw_url)
        is_https = 0
    else:
        parsed = urlparse(raw_url)
        is_https = 1 if parsed.scheme == "https" else 0

    host, reg_domain, subdomain, path, suffix = extract_url_parts(raw_url)

    url_length = len(raw_url)
    host_length = len(host)
    num_dots = raw_url.count(".")
    num_hyphens = raw_url.count("-")
    num_digits = sum(c.isdigit() for c in raw_url)
    digit_ratio = (num_digits / url_length) if url_length > 0 else 0.0

    has_at_symbol = 1 if "@" in raw_url else 0
    is_ip_address = 1 if IP_REGEX.match(host) else 0

    num_subdomains = len(subdomain.split(".")) if subdomain else 0
    has_punycode = 1 if "xn--" in host else 0
    is_shortener = 1 if host in settings.URL_SHORTENERS else 0

    # Redirect parameter check
    query = parsed.query.lower()
    redirect_params = ["url=", "redirect=", "next=", "dest=", "link=", "target=", "r="]
    has_redirect_param = 1 if any(p in query for p in redirect_params) else 0

    is_suspicious_tld = 1 if suffix in settings.SUSPICIOUS_TLDS else 0

    # Brand similarity and impersonation analysis
    # Check if domain or subdomain looks like a target brand
    best_similarity = 0.0
    brand_in_sub_or_path = 0

    # Domain main part (e.g. 'paytm' from 'paytm.com' or 'paytm-update' from 'paytm-update.xyz')
    extracted = tld_extractor(host)
    main_domain = extracted.domain.lower() if extracted.domain else host

    for brand in settings.TARGET_BRANDS:
        # Check brand similarity to the main domain
        dist = compute_levenshtein(brand, main_domain)
        max_l = max(len(brand), len(main_domain), 1)
        sim = 1.0 - (dist / max_l)
        if sim > best_similarity:
            best_similarity = max(0.0, sim)

        # Check if brand is contained as a substring in domain, subdomain, or path
        # but the registered domain is NOT the brand's official domain
        if brand in main_domain or brand in subdomain or brand in path:
            if reg_domain not in settings.LEGITIMATE_BRAND_DOMAINS:
                brand_in_sub_or_path = 1

    # Suspicious keywords
    num_suspicious_keywords = 0
    for kw in settings.SUSPICIOUS_KEYWORDS:
        if kw in url_lower:
            num_suspicious_keywords += 1

    url_entropy = calculate_entropy(host)
    path_depth = path.count("/")
    query_length = len(parsed.query)

    return {
        "url_length": float(url_length),
        "host_length": float(host_length),
        "num_dots": float(num_dots),
        "num_hyphens": float(num_hyphens),
        "num_digits": float(num_digits),
        "digit_ratio": float(digit_ratio),
        "has_at_symbol": float(has_at_symbol),
        "is_ip_address": float(is_ip_address),
        "num_subdomains": float(num_subdomains),
        "is_https": float(is_https),
        "has_punycode": float(has_punycode),
        "is_shortener": float(is_shortener),
        "has_redirect_param": float(has_redirect_param),
        "is_suspicious_tld": float(is_suspicious_tld),
        "brand_similarity_score": float(best_similarity),
        "brand_in_subdomain_or_path": float(brand_in_sub_or_path),
        "num_suspicious_keywords": float(num_suspicious_keywords),
        "url_entropy": float(url_entropy),
        "path_depth": float(path_depth),
        "query_length": float(query_length),
    }

def features_dict_to_vector(features: Dict[str, Any]) -> List[float]:
    """Converts feature dictionary to an ordered feature vector matching FEATURE_NAMES."""
    return [float(features[name]) for name in FEATURE_NAMES]
