from __future__ import annotations
from brain.local_brain import LocalBrain

def plan(task: str, context: str="") -> str:
    return LocalBrain().ask(f"Create a concise implementation plan for:\n{task}\nContext:\n{context}")
