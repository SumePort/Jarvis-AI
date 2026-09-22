"""Execution boundary: only validated tool calls reach executors."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable
from jarvis_v2.core.types import ActionRisk
from .planner import ActionPlan

@dataclass
class ActionObservation:
    tool: str
    success: bool
    output: Any = None
    error: str | None = None
    requires_confirmation: bool = False

class ActionExecutor:
    def __init__(self, handlers: dict[str, Callable[..., Any]] | None = None) -> None:
        self.handlers=handlers or {}

    def execute(self, plan: ActionPlan, confirmed: bool = False) -> list[ActionObservation]:
        results=[]
        for step in plan.steps:
            if step.risk == ActionRisk.CONFIRM and not confirmed:
                results.append(ActionObservation(step.tool, False, error="Confirmation required", requires_confirmation=True))
                continue
            handler=self.handlers.get(step.tool)
            if handler is None:
                results.append(ActionObservation(step.tool, False, error="No executor registered"))
                continue
            try:
                results.append(ActionObservation(step.tool, True, handler(**step.arguments)))
            except Exception as exc:
                results.append(ActionObservation(step.tool, False, error=str(exc)))
        return results
