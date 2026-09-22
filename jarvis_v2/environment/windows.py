"""Windows application/window perception providers."""
from __future__ import annotations

import os
import subprocess
from typing import Any

from jarvis_v2.core.types import EnvironmentSnapshot


class WindowsEnvironmentProvider:
    """Collect structured Windows state without taking screenshots."""

    def snapshot(self) -> EnvironmentSnapshot:
        snapshot = EnvironmentSnapshot(timestamp=__import__("time").time())
        snapshot.metadata["platform"] = os.name
        snapshot.processes = self._processes()
        snapshot.windows = self._windows()
        snapshot.applications = self._applications(snapshot.processes)
        return snapshot

    @staticmethod
    def _processes() -> list[dict[str, Any]]:
        try:
            import psutil
        except ImportError:
            return []
        result = []
        for proc in psutil.process_iter(["pid", "name", "exe"]):
            try:
                info = proc.info
                result.append({
                    "pid": info.get("pid"),
                    "name": info.get("name"),
                    "exe": info.get("exe"),
                })
            except (psutil.Error, OSError):
                continue
        return result

    @staticmethod
    def _windows() -> list[dict[str, Any]]:
        try:
            import pygetwindow as gw
        except ImportError:
            return []
        windows = []
        try:
            for window in gw.getAllWindows():
                title = (window.title or "").strip()
                if not title:
                    continue
                windows.append({
                    "title": title,
                    "visible": bool(window.visible),
                    "minimized": bool(window.isMinimized),
                    "maximized": bool(window.isMaximized),
                    "position": {"left": window.left, "top": window.top},
                    "size": {"width": window.width, "height": window.height},
                })
        except Exception:
            return []
        return windows

    @staticmethod
    def _applications(processes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        apps = []
        for process in processes:
            name = process.get("name")
            if not name or name.lower() in seen:
                continue
            seen.add(name.lower())
            apps.append({"name": name, "pid": process.get("pid"), "exe": process.get("exe")})
        return apps


class TerminalEnvironmentProvider:
    """Expose safe, read-only terminal/session metadata."""

    def snapshot(self) -> EnvironmentSnapshot:
        import time
        return EnvironmentSnapshot(
            timestamp=time.time(),
            metadata={
                "cwd": os.getcwd(),
                "shell": os.environ.get("ComSpec") or os.environ.get("SHELL"),
                "python": subprocess.check_output(
                    ["python", "--version"], stderr=subprocess.STDOUT, text=True
                ).strip(),
            },
        )
