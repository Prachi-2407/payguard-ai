import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from sqlalchemy.orm import Session

from extras.app.database.session import get_db
from extras.app.schemas.models import (
    CommunityReportRequest,
    CommunityReportResponse,
    BlocklistItem,
    ReputationResponse,
    StatsResponse,
)
from extras.app.database.repository import (
    record_community_report,
    get_entity_reputation,
    get_blocklist_entries,
    get_service_stats,
)
from extras.app.config import mask_upi_id, mask_phone_number

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ext", tags=["Community"])

def get_client_ip(request: Request) -> str:
    """Extracts client IP safely from forwarded headers or direct connection."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

@router.post("/reports", response_model=CommunityReportResponse)
def submit_report(
    payload: CommunityReportRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> CommunityReportResponse:
    """
    Submits a community fraud report for a URL, UPI VPA, or phone number.
    Applies IP-based rate limiting and deduplication.
    """
    client_ip = get_client_ip(request)
    status_str, report_count = record_community_report(
        db=db,
        target_type=payload.target_type,
        value=payload.value,
        reason=payload.reason,
        client_ip=client_ip,
    )

    if status_str == "rate_limited":
        logger.warning(f"Rate limit exceeded for reporter hash from IP")
        return CommunityReportResponse(
            status="rate_limited",
            report_count=report_count,
        )

    return CommunityReportResponse(
        status="recorded" if status_str == "recorded" else "duplicate_ignored",
        report_count=report_count,
    )

@router.get("/blocklist", response_model=List[BlocklistItem])
def get_blocklist(
    type: Optional[str] = Query(None, description="Filter by target type: vpa, url, or phone"),
    db: Session = Depends(get_db),
) -> List[BlocklistItem]:
    """Retrieves list of suspicious and reported entities from community reports."""
    if type and type not in ("vpa", "url", "phone"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 'type' query parameter. Must be one of: vpa, url, phone",
        )
    return get_blocklist_entries(db=db, target_type=type)

@router.get("/reputation", response_model=ReputationResponse)
def check_reputation(
    value: str = Query(..., min_length=1, description="Entity to check (VPA, URL, or phone)"),
    db: Session = Depends(get_db),
) -> ReputationResponse:
    """
    Checks the reputation of an identifier based on community intelligence.
    Reputation rule: 0 reports = UNKNOWN, 1-2 reports = SUSPICIOUS, 3+ reports = BAD.
    """
    return get_entity_reputation(db=db, value=value)

@router.get("/stats", response_model=StatsResponse)
def get_stats(
    db: Session = Depends(get_db),
) -> StatsResponse:
    """Aggregated statistics for community intelligence and scam signals."""
    return get_service_stats(db=db)

