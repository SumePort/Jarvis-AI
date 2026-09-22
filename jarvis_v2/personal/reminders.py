from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json
import uuid


@dataclass
class Reminder:
    id: str
    text: str
    remind_at: str
    status: str = "pending"
    delivered_at: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ReminderStore:
    """Persistent, identity-scoped reminder queue."""

    def __init__(self, path: str | Path = "data/jarvis_v2/reminders.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def all(self) -> list[Reminder]:
        if not self.path.exists():
            return []
        try:
            return [Reminder(**x) for x in json.loads(self.path.read_text(encoding="utf-8"))]
        except (OSError, json.JSONDecodeError, TypeError):
            return []

    def _save(self, reminders: list[Reminder]) -> list[Reminder]:
        self.path.write_text(
            json.dumps([asdict(x) for x in reminders], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return reminders

    def add(self, text: str, remind_at: str) -> Reminder:
        datetime.fromisoformat(remind_at)
        reminder = Reminder(str(uuid.uuid4()), text.strip(), remind_at)
        reminders = self.all()
        reminders.append(reminder)
        self._save(reminders)
        return reminder

    def due(self, now: datetime | None = None) -> list[Reminder]:
        current = now or datetime.now(timezone.utc)
        return [
            reminder for reminder in self.all()
            if reminder.status == "pending" and _parse(reminder.remind_at) <= current
        ]

    def mark_delivered(self, reminder_id: str) -> Reminder:
        reminders = self.all()
        for reminder in reminders:
            if reminder.id == reminder_id:
                reminder.status = "delivered"
                reminder.delivered_at = datetime.now(timezone.utc).isoformat()
                self._save(reminders)
                return reminder
        raise KeyError(reminder_id)


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value)
