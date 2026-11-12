import os
from typing import List, Set
from pydantic import BaseModel

class Settings(BaseModel):
    # App
    PROJECT_NAME: str = "PayGuard AI"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # CORS
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")
        if origin.strip()
    ]

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./payguard.db")

    # Risk Engine Thresholds
    # LOW 0-39 | MEDIUM 40-69 | HIGH 70-100
    THRESHOLD_LOW_MAX: int = 39
    THRESHOLD_MEDIUM_MAX: int = 69
    THRESHOLD_HIGH_MIN: int = 70

    # Weights for URL Risk Blending
    URL_RULE_WEIGHT: float = float(os.getenv("URL_RULE_WEIGHT", "0.55"))
    URL_ML_WEIGHT: float = float(os.getenv("URL_ML_WEIGHT", "0.45"))

    # Brand target list for typosquatting / impersonation
    TARGET_BRANDS: List[str] = [
        "paytm",
        "phonepe",
        "googlepay",
        "gpay",
        "bhim",
        "npci",
        "sbi",
        "hdfc",
        "icici",
        "axis",
        "amazon",
        "flipkart",
    ]

    # Legitimate brand domains (used to distinguish official sites from impersonators)
    LEGITIMATE_BRAND_DOMAINS: Set[str] = {
        "paytm.com",
        "phonepe.com",
        "pay.google.com",
        "google.com",
        "bhimupi.org.in",
        "npci.org.in",
        "sbi.co.in",
        "onlinesbi.sbi",
        "hdfcbank.com",
        "icicibank.com",
        "axisbank.com",
        "amazon.in",
        "amazon.com",
        "flipkart.com",
    }

    # Suspicious Top Level Domains frequently abused in phishing
    SUSPICIOUS_TLDS: Set[str] = {
        "xyz",
        "top",
        "tk",
        "ml",
        "ga",
        "cf",
        "gq",
        "click",
        "work",
        "buzz",
        "fit",
        "online",
        "site",
        "rest",
        "icu",
        "club",
        "vip",
        "tokyo",
        "country",
        "stream",
        "bid",
        "download",
        "loan",
        "racing",
        "accountant",
        "faith",
        "date",
        "men",
    }

    # Phishing / Urgency Keywords
    SUSPICIOUS_KEYWORDS: List[str] = [
        "verify",
        "secure",
        "update",
        "kyc",
        "refund",
        "reward",
        "lottery",
        "urgent",
        "blocked",
        "suspended",
        "cashback",
        "win",
        "winner",
        "prize",
        "claim",
        "bonus",
        "otp",
        "pin",
        "pan",
        "aadhaar",
        "card",
        "wallet",
        "unblock",
        "deactivate",
    ]

    # Recognized standard Indian UPI PSP handles
    TRUSTED_PSP_HANDLES: Set[str] = {
        "okaxis",
        "okhdfcbank",
        "okicici",
        "oksbi",
        "paytm",
        "ybl",
        "axl",
        "ibl",
        "sbi",
        "icici",
        "hdfcbank",
        "axisbank",
        "upi",
        "apl",
        "idfcbank",
        "barodampay",
        "kotak",
        "indus",
        "pnb",
        "federal",
        "cnrb",
        "aubank",
        "freecharge",
        "airtel",
        "jupiteraxis",
        "postbank",
    }

    # URL Shortener domains
    URL_SHORTENERS: Set[str] = {
        "bit.ly",
        "tinyurl.com",
        "t.co",
        "is.gd",
        "buff.ly",
        "ow.ly",
        "rb.gy",
        "cutt.ly",
        "goo.gl",
        "shorturl.at",
        "rebrand.ly",
    }

    # WHOIS Lookup setting
    WHOIS_LOOKUP_ENABLED: bool = os.getenv("WHOIS_LOOKUP_ENABLED", "false").lower() == "true"

    # Optional LLM Explainer
    USE_LLM_EXPLAINER: bool = os.getenv("USE_LLM_EXPLAINER", "false").lower() == "true"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    LLM_TIMEOUT_SECONDS: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "2.0"))

    # Extras Service Integration
    EXTRAS_API_URL: str = os.getenv(
        "EXTRAS_API_URL",
        "https://payguard-ai-izry.onrender.com" if os.getenv("RENDER") else "http://localhost:8001"
    )

settings = Settings()
