from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()

def get_utc_now():
    return datetime.now(timezone.utc)

class CommunityReport(Base):
    __tablename__ = "community_reports"

    id = Column(Integer, primary_key=True, index=True)
    target_type = Column(String(16), nullable=False, index=True)  # url, vpa, phone
    value = Column(String(512), nullable=False, index=True)       # normalized target
    reason = Column(String(512), nullable=False)
    reporter_hash = Column(String(64), nullable=False, index=True)  # SHA-256 of reporter IP
    created_at = Column(DateTime, default=get_utc_now, nullable=False, index=True)

    __table_args__ = (
        Index("idx_reporter_target_day", "reporter_hash", "value", "created_at"),
    )

class EntityReputation(Base):
    __tablename__ = "entity_reputation"

    id = Column(Integer, primary_key=True, index=True)
    target_type = Column(String(16), nullable=False, index=True)  # url, vpa, phone
    value = Column(String(512), nullable=False, unique=True, index=True)
    report_count = Column(Integer, default=1, nullable=False)
    first_reported = Column(DateTime, default=get_utc_now, nullable=False)
    last_reported = Column(DateTime, default=get_utc_now, nullable=False)

class AnalysisLog(Base):
    """Lightweight audit log for statistics and trends."""
    __tablename__ = "analysis_logs"

    id = Column(Integer, primary_key=True, index=True)
    analysis_type = Column(String(16), nullable=False)  # message, voice
    scam_category = Column(String(64), nullable=False)
    risk_level = Column(String(16), nullable=False)     # LOW, MEDIUM, HIGH
    signals_list = Column(String(1024), default="")     # comma-separated signal names
    created_at = Column(DateTime, default=get_utc_now, nullable=False, index=True)

