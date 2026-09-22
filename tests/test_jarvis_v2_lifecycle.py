from datetime import datetime, timedelta, timezone

from jarvis_v2.knowledge.findings import EvidenceItem, Finding
from jarvis_v2.knowledge.lifecycle import KnowledgeLifecycle


def test_old_knowledge_requires_revalidation():
    now = datetime.now(timezone.utc)
    old = (now - timedelta(days=90)).isoformat()
    evidence = EvidenceItem("ev_old", "config", "old config", "config", 0.9, old)
    finding = Finding("fd_old", "database is SQLite", "verified", 0.9, ["ev_old"], created_at=old)

    result = KnowledgeLifecycle(half_life_days=30).assess([finding], [evidence], now)
    assert result.stale_finding_ids == ["fd_old"]
    assert result.revalidation
    assert result.revalidation[0].priority == 10


def test_recent_knowledge_stays_fresh():
    now = datetime.now(timezone.utc)
    recent = (now - timedelta(days=2)).isoformat()
    evidence = EvidenceItem("ev_new", "config", "new config", "config", 0.95, recent)
    finding = Finding("fd_new", "database is PostgreSQL", "verified", 0.95, ["ev_new"], created_at=recent)

    result = KnowledgeLifecycle(half_life_days=30).assess([finding], [evidence], now)
    assert result.freshness[0].status == "fresh"
    assert not result.revalidation
