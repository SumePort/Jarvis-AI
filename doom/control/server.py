"""HTTP control plane for DOOM.

The initial server binds to localhost by default. Remote device connectivity will
be added only after a secure transport/enrollment layer is in place.
"""
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

class TaskRequestModel(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    required_capability: str = Field(min_length=1, max_length=100)
    data_class: DataClass = DataClass.NORMAL
    explicitly_authorized: bool = False

class DoomControlPlane:
    def __init__(self) -> None:
        self.identities = IdentityRegistry()
        self.workers = WorkerRegistry()
        self.scheduler = Scheduler(self.workers)

    def create_app(self) -> FastAPI:
        app = FastAPI(title="DOOM Control Plane", version="0.1.0")

        def auth(device_id: str = Header(default="", alias="X-DOOM-Device"), token: str = Header(default="", alias="X-DOOM-Token")) -> str:
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
            worker = self.workers.register(Worker(request.id, request.type, set(request.capabilities)))
            return {"worker": {**asdict(worker), "type": worker.type.value, "capabilities": sorted(worker.capabilities)}}

        @app.post("/v1/tasks/plan")
        def plan_task(request: TaskRequestModel, _: str = Depends(auth)) -> dict:
            scheduled = self.scheduler.select(TaskRequest(request.name, request.required_capability, request.data_class, request.explicitly_authorized))
            return {"task": request.name, "worker_id": scheduled.worker_id, "data_class": scheduled.data_class.value}

        return app
