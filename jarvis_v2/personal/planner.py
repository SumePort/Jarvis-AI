from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import re

from jarvis_v2.personal.tasks import PersonalTask, TaskStore
from jarvis_v2.personal.calendar import CalendarEvent, CalendarStore
from jarvis_v2.personal.reminders import Reminder, ReminderStore
from jarvis_v2.personal.contacts import Contact, ContactStore, CommunicationService, MessageRequest


@dataclass
class PersonalPlan:
    intent: str
    tasks: list[PersonalTask] = field(default_factory=list)
    events: list[CalendarEvent] = field(default_factory=list)
    reminders: list[Reminder] = field(default_factory=list)
    contacts: list[Contact] = field(default_factory=list)
    messages: list[MessageRequest] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> dict:
        return {
            "intent": self.intent,
            "tasks": [t.__dict__ for t in self.tasks],
            "events": [e.__dict__ for e in self.events],
            "reminders": [r.__dict__ for r in self.reminders],
            "contacts": [c.__dict__ for c in self.contacts],
            "messages": [m.__dict__ for m in self.messages],
            "explanation": self.explanation,
        }


class PersonalPlanner:
    """Deterministic personal planning layer.

    This class owns the base task/calendar/reminder routing. It must not
    instantiate itself recursively.
    """

    def __init__(self, tasks=None, calendar=None, reminders=None, contacts=None, communication=None):
        self.tasks = tasks if tasks is not None else TaskStore()
        self.calendar = calendar if calendar is not None else CalendarStore()
        self.reminders = reminders if reminders is not None else ReminderStore()
        self.contacts = contacts if contacts is not None else ContactStore()
        self.communication = communication if communication is not None else CommunicationService()

    def plan(self, request: str) -> PersonalPlan:
        text = request.strip()
        lower = text.lower()

        if lower.startswith("add contact "):
            contact = self.contacts.add(text[len("add contact "):].strip())
            return PersonalPlan("create_contact", contacts=[contact], explanation="Saved a personal contact.")

        if lower in {"show my contacts", "find my contacts"}:
            return PersonalPlan("list_contacts", contacts=self.contacts.all(), explanation="Listed personal contacts.")

        for prefix in ("prepare message ", "draft message "):
            if lower.startswith(prefix):
                payload = text[len(prefix):].strip()
                if " | " not in payload:
                    return PersonalPlan("conversation", explanation="Message requires recipient and body separated by ' | '.")
                recipient, body = payload.split(" | ", 1)
                message = self.communication.prepare("generic", recipient.strip(), body.strip())
                return PersonalPlan("prepare_message", messages=[message], explanation="Prepared a message; sending still requires explicit confirmation.")

        if lower.startswith("remind me to "):
            body = text[len("remind me to "):].strip()
            time_match = re.search(r"\bat\s+(\d{1,2}:\d{2})\s*$", lower)
            if time_match:
                hour, minute = map(int, time_match.group(1).split(":"))
                now = datetime.now(timezone.utc)
                remind_at = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if remind_at <= now:
                    remind_at += timedelta(days=1)
                reminder_text = text[len("remind me to "):len("remind me to ") + time_match.start()].strip()
                reminder = self.reminders.add(reminder_text, remind_at.isoformat())
                return PersonalPlan("create_reminder", reminders=[reminder], explanation="Created a timed reminder.")

            if body.lower().endswith(" tomorrow"):
                task_title = body[:-len(" tomorrow")].strip()
                due = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
                task = self.tasks.add(task_title, due_at=due)
            else:
                task = self.tasks.add(body)
            return PersonalPlan("create_task", tasks=[task], explanation="Created a personal task.")

        if lower.startswith("schedule "):
            payload = text[len("schedule "):].strip()
            match = re.match(r"(.+?)\s+at\s+(\d{1,2}:\d{2})$", payload, re.IGNORECASE)
            if match:
                hour, minute = map(int, match.group(2).split(":"))
                now = datetime.now(timezone.utc)
                starts = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if starts <= now:
                    starts += timedelta(days=1)
                event = self.calendar.add(match.group(1).strip(), starts.isoformat())
                return PersonalPlan("create_event", events=[event], explanation="Created a calendar event.")

        return PersonalPlan("conversation", explanation="No deterministic personal action matched.")
