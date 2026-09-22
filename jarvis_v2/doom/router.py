"""Route JARVIS work through DOOM without exposing protected data remotely."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from jarvis_v2.core.types import DataClass

@dataclass
class RoutedTask:
    task: str
    worker_id: str
    worker_type: str
    data_class: DataClass
    capability: str
    authorized_remote: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

class DoomResourceRouter:
    """Provider-neutral bridge; execution remains owned by DOOM adapters."""
    def __init__(self, doom_client: Any | None = None) -> None:
        self.doom_client = doom_client

    def workers(self) -> list[dict[str, Any]]:
        if self.doom_client is None:
            return []
        result=self.doom_client.status()
        return result.get("workers", [])

    def route(self, task: str, capability: str, data_class: DataClass = DataClass.NORMAL,
              preferred_type: str | None = None, explicitly_authorized: bool = False) -> RoutedTask:
        workers=self.workers()
        if data_class == DataClass.PROTECTED and not explicitly_authorized:
            candidates=[w for w in workers if w.get("type") == "local" and w.get("online", True) and capability in w.get("capabilities", [])]
        else:
            candidates=[w for w in workers if w.get("online", True) and capability in w.get("capabilities", [])]
            if preferred_type:
                preferred=[w for w in candidates if w.get("type") == preferred_type]
                if preferred: candidates=preferred
        if not candidates:
            raise RuntimeError(f"No eligible DOOM worker for capability={capability}, data_class={data_class.value}")
        worker=candidates[0]
        return RoutedTask(task, worker["id"], worker.get("type", "unknown"), data_class, capability, explicitly_authorized, {"protected_local_only": data_class == DataClass.PROTECTED and not explicitly_authorized})
