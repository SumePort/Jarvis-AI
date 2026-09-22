from pathlib import Path

from jarvis_v2.knowledge.findings import Finding
from jarvis_v2.knowledge.reconciliation import KnowledgeReconciler


def test_reconciliation_detects_conflict(tmp_path: Path):
    findings = [
        Finding("fd_1", "SumePort uses PostgreSQL", "verified", 0.9),
        Finding("fd_2", "SumePort uses SQLite", "verified", 0.9),
    ]
    result = KnowledgeReconciler().reconcile(findings)
    assert len(result.conflicts) == 1
    assert result.conflicts[0].status == "open"
