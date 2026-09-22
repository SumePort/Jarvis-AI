"""Bridge discovered capabilities into the action tool registry."""
from __future__ import annotations
from jarvis_v2.actions.planner import ActionPlanner
from jarvis_v2.core.types import ToolSpec, ActionRisk
from .registry import CapabilityRegistry

class CapabilityToolBridge:
    def __init__(self, capabilities: CapabilityRegistry) -> None:
        self.capabilities=capabilities

    def available_tools(self, specs: list[ToolSpec]) -> list[ToolSpec]:
        result=[]
        for spec in specs:
            capability=spec.metadata.get("capability") if hasattr(spec, "metadata") else None
            if capability and not self.capabilities.get(capability):
                continue
            status=self.capabilities.get(capability) if capability else None
            if status is not None and not status.available:
                continue
            result.append(spec)
        return result

    def planner(self, specs: list[ToolSpec]) -> ActionPlanner:
        return ActionPlanner(self.available_tools(specs))
