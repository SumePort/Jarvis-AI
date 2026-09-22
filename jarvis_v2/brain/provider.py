"""Stable interface between JARVIS runtime and any model provider."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Protocol
from jarvis_v2.actions import ActionPlan

@dataclass
class BrainResponse:
    text: str = ""
    plan: ActionPlan | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

class BrainProvider(Protocol):
    def plan(self, request: str, context: dict[str, Any]) -> ActionPlan: ...
    def respond(self, request: str, context: dict[str, Any], observations: list[dict[str, Any]]) -> BrainResponse: ...
