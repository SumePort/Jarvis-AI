"""Context assembly for JARVIS V2."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .types import EnvironmentSnapshot, Observation


@dataclass
class JarvisContext:
    user_request: str
    conversation: list[dict[str, str]] = field(default_factory=list)
    memories: list[dict[str, Any]] = field(default_factory=list)
    environment: EnvironmentSnapshot | None = None
    observations: list[Observation] = field(default_factory=list)
    available_tools: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_model_input(self) -> dict[str, Any]:
        """Return a model-friendly structure without exposing implementation objects."""
        return {
            "user_request": self.user_request,
            "conversation": self.conversation,
            "memories": self.memories,
            "environment": self.environment.__dict__ if self.environment else None,
            "observations": [o.__dict__ for o in self.observations],
            "available_tools": self.available_tools,
            "metadata": self.metadata,
        }
