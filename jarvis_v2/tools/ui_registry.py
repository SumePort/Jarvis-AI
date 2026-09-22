"""Register semantic UI actions when accessibility support is available."""
from __future__ import annotations
from .registry import ToolRegistry
from .ui_actions import SemanticUIActions, semantic_ui_specs
from jarvis_v2.capabilities import CapabilityRegistry

class UIActionRegistry:
    def __init__(self, capabilities: CapabilityRegistry) -> None:
        self.capabilities=capabilities
    def build(self) -> ToolRegistry:
        registry=ToolRegistry(); adapter=SemanticUIActions()
        if not all((s:=self.capabilities.get(c)) is not None and s.available for c in ("os.windows", "python.pywinauto")):
            return registry
        handlers={"ui_click":adapter.click,"ui_type_text":adapter.type_text,"ui_select":adapter.select}
        for spec in semantic_ui_specs(): registry.register(spec, handlers[spec.name])
        return registry
