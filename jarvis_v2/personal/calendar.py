from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json
import uuid


@dataclass
class CalendarEvent:
    id: str
    title: str
    starts_at: str
    ends_at: str | None = None
    notes: str = ""
    status: str = "scheduled"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CalendarStore:
    """Identity-scoped local calendar store."""

    def __init__(self, path: str | Path = "data/jarvis_v2/calendar.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def all(self) -> list[CalendarEvent]:
        if not self.path.exists():
            return []
        try:
            return [CalendarEvent(**x) for x in json.loads(self.path.read_text(encoding="utf-8"))]
        except (OSError, json.JSONDecodeError, TypeError):
            return []

    def _save(self, events: list[CalendarEvent]) -> list[CalendarEvent]:
        self.path.write_text(
            json.dumps([asdict(x) for x in events], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return events

    def add(self, title: str, starts_at: str, ends_at: str | None = None, notes: str = "") -> CalendarEvent:
        datetime.fromisoformat(starts_at)
        if ends_at:
            datetime.fromisoformat(ends_at)
        event = CalendarEvent(str(uuid.uuid4()), title.strip(), starts_at, ends_at, notes)
        events = self.all()
        events.append(event)
        self._save(events)
        return event

    def cancel(self, event_id: str) -> CalendarEvent:
        events = self.all()
        for event in events:
            if event.id == event_id:
                event.status = "cancelled"
                self._save(events)
                return event
        raise KeyError(event_id)

    def upcoming(self, now: datetime | None = None, limit: int = 20) -> list[CalendarEvent]:
        current = now or datetime.now(timezone.utc)
        events = []
        for event in self.all():
            if event.status != "scheduled":
                continue
            try:
                start = datetime.fromisoformat(event.starts_at)
            except ValueError:
                continue
            if start >= current:
                events.append((start, event))
        events.sort(key=lambda item: item[0])
        return [event for _, event in events[:limit]]
