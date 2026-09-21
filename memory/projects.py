from __future__ import annotations
from .store import MemoryStore

class ProjectMemory:
    def __init__(self, store=None):
        self.store=store or MemoryStore()
    def get(self,name: str):
        return self.store.project(name)
