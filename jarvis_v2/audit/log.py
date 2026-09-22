"""Append-only hash-chained audit events."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from pathlib import Path
import hashlib, json, time, uuid

@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    event_type: str
    timestamp: float
    identity: str | None
    request: str | None
    details: dict = field(default_factory=dict)
    previous_hash: str = ""
    event_hash: str = ""

class AuditLog:
    def __init__(self, path: str | Path = "data/jarvis/audit.jsonl") -> None:
        self.path=Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _last_hash(self) -> str:
        if not self.path.exists(): return ""
        last=""
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip(): last=json.loads(line).get("event_hash", "")
        return last

    def append(self, event_type: str, identity: str | None=None, request: str | None=None, details: dict | None=None) -> AuditEvent:
        previous=self._last_hash()
        base={"event_id":uuid.uuid4().hex,"event_type":event_type,"timestamp":time.time(),"identity":identity,"request":request,"details":details or {},"previous_hash":previous}
        payload=json.dumps(base, sort_keys=True, separators=(",",":"), default=str).encode()
        digest=hashlib.sha256(payload).hexdigest()
        event=AuditEvent(**base,event_hash=digest)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event), sort_keys=True, default=str)+"\n")
        return event

    def verify(self) -> bool:
        if not self.path.exists(): return True
        previous=""
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                obj=json.loads(line)
                expected=obj.pop("event_hash", "")
                if obj.get("previous_hash", "") != previous: return False
                payload=json.dumps(obj, sort_keys=True, separators=(",",":"), default=str).encode()
                if hashlib.sha256(payload).hexdigest() != expected: return False
                previous=expected
        return True
