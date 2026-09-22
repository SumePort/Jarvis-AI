from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from jarvis_v2.knowledge.findings import EvidenceItem, Finding
from jarvis_v2.knowledge.revalidation import RevalidationPlan, RevalidationStep


@dataclass
class RefreshResult:
    finding: Finding
    new_evidence: list[EvidenceItem] = field(default_factory=list)
    previous_status: str = ""
    refreshed: bool = False
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "finding": self.finding.to_dict(),
            "new_evidence": [e.to_dict() for e in self.new_evidence],
            "previous_status": self.previous_status,
            "refreshed": self.refreshed,
            "reason": self.reason,
        }


class KnowledgeRefresher:
    """Apply externally collected verification evidence to a finding.

    Evidence collection is delegated to explicitly registered handlers; this
    component only evaluates the returned evidence and updates knowledge state.
    """

    def refresh(
        self,
        finding: Finding,
        plan: RevalidationPlan,
        collected: list[EvidenceItem],
    ) -> RefreshResult:
        previous = finding.status
        if plan.blocked:
            return RefreshResult(finding, collected, previous, False, plan.reason)

        if not collected:
            updated = Finding(
                finding.id, finding.statement, "unresolved",
                max(0.0, finding.confidence * 0.75),
                finding.evidence_ids, finding.rejected_hypothesis_ids,
                sorted(set(finding.unresolved_questions + ["Revalidation produced no evidence."])),
                finding.created_at,
            )
            return RefreshResult(updated, [], previous, False, "No new evidence was collected.")

        support = [e for e in collected if e.confidence >= 0.7]
        contradict = [e for e in collected if e.confidence < 0.3]

        if support and not contradict:
            status = "verified"
            confidence = min(0.99, max(finding.confidence, sum(e.confidence for e in support) / len(support)))
            reason = "New verification evidence supports the existing finding."
            refreshed = True
        elif contradict and not support:
            status = "needs_reconciliation"
            confidence = max(0.1, finding.confidence * 0.5)
            reason = "New evidence conflicts with the existing finding."
            refreshed = True
        else:
            status = "unresolved"
            confidence = max(0.1, finding.confidence * 0.75)
            reason = "New evidence is mixed or insufficient to refresh the finding."
            refreshed = True

        updated = Finding(
            finding.id, finding.statement, status, confidence,
            sorted(set(finding.evidence_ids + [e.id for e in collected])),
            finding.rejected_hypothesis_ids,
            finding.unresolved_questions,
            datetime.now(timezone.utc).isoformat(),
        )
        return RefreshResult(updated, collected, previous, refreshed, reason)


class RevalidationExecutor:
    """Execute only explicitly registered revalidation adapters."""

    def __init__(self):
        self.handlers = {}

    def register(self, action: str, handler) -> None:
        self.handlers[action] = handler

    def execute(self, plan: RevalidationPlan) -> list[EvidenceItem]:
        evidence = []
        for step in plan.steps:
            handler = self.handlers.get(step.action)
            if handler is None:
                continue
            result = handler(step.target)
            if isinstance(result, EvidenceItem):
                evidence.append(result)
            elif isinstance(result, list):
                evidence.extend(x for x in result if isinstance(x, EvidenceItem))
        return evidence
