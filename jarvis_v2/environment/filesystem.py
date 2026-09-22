"""Filesystem perception for JARVIS V2."""
from __future__ import annotations

import os
from pathlib import Path
import time
from typing import Iterable

from jarvis_v2.core.types import EnvironmentSnapshot


IGNORED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".idea", ".vscode"}


class FilesystemEnvironmentProvider:
    """Inspect selected roots; never recursively scan an entire disk by default."""

    def __init__(self, roots: Iterable[str | Path] | None = None, max_entries: int = 500) -> None:
        self.roots = [Path(r).expanduser().resolve() for r in (roots or [Path.cwd()])]
        self.max_entries = max_entries

    def snapshot(self) -> EnvironmentSnapshot:
        snapshot = EnvironmentSnapshot(timestamp=time.time())
        for root in self.roots:
            if not root.exists() or not root.is_dir():
                continue
            snapshot.filesystem.append(self._describe_root(root))
        return snapshot

    def _describe_root(self, root: Path) -> dict:
        entries = []
        for current, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            for name in dirs + files:
                path = Path(current) / name
                try:
                    stat = path.stat()
                except OSError:
                    continue
                entries.append({
                    "path": str(path),
                    "relative": str(path.relative_to(root)),
                    "kind": "directory" if path.is_dir() else "file",
                    "size": stat.st_size if path.is_file() else None,
                    "suffix": path.suffix.lower() if path.is_file() else None,
                })
                if len(entries) >= self.max_entries:
                    return {"root": str(root), "entries": entries, "truncated": True}
        return {"root": str(root), "entries": entries, "truncated": False}
