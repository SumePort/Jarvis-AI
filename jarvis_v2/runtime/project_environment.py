from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os
import socket
import subprocess
import time
from typing import Iterable


@dataclass
class ProjectProcess:
    name: str
    command: list[str]
    pid: int | None = None
    port: int | None = None
    status: str = "unknown"
    log_file: str | None = None

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class ProjectEnvironmentSnapshot:
    root: str
    processes: list[ProjectProcess] = field(default_factory=list)
    listening_ports: list[int] = field(default_factory=list)
    services: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"root": self.root, "processes": [p.to_dict() for p in self.processes], "listening_ports": self.listening_ports, "services": self.services}


class ProjectExecutionEnvironment:
    """Safe runtime manager for project-local processes and service observation."""

    def __init__(self, root: str | Path, max_log_bytes: int = 200_000):
        self.root = Path(root).resolve()
        self.max_log_bytes = max_log_bytes
        self._processes: dict[str, subprocess.Popen] = {}
        self._logs: dict[str, Path] = {}

    def _safe_name(self, name: str) -> str:
        if not name or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in name):
            raise ValueError("Invalid service name")
        return name

    def start(self, name: str, command: list[str], port: int | None = None, env: dict[str, str] | None = None) -> ProjectProcess:
        name = self._safe_name(name)
        if not command or any("\n" in part or "\r" in part for part in command):
            raise ValueError("Invalid process command")
        existing = self._processes.get(name)
        if existing and existing.poll() is None:
            raise RuntimeError(f"Service '{name}' is already running")
        log_dir = self.root / ".jarvis" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{name}.log"
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        handle = log_path.open("a", encoding="utf-8")
        try:
            proc = subprocess.Popen(command, cwd=self.root, env=merged_env, stdout=handle, stderr=subprocess.STDOUT, shell=False)
        finally:
            handle.close()
        self._processes[name] = proc
        self._logs[name] = log_path
        return ProjectProcess(name, list(command), proc.pid, port, "running", str(log_path))

    def stop(self, name: str, timeout: float = 5.0) -> ProjectProcess:
        name = self._safe_name(name)
        proc = self._processes.get(name)
        if not proc:
            raise KeyError(name)
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)
        return self.inspect(name)

    def restart(self, name: str, timeout: float = 5.0) -> ProjectProcess:
        name = self._safe_name(name)
        proc = self._processes.get(name)
        if not proc:
            raise KeyError(name)
        command = proc.args if isinstance(proc.args, list) else [str(proc.args)]
        current = self.inspect(name)
        self.stop(name, timeout)
        return self.start(name, command, current.port)

    def inspect(self, name: str) -> ProjectProcess:
        name = self._safe_name(name)
        proc = self._processes.get(name)
        if not proc:
            raise KeyError(name)
        status = "running" if proc.poll() is None else f"exited:{proc.returncode}"
        return ProjectProcess(name, list(proc.args) if isinstance(proc.args, list) else [str(proc.args)], proc.pid, None, status, str(self._logs.get(name)) if name in self._logs else None)

    def log(self, name: str, lines: int = 100) -> str:
        name = self._safe_name(name)
        path = self._logs.get(name)
        if not path or not path.exists():
            return ""
        lines = max(1, min(lines, 1000))
        data = path.read_bytes()[-self.max_log_bytes:]
        return "\n".join(data.decode("utf-8", errors="replace").splitlines()[-lines:])

    def port_open(self, port: int, host: str = "127.0.0.1", timeout: float = 0.25) -> bool:
        if not 1 <= port <= 65535:
            raise ValueError("Invalid port")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            return sock.connect_ex((host, port)) == 0

    def snapshot(self, ports: Iterable[int] = ()) -> ProjectEnvironmentSnapshot:
        processes = [self.inspect(name) for name in list(self._processes)]
        checked = sorted({int(p) for p in ports if 1 <= int(p) <= 65535})
        open_ports = [p for p in checked if self.port_open(p)]
        return ProjectEnvironmentSnapshot(str(self.root), processes, open_ports, [p.name for p in processes if p.status == "running"])
