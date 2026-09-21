from __future__ import annotations
from .terminal import run

def status(cwd: str=".") -> str:
    return run("git status --short --branch",cwd=cwd)
