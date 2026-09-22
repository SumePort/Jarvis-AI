"""Bridge discovered capabilities into the action tool registry."""
from __future__ import annotations
from jarvis_v2.actions.planner import ActionPlanner
from jarvis_v2.core.types import ToolSpec
from .registry import CapabilityRegistry

class CapabilityToolBridge:
    def __init__(self, capabilities: CapabilityRegistry) -> None:
        self.capabilities=capabilities

    def available_tools(self, specs: list[ToolSpec]) -> list[ToolSpec]:
        result=[]
        for spec in specs:
            required=spec.capabilities
            if required and any((self.capabilities.get(c) is None or not self.capabilities.get(c).available) for c in required):
                continue
            result.append(spec)
        return result

    def planner(self, specs: list[ToolSpec]) -> ActionPlanner:
        return ActionPlanner(self.available_tools(specs))
