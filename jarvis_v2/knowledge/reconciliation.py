from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable

from jarvis_v2.knowledge.findings import Finding, EvidenceItem


@dataclass
class KnowledgeConflict:
    conflict_id: str
    finding_ids: list[str]
    reason: str
    status: str = "open"
    resolution: str = ""
    resolved_by: str = ""
    resolved_at: str = ""

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class ReconciliationResult:
    conflicts: list[KnowledgeConflict] = field(default_factory=list)
    consistent_findings: list[str] = field(default_factory=list)
    stale_findings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "conflicts": [c.to_dict() for c in self.conflicts],
            "consistent_findings": self.consistent_findings,
            "stale_findings": self.stale_findings,
        }


class KnowledgeReconciler:
    """Detect and explicitly track contradictory findings.

    It never silently chooses a winner. Resolution requires evidence or an
    explicit host decision.
    """

    def reconcile(self, findings: Iterable[Finding], evidence: Iterable[EvidenceItem] = ()) -> ReconciliationResult:
        items = list(findings)
        evidence_by_id = {e.id: e for e in evidence}
        conflicts: list[KnowledgeConflict] = []
        consistent: list[str] = []
        stale: list[str] = []

        for index, left in enumerate(items):
            for right in items[index + 1:]:
                if left.status == "rejected" or right.status == "rejected":
                    continue
                if self._contradict(left.statement, right.statement):
                    conflict = KnowledgeConflict(
                        conflict_id=f"conflict:{left.id}:{right.id}",
                        finding_ids=[left.id, right.id],
                        reason="Findings contain mutually exclusive assertions.",
                    )
                    conflicts.append(conflict)

        conflicted_ids = {fid for c in conflicts for fid in c.finding_ids}
        for finding in items:
            if finding.id not in conflicted_ids:
                consistent.append(finding.id)
                continue
            times = [
                evidence_by_id[eid].observed_at
                for eid in finding.evidence_ids
                if eid in evidence_by_id and evidence_by_id[eid].observed_at
            ]
            if times and max(times) < datetime.now(timezone.utc).isoformat():
                stale.append(finding.id)

        return ReconciliationResult(conflicts, consistent, stale)

    @staticmethod
    def _contradict(left: str, right: str) -> bool:
        a, b = left.strip().lower(), right.strip().lower()
        if a == b:
            return False
        pairs = [
            ("uses postgresql", "uses sqlite"),
            ("uses sqlite", "uses postgresql"),
            ("uses postgres", "uses sqlite"),
            ("enabled", "disabled"),
            ("is enabled", "is disabled"),
            ("exists", "does not exist"),
            ("is running", "is not running"),
        ]
        return any(x in a and y in b for x, y in pairs)
