from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from jarvis_v2.actions.executor import ActionExecutor, ActionObservation
from jarvis_v2.actions.planner import ActionPlan, ActionPlanner
from jarvis_v2.loop.controller import Verification
from .adaptive import Replanner


@dataclass
class EnvironmentLoopResult:
    iterations: int
    actions: list[ActionObservation] = field(default_factory=list)
    observations: list[dict[str, Any]] = field(default_factory=list)
    verifications: list[Verification] = field(default_factory=list)
    replanned: bool = False


class EnvironmentAgentLoop:
    """Adaptive loop wired directly to structured computer observations."""

    def __init__(self, planner: ActionPlanner, executor: ActionExecutor,
                 observer: Any, max_iterations: int = 4):
        self.planner = planner
        self.executor = executor
        self.observer = observer
        self.max_iterations = max(1, max_iterations)

    def run(self, plan: ActionPlan,
            verifier: Callable[[ActionPlan, list[ActionObservation], dict[str, Any]], Verification],
            replanner: Replanner | None = None, confirmed: bool = False) -> EnvironmentLoopResult:
        current = self.planner.validate(plan)
        result = EnvironmentLoopResult(0)
        before = self.observer.capture()
        for _ in range(self.max_iterations):
            result.iterations += 1
            current = self.planner.validate(current)
            actions = self.executor.execute(current, confirmed=confirmed)
            result.actions.extend(actions)
            after = self.observer.observe_change(before)
            evidence = {"snapshot": after.snapshot, "changes": after.changes}
            result.observations.append(evidence)
            verification = verifier(current, actions, evidence)
            result.verifications.append(verification)
            if verification.success or any(a.requires_confirmation for a in actions):
                return result
            if replanner is None:
                return result
            current = replanner.replan(plan.goal, result.observations, current)
            result.replanned = True
            before = after
        return result
