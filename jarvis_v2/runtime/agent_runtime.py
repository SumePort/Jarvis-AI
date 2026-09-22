from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from jarvis_v2.actions.executor import ActionExecutor, ActionObservation
from jarvis_v2.actions.planner import ActionPlan, ActionPlanner, ActionPlannerBrain
from jarvis_v2.core.types import DataClass
from jarvis_v2.knowledge.fabric import JarvisKnowledgeFabric
from jarvis_v2.reasoning.action_reasoner import KnowledgeActionReasoner
from jarvis_v2.environment.observer import EnvironmentObserver
from jarvis_v2.loop.controller import Verification
from jarvis_v2.loop.environment_loop import EnvironmentAgentLoop, EnvironmentLoopResult
from jarvis_v2.runtime.high_impact_workflow import HighImpactWorkflow, WorkflowState


class _BrainReplanner:
    def __init__(self, brain: ActionPlannerBrain, planner: ActionPlanner):
        self.brain, self.planner = brain, planner

    def replan(self, goal: str, observations: list[dict[str, Any]], previous: ActionPlan) -> ActionPlan:
        return self.planner.from_brain(
            self.brain, goal,
            {"goal": goal, "previous_plan": previous.goal, "observations": observations[-4:]},
        )


@dataclass
class _PausedRun:
    request: str
    plan: ActionPlan
    confirmed: bool
    data_class: DataClass
    verifier: Callable | None
    replanner: Any | None


@dataclass
class JarvisAgentResult:
    request: str
    relevant_nodes: list[str]
    rationale: list[str]
    execution: Any = None
    blocked: bool = False
    reason: str = ""
    state: WorkflowState = WorkflowState.RUNNING
    resume_request_id: str | None = None
    user_message: str | None = None


class JarvisAgentRuntime:
    """End-to-end agent boundary with resumable high-impact workflows."""

    def __init__(self, planner: ActionPlanner, executor: ActionExecutor,
                 fabric: JarvisKnowledgeFabric, brain: ActionPlannerBrain | None = None,
                 environment_observer: EnvironmentObserver | None = None,
                 max_iterations: int = 4,
                 high_impact_workflow: HighImpactWorkflow | None = None):
        self.planner = planner
        self.executor = executor
        self.fabric = fabric
        self.brain = brain
        self.reasoner = KnowledgeActionReasoner(fabric, planner)
        self.environment_observer = environment_observer
        self.max_iterations = max(1, max_iterations)
        self.high_impact_workflow = high_impact_workflow or HighImpactWorkflow()
        self._paused: dict[str, _PausedRun] = {}

    def _execute(self, request, plan, confirmed, verifier, replanner, data_class,
                 resume_request_id=None) -> JarvisAgentResult:
        decision = self.reasoner.prepare(request)
        if self.environment_observer is None:
            return JarvisAgentResult(request, decision.relevant_nodes, decision.rationale,
                                     blocked=True, reason="Environment observer is required")
        verifier = verifier or self._default_verifier
        if replanner is None and self.brain is not None:
            replanner = _BrainReplanner(self.brain, self.planner)
        loop = EnvironmentAgentLoop(
            self.planner, self.executor, self.environment_observer, self.max_iterations,
            high_impact_workflow=self.high_impact_workflow,
        )
        execution = loop.run(plan, verifier, replanner, confirmed, resume_request_id)
        result = JarvisAgentResult(
            request, decision.relevant_nodes, decision.rationale, execution=execution,
            state=execution.state, resume_request_id=execution.sensitive_request_id,
            user_message=execution.user_message,
        )
        if execution.state == WorkflowState.WAITING_FOR_USER and execution.sensitive_request_id:
            self._paused[execution.sensitive_request_id] = _PausedRun(
                request, plan, confirmed, data_class, verifier, replanner
            )
        return result

    def run(self, request: str, *, plan: ActionPlan | None = None,
            confirmed: bool = False,
            verifier: Callable | None = None,
            replanner: Any | None = None,
            data_class: DataClass = DataClass.NORMAL) -> JarvisAgentResult:
        decision = self.reasoner.prepare(request)
        if plan is None:
            if self.brain is None:
                return JarvisAgentResult(request, decision.relevant_nodes, decision.rationale,
                                         blocked=True, reason="No action plan or planning brain supplied")
            plan = self.planner.from_brain(self.brain, request, {
                "knowledge": decision.rationale,
                "relevant_nodes": decision.relevant_nodes,
                "data_class": data_class.value,
                "available_tools": [
                    {"name": s.name, "description": s.description, "risk": s.risk.value,
                     "data_class": s.data_class.value} for s in self.planner.tools.values()
                ],
            })
        else:
            plan = self.planner.validate(plan)
        if plan.blocked:
            return JarvisAgentResult(request, decision.relevant_nodes, decision.rationale,
                                     blocked=True, reason="Plan blocked: " + "; ".join(plan.warnings))
        return self._execute(request, plan, confirmed, verifier, replanner, data_class)

    def resume(self, request_id: str, *, confirmed: bool = False) -> JarvisAgentResult:
        """Resume a paused workflow after the user completes the trusted UI step.

        The request_id is a workflow handle, never a secret. The secret itself
        stays inside the target application and is never passed to this method.
        """
        pending = self._paused.pop(request_id, None)
        if pending is None:
            raise KeyError("Unknown or expired workflow request")
        transition = self.high_impact_workflow.resume(request_id)
        if transition.state == WorkflowState.BLOCKED:
            raise PermissionError(transition.message or "Workflow cannot resume")
        return self._execute(
            pending.request, pending.plan, confirmed or pending.confirmed,
            pending.verifier, pending.replanner, pending.data_class,
            resume_request_id=request_id,
        )

    def cancel(self, request_id: str) -> None:
        self._paused.pop(request_id, None)
        self.high_impact_workflow.cancel(request_id)

    def pending_workflows(self) -> tuple[str, ...]:
        return tuple(self._paused)

    @staticmethod
    def _default_verifier(plan, actions, evidence) -> Verification:
        failed = [a for a in actions if not a.success]
        if failed:
            return Verification(False, "One or more actions failed.",
                                {"failed": [a.tool for a in failed]})
        if any(a.requires_confirmation for a in actions):
            return Verification(False, "Confirmation required.", {"confirmation": True})
        return Verification(True, "Actions executed successfully.",
                            {"changes": len(evidence.get("changes", []))})
