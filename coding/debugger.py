from __future__ import annotations
from .terminal import run

def run_diagnostic(command: str, cwd: str|None=None) -> str:
    return run(command,cwd=cwd,timeout=180)
