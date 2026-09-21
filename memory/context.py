from __future__ import annotations
from .store import MemoryStore

def build_context(store: MemoryStore, limit: int=12) -> str:
    rows=store.recent(limit)
    return "\n".join(f"{x['role']}: {x['content']}" for x in rows)
