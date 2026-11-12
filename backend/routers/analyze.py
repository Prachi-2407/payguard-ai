from datetime import datetime, timezone
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.db.repository import save_scan_result, record_transaction
from backend.models.api import (
    UrlAnalyzeRequest,
    QrAnalyzeRequest,
    TransactionAnalyzeRequest,
    AnalyzeResponse,
)
from backend.analyzers.url_analyzer import UrlAnalyzer
from backend.analyzers.qr_analyzer import QrAnalyzer
from backend.analyzers.txn_analyzer import TransactionAnalyzer

router = APIRouter(prefix="/api/analyze", tags=["Analyze"])

url_analyzer = UrlAnalyzer()
qr_analyzer = QrAnalyzer(url_analyzer=url_analyzer)
txn_analyzer = TransactionAnalyzer()

def mask_url_sensitive_params(url: str) -> str:
    """Masks query parameter values in URLs to preserve privacy in logs/storage."""
    # Matches ?key=val or &key=val and masks val
    return re.sub(r'([?&][^=]+=)[^&]+', r'\1***', url)

@router.post("/url", response_model=AnalyzeResponse)
def analyze_url(
    payload: UrlAnalyzeRequest,
    db: Session = Depends(get_db),
) -> AnalyzeResponse:
    try:
        result = url_analyzer.analyze(payload.url)
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        response = AnalyzeResponse(
            risk_score=result["risk_score"],
            risk_level=result["risk_level"],
            verdict=result["verdict"],
            signals=result["signals"],
            explanation=result["explanation"],
            recommended_action=result["recommended_action"],
            analyzed_at=now_iso,
            type="url",
        )

        masked_input = mask_url_sensitive_params(payload.url)
        save_scan_result(db, response, raw_input_masked=masked_input)

        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/qr", response_model=AnalyzeResponse)
def analyze_qr(
    payload: QrAnalyzeRequest,
    db: Session = Depends(get_db),
) -> AnalyzeResponse:
    try:
        result = qr_analyzer.analyze(payload.qr_payload)
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        response = AnalyzeResponse(
            risk_score=result["risk_score"],
            risk_level=result["risk_level"],
            verdict=result["verdict"],
            signals=result["signals"],
            explanation=result["explanation"],
            recommended_action=result["recommended_action"],
            analyzed_at=now_iso,
            type="qr",
        )

        masked_input = mask_url_sensitive_params(payload.qr_payload)
        save_scan_result(db, response, raw_input_masked=masked_input)

        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/transaction", response_model=AnalyzeResponse)
def analyze_transaction(
    payload: TransactionAnalyzeRequest,
    db: Session = Depends(get_db),
) -> AnalyzeResponse:
    try:
        result = txn_analyzer.analyze(
            user_id=payload.user_id,
            amount=payload.amount,
            receiver=payload.receiver,
            timestamp_str=payload.timestamp,
            channel=payload.channel,
            note=payload.note,
            db=db,
        )
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        response = AnalyzeResponse(
            risk_score=result["risk_score"],
            risk_level=result["risk_level"],
            verdict=result["verdict"],
            signals=result["signals"],
            explanation=result["explanation"],
            recommended_action=result["recommended_action"],
            analyzed_at=now_iso,
            type="transaction",
        )

        # Record to history
        save_scan_result(
            db,
            response,
            raw_input_masked=f"user={payload.user_id};amt={payload.amount};receiver={payload.receiver}",
        )

        # Record transaction to audit log for velocity & behavior baselining
        record_transaction(
            db=db,
            user_id=payload.user_id,
            amount=payload.amount,
            receiver=payload.receiver,
            timestamp=payload.timestamp,
            channel=payload.channel,
            note=payload.note or "",
            risk_score=result["risk_score"],
        )

        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
