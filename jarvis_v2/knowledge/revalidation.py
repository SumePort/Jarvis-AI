from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from jarvis_v2.knowledge.findings import EvidenceItem, Finding
from jarvis_v2.knowledge.lifecycle import RevalidationRequest


@dataclass
class RevalidationStep:
    action: str
    target: str
    reason: str
    priority: int
    source_evidence_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class RevalidationPlan:
    finding_id: str
    steps: list[RevalidationStep] = field(default_factory=list)
    blocked: bool = False
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "finding_id": self.finding_id,
            "steps": [x.to_dict() for x in self.steps],
            "blocked": self.blocked,
            "reason": self.reason,
        }


class RevalidationPlanner:
    """Turn stale findings into bounded, explicit verification plans."""

    SAFE_ACTIONS = {
        "inspect_source",
        "inspect_config",
        "inspect_git_history",
        "run_targeted_test",
        "inspect_runtime",
    }

    def plan(
        self,
        request: RevalidationRequest,
        finding: Finding,
        evidence: list[EvidenceItem] = (),
    ) -> RevalidationPlan:
        evidence_by_id = {e.id: e for e in evidence}
        steps: list[RevalidationStep] = []

        for evidence_id in finding.evidence_ids:
            item = evidence_by_id.get(evidence_id)
            if not item:
                continue

            action = self._action_for_source(item.source, item.kind)
            if action not in self.SAFE_ACTIONS:
                continue

            steps.append(RevalidationStep(
                action=action,
                target=item.source or finding.statement,
                reason=f"Revalidate finding using its original evidence source: {item.source or item.kind}.",
                priority=request.priority,
                source_evidence_ids=[evidence_id],
            ))

        if not steps:
            steps.append(RevalidationStep(
                "inspect_source",
                finding.statement,
                "Original evidence is unavailable; inspect the current source of truth.",
                request.priority,
                [],
            ))

        return RevalidationPlan(request.finding_id, steps, False)

    @staticmethod
    def _action_for_source(source: str, kind: str) -> str:
        value = f"{source} {kind}".lower()
        if "git" in value or "history" in value:
            return "inspect_git_history"
        if "test" in value or "pytest" in value:
            return "run_targeted_test"
        if "runtime" in value or "process" in value:
            return "inspect_runtime"
        if "config" in value or "env" in value:
            return "inspect_config"
        return "inspect_source"
