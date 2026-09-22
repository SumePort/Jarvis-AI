"""Tool registry bridging abstract plans to concrete handlers."""
from __future__ import annotations
from jarvis_v2.actions.executor import ActionExecutor
from jarvis_v2.core.types import ToolSpec

class ToolRegistry:
    def __init__(self) -> None:
        self.specs: dict[str, ToolSpec] = {}
        self.handlers = {}

    def register(self, spec: ToolSpec, handler) -> None:
        self.specs[spec.name] = spec
        self.handlers[spec.name] = handler

    def handlers(self) -> dict:
        return dict(self.handlers)

    def executor(self) -> ActionExecutor:
        return ActionExecutor(dict(self.handlers))

    def specs_list(self) -> list[ToolSpec]:
        return list(self.specs.values())
