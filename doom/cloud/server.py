"""Reference worker service for a DOOM private/cloud node.

This service is intentionally capability-gated and contains no arbitrary shell
execution. Phase 4 establishes the transport contract; concrete safe task
executors are added in later phases.
"""
from __future__ import annotations
import os
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

class ExecuteRequest(BaseModel):
    task: str = Field(min_length=1, max_length=200)
    payload: dict = {}

def create_worker_app(token: str | None = None) -> FastAPI:
    expected = token or os.getenv("DOOM_WORKER_TOKEN", "")
    app = FastAPI(title="DOOM Worker", version="0.1.0")

    def authenticate(authorization: str = Header(default="")) -> None:
        if not expected or authorization != f"Bearer {expected}":
            raise HTTPException(status_code=401, detail="Invalid worker credentials")

    @app.get("/health")
    def health(authorization: str = Header(default="")) -> dict:
        authenticate(authorization)
        return {"ok": True, "service": "doom-worker", "version": "0.1.0"}

    @app.post("/v1/execute")
    def execute(request: ExecuteRequest, authorization: str = Header(default="")) -> dict:
        authenticate(authorization)
        raise HTTPException(
            status_code=501,
            detail="No remote task executor is enabled in Phase 4.",
        )

    return app
