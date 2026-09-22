from __future__ import annotations

from dataclasses import dataclass
import time
import uuid

from jarvis_v2.memory.store import MemoryRecord, MemoryStore

@dataclass
class MemoryPolicy:
    durable_kinds: tuple[str, ...] = ("preference", "goal", "routine", "identity", "important")
    temporary_kinds: tuple[str, ...] = ("conversation", "observation", "working")
    default_ttl_seconds: float = 7 * 24 * 3600

class PersonalMemory:
    """Personal memory layer separating durable knowledge from temporary context."""
    def __init__(self, store: MemoryStore | None = None, policy: MemoryPolicy | None = None):
        self.store=store or MemoryStore(); self.policy=policy or MemoryPolicy()
    def remember(self, text: str, kind: str="working", tags: list[str] | None=None, source: str="user", ttl_seconds: float | None=None) -> MemoryRecord:
        if kind not in self.policy.durable_kinds + self.policy.temporary_kinds:
            raise ValueError("Unsupported personal memory kind")
        now=time.time(); ttl=None if kind in self.policy.durable_kinds else (ttl_seconds if ttl_seconds is not None else self.policy.default_ttl_seconds)
        metadata={"durable": kind in self.policy.durable_kinds}
        if ttl is not None: metadata["expires_at"]=now+max(0,ttl)
        record=MemoryRecord(str(uuid.uuid4()),kind,text,source=source,tags=tags or [],metadata=metadata,created_at=now,updated_at=now)
        self.store.add(record); return record
    def recall(self, query: str, limit: int=8) -> list[MemoryRecord]:
        now=time.time(); out=[]
        for record in self.store.search(query, limit=max(limit*3,limit)):
            expires=record.metadata.get("expires_at")
            if expires is not None and float(expires) <= now: continue
            out.append(record)
            if len(out)>=limit: break
        return out
    def forget(self, memory_id: str) -> bool:
        records=self.store.all(); found=False
        for record in records:
            if record.id==memory_id:
                record.metadata["forgotten"]=True; record.updated_at=time.time(); found=True
        if not found: return False
        self.store.path.write_text("".join(__import__("json").dumps(r.__dict__,ensure_ascii=False)+"\n" for r in records),encoding="utf-8")
        return True
