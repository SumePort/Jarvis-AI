from jarvis_v2.knowledge.findings import Finding, EvidenceItem
from jarvis_v2.knowledge.reconciliation import KnowledgeConflict
from jarvis_v2.knowledge.resolution import KnowledgeResolver


def test_resolution_selects_explicit_finding():
    conflict = KnowledgeConflict("conflict:fd_1:fd_2", ["fd_1", "fd_2"], "contradiction")
    findings = [
        Finding("fd_1", "uses PostgreSQL", "verified", 0.9, ["ev_1"]),
        Finding("fd_2", "uses SQLite", "verified", 0.8, ["ev_2"]),
    ]
    evidence = [
        EvidenceItem("ev_1", "config", "postgres config", "config", 0.99),
        EvidenceItem("ev_2", "history", "old sqlite config", "git", 0.4),
    ]
    result = KnowledgeResolver().resolve(conflict, findings, evidence)
    assert result.status == "resolved"
    assert result.selected_finding_id == "fd_1"


def test_resolution_can_remain_unresolved():
    conflict = KnowledgeConflict("conflict:fd_1:fd_2", ["fd_1", "fd_2"], "contradiction")
    findings = [Finding("fd_1", "enabled", "verified", 0.8), Finding("fd_2", "disabled", "verified", 0.8)]
    result = KnowledgeResolver().resolve(conflict, findings)
    assert result.status == "unresolved"
