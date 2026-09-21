from __future__ import annotations
from .local_brain import LocalBrain

def run(prompt: str, system: str|None=None) -> str:
    return LocalBrain().ask(prompt,system=system)
