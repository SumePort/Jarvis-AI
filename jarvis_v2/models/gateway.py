"""Provider-neutral model gateway with privacy-aware selection."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable
from jarvis_v2.core.types import DataClass

@dataclass
class ModelProfile:
    id: str
    provider: str
    capabilities: set[str] = field(default_factory=set)
    local: bool = True
    available: bool = True
    cost_class: str = "free"

@dataclass
class ModelSelection:
    model_id: str
    reason: str
    profile: ModelProfile

class ModelGateway:
    def __init__(self) -> None:
        self.models: dict[str, ModelProfile] = {}
        self.clients: dict[str, Callable[[str], str]] = {}

    def register(self, profile: ModelProfile, client: Callable[[str], str]) -> None:
        self.models[profile.id]=profile
        self.clients[profile.id]=client

    def select(self, capability: str, data_class: DataClass = DataClass.NORMAL,
               prefer_local: bool = False) -> ModelSelection:
        candidates=[m for m in self.models.values() if m.available and capability in m.capabilities]
        if data_class == DataClass.PROTECTED:
            candidates=[m for m in candidates if m.local]
        if not candidates:
            raise RuntimeError(f"No eligible model for capability={capability}, data_class={data_class.value}")
        if prefer_local or data_class == DataClass.PROTECTED:
            candidates.sort(key=lambda m: (not m.local, m.cost_class != "free"))
        else:
            candidates.sort(key=lambda m: (not m.local, m.cost_class != "free"))
        chosen=candidates[0]
        return ModelSelection(chosen.id, f"selected {chosen.provider}; local={chosen.local}; capability={capability}", chosen)

    def complete(self, model_id: str, prompt: str) -> str:
        if model_id not in self.models or not self.models[model_id].available:
            raise RuntimeError("Model unavailable")
        return self.clients[model_id](prompt)
