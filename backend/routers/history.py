from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.db.repository import get_scan_history
from backend.models.api import HistoryItemResponse, Signal

router = APIRouter(prefix="/api", tags=["History"])

@router.get("/history", response_model=List[HistoryItemResponse])
def get_history(
    limit: int = Query(default=20, ge=1, le=100, description="Max records to return"),
    type: Optional[str] = Query(default=None, description="Filter by type (url, qr, transaction)"),
    risk_level: Optional[str] = Query(default=None, description="Filter by risk level (LOW, MEDIUM, HIGH)"),
    db: Session = Depends(get_db),
) -> List[HistoryItemResponse]:
    records = get_scan_history(
        db=db,
        limit=limit,
        scan_type=type,
        risk_level=risk_level,
    )

    items = []
    for r in records:
        signals_data = [Signal(**s) for s in r.signals]
        items.append(
            HistoryItemResponse(
                id=r.id,
                risk_score=r.risk_score,
                risk_level=r.risk_level, # type: ignore
                verdict=r.verdict,
                signals=signals_data,
                explanation=r.explanation,
                recommended_action=r.recommended_action,
                analyzed_at=r.analyzed_at,
                type=r.type, # type: ignore
            )
        )
    return items
