import pytest
from extras.app.database.repository import (
    record_community_report,
    get_entity_reputation,
    get_blocklist_entries,
    get_service_stats,
)
from extras.app.analyzers.message_analyzer import MessageAnalyzer

def test_community_report_and_reputation_tiers(db_session):
    # Initial state: 0 reports -> UNKNOWN
    rep0 = get_entity_reputation(db_session, "test@ybl")
    assert rep0.report_count == 0
    assert rep0.reputation == "UNKNOWN"

    # Report 1 from IP 1.1.1.1 -> SUSPICIOUS
    status1, count1 = record_community_report(db_session, "vpa", "test@ybl", "Suspicious fee", "1.1.1.1")
    assert status1 == "recorded"
    assert count1 == 1

    rep1 = get_entity_reputation(db_session, "test@ybl")
    assert rep1.report_count == 1
    assert rep1.reputation == "SUSPICIOUS"

    # Report 2 from IP 2.2.2.2 -> SUSPICIOUS
    status2, count2 = record_community_report(db_session, "vpa", "test@ybl", "Deceptive refund", "2.2.2.2")
    assert status2 == "recorded"
    assert count2 == 2

    rep2 = get_entity_reputation(db_session, "test@ybl")
    assert rep2.report_count == 2
    assert rep2.reputation == "SUSPICIOUS"

    # Report 3 from IP 3.3.3.3 -> BAD (>= 3)
    status3, count3 = record_community_report(db_session, "vpa", "test@ybl", "Fraud confirm", "3.3.3.3")
    assert status3 == "recorded"
    assert count3 == 3

    rep3 = get_entity_reputation(db_session, "test@ybl")
    assert rep3.report_count == 3
    assert rep3.reputation == "BAD"

def test_duplicate_prevention_same_ip(db_session):
    # Same IP 10.0.0.1 reports same entity twice
    st1, c1 = record_community_report(db_session, "phone", "+919876543210", "First scam call", "10.0.0.1")
    assert st1 == "recorded"
    assert c1 == 1

    # Second submission from same IP within 24h
    st2, c2 = record_community_report(db_session, "phone", "+919876543210", "Duplicate report", "10.0.0.1")
    assert st2 == "duplicate_ignored"
    assert c2 == 1  # count does NOT increment

def test_rate_limiting_per_ip(db_session):
    ip = "192.168.1.100"
    # Submit max reports
    for i in range(15):
        record_community_report(db_session, "vpa", f"bot{i}@ybl", "Report", ip)

    # 16th report should hit rate limit
    st_limit, _ = record_community_report(db_session, "vpa", "overflow@ybl", "Report", ip)
    assert st_limit == "rate_limited"

def test_blocklist_retrieval(db_session):
    record_community_report(db_session, "url", "http://bad1.xyz", "Phish", "1.1.1.1")
    record_community_report(db_session, "vpa", "bad1@ybl", "Fraud", "1.1.1.2")

    all_items = get_blocklist_entries(db_session)
    assert len(all_items) >= 2

    vpa_items = get_blocklist_entries(db_session, target_type="vpa")
    assert all(i.type == "vpa" for i in vpa_items)

def test_stats_generation(db_session):
    stats = get_service_stats(db_session)
    assert stats.total_reports >= 0
    assert isinstance(stats.by_category, dict)
    assert isinstance(stats.top_signals, list)

def test_seed_script_execution():
    from extras.app.database.seed import seed_community_reports
    seed_community_reports("sample_data/extras/reports_seed.json")
    # Verify non-existent seed path is handled gracefully
    seed_community_reports("sample_data/extras/non_existent.json")

@pytest.mark.asyncio
async def test_community_signal_injection_in_message_analyzer(db_session):
    # Seed a bad VPA with 3 reports
    record_community_report(db_session, "vpa", "blockedvpa@ybl", "R1", "1.1.1.1")
    record_community_report(db_session, "vpa", "blockedvpa@ybl", "R2", "1.1.1.2")
    record_community_report(db_session, "vpa", "blockedvpa@ybl", "R3", "1.1.1.3")

    analyzer = MessageAnalyzer()
    msg = "Please transfer Rs 500 to blockedvpa@ybl to verify your account"
    res = await analyzer.analyze(msg, source="sms", db=db_session)

    # Check that Community Blocklist Match signal was injected
    signal_names = [s.name for s in res.signals]
    assert "Community Blocklist Match" in signal_names
    assert res.risk_level in ("MEDIUM", "HIGH")
