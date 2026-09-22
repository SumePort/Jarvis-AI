from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from jarvis_v2.personal.reminders import Reminder, ReminderStore


@dataclass
class ReminderDelivery:
    reminder: Reminder
    delivered: bool


class ReminderScheduler:
    """Bounded polling scheduler; the host process decides how often to poll."""

    def __init__(self, store: ReminderStore | None = None):
        self.store = store or ReminderStore()

    def poll(self, now: datetime | None = None, deliver: Callable[[Reminder], None] | None = None) -> list[ReminderDelivery]:
        due = self.store.due(now or datetime.now(timezone.utc))
        results = []
        for reminder in due:
            if deliver:
                deliver(reminder)
            self.store.mark_delivered(reminder.id)
            results.append(ReminderDelivery(reminder, True))
        return results
