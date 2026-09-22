from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import re

from jarvis_v2.personal.tasks import PersonalTask, TaskStore
from jarvis_v2.personal.calendar import CalendarEvent, CalendarStore
from jarvis_v2.personal.reminders import Reminder, ReminderStore


@dataclass
class PersonalPlan:
    intent: str
    tasks: list[PersonalTask] = field(default_factory=list)
    events: list[CalendarEvent] = field(default_factory=list)
    reminders: list[Reminder] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> dict:
        return {
            "intent": self.intent,
            "tasks": [t.__dict__ for t in self.tasks],
            "events": [e.__dict__ for e in self.events],
            "reminders": [r.__dict__ for r in self.reminders],
            "explanation": self.explanation,
        }


class PersonalPlanner:
    """Deterministic first-stage planner for common personal-assistant requests."""

    def __init__(self, tasks: TaskStore | None = None, calendar: CalendarStore | None = None, reminders: ReminderStore | None = None):
        self.tasks = tasks or TaskStore()
        self.calendar = calendar or CalendarStore()
        self.reminders = reminders or ReminderStore()

    def plan(self, request: str) -> PersonalPlan:
        text = request.strip()
        lower = text.lower()

        if lower.startswith(("remind me to ", "remember to ", "add a task to ", "add task ")):
            prefix = next(p for p in ("remind me to ", "remember to ", "add a task to ", "add task ") if lower.startswith(p))
            title = text[len(prefix):].strip()
            due = None
            if " tomorrow" in lower:
                due = (datetime.now(timezone.utc) + timedelta(days=1)).date().isoformat()
                title = re.sub(r"\s+tomorrow\b", "", title, flags=re.I).strip()
            task = self.tasks.add(title, due_at=due)
            return PersonalPlan("create_task", [task], explanation="Created a personal task from the explicit request.")

        reminder_match = re.match(r"^remind me(?: to)? (.+?) (?:at|on) (.+)$", text, re.I)
        if reminder_match:
            reminder_text = reminder_match.group(1).strip()
            remind_at = _parse_when(reminder_match.group(2).strip())
            if remind_at:
                reminder = self.reminders.add(reminder_text, remind_at)
                return PersonalPlan("create_reminder", reminders=[reminder], explanation="Scheduled a persistent reminder.")

        event_match = re.match(r"^(?:schedule|add) (?:a )?(?:meeting|event)? ?(.+?) (?:at|on) (.+)$", text, re.I)
        if event_match and not lower.startswith(("add task", "add a task")):
            title = event_match.group(1).strip()
            starts_at = _parse_when(event_match.group(2).strip())
            if starts_at:
                event = self.calendar.add(title, starts_at)
                return PersonalPlan("create_event", events=[event], explanation="Added a calendar event.")

        if lower in {"show my tasks", "what are my tasks", "show my pending tasks"}:
            return PersonalPlan("list_tasks", self.tasks.pending(), explanation="Listed pending personal tasks.")

        if lower in {"show my calendar", "what is on my calendar", "show my upcoming events"}:
            return PersonalPlan("list_events", events=self.calendar.upcoming(), explanation="Listed upcoming calendar events.")

        if lower in {"show my reminders", "what are my reminders"}:
            pending = [r for r in self.reminders.all() if r.status == "pending"]
            return PersonalPlan("list_reminders", reminders=pending, explanation="Listed pending reminders.")

        return PersonalPlan("conversation", explanation="No deterministic personal action matched; defer to the conversational brain.")


def _parse_when(value: str) -> str | None:
    now = datetime.now(timezone.utc)
    value = value.strip().lower()
    if value == "tomorrow":
        return (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0).isoformat()
    if value == "today":
        return now.replace(second=0, microsecond=0).isoformat()
    match = re.fullmatch(r"(?:tomorrow\s+)?(\d{1,2}):(\d{2})(?:\s*(am|pm))?", value)
    if not match:
        return None
    hour, minute = int(match.group(1)), int(match.group(2))
    meridiem = match.group(3)
    if meridiem:
        if hour < 1 or hour > 12 or minute > 59:
            return None
        if meridiem == "pm" and hour != 12:
            hour += 12
        if meridiem == "am" and hour == 12:
            hour = 0
    elif hour > 23 or minute > 59:
        return None
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if "tomorrow" in value:
        target += timedelta(days=1)
    elif target < now:
        target += timedelta(days=1)
    return target.isoformat()
