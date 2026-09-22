"""DOOM runtime coordinator for local/private/cloud resources."""
from __future__ import annotations
from dataclasses import dataclass
from jarvis_v2.core.types import DataClass


@dataclass(frozen=True)
class RuntimeTarget:
    worker_id: str
    worker_type: str
    local: bool


class DoomRuntime:
    def __init__(self, router) -> None:
        self.router = router

    def select(self, task: str, capability: str, data_class: DataClass,
               remote_authorized: bool = False) -> RuntimeTarget:
        worker = self.router.route(task, capability, data_class,
                                   explicitly_authorized=remote_authorized)
        return RuntimeTarget(worker.id, worker.type.value, worker.type.value == "local")
