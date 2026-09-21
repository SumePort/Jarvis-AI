"""Controlled local command runner. Dangerous operations are still gated by ToolExecutor."""
from __future__ import annotations
import subprocess

def run(command: str, cwd: str|None=None, timeout: int=120) -> str:
    result=subprocess.run(command, cwd=cwd, shell=True, capture_output=True, text=True,
                          timeout=timeout)
    out=(result.stdout or "") + (result.stderr or "")
    return out[-20_000:]
