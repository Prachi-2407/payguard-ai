import os
import random
import pandas as pd
from typing import List, Tuple

# Random seed for reproducibility
random.seed(42)

SAFE_DOMAINS = [
    "google.com", "youtube.com", "amazon.in", "amazon.com", "flipkart.com",
    "paytm.com", "phonepe.com", "sbi.co.in", "onlinesbi.sbi", "hdfcbank.com",
    "icicibank.com", "axisbank.com", "bhimupi.org.in", "npci.org.in", "rbi.org.in",
    "github.com", "wikipedia.org", "microsoft.com", "apple.com", "linkedin.com",
    "stackoverflow.com", "medium.com", "reddit.com", "quora.com", "netflix.com",
    "spotify.com", "incometax.gov.in", "uidai.gov.in", "epfindia.gov.in", "irctc.co.in",
    "tatamotors.com", "reliance.com", "infosys.com", "tcs.com", "wipro.com",
    "airtel.in", "jio.com", "zomato.com", "swiggy.com", "makemytrip.com"
]

SAFE_HYPHEN_DOMAINS = [
    "mercedes-benz.com", "t-mobile.com", "c-sharpcorner.com", "roll-royce.com",
    "free-code-camp.org", "tech-crunch.com", "e-filing.incometax.gov.in",
    "my-account.google.com", "mail-attachment.google.com", "self-service.apple.com",
    "developer-support.microsoft.com", "api-docs.github.com", "cloud-storage.aws.com",
    "secure-code-review.owasp.org", "customer-care.airtel.in"
]

SAFE_PATHS = [
    "/about", "/contact", "/terms-and-conditions", "/privacy-policy",
    "/products/item-detail-2026", "/documentation/api/v2/overview",
    "/search?q=machine+learning+cybersecurity&source=web&ref=topnav",
    "/account/settings/security/passwords", "/catalog/electronics/smartphones",
    "/blog/engineering-best-practices-2026", "/help/faq/common-questions",
    "/downloads/latest-release-x86_64", "/support/tickets/create?category=billing",
    "/news/tech/ai-safety-developments", "/dashboard/overview?period=last_30_days",
    "/courses/python-for-data-science/lecture-1", "/investor-relations/quarterly-reports"
]

PHISHING_BRANDS = [
    "paytm", "phonepe", "gpay", "googlepay", "bhim", "sbi", "hdfc",
    "icici", "axis", "amazon", "flipkart", "npci", "rbi"
]

PHISHING_KEYWORDS = [
    "verify", "secure", "update", "kyc", "refund", "reward", "lottery",
    "urgent", "blocked", "suspended", "cashback", "win", "winner",
    "claim", "bonus", "otp", "pin", "pan", "unblock", "deactivate"
]

SUSPICIOUS_TLDS = [
    "xyz", "top", "tk", "ml", "ga", "cf", "gq", "click", "work",
    "buzz", "fit", "online", "site", "rest", "icu", "club", "vip"
]

SHORTENERS = ["bit.ly", "tinyurl.com", "t.co", "is.gd", "rb.gy", "cutt.ly"]

def generate_legitimate_url() -> str:
    """Generate a realistic legitimate URL, including hard negatives (long, hyphens, subdomains)."""
    r = random.random()
    if r < 0.25:
        # Domain with hyphens (hard negative)
        domain = random.choice(SAFE_HYPHEN_DOMAINS)
    else:
        domain = random.choice(SAFE_DOMAINS)

    scheme = "https://" if random.random() > 0.05 else "http://"
    sub = ""
    if random.random() < 0.35 and not domain.startswith(("my-", "developer-", "api-")):
        sub = random.choice(["www.", "app.", "m.", "blog.", "docs.", "support.", "portal."])

    path = random.choice(SAFE_PATHS)

    # Some legitimate long URLs with multiple parameters
    if random.random() < 0.4:
        query_parts = [
            f"utm_source={random.choice(['google', 'newsletter', 'linkedin', 'direct'])}",
            f"utm_medium={random.choice(['cpc', 'email', 'social', 'referral'])}",
            f"session_id={random.randint(10000000, 99999999)}",
            f"view={random.choice(['list', 'grid', 'compact'])}",
            f"timestamp={random.randint(1600000000, 1750000000)}"
        ]
        sample_size = random.randint(1, len(query_parts))
        delim = "&" if "?" in path else "?"
        path += delim + "&".join(random.sample(query_parts, sample_size))

    return f"{scheme}{sub}{domain}{path}"

def generate_phishing_url() -> str:
    """Generate a realistic phishing URL targeting Indian payment users."""
    brand = random.choice(PHISHING_BRANDS)
    kw1 = random.choice(PHISHING_KEYWORDS)
    kw2 = random.choice(PHISHING_KEYWORDS)
    tld = random.choice(SUSPICIOUS_TLDS)
    scheme = "http://" if random.random() > 0.4 else "https://"

    strategy = random.choice([
        "typosquat_hyphen",
        "subdomain_spoof",
        "ip_address",
        "path_spoof",
        "shortener_redirect",
        "at_symbol",
        "excessive_subdomains",
        "keyword_stack"
    ])

    if strategy == "typosquat_hyphen":
        # e.g. paytm-kyc-verify-portal.xyz
        variants = [
            f"{brand}-{kw1}-login.{tld}",
            f"{brand}-{kw1}-{kw2}.{tld}",
            f"{kw1}-{brand}-secure-update.{tld}",
            f"{brand}bank-{kw1}.{tld}",
            f"{brand}pay-{kw2}.{tld}"
        ]
        host = random.choice(variants)
        path = f"/auth/{kw1}?user_id={random.randint(10000, 99999)}"
        return f"{scheme}{host}{path}"

    elif strategy == "subdomain_spoof":
        # e.g. paytm.com.secure-banking.xyz/login
        noise_domain = random.choice(["secure-banking", "account-alert", "web-portal", "auth-center", "net-secure"])
        return f"{scheme}{brand}.com.{noise_domain}.{tld}/{kw1}-account"

    elif strategy == "ip_address":
        ip = f"{random.randint(11, 215)}.{random.randint(10, 250)}.{random.randint(1, 250)}.{random.randint(1, 250)}"
        port = f":{random.choice([8080, 8443, 3000, 8000])}" if random.random() < 0.3 else ""
        return f"http://{ip}{port}/{brand}/{kw1}?token={random.randint(10000, 99999)}"

    elif strategy == "path_spoof":
        # generic domain with brand in path
        noise_domain = random.choice(["freewebhost", "mypage-service", "cloud-storage-net", "temp-site"])
        return f"{scheme}{noise_domain}.{tld}/{brand}/{kw1}/{kw2}?ref=sms"

    elif strategy == "shortener_redirect":
        shortener = random.choice(SHORTENERS)
        slug = f"{brand[:3]}{random.randint(100, 999)}{kw1[:3]}"
        return f"{scheme}{shortener}/{slug}?redirect=http://{brand}-{kw1}.{tld}"

    elif strategy == "at_symbol":
        safe = random.choice(SAFE_DOMAINS)
        return f"http://{safe}@{brand}-{kw1}-support.{tld}/login"

    elif strategy == "excessive_subdomains":
        return f"{scheme}secure.login.verify.{brand}.account-update.{tld}/index.html"

    else: # keyword_stack
        return f"{scheme}{brand}-{kw1}-{kw2}-claim-reward-{random.randint(100, 999)}.{tld}/redeem.php"

def generate_balanced_dataset(n_samples: int = 10000) -> pd.DataFrame:
    """Generate a balanced labeled dataset of n_samples URLs."""
    half = n_samples // 2
    data: List[Tuple[str, int]] = []

    # Generate legitimate URLs (label = 0)
    for _ in range(half):
        data.append((generate_legitimate_url(), 0))

    # Generate phishing URLs (label = 1)
    for _ in range(n_samples - half):
        data.append((generate_phishing_url(), 1))

    # Shuffle the dataset
    random.shuffle(data)

    df = pd.DataFrame(data, columns=["url", "label"])
    return df

def main(n_samples: int = 10000, output_path: str = "backend/ml/dataset.csv") -> pd.DataFrame:
    print(f"Generating {n_samples} balanced synthetic URLs...")
    df = generate_balanced_dataset(n_samples=n_samples)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Dataset saved to {output_path} ({len(df)} records, {df['label'].value_counts().to_dict()})")
    return df

if __name__ == "__main__":
    main()
