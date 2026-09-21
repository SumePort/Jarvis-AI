from __future__ import annotations
from pathlib import Path

def project_files(root: str) -> list[str]:
    return [str(p) for p in Path(root).rglob("*") if p.is_file() and ".git" not in p.parts and "node_modules" not in p.parts]
