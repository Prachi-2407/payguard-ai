import hashlib
import re
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from extras.app.config import settings
from extras.app.database.models import CommunityReport, EntityReputation, AnalysisLog
from extras.app.schemas.models import (
    BlocklistItem,
    ReputationResponse,
    DailyCount,
    StatsResponse,
)

def hash_reporter_ip(ip: str) -> str:
    """Anonymizes reporter IP with SHA-256 hash."""
    return hashlib.sha256(ip.strip().encode("utf-8")).hexdigest()

def normalize_target_value(target_type: str, value: str) -> str:
    """Normalizes target value for consistent deduplication and matching."""
    val = value.strip()
    if target_type == "vpa":
        return val.lower()
    elif target_type == "url":
        # Remove trailing slash and lower scheme/host
        val_lower = val.lower()
        if not (val_lower.startswith("http://") or val_lower.startswith("https://")):
            val = "http://" + val
        return val.rstrip("/")
    elif target_type == "phone":
        # Keep digits and leading +
        cleaned = re.sub(r'[\s\-()]', '', val)
        digits = re.sub(r'\D', '', cleaned)
        if len(digits) == 10:
            return f"+91{digits}"
        elif len(digits) == 12 and digits.startswith("91"):
            return f"+{digits}"
        return cleaned
    return val.lower()

def record_community_report(
    db: Session,
    target_type: str,
    value: str,
    reason: str,
    client_ip: str,
) -> Tuple[str, int]:
    """
    Records a community report with rate-limiting and duplicate prevention.
    Returns (status, report_count).
    Status can be 'recorded', 'duplicate_ignored', or 'rate_limited'.
    """
    norm_val = normalize_target_value(target_type, value)
    reporter_hash = hash_reporter_ip(client_ip)
    now = datetime.now(timezone.utc)

    # 1. Rate Limiting: Max reports per IP in the last 1 hour
    one_hour_ago = now - timedelta(hours=1)
    recent_reports_count = (
        db.query(func.count(CommunityReport.id))
        .filter(
            CommunityReport.reporter_hash == reporter_hash,
            CommunityReport.created_at >= one_hour_ago,
        )
        .scalar()
        or 0
    )

    if recent_reports_count >= settings.MAX_REPORTS_PER_IP_PER_HOUR:
        rep = db.query(EntityReputation).filter(EntityReputation.value == norm_val).first()
        return "rate_limited", rep.report_count if rep else 0

    # 2. Duplicate Prevention: Check if same reporter submitted for same entity in last 24h
    one_day_ago = now - timedelta(days=1)
    duplicate_report = (
        db.query(CommunityReport)
        .filter(
            CommunityReport.reporter_hash == reporter_hash,
            CommunityReport.value == norm_val,
            CommunityReport.created_at >= one_day_ago,
        )
        .first()
    )

    if duplicate_report:
        # Don't increment count; return existing count
        rep = db.query(EntityReputation).filter(EntityReputation.value == norm_val).first()
        return "duplicate_ignored", rep.report_count if rep else 1

    # 3. Record valid report
    new_report = CommunityReport(
        target_type=target_type,
        value=norm_val,
        reason=reason[:500],
        reporter_hash=reporter_hash,
        created_at=now,
    )
    db.add(new_report)

    # 4. Update / Insert Reputation Entry
    rep = db.query(EntityReputation).filter(EntityReputation.value == norm_val).first()
    if rep:
        rep.report_count += 1
        rep.last_reported = now
    else:
        rep = EntityReputation(
            target_type=target_type,
            value=norm_val,
            report_count=1,
            first_reported=now,
            last_reported=now,
        )
        db.add(rep)

    db.commit()
    db.refresh(rep)
    return "recorded", rep.report_count

def get_entity_reputation(db: Session, value: str) -> ReputationResponse:
    """Evaluates reputation of an entity based on community report counts."""
    norm_val = value.strip().lower()
    # Also check variations for phone or url
    cleaned_digits = re.sub(r'\D', '', norm_val)
    phone_with_prefix = f"+91{cleaned_digits}" if len(cleaned_digits) == 10 else None

    filters = [EntityReputation.value == norm_val]
    if phone_with_prefix:
        filters.append(EntityReputation.value == phone_with_prefix)

    from sqlalchemy import or_
    rep = db.query(EntityReputation).filter(or_(*filters)).first()

    if not rep or rep.report_count == 0:
        return ReputationResponse(
            value=value,
            report_count=0,
            reputation="UNKNOWN",
            last_reported=None,
        )

    count = rep.report_count
    if count >= 3:
        status_str = "BAD"
    elif count >= 1:
        status_str = "SUSPICIOUS"
    else:
        status_str = "UNKNOWN"

    last_rep_iso = rep.last_reported.strftime("%Y-%m-%dT%H:%M:%SZ") if rep.last_reported else None

    return ReputationResponse(
        value=rep.value,
        report_count=count,
        reputation=status_str,
        last_reported=last_rep_iso,
    )

def get_blocklist_entries(db: Session, target_type: Optional[str] = None) -> List[BlocklistItem]:
    """Retrieves all reported entities, optionally filtered by target type."""
    query = db.query(EntityReputation)
    if target_type:
        query = query.filter(EntityReputation.target_type == target_type)

    results = query.order_by(desc(EntityReputation.report_count), desc(EntityReputation.last_reported)).all()

    items = []
    for r in results:
        items.append(
            BlocklistItem(
                value=r.value,
                type=r.target_type,
                report_count=r.report_count,
                first_reported=r.first_reported.strftime("%Y-%m-%dT%H:%M:%SZ"),
                last_reported=r.last_reported.strftime("%Y-%m-%dT%H:%M:%SZ"),
            )
        )
    return items

def log_analysis_event(
    db: Session,
    analysis_type: str,
    scam_category: str,
    risk_level: str,
    signals: List[str],
):
    """Logs an analysis event for trend and statistical tracking."""
    log_item = AnalysisLog(
        analysis_type=analysis_type,
        scam_category=scam_category,
        risk_level=risk_level,
        signals_list=",".join(signals[:10]),
        created_at=datetime.now(timezone.utc),
    )
    db.add(log_item)
    db.commit()

def get_service_stats(db: Session) -> StatsResponse:
    """Computes aggregated service statistics for the stats endpoint."""
    total_reports = db.query(func.count(CommunityReport.id)).scalar() or 0

    # Counts by category from analysis logs
    cat_counts = (
        db.query(AnalysisLog.scam_category, func.count(AnalysisLog.id))
        .group_by(AnalysisLog.scam_category)
        .all()
    )
    by_category = {cat: count for cat, count in cat_counts if cat != "NONE"}

    # Top signals
    logs = db.query(AnalysisLog.signals_list).filter(AnalysisLog.signals_list != "").all()
    signal_counts: Dict[str, int] = {}
    for (s_list,) in logs:
        for s in s_list.split(","):
            s_clean = s.strip()
            if s_clean:
                signal_counts[s_clean] = signal_counts.get(s_clean, 0) + 1

    top_signals = [
        sig for sig, _ in sorted(signal_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    ]

    # Daily counts of community reports (last 7 days)
    daily_results = (
        db.query(
            func.strftime("%Y-%m-%d", CommunityReport.created_at).label("day"),
            func.count(CommunityReport.id),
        )
        .group_by("day")
        .order_by("day")
        .all()
    )

    daily_counts = [DailyCount(date=d or "2026-11-12", count=c) for d, c in daily_results]

    # Ensure at least some default representation if DB is fresh
    if not daily_counts:
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        daily_counts = [DailyCount(date=today_str, count=total_reports)]

    return StatsResponse(
        total_reports=total_reports,
        by_category=by_category,
        top_signals=top_signals,
        daily_counts=daily_counts,
    )

