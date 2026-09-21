from __future__ import annotations
from pathlib import Path

def summarize_project(root: str) -> dict:
    p=Path(root)
    counts={}
    for f in p.rglob("*"):
        if f.is_file() and ".git" not in f.parts and "node_modules" not in f.parts:
            counts[f.suffix.lower()]=counts.get(f.suffix.lower(),0)+1
    return {"root":str(p.resolve()),"extensions":counts}
