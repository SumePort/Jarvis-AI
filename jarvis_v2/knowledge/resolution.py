from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from jarvis_v2.knowledge.findings import Finding, FindingStore, EvidenceItem
from jarvis_v2.knowledge.reconciliation import KnowledgeConflict


@dataclass
class Resolution:
    conflict_id: str
    selected_finding_id: str | None
    status: str
    rationale: str
    evidence_ids: list[str] = field(default_factory=list)
    resolved_at: str = ""

    def __post_init__(self):
        if not self.resolved_at:
            self.resolved_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return self.__dict__.copy()


class KnowledgeResolver:
    """Resolve knowledge conflicts only with explicit evidence or an explicit decision."""

    def resolve(
        self,
        conflict: KnowledgeConflict,
        findings: list[Finding],
        evidence: list[EvidenceItem] = (),
        selected_finding_id: str | None = None,
        rationale: str = "",
    ) -> Resolution:
        allowed = set(conflict.finding_ids)
        candidates = [f for f in findings if f.id in allowed]
        if selected_finding_id is not None and selected_finding_id not in allowed:
            raise ValueError("selected finding is not part of the conflict")

        evidence_by_id = {e.id: e for e in evidence}
        if selected_finding_id is None:
            scored = []
            for finding in candidates:
                support = [
                    evidence_by_id[eid] for eid in finding.evidence_ids
                    if eid in evidence_by_id
                ]
                score = sum(e.confidence for e in support) + finding.confidence
                scored.append((score, finding))
            scored.sort(key=lambda x: x[0], reverse=True)
            if len(scored) == 1 or not scored:
                return Resolution(
                    conflict.conflict_id, None, "unresolved",
                    rationale or "Insufficient evidence to resolve the conflict.",
                )
            if scored[0][0] <= scored[1][0]:
                return Resolution(
                    conflict.conflict_id, None, "unresolved",
                    rationale or "Available evidence does not distinguish the competing findings.",
                )
            selected_finding_id = scored[0][1].id

        if not rationale:
            rationale = "Selected using explicit resolution input or stronger available evidence."

        evidence_ids = []
        for finding in candidates:
            if finding.id == selected_finding_id:
                evidence_ids.extend(finding.evidence_ids)

        return Resolution(
            conflict.conflict_id, selected_finding_id, "resolved",
            rationale, sorted(set(evidence_ids)),
        )

    def apply(self, resolution: Resolution, findings: list[Finding]) -> list[Finding]:
        if resolution.status != "resolved" or not resolution.selected_finding_id:
            return findings

        result = []
        for finding in findings:
            if finding.id not in {resolution.selected_finding_id} and finding.id in set(
                resolution.conflict_id.split(":")[1:]
            ):
                result.append(Finding(
                    finding.id, finding.statement, "rejected", finding.confidence,
                    finding.evidence_ids, finding.rejected_hypothesis_ids,
                    finding.unresolved_questions, finding.created_at,
                ))
            else:
                result.append(finding)
        return result
