from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from jarvis_v2.code.change_intelligence import ChangedFile
from jarvis_v2.diagnostics.incident import IncidentReport
from jarvis_v2.knowledge.world_graph import UnifiedWorldGraph


@dataclass
class CauseHypothesis:
    target: str
    hypothesis: str
    evidence_for: list[str] = field(default_factory=list)
    evidence_against: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class InvestigationAction:
    action: str
    target: str
    reason: str
    priority: int = 0

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class RootCauseInvestigation:
    hypotheses: list[CauseHypothesis] = field(default_factory=list)
    next_actions: list[InvestigationAction] = field(default_factory=list)
    conclusion: str = ""

    def to_dict(self) -> dict:
        return {
            "hypotheses": [h.to_dict() for h in self.hypotheses],
            "next_actions": [a.to_dict() for a in self.next_actions],
            "conclusion": self.conclusion,
        }


class RootCauseInvestigator:
    """Generate conservative, evidence-traceable root-cause hypotheses."""

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def investigate(
        self,
        incident: IncidentReport,
        graph: UnifiedWorldGraph,
        changes: list[ChangedFile],
    ) -> RootCauseInvestigation:
        hypotheses: list[CauseHypothesis] = []

        changed_paths = {x.path.replace("\\", "/") for x in changes}
        for path in changed_paths:
            node_id = "file:" + path
            if node_id not in graph.nodes:
                continue
            downstream = graph.related(node_id, depth=2)
            affected_labels = [n.label for n in downstream[:8]]
            evidence_for = [
                f"file changed: {path}",
                *[f"downstream component: {label}" for label in affected_labels[:4]],
            ]
            against = []
            missing = []
            if not incident.failures:
                missing.append("A reproducible failure is not available.")
            if not incident.timeline:
                missing.append("A commit timeline is not available.")
            hypotheses.append(CauseHypothesis(
                target=node_id,
                hypothesis=f"The change in {path} may be related to the incident.",
                evidence_for=evidence_for,
                evidence_against=against,
                missing_evidence=missing,
                confidence=min(0.9, 0.4 + 0.1 * len(affected_labels)),
            ))

        actions: list[InvestigationAction] = []
        if not incident.failures:
            actions.append(InvestigationAction(
                "reproduce_failure", "incident", "No failure evidence is available.", 10
            ))
        if not incident.timeline:
            actions.append(InvestigationAction(
                "inspect_git_history", "incident", "Timeline evidence is missing.", 8
            ))
        for hypothesis in hypotheses[:10]:
            actions.append(InvestigationAction(
                "inspect_change", hypothesis.target,
                "Inspect the changed file and its downstream dependencies.", 6
            ))

        if hypotheses:
            conclusion = (
                f"Generated {len(hypotheses)} candidate cause(s). "
                "They are hypotheses requiring verification, not established root causes."
            )
        else:
            conclusion = "No candidate cause could be mapped to the current world graph."

        return RootCauseInvestigation(hypotheses, sorted(actions, key=lambda x: -x.priority), conclusion)
