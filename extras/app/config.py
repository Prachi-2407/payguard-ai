import os
import re
from typing import List, Set
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "PayGuard AI - Extras Intelligence Layer"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8001"))

    # Service & Integration URLs
    MAIN_API_URL: str = os.getenv("MAIN_API_URL", "http://localhost:8000")
    MAIN_API_TIMEOUT_SECONDS: float = float(os.getenv("MAIN_API_TIMEOUT_SECONDS", "2.0"))

    # Database
    EXTRAS_DB_URL: str = os.getenv("EXTRAS_DB_URL", "sqlite:///./extras.db")

    # CORS
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")
        if origin.strip()
    ]

    # ML Model Paths
    MODEL_PATH: str = os.getenv("MODEL_PATH", "extras/ml/models/message_model.joblib")
    VOICE_MODEL_PATH: str = os.getenv("VOICE_MODEL_PATH", "extras/ml/models/voice_model.joblib")

    # Whisper Settings
    WHISPER_MODEL_SIZE: str = os.getenv("WHISPER_MODEL_SIZE", "base")
    WHISPER_DEVICE: str = os.getenv("WHISPER_DEVICE", "cpu")
    WHISPER_COMPUTE_TYPE: str = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

    # Audio Limits
    MAX_AUDIO_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB
    MAX_AUDIO_DURATION_SECONDS: int = 300  # 5 minutes

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Risk Boundaries (Matching Main API Contract)
    THRESHOLD_LOW_MAX: int = 39
    THRESHOLD_MEDIUM_MAX: int = 69
    THRESHOLD_HIGH_MIN: int = 70

    # Rate Limiting
    MAX_REPORTS_PER_IP_PER_HOUR: int = int(os.getenv("MAX_REPORTS_PER_IP_PER_HOUR", "15"))

    # Suspicious TLDs (Local fallback)
    SUSPICIOUS_TLDS: Set[str] = {
        "xyz", "top", "tk", "ml", "ga", "cf", "gq", "click", "work",
        "buzz", "fit", "online", "site", "rest", "icu", "club", "vip",
        "tokyo", "country", "stream", "bid", "download", "loan", "racing",
        "accountant", "faith", "date", "men", "support", "help", "live", "cc"
    }

settings = Settings()

# Privacy masking helpers for logging
UPI_REGEX_MASK = re.compile(r'([a-zA-Z0-9.\-_]{2})[a-zA-Z0-9.\-_]+(@[a-zA-Z0-9]+)')
PHONE_REGEX_MASK = re.compile(r'(?:\+?91[\-\s]?)?[6-9]\d{9}')

def mask_upi_id(upi: str) -> str:
    """Masks a UPI ID: abcd@okaxis -> ab***@okaxis"""
    if not upi:
        return upi
    return UPI_REGEX_MASK.sub(r'\1***\2', upi)

def mask_phone_number(phone: str) -> str:
    """Masks a phone number: +919876543210 -> +9198****3210"""
    digits = re.sub(r'\D', '', phone)
    if len(digits) >= 10:
        last4 = digits[-4:]
        prefix = digits[:-8]
        first2 = digits[-10:-8]
        return f"+{prefix if prefix else '91'}{first2}****{last4}"
    return "******" + phone[-2:] if len(phone) > 2 else "***"

def mask_pii_in_text(text: str) -> str:
    """Masks phone numbers and UPI IDs in log messages."""
    if not text:
        return ""
    # Mask UPI IDs
    masked = UPI_REGEX_MASK.sub(r'\1***\2', text)
    # Mask Indian phone numbers
    def _mask_phone(m):
        raw = m.group(0)
        return mask_phone_number(raw)
    masked = PHONE_REGEX_MASK.sub(_mask_phone, masked)
    return masked

