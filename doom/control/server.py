"""HTTP control plane for DOOM."""
from __future__ import annotations
from dataclasses import asdict
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from doom.policy import DataClass
from doom.workers import TaskRequest, Worker, WorkerType
from .identity import IdentityRegistry
from .registry import WorkerRegistry
from .scheduler import Scheduler

class EnrollRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)

class WorkerRequest(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    type: WorkerType
    capabilities: set[str] = set()
    endpoint: str | None = None
    region: str | None = Field(default=None, max_length=80)

class TaskRequestModel(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    required_capability: str = Field(min_length=1, max_length=100)
    data_class: DataClass = DataClass.NORMAL
    explicitly_authorized: bool = False
    preferred_worker_type: WorkerType | None = None

class DoomControlPlane:
    def __init__(self) -> None:
        self.identities = IdentityRegistry()
        self.workers = WorkerRegistry()
        self.scheduler = Scheduler(self.workers)

    def create_app(self) -> FastAPI:
        app = FastAPI(title="DOOM Control Plane", version="0.1.0")

        def auth(device_id: str = Header(default="", alias="X-DOOM-Device"),
                 token: str = Header(default="", alias="X-DOOM-Token")) -> str:
            if not self.identities.authenticate(device_id, token):
                raise HTTPException(status_code=401, detail="Invalid DOOM device credentials")
            return device_id

        @app.get("/health")
        def health() -> dict:
            return {"ok": True, "service": "doom-control", "version": "0.1.0"}

        @app.post("/v1/devices/enroll")
        def enroll(request: EnrollRequest) -> dict:
            identity, token = self.identities.enroll(request.name)
            return {"device_id": identity.device_id, "device_name": identity.name, "token": token}

        @app.get("/v1/workers")
        def workers(_: str = Depends(auth)) -> list[dict]:
            return self.workers.snapshot()

        @app.post("/v1/workers")
        def register_worker(request: WorkerRequest, _: str = Depends(auth)) -> dict:
            worker = self.workers.register(
                Worker(request.id, request.type, set(request.capabilities), True, request.endpoint, request.region)
            )
            return {"worker": {**asdict(worker), "type": worker.type.value, "capabilities": sorted(worker.capabilities)}}

        @app.post("/v1/workers/{worker_id}/heartbeat")
        def heartbeat(worker_id: str, _: str = Depends(auth)) -> dict:
            try:
                worker = self.workers.heartbeat(worker_id, True)
            except KeyError as exc:
                raise HTTPException(status_code=404, detail="Unknown worker") from exc
            return {"worker_id": worker.id, "online": worker.online}

        @app.post("/v1/workers/{worker_id}/offline")
        def offline(worker_id: str, _: str = Depends(auth)) -> dict:
            try:
                worker = self.workers.heartbeat(worker_id, False)
            except KeyError as exc:
                raise HTTPException(status_code=404, detail="Unknown worker") from exc
            return {"worker_id": worker.id, "online": worker.online}

        @app.post("/v1/tasks/plan")
        def plan_task(request: TaskRequestModel, _: str = Depends(auth)) -> dict:
            scheduled = self.scheduler.select(
                TaskRequest(
                    request.name,
                    request.required_capability,
                    request.data_class,
                    request.explicitly_authorized,
                    request.preferred_worker_type,
                )
            )
            worker = self.workers.get(scheduled.worker_id)
            return {
                "task": request.name,
                "worker_id": scheduled.worker_id,
                "worker_type": worker.type.value if worker else None,
                "worker_endpoint": worker.endpoint if worker else None,
                "data_class": scheduled.data_class.value,
            }

        return app
