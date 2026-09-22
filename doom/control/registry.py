"""In-memory worker registry used by the DOOM control plane."""
from __future__ import annotations
from dataclasses import asdict
from threading import RLock
from doom.workers import Worker, WorkerType

class WorkerRegistry:
    def __init__(self) -> None:
        self._workers: dict[str, Worker] = {}
        self._lock = RLock()

    def register(self, worker: Worker) -> Worker:
        with self._lock:
            self._workers[worker.id] = worker
        return worker

    def unregister(self, worker_id: str) -> None:
        with self._lock:
            self._workers.pop(worker_id, None)

    def heartbeat(self, worker_id: str, online: bool = True) -> Worker:
        with self._lock:
            worker = self._workers[worker_id]
            worker.online = online
            return worker

    def get(self, worker_id: str) -> Worker | None:
        return self._workers.get(worker_id)

    def all(self) -> list[Worker]:
        with self._lock:
            return list(self._workers.values())

    def snapshot(self) -> list[dict]:
        return [{**asdict(w), "type": w.type.value, "capabilities": sorted(w.capabilities)} for w in self.all()]
