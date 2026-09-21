"""Offline project learner for building a local project inventory.

This first phase intentionally stores structural metadata only. A later phase can
add code-aware summaries and retrieval without changing the public API.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


IGNORED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".dart_tool", "build"}
TEXT_EXTENSIONS = {
    ".py", ".dart", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".json",
    ".md", ".txt", ".yaml", ".yml", ".toml", ".sql", ".env.example", ".xml",
}


@dataclass
class ProjectFile:
    path: str
    size: int
    extension: str


@dataclass
class ProjectSnapshot:
    name: str
    root: str
    files: list[ProjectFile]
    directories: list[str]


class ProjectLearner:
    def __init__(self, ignored_dirs: Iterable[str] = IGNORED_DIRS):
        self.ignored_dirs = set(ignored_dirs)

    def scan(self, root: str | os.PathLike[str]) -> ProjectSnapshot:
        base = Path(root).expanduser().resolve()
        if not base.is_dir():
            raise FileNotFoundError(f"Project directory does not exist: {base}")

        files: list[ProjectFile] = []
        directories: list[str] = []
        for current, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in self.ignored_dirs]
            current_path = Path(current)
            if current_path != base:
                directories.append(str(current_path.relative_to(base)))
            for filename in filenames:
                path = current_path / filename
                try:
                    stat = path.stat()
                except OSError:
                    continue
                files.append(ProjectFile(
                    path=str(path.relative_to(base)),
                    size=stat.st_size,
                    extension=path.suffix.lower(),
                ))
        return ProjectSnapshot(base.name, str(base), files, directories)

    def save_snapshot(self, snapshot: ProjectSnapshot, destination: str | os.PathLike[str]) -> None:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(snapshot), indent=2), encoding="utf-8")
