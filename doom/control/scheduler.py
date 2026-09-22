"""Policy-aware task scheduler for DOOM."""
from __future__ import annotations
from dataclasses import dataclass
from doom.policy import DataClass
from doom.workers import ResourcePolicyError, TaskRequest, Worker, WorkerType
from .registry import WorkerRegistry

@dataclass(frozen=True, slots=True)
class ScheduledTask:
    name: str
    worker_id: str
    data_class: DataClass

class Scheduler:
    def __init__(self, registry: WorkerRegistry) -> None:
        self.registry = registry

    def select(self, task: TaskRequest) -> ScheduledTask:
        workers = self.registry.all()
        candidates = [w for w in workers if w.online and task.required_capability in w.capabilities]
        if not candidates:
            raise ResourcePolicyError(f"No worker can satisfy capability: {task.required_capability}")
        if task.data_class == DataClass.PROTECTED and not task.explicitly_authorized:
            candidates = [w for w in candidates if w.type == WorkerType.LOCAL]
            if not candidates:
                raise ResourcePolicyError("Protected data is local-only by default.")
        if task.preferred_worker_type is not None:
            preferred = [w for w in candidates if w.type == task.preferred_worker_type]
            if preferred:
                candidates = preferred
        order = {WorkerType.LOCAL: 0, WorkerType.PRIVATE: 1, WorkerType.CLOUD: 2}
        worker: Worker = sorted(candidates, key=lambda w: order[w.type])[0]
        return ScheduledTask(task.name, worker.id, task.data_class)
