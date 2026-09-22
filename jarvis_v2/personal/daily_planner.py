from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Iterable

from jarvis_v2.personal.calendar import CalendarEvent, CalendarStore
from jarvis_v2.personal.profile import PersonalProfileStore
from jarvis_v2.personal.tasks import PersonalTask, TaskStore


@dataclass
class DailyPlan:
    date: str
    focus: list[str] = field(default_factory=list)
    tasks: list[PersonalTask] = field(default_factory=list)
    events: list[CalendarEvent] = field(default_factory=list)
    routines: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "focus": self.focus,
            "tasks": [t.__dict__ for t in self.tasks],
            "events": [e.__dict__ for e in self.events],
            "routines": self.routines,
            "goals": self.goals,
            "notes": self.notes,
        }


class DailyPlanner:
    """Builds a bounded daily plan from one user's profile, tasks and calendar."""

    def __init__(
        self,
        profile: PersonalProfileStore,
        tasks: TaskStore,
        calendar: CalendarStore,
    ):
        self.profile = profile
        self.tasks = tasks
        self.calendar = calendar

    def build(self, target: date | None = None) -> DailyPlan:
        target = target or datetime.now(timezone.utc).date()
        start = datetime.combine(target, datetime.min.time(), timezone.utc)
        end = start + timedelta(days=1)

        events = [
            event for event in self.calendar.all()
            if event.status == "scheduled" and _between(event.starts_at, start, end)
        ]
        events.sort(key=lambda event: event.starts_at)

        tasks = [
            task for task in self.tasks.pending()
            if task.due_at and _due_on(task.due_at, target)
        ]
        priority_order = {"high": 0, "normal": 1, "low": 2}
        tasks.sort(key=lambda task: (priority_order.get(task.priority, 1), task.due_at or ""))

        profile = self.profile.load()
        focus = []
        if profile.goals:
            focus.append(f"Goal: {profile.goals[0]}")
        if tasks:
            focus.append(f"Complete {len(tasks)} due task{'s' if len(tasks) != 1 else ''}")
        if events:
            focus.append(f"Attend {len(events)} scheduled event{'s' if len(events) != 1 else ''}")

        return DailyPlan(
            date=target.isoformat(),
            focus=focus[:3],
            tasks=tasks,
            events=events,
            routines=list(profile.routines.values())[:10],
            goals=profile.goals[:10],
            notes=profile.important_notes[-5:],
        )


def _between(value: str, start: datetime, end: datetime) -> bool:
    try:
        point = datetime.fromisoformat(value)
        if point.tzinfo is None:
            point = point.replace(tzinfo=timezone.utc)
        return start <= point < end
    except ValueError:
        return False


def _due_on(value: str, target: date) -> bool:
    try:
        if "T" not in value:
            return date.fromisoformat(value) == target
        point = datetime.fromisoformat(value)
        if point.tzinfo is None:
            point = point.replace(tzinfo=timezone.utc)
        return point.date() == target
    except ValueError:
        return False
