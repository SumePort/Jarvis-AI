"""DOOM distributed resource registry and task routing foundation."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from .policy import DataClass

class WorkerType(str, Enum):
    LOCAL = "local"
    PRIVATE = "private"
    CLOUD = "cloud"

@dataclass(slots=True)
class Worker:
    id: str
    type: WorkerType
    capabilities: set[str] = field(default_factory=set)
    online: bool = True
    @property
    def trusted_local(self) -> bool:
        return self.type == WorkerType.LOCAL

@dataclass(slots=True)
class TaskRequest:
    name: str
    required_capability: str
    data_class: DataClass = DataClass.NORMAL
    explicitly_authorized: bool = False

class ResourcePolicyError(PermissionError):
    pass

class ResourceManager:
    def __init__(self) -> None:
        self.workers: dict[str, Worker] = {}
    def register(self, worker: Worker) -> None:
        self.workers[worker.id] = worker
    def route(self, task: TaskRequest) -> Worker:
        candidates = [w for w in self.workers.values() if w.online and task.required_capability in w.capabilities]
        if not candidates:
            raise ResourcePolicyError(f"No online worker provides capability: {task.required_capability}")
        if task.data_class == DataClass.PROTECTED and not task.explicitly_authorized:
            local = next((w for w in candidates if w.trusted_local), None)
            if local is None:
                raise ResourcePolicyError("Protected data is local-only and cannot be routed to a remote worker.")
            return local
        return candidates[0]
