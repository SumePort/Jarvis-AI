from __future__ import annotations
from .terminal import run

def run_tests(command: str="python -m pytest") -> str:
    return run(command, timeout=300)
