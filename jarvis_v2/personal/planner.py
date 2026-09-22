from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

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
    def __init__(self, tasks=None, calendar=None, reminders=None, contacts=None, communication=None):
        self.tasks = tasks or TaskStore()
        self.calendar = calendar or CalendarStore()
        self.reminders = reminders or ReminderStore()
        self.contacts = contacts or ContactStore()
        self.communication = communication or CommunicationService()

    def plan(self, request: str) -> PersonalPlan:
        from jarvis_v2.personal.planner import PersonalPlanner as BasePlanner
        base = BasePlanner(self.tasks, self.calendar, self.reminders)
        result = base.plan(request)
        lower = request.strip().lower()

        if result.intent != "conversation":
            return PersonalPlan(result.intent, result.tasks, result.events, result.reminders, explanation=result.explanation)

        if lower.startswith("add contact "):
            value = request.strip()[12:].strip()
            contact = self.contacts.add(value)
            return PersonalPlan("create_contact", contacts=[contact], explanation="Saved a personal contact.")

        if lower in {"show my contacts", "find my contacts"}:
            return PersonalPlan("list_contacts", contacts=self.contacts.all(), explanation="Listed personal contacts.")

        if lower.startswith("prepare message ") or lower.startswith("draft message "):
            prefix = "prepare message " if lower.startswith("prepare message ") else "draft message "
            payload = request.strip()[len(prefix):].strip()
            if " | " not in payload:
                return PersonalPlan("conversation", explanation="Message requires recipient and body separated by ' | '.")
            recipient, body = payload.split(" | ", 1)
            message = self.communication.prepare("generic", recipient.strip(), body.strip())
            return PersonalPlan("prepare_message", messages=[message], explanation="Prepared a message; sending still requires explicit confirmation.")

        return PersonalPlan("conversation", explanation="No deterministic personal action matched.")
