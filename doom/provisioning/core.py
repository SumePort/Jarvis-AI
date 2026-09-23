"""Provider-neutral infrastructure provisioning."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkerRequest:
    name: str
    capabilities: tuple[str, ...]
    cpu: int = 1
    memory_gb: int = 2
    gpu: bool = False
    region: str = ""


class Provisioner:
    def __init__(self, adapter=None):
        self.adapter = adapter

    def plan(self, request: WorkerRequest):
        return {
            "request": request,
            "action": "provision",
            "provider": getattr(self.adapter, "name", "unconfigured"),
        }

    def provision(self, request: WorkerRequest):
        if self.adapter is None:
            raise RuntimeError("No trusted infrastructure adapter configured")
        return self.adapter.provision(request)