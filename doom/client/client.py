"""DOOM client for registering a device and its local worker."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import requests
from .config import ClientConfig

class DoomClientError(RuntimeError): pass

@dataclass
class DoomClient:
    config: ClientConfig
    config_path: Path = Path("data/doom/client.json")

    def enroll(self) -> ClientConfig:
        try:
            response = requests.post(
                f"{self.config.control_url.rstrip('/')}/v1/devices/enroll",
                json={"name": self.config.device_name},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise DoomClientError(f"DOOM enrollment failed: {exc}") from exc
        self.config.device_id = data["device_id"]
        self.config.token = data["token"]
        self.config.save(self.config_path)
        return self.config

    def _headers(self) -> dict[str, str]:
        if not self.config.device_id or not self.config.token:
            raise DoomClientError("Device is not enrolled.")
        return {"X-DOOM-Device": self.config.device_id, "X-DOOM-Token": self.config.token}

    def register_local_worker(self, worker_id: str = "local-pc", capabilities: set[str] | None = None) -> dict:
        payload = {
            "id": worker_id,
            "type": "local",
            "capabilities": sorted(capabilities or {"cpu", "filesystem", "browser"}),
        }
        try:
            response = requests.post(
                f"{self.config.control_url.rstrip('/')}/v1/workers",
                json=payload, headers=self._headers(), timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            raise DoomClientError(f"Worker registration failed: {exc}") from exc

    def heartbeat(self, worker_id: str = "local-pc") -> dict:
        try:
            response = requests.post(
                f"{self.config.control_url.rstrip('/')}/v1/workers/{worker_id}/heartbeat",
                headers=self._headers(), timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            raise DoomClientError(f"DOOM heartbeat failed: {exc}") from exc

    def status(self) -> dict:
        try:
            response = requests.get(
                f"{self.config.control_url.rstrip('/')}/v1/workers",
                headers=self._headers(), timeout=10,
            )
            response.raise_for_status()
            return {"device_id": self.config.device_id, "workers": response.json()}
        except (requests.RequestException, ValueError) as exc:
            raise DoomClientError(f"DOOM status failed: {exc}") from exc
