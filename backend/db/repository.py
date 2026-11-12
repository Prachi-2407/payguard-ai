import json
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.models.db import ScanHistory, TransactionAudit
from backend.models.api import AnalyzeResponse

def save_scan_result(
    db: Session,
    response: AnalyzeResponse,
    raw_input_masked: str = "",
) -> ScanHistory:
    record = ScanHistory(
        type=response.type,
        risk_score=response.risk_score,
        risk_level=response.risk_level,
        verdict=response.verdict,
        signals_json=json.dumps([s.model_dump() for s in response.signals]),
        explanation=response.explanation,
        recommended_action=response.recommended_action,
        analyzed_at=response.analyzed_at,
        raw_input_masked=raw_input_masked,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_scan_history(
    db: Session,
    limit: int = 20,
    scan_type: Optional[str] = None,
    risk_level: Optional[str] = None,
) -> List[ScanHistory]:
    query = db.query(ScanHistory)
    if scan_type:
        query = query.filter(ScanHistory.type == scan_type.lower())
    if risk_level:
        query = query.filter(ScanHistory.risk_level == risk_level.upper())
    
    return query.order_by(desc(ScanHistory.id)).limit(limit).all()

def record_transaction(
    db: Session,
    user_id: str,
    amount: float,
    receiver: str,
    timestamp: str,
    channel: str,
    note: str,
    risk_score: int,
) -> TransactionAudit:
    record = TransactionAudit(
        user_id=user_id,
        amount=amount,
        receiver=receiver,
        timestamp=timestamp,
        channel=channel,
        note=note,
        risk_score=risk_score,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_user_transactions(db: Session, user_id: str) -> List[TransactionAudit]:
    return (
        db.query(TransactionAudit)
        .filter(TransactionAudit.user_id == user_id)
        .order_by(desc(TransactionAudit.id))
        .all()
    )
