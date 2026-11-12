from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

# Message Scam Categories
MessageScamCategory = Literal[
    "KYC_FRAUD",
    "LOTTERY",
    "REFUND_SCAM",
    "JOB_SCAM",
    "FAKE_CUSTOMER_CARE",
    "COLLECT_REQUEST",
    "LOAN_SCAM",
    "OTHER",
    "NONE"
]

# Voice Scam Categories
VoiceScamCategory = Literal[
    "BANK_IMPERSONATION",
    "POLICE_OR_GOVERNMENT_IMPERSONATION",
    "DIGITAL_ARREST",
    "OTP_FRAUD",
    "FAKE_CUSTOMER_CARE",
    "LOAN_SCAM",
    "INVESTMENT_SCAM",
    "PAYMENT_FRAUD",
    "REMOTE_ACCESS_SCAM",
    "OTHER",
    "NONE"
]

class Signal(BaseModel):
    name: str = Field(..., description="Short name of the detected signal")
    severity: Literal["low", "medium", "high"] = Field(..., description="Severity level")
    detail: str = Field(..., description="Explanation of why this signal was triggered")

class ExtractedEntities(BaseModel):
    urls: List[str] = Field(default_factory=list, description="Extracted web links")
    upi_ids: List[str] = Field(default_factory=list, description="Extracted UPI VPAs")
    phone_numbers: List[str] = Field(default_factory=list, description="Extracted phone numbers")
    scam_category: MessageScamCategory = Field(default="NONE", description="Categorized scam category")

class MessageAnalyzeRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Message text to analyze")
    source: Literal["sms", "whatsapp", "email", "other"] = Field(
        default="sms", description="Communication channel"
    )

    @field_validator("message")
    @classmethod
    def validate_message_not_blank(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Message cannot be empty or whitespace only")
        return s

class MessageAnalyzeResponse(BaseModel):
    risk_score: int = Field(..., ge=0, le=100, description="Risk score from 0 to 100")
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] = Field(..., description="Risk category")
    verdict: str = Field(..., description="Human verdict")
    signals: List[Signal] = Field(default_factory=list, description="List of detected signals")
    explanation: str = Field(..., description="Plain-English explanation")
    recommended_action: str = Field(..., description="Actionable recommendation")
    analyzed_at: str = Field(..., description="ISO 8601 UTC timestamp")
    type: Literal["message"] = "message"
    extracted: ExtractedEntities = Field(..., description="Extracted entities and scam category")

class VoiceAnalyzeRequest(BaseModel):
    transcript: str = Field(..., min_length=1, description="Transcript of call to analyze")
    language: Literal["en", "hi", "auto"] = Field(default="auto", description="Spoken language")

    @field_validator("transcript")
    @classmethod
    def validate_transcript_not_blank(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Transcript cannot be empty or whitespace only")
        return s

class TranscriptionMetadata(BaseModel):
    language: str = Field(default="en", description="Detected or specified language")
    duration_seconds: Optional[float] = Field(default=None, description="Audio duration if transcribed from audio")
    confidence: Optional[float] = Field(default=None, description="Average transcription confidence")
    source: Literal["audio", "transcript"] = Field(..., description="Whether source was audio or manual transcript")

class VoiceAnalyzeResponse(BaseModel):
    risk_score: int = Field(..., ge=0, le=100, description="Risk score from 0 to 100")
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] = Field(..., description="Risk category")
    verdict: str = Field(..., description="Human verdict")
    transcript: str = Field(..., description="Call transcript that was analyzed")
    scam_category: VoiceScamCategory = Field(default="NONE", description="Categorized voice scam category")
    signals: List[Signal] = Field(default_factory=list, description="Detected signals")
    explanation: str = Field(..., description="Plain-English explanation")
    recommended_action: str = Field(..., description="Actionable recommendation")
    analyzed_at: str = Field(..., description="ISO 8601 UTC timestamp")
    type: Literal["voice"] = "voice"
    transcription_metadata: TranscriptionMetadata = Field(..., description="Metadata on transcription")

class CommunityReportRequest(BaseModel):
    target_type: Literal["url", "vpa", "phone"] = Field(..., description="Entity type being reported")
    value: str = Field(..., min_length=1, description="Value being reported (URL, VPA, or phone)")
    reason: str = Field(..., min_length=3, description="Reason for the report")

    @field_validator("value")
    @classmethod
    def sanitize_value(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Reported value cannot be empty")
        return s

class CommunityReportResponse(BaseModel):
    status: Literal["recorded", "duplicate_ignored", "rate_limited"] = "recorded"
    report_count: int = Field(..., description="Total verified reports for this entity")

class BlocklistItem(BaseModel):
    value: str
    type: Literal["url", "vpa", "phone"]
    report_count: int
    first_reported: str
    last_reported: str

class ReputationResponse(BaseModel):
    value: str
    report_count: int
    reputation: Literal["BAD", "SUSPICIOUS", "UNKNOWN"]
    last_reported: Optional[str] = None

class DailyCount(BaseModel):
    date: str
    count: int

class StatsResponse(BaseModel):
    total_reports: int
    by_category: Dict[str, int]
    top_signals: List[str]
    daily_counts: List[DailyCount]

class HealthResponse(BaseModel):
    status: str = "ok"

class ErrorResponse(BaseModel):
    error: str
    code: int = 400

