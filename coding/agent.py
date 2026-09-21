from __future__ import annotations
from .planner import plan
from .analyzer import project_files

class CodingAgent:
    def inspect(self, root: str):
        return project_files(root)
    def plan(self, task: str, context: str=""):
        return plan(task,context)
