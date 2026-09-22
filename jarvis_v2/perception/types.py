"""Normalized perception records independent of input modality."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class InputKind(str, Enum):
    TEXT="text"; AUDIO="audio"; IMAGE="image"; VIDEO="video"; DOCUMENT="document"; ENVIRONMENT="environment"

@dataclass
class Percept:
    kind: InputKind
    text: str = ""
    source: str = ""
    confidence: float | None = None
    data_class: str = "normal"
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class PerceptionResult:
    percepts: list[Percept] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
