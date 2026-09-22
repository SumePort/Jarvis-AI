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
from jarvis_v2.loop.environment_loop import EnvironmentAgentLoop
from jarvis_v2.runtime.high_impact_workflow import HighImpactWorkflow


class _BrainReplanner:
    def __init__(self, brain: ActionPlannerBrain, planner: ActionPlanner):
        self.brain = brain
        self.planner = planner

    def replan(self, goal: str, observations: list[dict[str, Any]], previous: ActionPlan) -> ActionPlan:
        context = {"goal": goal, "previous_plan": previous.goal, "observations": observations[-4:]}
        return self.planner.from_brain(self.brain, goal, context)


@dataclass
class JarvisAgentResult:
    request: str
    relevant_nodes: list[str]
    rationale: list[str]
    execution: Any = None
    blocked: bool = False
    reason: str = ""


class JarvisAgentRuntime:
    """End-to-end agent boundary: knowledge -> plan -> secure action -> observe -> replan."""

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

    def run(self, request: str, *, plan: ActionPlan | None = None,
            confirmed: bool = False,
            verifier: Callable[[ActionPlan, list[ActionObservation], dict[str, Any]], Verification] | None = None,
            replanner: Any | None = None,
            data_class: DataClass = DataClass.NORMAL) -> JarvisAgentResult:
        decision = self.reasoner.prepare(request)
        if plan is None:
            if self.brain is None:
                return JarvisAgentResult(request, decision.relevant_nodes, decision.rationale, blocked=True,
                                         reason="No action plan or planning brain supplied")
            plan = self.planner.from_brain(self.brain, request, {
                "knowledge": decision.rationale,
                "relevant_nodes": decision.relevant_nodes,
                "data_class": data_class.value,
                "available_tools": [
                    {"name": spec.name, "description": spec.description, "risk": spec.risk.value,
                     "data_class": spec.data_class.value}
                    for spec in self.planner.tools.values()
                ],
            })
        else:
            plan = self.planner.validate(plan)
        if plan.blocked:
            return JarvisAgentResult(request, decision.relevant_nodes, decision.rationale, blocked=True,
                                     reason="Plan blocked: " + "; ".join(plan.warnings))
        if self.environment_observer is None:
            return JarvisAgentResult(request, decision.relevant_nodes, decision.rationale, blocked=True,
                                     reason="Environment observer is required for agent execution")
        verifier = verifier or self._default_verifier
        loop = EnvironmentAgentLoop(self.planner, self.executor, self.environment_observer, self.max_iterations,
                                    high_impact_workflow=self.high_impact_workflow)
        if replanner is None and self.brain is not None:
            replanner = _BrainReplanner(self.brain, self.planner)
        execution = loop.run(plan, verifier, replanner, confirmed)
        return JarvisAgentResult(request, decision.relevant_nodes, decision.rationale, execution=execution)

    @staticmethod
    def _default_verifier(plan, actions, evidence) -> Verification:
        if any(a.requires_confirmation for a in actions):
            return Verification(False, "Confirmation required.", {"confirmation": True})
        failed = [a for a in actions if not a.success]
        if failed:
            return Verification(False, "One or more actions failed.", {"failed": [a.tool for a in failed]})
        return Verification(True, "Actions executed successfully.", {"changes": len(evidence.get("changes", []))})
