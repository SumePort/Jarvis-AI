from __future__ import annotations
from pathlib import Path

class ProjectWatcher:
    def changed(self, root: str, known: set[str]) -> list[str]:
        current={str(p) for p in Path(root).rglob("*") if p.is_file() and ".git" not in p.parts}
        return sorted(current-known)
