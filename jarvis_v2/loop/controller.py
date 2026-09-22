"""Plan -> act -> observe -> verify control loop."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

from jarvis_v2.actions.executor import ActionExecutor, ActionObservation
from jarvis_v2.actions.planner import ActionPlan, ActionPlanner

@dataclass
class Verification:
    success: bool
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)

@dataclass
class LoopResult:
    plan: ActionPlan
    actions: list[ActionObservation]
    verification: Verification
    observations: list[dict[str, Any]] = field(default_factory=list)

class AgentLoop:
    """Execute a bounded action loop and verify the resulting state."""
    def __init__(self, planner: ActionPlanner, executor: ActionExecutor, max_steps: int = 8) -> None:
        self.planner = planner
        self.executor = executor
        self.max_steps = max_steps

    def run(self, plan: ActionPlan, observer: Callable[[], dict[str, Any]] | None = None,
            verifier: Callable[[ActionPlan, list[ActionObservation], dict[str, Any]], Verification] | None = None,
            confirmed: bool = False) -> LoopResult:
        plan = self.planner.validate(plan)
        bounded = ActionPlan(plan.goal, plan.steps[:self.max_steps], plan.blocked, list(plan.warnings))
        actions = self.executor.execute(bounded, confirmed=confirmed)
        state = observer() if observer else {}
        observations = [state] if state else []
        if verifier:
            verification = verifier(bounded, actions, state)
        else:
            failed = [a for a in actions if not a.success and not a.requires_confirmation]
            pending = [a for a in actions if a.requires_confirmation]
            if pending:
                verification = Verification(False, "Action requires confirmation.", {"pending": len(pending)})
            elif failed:
                verification = Verification(False, "One or more actions failed.", {"failed": len(failed)})
            elif not actions and bounded.steps:
                verification = Verification(False, "No action was executed.")
            else:
                verification = Verification(True, "Actions executed; no explicit state verifier was provided.")
        return LoopResult(bounded, actions, verification, observations)
