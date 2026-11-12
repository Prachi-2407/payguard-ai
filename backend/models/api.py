from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator

class Signal(BaseModel):
    name: str = Field(..., description="Short name of the detected signal")
    severity: Literal["low", "medium", "high"] = Field(..., description="Severity level")
    detail: str = Field(..., description="Explanation of why this signal was triggered")

class AnalyzeResponse(BaseModel):
    risk_score: int = Field(..., ge=0, le=100, description="Risk score from 0 to 100")
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] = Field(..., description="Categorical risk level")
    verdict: str = Field(..., description="Clear verdict e.g. 'Safe to proceed', 'Proceed with caution', 'Do not proceed'")
    signals: List[Signal] = Field(default_factory=list, description="List of detected signals")
    explanation: str = Field(..., description="Plain-English explanation for non-technical users")
    recommended_action: str = Field(..., description="Actionable recommendation for the user")
    analyzed_at: str = Field(..., description="ISO 8601 UTC timestamp of analysis")
    type: Literal["url", "qr", "transaction"] = Field(..., description="Type of analysis performed")

class HistoryItemResponse(AnalyzeResponse):
    id: int = Field(..., description="Unique persistent identifier for the scan")

class UrlAnalyzeRequest(BaseModel):
    url: str = Field(..., min_length=1, description="URL string to analyze")

    @field_validator("url")
    @classmethod
    def validate_url_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("URL cannot be empty")
        return stripped

class QrAnalyzeRequest(BaseModel):
    qr_payload: str = Field(..., min_length=1, description="Decoded QR payload string")

    @field_validator("qr_payload")
    @classmethod
    def validate_qr_payload_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("QR payload cannot be empty")
        return stripped

class TransactionAnalyzeRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="Unique identifier of the paying user")
    amount: float = Field(..., gt=0, description="Transaction amount in INR")
    receiver: str = Field(..., min_length=1, description="Receiver UPI VPA, phone number, or account ID")
    timestamp: str = Field(..., description="ISO formatted timestamp of the transaction")
    channel: str = Field(default="upi", description="Payment channel e.g. upi, netbanking, card")
    note: Optional[str] = Field(default="", description="Optional payment note or description")

    @field_validator("user_id", "receiver")
    @classmethod
    def validate_non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field cannot be empty")
        return stripped

class HealthResponse(BaseModel):
    status: str = "ok"

class ErrorResponse(BaseModel):
    error: str
    code: int = 400
