"""Discover available JARVIS capabilities without executing them."""
from __future__ import annotations
from dataclasses import dataclass, field
import importlib.util, os, platform, shutil

@dataclass(frozen=True)
class CapabilityStatus:
    name: str
    available: bool
    reason: str = ""
    metadata: dict = field(default_factory=dict)

class CapabilityRegistry:
    def __init__(self) -> None:
        self._items: dict[str, CapabilityStatus] = {}

    def register(self, name: str, available: bool, reason: str = "", metadata: dict | None = None) -> None:
        self._items[name] = CapabilityStatus(name, available, reason, metadata or {})

    def discover(self) -> "CapabilityRegistry":
        self.register("os.windows", platform.system() == "Windows", platform.platform())
        self.register("python", True, platform.python_version())
        for module in ("psutil", "pyautogui", "pygetwindow", "win32api"):
            ok=importlib.util.find_spec(module) is not None
            self.register(f"python.{module}", ok, "installed" if ok else "not installed")
        for command in ("git", "python"):
            path=shutil.which(command)
            self.register(f"command.{command}", bool(path), path or "not found", {"path": path} if path else {})
        self.register("microphone", bool(os.environ.get("JARVIS_AUDIO_DEVICE")),
                      "configured by JARVIS_AUDIO_DEVICE" if os.environ.get("JARVIS_AUDIO_DEVICE") else "no explicit device configured")
        return self

    def get(self, name: str) -> CapabilityStatus | None:
        return self._items.get(name)

    def available(self) -> list[CapabilityStatus]:
        return [x for x in self._items.values() if x.available]

    def all(self) -> list[CapabilityStatus]:
        return list(self._items.values())

    def as_dict(self) -> dict:
        return {x.name: {"available":x.available,"reason":x.reason,"metadata":x.metadata} for x in self._items.values()}
