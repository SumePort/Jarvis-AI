"""Minimal session state for multi-turn JARVIS V2 interactions."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class JarvisSession:
    session_id: str
    authenticated: bool = False
    active_project: str | None = None
    history: list[dict[str, Any]] = field(default_factory=list)

    def add_turn(self, request: str, result: dict[str, Any]) -> None:
        self.history.append({"request": request, "result": result})
        self.history=self.history[-50:]
