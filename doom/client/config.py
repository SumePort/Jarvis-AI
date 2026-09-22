"""Persistent local DOOM client configuration."""
from __future__ import annotations
import json
from dataclasses import asdict, dataclass
from pathlib import Path

@dataclass
class ClientConfig:
    control_url: str = "http://127.0.0.1:8787"
    device_id: str | None = None
    token: str | None = None
    device_name: str = "DOOM-PC"
    heartbeat_seconds: int = 30

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "ClientConfig":
        if not path.exists():
            return cls()
        return cls(**json.loads(path.read_text(encoding="utf-8")))
