from __future__ import annotations
from .store import MemoryStore

class ConversationMemory:
    def __init__(self, store=None):
        self.store=store or MemoryStore()
    def add(self,role: str,content: str):
        self.store.add_message(role,content)
    def recent(self,limit: int=20):
        return self.store.recent(limit)
