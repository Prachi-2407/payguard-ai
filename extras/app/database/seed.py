import os
import json
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from extras.app.database.session import SessionLocal, init_db
from extras.app.database.models import CommunityReport, EntityReputation
from extras.app.database.repository import normalize_target_value, hash_reporter_ip

logger = logging.getLogger(__name__)

def seed_community_reports(seed_path: str = "sample_data/extras/reports_seed.json"):
    """
    Idempotently seeds community reports from a JSON seed file.
    Does not duplicate records on repeated executions.
    """
    init_db()
    if not os.path.exists(seed_path):
        logger.warning(f"Seed file not found: {seed_path}")
        return

    with open(seed_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    db: Session = SessionLocal()
    now = datetime.now(timezone.utc)
    seeded_count = 0

    try:
        for item in items:
            t_type = item["target_type"]
            raw_val = item["value"]
            norm_val = normalize_target_value(t_type, raw_val)
            reason = item.get("reason", "Community fraud report")
            count = int(item.get("report_count", 1))

            # Check if reputation entry already exists
            rep = db.query(EntityReputation).filter(EntityReputation.value == norm_val).first()
            if not rep:
                rep = EntityReputation(
                    target_type=t_type,
                    value=norm_val,
                    report_count=count,
                    first_reported=now - timedelta(days=count * 2),
                    last_reported=now - timedelta(hours=count),
                )
                db.add(rep)
                seeded_count += 1
            else:
                # Update count if seed specifies higher count
                if count > rep.report_count:
                    rep.report_count = count
                    rep.last_reported = now

            # Ensure at least one matching CommunityReport exists for auditing
            dummy_hash = hash_reporter_ip(f"seed-reporter-{norm_val}")
            existing_report = (
                db.query(CommunityReport)
                .filter(CommunityReport.value == norm_val, CommunityReport.reporter_hash == dummy_hash)
                .first()
            )
            if not existing_report:
                report = CommunityReport(
                    target_type=t_type,
                    value=norm_val,
                    reason=reason,
                    reporter_hash=dummy_hash,
                    created_at=now - timedelta(days=1),
                )
                db.add(report)

        db.commit()
        print(f"Community reports seed completed. Successfully processed {len(items)} seed entities.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding community reports: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_community_reports()

