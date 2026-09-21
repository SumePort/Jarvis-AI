from __future__ import annotations
from .terminal import run

def build(command: str, cwd: str|None=None) -> str:
    return run(command,cwd=cwd,timeout=600)
