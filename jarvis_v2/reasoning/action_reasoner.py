from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from jarvis_v2.actions.planner import ActionPlan, ActionStep, ActionPlanner
from jarvis_v2.core.types import ActionRisk, DataClass, ToolSpec
from jarvis_v2.knowledge.fabric import FabricQuery, JarvisKnowledgeFabric


@dataclass
class ReasoningDecision:
    request: str
    relevant_nodes: list[str] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)
    plan: ActionPlan | None = None
    needs_more_evidence: bool = False


class KnowledgeActionReasoner:
    """Turns world-model evidence into a safety-validated action plan.

    This layer selects context and deterministic constraints; an LLM may still
    propose actions, but ToolSpec and ActionPlanner remain authoritative.
    """

    def __init__(self, fabric: JarvisKnowledgeFabric, planner: ActionPlanner):
        self.fabric = fabric
        self.planner = planner

    def prepare(self, request: str, limit: int = 12) -> ReasoningDecision:
        result = self.fabric.query(FabricQuery(request, limit=limit, depth=1))
        rationale = [f"Relevant {node.kind}: {node.label}" for node in result.nodes]
        return ReasoningDecision(
            request=request,
            relevant_nodes=[node.id for node in result.nodes],
            rationale=rationale,
            needs_more_evidence=not bool(result.nodes),
        )

    def validate_plan(self, decision: ReasoningDecision, plan: ActionPlan) -> ReasoningDecision:
        decision.plan = self.planner.validate(plan)
        return decision

    @staticmethod
    def tool_constraints(spec: ToolSpec) -> dict[str, Any]:
        return {
            "risk": spec.risk.value,
            "data_class": spec.data_class.value,
            "requires_confirmation": spec.risk == ActionRisk.CONFIRM,
            "protected": spec.data_class == DataClass.PROTECTED,
        }
