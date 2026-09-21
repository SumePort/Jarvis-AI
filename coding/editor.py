from __future__ import annotations
from pathlib import Path

def write_file(path: str, content: str, overwrite: bool=False) -> str:
    p=Path(path).expanduser().resolve()
    if p.exists() and not overwrite:
        raise FileExistsError(f"{p} exists; confirmation/overwrite required.")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content,encoding="utf-8")
    return f"Wrote {p}"
