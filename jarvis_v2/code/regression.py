from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from jarvis_v2.code.change_intelligence import ChangedFile, RepositoryChangeIntelligence
from jarvis_v2.code.impact_graph import ImpactGraph
from jarvis_v2.tests.intelligence import TestSuite


@dataclass
class VerificationTarget:
    path: str
    reason: str
    priority: int = 0
    affected_nodes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class RegressionAssessment:
    risk: str
    changed_files: list[ChangedFile]
    targets: list[VerificationTarget]
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "risk": self.risk,
            "changed_files": [x.to_dict() for x in self.changed_files],
            "targets": [x.to_dict() for x in self.targets],
            "reasons": self.reasons,
        }


class RegressionIntelligence:
    """Use Git changes and the cross-layer graph to select targeted verification."""

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.changes = RepositoryChangeIntelligence(self.root)

    def assess(self, changed: list[ChangedFile], graph: ImpactGraph) -> RegressionAssessment:
        changed_ids = {"file:" + x.path.replace("\\", "/") for x in changed}
        targets: dict[str, VerificationTarget] = {}
        reasons = []

        for edge in graph.edges:
            if edge.source not in changed_ids:
                continue
            target = graph.nodes.get(edge.target)
            if not target:
                continue
            if target.kind == "file":
                reason = f"{edge.relation} from changed file"
                targets.setdefault(target.file, VerificationTarget(target.file, reason, 3)).affected_nodes.append(target.id)
            elif target.kind == "api_route":
                reason = f"API route affected: {target.label}"
                targets.setdefault(target.file, VerificationTarget(target.file, reason, 5)).affected_nodes.append(target.id)
            elif target.kind == "database_table":
                reason = f"Database table affected: {target.label}"
                targets.setdefault(target.file, VerificationTarget(target.file, reason, 5)).affected_nodes.append(target.id)

        for target in list(targets.values()):
            if target.path.startswith(("test_", "tests/")) or ".test." in target.path or ".spec." in target.path:
                target.priority = max(target.priority, 10)

        if any(x.status.startswith(("D", "R")) for x in changed):
            risk = "high"
            reasons.append("A deleted or renamed file is part of the change.")
        elif any(t.priority >= 5 for t in targets.values()):
            risk = "high"
            reasons.append("The change touches an API or database boundary.")
        elif len(changed) > 5:
            risk = "medium"
            reasons.append("Multiple files changed.")
        else:
            risk = "low"

        return RegressionAssessment(risk, changed, sorted(targets.values(), key=lambda x: -x.priority), reasons)

    def test_plan(self, assessment: RegressionAssessment, suites: list[TestSuite]) -> list[list[str]]:
        """Return bounded test commands, prioritizing discovered test files when possible."""
        plan = []
        target_names = {Path(t.path).name for t in assessment.targets}
        for suite in suites:
            selected = [p for p in suite.test_files if Path(p).name in target_names]
            if selected and suite.framework == "pytest":
                plan.append([*suite.command[:-1], *selected])
            else:
                plan.append(suite.command)
        return plan
