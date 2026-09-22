from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from datetime import datetime, timezone
import json
import uuid

@dataclass
class PersonalTask:
    id: str
    title: str
    due_at: str | None = None
    priority: str = "normal"
    status: str = "pending"
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class TaskStore:
    def __init__(self, path: str | Path = "data/jarvis_v2/tasks.json"):
        self.path=Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
    def all(self) -> list[PersonalTask]:
        if not self.path.exists(): return []
        try: return [PersonalTask(**x) for x in json.loads(self.path.read_text(encoding="utf-8"))]
        except (OSError, json.JSONDecodeError, TypeError): return []
    def _save(self, tasks: list[PersonalTask]) -> list[PersonalTask]:
        self.path.write_text(json.dumps([asdict(x) for x in tasks], indent=2, ensure_ascii=False), encoding="utf-8"); return tasks
    def add(self, title: str, due_at: str | None = None, priority: str = "normal", notes: str = "") -> PersonalTask:
        task=PersonalTask(str(uuid.uuid4()), title, due_at, priority, "pending", notes); tasks=self.all(); tasks.append(task); self._save(tasks); return task
    def complete(self, task_id: str) -> PersonalTask:
        tasks=self.all()
        for t in tasks:
            if t.id==task_id: t.status="completed"; self._save(tasks); return t
        raise KeyError(task_id)
    def pending(self) -> list[PersonalTask]: return [t for t in self.all() if t.status=="pending"]
