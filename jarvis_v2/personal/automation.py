from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
import json
import uuid


@dataclass
class Automation:
    id: str
    name: str
    trigger: str
    action: str
    enabled: bool = True
    last_run_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AutomationStore:
    """Identity-scoped persistent automation definitions."""

    def __init__(self, path: str | Path = "data/jarvis_v2/automations.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def all(self) -> list[Automation]:
        if not self.path.exists():
            return []
        try:
            return [Automation(**x) for x in json.loads(self.path.read_text(encoding="utf-8"))]
        except (OSError, json.JSONDecodeError, TypeError):
            return []

    def _save(self, items: list[Automation]) -> None:
        self.path.write_text(json.dumps([asdict(x) for x in items], indent=2), encoding="utf-8")

    def add(self, name: str, trigger: str, action: str, metadata: dict[str, Any] | None = None) -> Automation:
        item = Automation(str(uuid.uuid4()), name.strip(), trigger.strip(), action.strip(), metadata=metadata or {})
        items = self.all()
        items.append(item)
        self._save(items)
        return item

    def set_enabled(self, automation_id: str, enabled: bool) -> Automation:
        items = self.all()
        for item in items:
            if item.id == automation_id:
                item.enabled = enabled
                self._save(items)
                return item
        raise KeyError(automation_id)


class AutomationEngine:
    """Bounded automation runner; only explicitly registered action handlers execute."""

    def __init__(self, store: AutomationStore, handlers: dict[str, Callable[[Automation], Any]] | None = None):
        self.store = store
        self.handlers = handlers or {}

    def due(self, now: datetime | None = None) -> list[Automation]:
        current = now or datetime.now(timezone.utc)
        due = []
        for item in self.store.all():
            if not item.enabled:
                continue
            if item.trigger == "daily":
                if not item.last_run_at or _date(item.last_run_at) < current.date():
                    due.append(item)
            elif item.trigger.startswith("interval:"):
                try:
                    seconds = int(item.trigger.split(":", 1)[1])
                    if not item.last_run_at or (current - datetime.fromisoformat(item.last_run_at)).total_seconds() >= seconds:
                        due.append(item)
                except (ValueError, TypeError):
                    continue
        return due

    def run_due(self, now: datetime | None = None) -> list[Any]:
        current = now or datetime.now(timezone.utc)
        results = []
        for item in self.due(current):
            handler = self.handlers.get(item.action)
            if handler is None:
                continue
            result = handler(item)
            item.last_run_at = current.isoformat()
            items = self.store.all()
            for saved in items:
                if saved.id == item.id:
                    saved.last_run_at = item.last_run_at
            self.store._save(items)
            results.append(result)
        return results


def _date(value: str):
    return datetime.fromisoformat(value).date()
