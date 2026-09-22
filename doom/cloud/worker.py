"""HTTP worker contract for remote DOOM compute nodes."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import requests

class WorkerExecutionError(RuntimeError):
    pass

@dataclass(frozen=True, slots=True)
class CloudWorkerSpec:
    worker_id: str
    endpoint: str
    token: str
    capabilities: frozenset[str]
    timeout_seconds: float = 30.0

class CloudWorkerClient:
    """Small provider-neutral client. Cloud vendors are hidden behind this contract."""
    def __init__(self, spec: CloudWorkerSpec) -> None:
        self.spec = spec

    def health(self) -> bool:
        try:
            response = requests.get(
                f"{self.spec.endpoint.rstrip('/')}/health",
                headers={"Authorization": f"Bearer {self.spec.token}"},
                timeout=self.spec.timeout_seconds,
            )
            return response.ok
        except requests.RequestException:
            return False

    def execute(self, task: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = requests.post(
                f"{self.spec.endpoint.rstrip('/')}/v1/execute",
                json={"task": task, "payload": payload},
                headers={"Authorization": f"Bearer {self.spec.token}"},
                timeout=self.spec.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise WorkerExecutionError(f"Remote worker execution failed: {exc}") from exc
        if not isinstance(data, dict):
            raise WorkerExecutionError("Remote worker returned an invalid response.")
        return data
