"""Local, structured persistent memory with simple relevance retrieval."""
from __future__ import annotations
import json, re, time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

@dataclass
class MemoryRecord:
    id: str
    kind: str
    text: str
    source: str = ""
    project: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

class MemoryStore:
    def __init__(self, path: str | Path = "data/jarvis_v2/memory.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def add(self, record: MemoryRecord) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")

    def all(self) -> list[MemoryRecord]:
        if not self.path.exists(): return []
        out=[]
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try: out.append(MemoryRecord(**json.loads(line)))
            except (json.JSONDecodeError, TypeError): continue
        return out

    def search(self, query: str, limit: int = 8, project: str | None = None) -> list[MemoryRecord]:
        terms=set(re.findall(r"[a-zA-Z0-9_]+", query.lower()))
        scored=[]
        for r in self.all():
            if project and r.project and r.project != project: continue
            hay=(r.text+" "+r.source+" "+" ".join(r.tags)).lower()
            score=sum(1 for t in terms if t in hay)
            if score: scored.append((score, r.updated_at, r))
        scored.sort(key=lambda x:(x[0],x[1]), reverse=True)
        return [x[2] for x in scored[:limit]]
