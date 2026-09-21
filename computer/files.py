"""Safe local file and folder operations. No hard-coded drive/user paths."""
from __future__ import annotations
import os
import subprocess
from pathlib import Path
from difflib import get_close_matches

def open_path(path: str) -> str:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"Path not found: {p}"
    os.startfile(str(p)) if os.name == "nt" else subprocess.Popen(["xdg-open", str(p)])
    return f"Opened {p}"

def create_folder(path: str) -> str:
    p = Path(path).expanduser().resolve()
    p.mkdir(parents=True, exist_ok=True)
    return f"Created folder {p}"

def read_file(path: str, max_chars: int = 20_000) -> str:
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        return f"File not found: {p}"
    return p.read_text(encoding="utf-8", errors="replace")[:max_chars]

def search_files(root: str, query: str, limit: int = 20) -> list[str]:
    base = Path(root).expanduser().resolve()
    if not base.is_dir():
        return []
    matches = []
    q = query.lower()
    for current, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in {".git",".venv","venv","node_modules","__pycache__"}]
        for name in files:
            if q in name.lower():
                matches.append(str(Path(current) / name))
                if len(matches) >= limit:
                    return matches
    return matches
