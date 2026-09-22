from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
import time


@dataclass
class DeviceWorkspaceState:
    identity_id: str
    device_id: str
    project_id: str
    manifest_path: str
    updated_at: float


class DeviceWorkspaceRegistry:
    """Local registry of which identity owns which workspace on a device."""

    def __init__(self, path: str | Path = "data/jarvis_v2/device_workspaces.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> list[DeviceWorkspaceState]:
        if not self.path.exists():
            return []
        try:
            return [DeviceWorkspaceState(**x) for x in json.loads(self.path.read_text(encoding="utf-8"))]
        except (OSError, json.JSONDecodeError, TypeError):
            return []

    def _save(self, states):
        self.path.write_text(json.dumps([asdict(x) for x in states], indent=2), encoding="utf-8")

    def bind(self, identity_id: str, device_id: str, project_id: str, manifest_path: str) -> DeviceWorkspaceState:
        states = [x for x in self._load() if not (x.identity_id == identity_id and x.device_id == device_id and x.project_id == project_id)]
        state = DeviceWorkspaceState(identity_id, device_id, project_id, manifest_path, time.time())
        states.append(state)
        self._save(states)
        return state

    def for_identity(self, identity_id: str) -> list[DeviceWorkspaceState]:
        return [x for x in self._load() if x.identity_id == identity_id]
