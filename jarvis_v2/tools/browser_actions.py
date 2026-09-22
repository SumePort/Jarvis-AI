"""Semantic browser actions. Connectors provide the actual browser implementation."""
from __future__ import annotations
from typing import Protocol, Any
from jarvis_v2.core.types import ToolSpec, ActionRisk, DataClass

class BrowserController(Protocol):
    def click(self, selector: dict[str, str]) -> Any: ...
    def type_text(self, selector: dict[str, str], text: str) -> Any: ...
    def navigate(self, url: str) -> Any: ...

class BrowserActions:
    def __init__(self, controller: BrowserController) -> None: self.controller=controller
    def click(self, selector: dict[str,str]): return self.controller.click(selector)
    def type_text(self, selector: dict[str,str], text: str): return self.controller.type_text(selector,text)
    def navigate(self, url: str): return self.controller.navigate(url)

def browser_tool_specs() -> list[ToolSpec]:
    return [
        ToolSpec("browser_click","Click a semantic DOM element",{"selector":"object"},("browser.dom",),ActionRisk.CONFIRM,DataClass.CONTROLLED),
        ToolSpec("browser_type_text","Type into a semantic DOM input",{"selector":"object","text":"string"},("browser.dom",),ActionRisk.CONFIRM,DataClass.CONTROLLED),
        ToolSpec("browser_navigate","Navigate to a URL",{"url":"string"},("browser.dom",),ActionRisk.CONFIRM,DataClass.NORMAL),
    ]
