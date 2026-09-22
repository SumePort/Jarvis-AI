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
        self.models[profile.id] = profile
        self.clients[profile.id] = client

    def select(self, capability: str, data_class: DataClass = DataClass.NORMAL,
               prefer_local: bool = False) -> ModelSelection:
        candidates = [
            m for m in self.models.values()
            if m.available and capability in m.capabilities
        ]
        if data_class == DataClass.PROTECTED:
            candidates = [m for m in candidates if m.local]
        if not candidates:
            raise RuntimeError(
                f"No eligible model for capability={capability}, data_class={data_class.value}"
            )
        candidates.sort(key=lambda m: (not m.local if prefer_local or data_class == DataClass.PROTECTED else False,
                                       m.cost_class != "free", m.id))
        chosen = candidates[0]
        return ModelSelection(
            chosen.id,
            f"selected {chosen.provider}; local={chosen.local}; capability={capability}",
            chosen,
        )

    def complete(self, model_id: str, prompt: str) -> str:
        if model_id not in self.models or not self.models[model_id].available:
            raise RuntimeError("Model unavailable")
        return self.clients[model_id](prompt)

    def complete_selected(self, capability: str, prompt: str,
                          data_class: DataClass = DataClass.NORMAL,
                          prefer_local: bool = False) -> tuple[ModelSelection, str]:
        selection = self.select(capability, data_class, prefer_local)
        return selection, self.complete(selection.model_id, prompt)


def llama_cpp_client(base_url: str = "http://127.0.0.1:8080/v1",
                     model: str | None = None, timeout: float = 120.0) -> Callable[[str], str]:
    """Create a local llama.cpp OpenAI-compatible completion client."""
    import requests

    endpoint = base_url.rstrip("/") + "/chat/completions"

    def complete(prompt: str) -> str:
        raw_mode = prompt.startswith("[JARVIS_RAW]")
        raw_json = prompt.startswith("[JARVIS_RAW_JSON]")
        system = (
            "You are JARVIS. Return ONLY valid JSON matching the requested action-plan "
            "schema. Never invent tools. Follow tool risk and data class constraints."
        )
        if raw_mode:
            system = (
                "You are JARVIS. Answer the user's requested synthesis directly. "
                "Do not invent facts. Preserve uncertainty and source provenance."
            )
        elif raw_json:
            system = (
                "You are JARVIS. Return ONLY valid JSON matching the schema requested "
                "by the user. Do not add markdown fences or commentary."
            )
        payload = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }
        if model:
            payload["model"] = model
        response = requests.post(endpoint, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("llama.cpp returned no choices")
        message = choices[0].get("message", {})
        content = message.get("content", "")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("llama.cpp returned empty content")
        return content.strip()

    return complete
