import json
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class ScanHistory(Base):
    __tablename__ = "scan_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    type = Column(String(32), index=True, nullable=False)
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(String(16), index=True, nullable=False)
    verdict = Column(String(128), nullable=False)
    signals_json = Column(Text, nullable=False, default="[]")
    explanation = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=False)
    analyzed_at = Column(String(64), nullable=False)
    raw_input_masked = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    @property
    def signals(self):
        try:
            return json.loads(self.signals_json)
        except Exception:
            return []

    @signals.setter
    def signals(self, value):
        self.signals_json = json.dumps(value)

class TransactionAudit(Base):
    __tablename__ = "transaction_audit"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(64), index=True, nullable=False)
    amount = Column(Float, nullable=False)
    receiver = Column(String(128), index=True, nullable=False)
    timestamp = Column(String(64), nullable=False)
    channel = Column(String(32), default="upi")
    note = Column(Text, default="")
    risk_score = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
