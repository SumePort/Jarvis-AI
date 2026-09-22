"""Stable data contracts for JARVIS V2.

These contracts deliberately separate the model from the environment. The
model proposes intent/plans; adapters and DOOM perform actual operations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DataClass(str, Enum):
    PROTECTED = "protected"
    CONTROLLED = "controlled"
    NORMAL = "normal"


class ActionRisk(str, Enum):
    ALLOW = "allow"
    CONFIRM = "confirm"
    DENY = "deny"


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    capabilities: tuple[str, ...] = ()
    risk: ActionRisk = ActionRisk.CONFIRM
    data_class: DataClass = DataClass.NORMAL

    def __post_init__(self) -> None:
        # Backward-compatible shorthand: ToolSpec(name, description, ActionRisk).
        if isinstance(self.parameters, ActionRisk):
            object.__setattr__(self, "risk", self.parameters)
            object.__setattr__(self, "parameters", {})

@dataclass(frozen=True)
class ToolCall:
    tool: str
    arguments: dict[str, Any] = field(default_factory=dict)
    call_id: str | None = None


@dataclass(frozen=True)
class Observation:
    source: str
    content: Any
    data_class: DataClass = DataClass.NORMAL
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PlanStep:
    id: str
    purpose: str
    tool_call: ToolCall | None = None
    depends_on: tuple[str, ...] = ()
    requires_confirmation: bool = False


@dataclass(frozen=True)
class Plan:
    goal: str
    steps: tuple[PlanStep, ...]
    success_criteria: tuple[str, ...] = ()
    requires_confirmation: bool = False


@dataclass
class EnvironmentSnapshot:
    """Structured environment state; screenshots are optional evidence."""

    timestamp: float
    devices: list[dict[str, Any]] = field(default_factory=list)
    applications: list[dict[str, Any]] = field(default_factory=list)
    windows: list[dict[str, Any]] = field(default_factory=list)
    workspaces: list[dict[str, Any]] = field(default_factory=list)
    processes: list[dict[str, Any]] = field(default_factory=list)
    repositories: list[dict[str, Any]] = field(default_factory=list)
    browser_pages: list[dict[str, Any]] = field(default_factory=list)
    filesystem: list[dict[str, Any]] = field(default_factory=list)
    visual_evidence: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
