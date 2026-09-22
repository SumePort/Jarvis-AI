"""Bounded project workspace operations for the coding agent."""
from __future__ import annotations
from pathlib import Path
import os


class ProjectWorkspace:
    """Read/write project files while preventing traversal outside the project."""

    IGNORED = {".git", ".venv", "venv", "node_modules", "__pycache__", ".idea", ".vscode"}

    def __init__(self, project_root: str):
        self.root = Path(project_root).expanduser().resolve()
        if not self.root.is_dir():
            raise ValueError("Project root does not exist")

    def resolve(self, relative: str) -> Path:
        target = (self.root / relative).resolve()
        if target != self.root and self.root not in target.parents:
            raise PermissionError("Path escapes project root")
        if any(part in self.IGNORED for part in target.relative_to(self.root).parts):
            raise PermissionError("Path is inside a protected project directory")
        return target

    def read(self, relative: str, max_chars: int = 100_000) -> str:
        path = self.resolve(relative)
        return path.read_text(encoding="utf-8", errors="replace")[:max_chars]

    def write(self, relative: str, content: str) -> str:
        path = self.resolve(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".jarvis.tmp")
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, path)
        return str(path)

    def exists(self, relative: str) -> bool:
        return self.resolve(relative).exists()
