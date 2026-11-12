import re
from typing import List, Dict, Set, Tuple

# Common standard email domain extensions to exclude from UPI VPA extraction
EMAIL_TLD_EXTENSIONS = {
    "com", "org", "net", "edu", "gov", "mil", "io", "co", "ai",
    "in", "info", "biz", "me", "tech", "app", "online", "xyz", "dev"
}

# Known popular Indian UPI PSP / Bank handles
KNOWN_UPI_HANDLES = {
    "okhdfcbank", "okaxis", "oksbi", "okicici", "paytm", "ybl", "ibl", "axl",
    "apl", "upi", "fbl", "barodampay", "sbi", "hdfcbank", "icici", "axisbank",
    "kotak", "indus", "federal", "pnb", "cnrb", "unionbank", "boi", "citi",
    "freecharge", "airtel", "jio", "postbank", "aubank", "idfcbank", "dlb",
    "equitas", "nsdl", "timecosmos", "allbank", "andb", "corp", "synd",
    "rbl", "yesbank", "sc", "hsbc", "bandhan", "dbs", "kvb", "tjsb"
}

# Regex for URLs (http/https or naked domains with path)
URL_REGEX = re.compile(
    r'(?:https?://[^\s<>"\',;]+|(?:www\.)[^\s<>"\',;]+|[a-zA-Z0-9.\-]+\.(?:com|in|org|net|xyz|top|site|online|club|ru|biz|info|cc)(?:/[^\s<>"\',;]*)?)',
    re.IGNORECASE
)

# Potential UPI VPA pattern: identifier@handle
POTENTIAL_VPA_REGEX = re.compile(
    r'\b([a-zA-Z0-9.\-_]{2,64})@([a-zA-Z0-9.\-_]{2,64})\b'
)

# Indian phone numbers: +91, 91, 0 or direct 10-digit starting with 6-9
INDIAN_PHONE_REGEX = re.compile(
    r'(?:(?:\+91|91|0)[\-\s]?)?([6-9]\d{4}[\-\s]?\d{5}|[6-9]\d{9})\b'
)

# International phone numbers with explicit leading + (e.g. +1 800 123 4567, +44 20 7946 0958)
INTL_PHONE_REGEX = re.compile(
    r'(\+[1-9]\d{0,3}[\-\s]?(?:\(?\d{1,4}\)?[\-\s]?){1,4}\d{4,10})\b'
)

def extract_urls(text: str) -> List[str]:
    """Extracts URLs from message text, cleaning trailing punctuation and deduplicating."""
    if not text:
        return []
    raw_matches = URL_REGEX.findall(text)
    urls = []
    seen = set()

    for m in raw_matches:
        # Strip trailing punctuation often adjacent in prose (e.g., "visit sbi.com.")
        clean_url = re.sub(r'[.,;!?)\]>]+$', '', m).strip()
        if not clean_url:
            continue
        # Ensure it has a dot and looks like a valid domain
        if "." in clean_url and len(clean_url) > 4:
            # If not starting with protocol, add http:// for uniform downstream handling
            formatted = clean_url if clean_url.startswith(("http://", "https://")) else f"http://{clean_url}"
            lower_fmt = formatted.lower()
            if lower_fmt not in seen:
                seen.add(lower_fmt)
                urls.append(formatted)
    return urls

def is_valid_upi_vpa(prefix: str, handle: str) -> bool:
    """
    Distinguishes legitimate UPI VPAs from typical email addresses.
    Example:
      'fraud@ybl' -> True
      'merchant@paytm' -> True
      'john.doe@gmail.com' -> False
      'support@company.org' -> False
    """
    handle_lower = handle.lower().strip()
    prefix_lower = prefix.lower().strip()

    # Rule 1: If handle matches known Indian UPI handles, it is definitely a UPI VPA
    if handle_lower in KNOWN_UPI_HANDLES:
        return True

    # Rule 2: If handle contains dots (like gmail.com, yahoo.co.in), check if the rightmost part is an email TLD
    if "." in handle_lower:
        parts = handle_lower.split(".")
        tld = parts[-1]
        # Most email providers have 2 or 3 parts ending in a standard email TLD
        if tld in EMAIL_TLD_EXTENSIONS:
            # Extra check: if someone uses an email as a VPA, UPI does NOT use .com handles
            return False

    # Rule 3: UPI handles are almost exclusively single words without dots (e.g., @ybl, @axl, @ibl, @upi)
    # and typically under 25 chars
    if "." not in handle_lower and len(handle_lower) <= 25 and handle_lower.isalpha():
        # Exclude common mistaken words like 'today', 'now', 'here' if matched accidentally
        if handle_lower not in {"com", "net", "org", "gov", "edu"}:
            return True

    return False

def extract_upi_ids(text: str) -> List[str]:
    """Extracts genuine UPI IDs while rigorously filtering out regular email addresses."""
    if not text:
        return []
    matches = POTENTIAL_VPA_REGEX.findall(text)
    upi_ids = []
    seen = set()

    for prefix, handle in matches:
        if is_valid_upi_vpa(prefix, handle):
            vpa = f"{prefix}@{handle}".lower()
            if vpa not in seen:
                seen.add(vpa)
                upi_ids.append(vpa)
    return upi_ids

def normalize_phone(raw: str) -> str:
    """Normalizes phone number to standard +91XXXXXXXXXX or canonical E.164-like string."""
    digits = re.sub(r'\D', '', raw)
    if len(digits) == 10 and digits[0] in "6789":
        return f"+91{digits}"
    elif len(digits) == 11 and digits.startswith("0") and digits[1] in "6789":
        return f"+91{digits[1:]}"
    elif len(digits) == 12 and digits.startswith("91") and digits[2] in "6789":
        return f"+{digits}"
    elif raw.startswith("+"):
        return f"+{digits}"
    return raw.strip()

def extract_phone_numbers(text: str) -> List[str]:
    """Extracts and normalizes phone numbers (Indian mobile and international)."""
    if not text:
        return []
    phones = []
    seen = set()

    # 1. Indian Phone numbers
    for m in INDIAN_PHONE_REGEX.finditer(text):
        raw = m.group(0)
        norm = normalize_phone(raw)
        # Verify it has at least 10 digits
        digits = re.sub(r'\D', '', norm)
        if len(digits) >= 10 and norm not in seen:
            seen.add(norm)
            phones.append(norm)

    # 2. International Phone numbers (only if starting with explicit + and not already captured)
    for m in INTL_PHONE_REGEX.finditer(text):
        raw = m.group(0)
        norm = normalize_phone(raw)
        digits = re.sub(r'\D', '', norm)
        if 8 <= len(digits) <= 15 and norm not in seen:
            # Check overlap with existing
            if not any(digits in re.sub(r'\D', '', p) for p in phones):
                seen.add(norm)
                phones.append(norm)

    return phones

def extract_all_entities(text: str) -> Dict[str, List[str]]:
    """Extracts URLs, UPI VPAs, and Phone numbers in a single pass."""
    return {
        "urls": extract_urls(text),
        "upi_ids": extract_upi_ids(text),
        "phone_numbers": extract_phone_numbers(text),
    }

