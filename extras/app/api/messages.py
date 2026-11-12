import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from extras.app.database.session import get_db
from extras.app.schemas.models import (
    MessageAnalyzeRequest,
    MessageAnalyzeResponse,
)
from extras.app.analyzers.message_analyzer import MessageAnalyzer
from extras.app.config import mask_pii_in_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ext", tags=["Messages"])

message_analyzer = MessageAnalyzer()

@router.post("/analyze/message", response_model=MessageAnalyzeResponse)
async def analyze_message_endpoint(
    payload: MessageAnalyzeRequest,
    db: Session = Depends(get_db),
) -> MessageAnalyzeResponse:
    """
    Analyzes an incoming SMS, WhatsApp, or email message for scam patterns,
    coercive social engineering, and fraudulent links or payment identifiers.
    """
    try:
        masked_log = mask_pii_in_text(payload.message[:80])
        logger.info(f"Analyzing message from source='{payload.source}': {masked_log}...")
        result = await message_analyzer.analyze(
            message=payload.message,
            source=payload.source,
            db=db,
        )
        return result
    except Exception as e:
        logger.exception("Error processing message analysis: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

