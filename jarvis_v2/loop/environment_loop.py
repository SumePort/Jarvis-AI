from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from jarvis_v2.actions.executor import ActionExecutor, ActionObservation
from jarvis_v2.actions.planner import ActionPlan, ActionPlanner
from jarvis_v2.loop.controller import Verification
from jarvis_v2.runtime.high_impact_workflow import HighImpactWorkflow, WorkflowState
from .adaptive import Replanner


@dataclass
class EnvironmentLoopResult:
    iterations: int
    actions: list[ActionObservation] = field(default_factory=list)
    observations: list[dict[str, Any]] = field(default_factory=list)
    verifications: list[Verification] = field(default_factory=list)
    replanned: bool = False
    state: WorkflowState = WorkflowState.RUNNING
    user_message: str | None = None
    sensitive_request_id: str | None = None


class EnvironmentAgentLoop:
    """Adaptive loop with a deterministic sensitive-input stop boundary."""

    def __init__(self, planner: ActionPlanner, executor: ActionExecutor,
                 observer: Any, max_iterations: int = 4,
                 high_impact_workflow: HighImpactWorkflow | None = None):
        self.planner = planner
        self.executor = executor
        self.observer = observer
        self.max_iterations = max(1, max_iterations)
        self.high_impact_workflow = high_impact_workflow or HighImpactWorkflow()

    @staticmethod
    def _ui_evidence(snapshot: dict[str, Any], changes: list[dict[str, Any]]) -> str:
        parts: list[str] = []
        for key in ("windows", "applications", "browser_pages", "visual_evidence"):
            value = snapshot.get(key, [])
            if value:
                parts.append(str(value))
        if changes:
            parts.append(str(changes[-20:]))
        return " ".join(parts)

    def run(self, plan: ActionPlan,
            verifier: Callable[[ActionPlan, list[ActionObservation], dict[str, Any]], Verification],
            replanner: Replanner | None = None, confirmed: bool = False,
            resume_request_id: str | None = None) -> EnvironmentLoopResult:
        current = self.planner.validate(plan)
        result = EnvironmentLoopResult(0)
        before = self.observer.capture()

        if resume_request_id:
            transition = self.high_impact_workflow.resume(resume_request_id)
            result.state = transition.state
            result.user_message = transition.message

        for _ in range(self.max_iterations):
            result.iterations += 1
            current = self.planner.validate(current)

            # Inspect the current UI BEFORE allowing another model action.
            evidence_text = self._ui_evidence(before.snapshot, before.changes)
            transition = self.high_impact_workflow.inspect_ui(evidence_text)
            if transition.state == WorkflowState.WAITING_FOR_USER:
                result.state = transition.state
                result.user_message = transition.message
                result.sensitive_request_id = transition.request_id
                return result

            actions = self.executor.execute(current, confirmed=confirmed)
            result.actions.extend(actions)

            after = self.observer.observe_change(before)
            evidence = {"snapshot": after.snapshot, "changes": after.changes}
            result.observations.append(evidence)

            # The action may have navigated into a PIN/OTP/password/amount
            # screen. Detect it immediately and stop before the next action.
            evidence_text = self._ui_evidence(after.snapshot, after.changes)
            transition = self.high_impact_workflow.inspect_ui(evidence_text)
            if transition.state == WorkflowState.WAITING_FOR_USER:
                result.state = transition.state
                result.user_message = transition.message
                result.sensitive_request_id = transition.request_id
                return result

            verification = verifier(current, actions, evidence)
            result.verifications.append(verification)
            if verification.success or any(a.requires_confirmation for a in actions):
                result.state = WorkflowState.COMPLETED if verification.success else WorkflowState.RUNNING
                return result
            if replanner is None:
                return result
            current = replanner.replan(plan.goal, result.observations, current)
            result.replanned = True
            before = after
        return result
