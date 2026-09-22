from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from jarvis_v2.actions.executor import ActionExecutor, ActionObservation
from jarvis_v2.actions.planner import ActionPlan, ActionPlanner
from jarvis_v2.loop.controller import Verification


class Replanner(Protocol):
    def replan(self, goal: str, observations: list[dict[str, Any]], previous: ActionPlan) -> ActionPlan: ...


@dataclass
class AdaptiveLoopResult:
    goal: str
    iterations: int
    actions: list[ActionObservation] = field(default_factory=list)
    observations: list[dict[str, Any]] = field(default_factory=list)
    verifications: list[Verification] = field(default_factory=list)
    replanned: bool = False


class AdaptiveAgentLoop:
    """Bounded observe -> verify -> replan loop.

    Replanning is only given observations and the original goal. Every new
    plan is validated again by ActionPlanner before execution.
    """

    def __init__(self, planner: ActionPlanner, executor: ActionExecutor, max_iterations: int = 4,
                 max_steps_per_iteration: int = 4):
        self.planner = planner
        self.executor = executor
        self.max_iterations = max(1, max_iterations)
        self.max_steps = max(1, max_steps_per_iteration)

    def run(self, plan: ActionPlan, observer: Callable[[], dict[str, Any]],
            verifier: Callable[[ActionPlan, list[ActionObservation], dict[str, Any]], Verification],
            replanner: Replanner | None = None, confirmed: bool = False) -> AdaptiveLoopResult:
        current = self.planner.validate(plan)
        result = AdaptiveLoopResult(current.goal, 0)
        for iteration in range(self.max_iterations):
            result.iterations += 1
            current = self.planner.validate(
                ActionPlan(current.goal, current.steps[:self.max_steps], current.blocked, list(current.warnings))
            )
            actions = self.executor.execute(current, confirmed=confirmed)
            result.actions.extend(actions)
            state = observer()
            result.observations.append(state)
            verification = verifier(current, actions, state)
            result.verifications.append(verification)
            if verification.success:
                return result
            if replanner is None:
                return result
            if any(a.requires_confirmation for a in actions):
                return result
            current = replanner.replan(plan.goal, result.observations, current)
            result.replanned = True
        return result
