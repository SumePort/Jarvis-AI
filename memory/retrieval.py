from __future__ import annotations
from .store import MemoryStore

def recent_messages(limit: int=20):
    return MemoryStore().recent(limit)
