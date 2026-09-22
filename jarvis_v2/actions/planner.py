"""Provider-neutral action planning with deterministic safety validation."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Protocol
from jarvis_v2.core.types import ActionRisk, ToolSpec

@dataclass
class ActionStep:
    tool: str
    arguments: dict[str, Any] = field(default_factory=dict)
    risk: ActionRisk = ActionRisk.CONFIRM
    reason: str = ""

@dataclass
class ActionPlan:
    goal: str
    steps: list[ActionStep] = field(default_factory=list)
    blocked: bool = False
    warnings: list[str] = field(default_factory=list)

class ActionPlannerBrain(Protocol):
    def propose_actions(self, request: str, context: dict[str, Any], tools: list[ToolSpec]) -> ActionPlan: ...

class ActionPlanner:
    """Validate model-proposed actions before an executor can run them."""
    def __init__(self, tools: list[ToolSpec] | None = None) -> None:
        self.tools = {t.name: t for t in (tools or [])}

    def validate(self, plan: ActionPlan) -> ActionPlan:
        warnings=[]
        valid=[]
        for step in plan.steps:
            spec=self.tools.get(step.tool)
            if spec is None:
                warnings.append(f"Unknown tool blocked: {step.tool}")
                continue
            if spec.risk == ActionRisk.DENY:
                warnings.append(f"Denied tool blocked: {step.tool}")
                continue
            # The tool contract is authoritative; a model cannot lower its risk.
            if spec.risk.value == "confirm" and step.risk == ActionRisk.ALLOW:
                step.risk=ActionRisk.CONFIRM
            valid.append(step)
        plan.steps=valid
        plan.warnings.extend(warnings)
        plan.blocked = bool(plan.steps == [] and warnings)
        return plan

    def from_brain(self, brain: ActionPlannerBrain, request: str, context: dict[str, Any]) -> ActionPlan:
        return self.validate(brain.propose_actions(request, context, list(self.tools.values())))
