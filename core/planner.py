from __future__ import annotations
from dataclasses import dataclass
from brain.local_brain import LocalBrain

@dataclass
class Plan:
    text: str
    steps: list[str]

class Planner:
    def __init__(self, brain=None):
        self.brain=brain or LocalBrain()
    def make_plan(self, request: str, context: str="") -> Plan:
        text=self.brain.ask("Return a short numbered plan only.\nRequest: "+request+"\nContext: "+context)
        steps=[line.strip(" -") for line in text.splitlines() if line.strip()]
        return Plan(text,steps)
