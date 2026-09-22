from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from jarvis_v2.diagnostics.root_cause import CauseHypothesis, InvestigationAction, RootCauseInvestigation


@dataclass
class InvestigationEvidence:
    action: str
    target: str
    result: str
    success: bool
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class InvestigationRun:
    hypothesis: CauseHypothesis
    evidence: list[InvestigationEvidence] = field(default_factory=list)
    iterations: int = 0
    resolved: bool = False
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "hypothesis": self.hypothesis.to_dict(),
            "evidence": [e.to_dict() for e in self.evidence],
            "iterations": self.iterations,
            "resolved": self.resolved,
            "summary": self.summary,
        }


class InvestigationExecutor:
    """Execute only explicitly registered, bounded investigation actions."""

    def __init__(self):
        self.handlers: dict[str, Callable[[str], InvestigationEvidence]] = {}

    def register(self, action: str, handler: Callable[[str], InvestigationEvidence]) -> None:
        self.handlers[action] = handler

    def execute(self, action: InvestigationAction) -> InvestigationEvidence:
        handler = self.handlers.get(action.action)
        if handler is None:
            return InvestigationEvidence(
                action.action, action.target, "No investigation adapter registered.", False
            )
        try:
            return handler(action.target)
        except Exception as exc:
            return InvestigationEvidence(
                action.action, action.target, str(exc), False
            )


class InvestigationLoop:
    """Bounded hypothesis → evidence → reassessment loop.

    The loop never executes arbitrary commands; every investigation action must
    be registered explicitly by the host application.
    """

    def __init__(self, executor: InvestigationExecutor, max_iterations: int = 5):
        self.executor = executor
        self.max_iterations = max(1, min(max_iterations, 20))

    def run(
        self,
        investigation: RootCauseInvestigation,
        reassess: Callable[[CauseHypothesis, list[InvestigationEvidence]], CauseHypothesis],
    ) -> InvestigationRun | None:
        if not investigation.hypotheses:
            return None

        hypothesis = investigation.hypotheses[0]
        evidence: list[InvestigationEvidence] = []

        for iteration in range(self.max_iterations):
            actions = [
                action for action in investigation.next_actions
                if action.target == hypothesis.target or action.target == "incident"
            ]
            if not actions:
                break

            action = actions[min(iteration, len(actions) - 1)]
            item = self.executor.execute(action)
            evidence.append(item)

            updated = reassess(hypothesis, evidence)
            hypothesis = updated

            if updated.confidence >= 0.9 and not updated.missing_evidence:
                return InvestigationRun(
                    hypothesis, evidence, iteration + 1, True,
                    "Evidence threshold reached for this hypothesis.",
                )

        return InvestigationRun(
            hypothesis, evidence, len(evidence), False,
            "Investigation stopped at the configured evidence/iteration bound.",
        )
