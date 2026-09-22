from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from jarvis_v2.brain.provider import BrainProvider
from jarvis_v2.personal.conversation import JarvisConversation, ConversationResult
from jarvis_v2.personal.identity import IdentityStore, IdentityDataPaths
from jarvis_v2.personal.planner import PersonalPlanner
from jarvis_v2.personal.daily_planner import DailyPlanner
from jarvis_v2.personal.contacts import ContactStore, CommunicationService


@dataclass
class AssistantResult:
    mode: str
    conversation: ConversationResult | None = None
    plan: dict[str, Any] | None = None


class PersonalAssistant:
    def __init__(self, brain: BrainProvider, conversation=None, planner=None, identity_store=None):
        self.conversation = conversation or JarvisConversation(brain, identity_store=identity_store)
        self.identity_store = identity_store or self.conversation.identity_store
        self.planner = planner or PersonalPlanner(self.conversation.personal.tasks)

    def register_identity(self, identity_id: str, name: str, credential: str | None = None):
        return self.identity_store.register(identity_id, name, credential)

    def authenticate(self, identity_id: str = "default", credential: str | None = None):
        self.conversation.authenticate(identity_id, credential)
        self.planner = PersonalPlanner(
            self.conversation.personal.tasks,
            calendar=self._calendar(),
            reminders=self._reminders(),
            contacts=self._contacts(),
            communication=self._communication(),
        )

    def logout(self):
        self.conversation.logout()

    def build_daily_plan(self):
        if not self.conversation.session.authenticated:
            raise PermissionError("JARVIS session is not authenticated")
        return DailyPlanner(self.conversation.personal.profile, self.conversation.personal.tasks, self._calendar()).build()

    def handle(self, text: str) -> AssistantResult:
        if not self.conversation.session.authenticated:
            raise PermissionError("JARVIS session is not authenticated")
        plan = self.planner.plan(text)
        if plan.intent != "conversation":
            return AssistantResult("action", plan=plan.to_dict())
        return AssistantResult("conversation", conversation=self.conversation.handle(text))

    def _paths(self):
        return IdentityDataPaths(self.conversation.session.identity_id).root

    def _calendar(self):
        from jarvis_v2.personal.calendar import CalendarStore
        return CalendarStore(self._paths() / "calendar.json")

    def _reminders(self):
        from jarvis_v2.personal.reminders import ReminderStore
        return ReminderStore(self._paths() / "reminders.json")

    def _contacts(self):
        return ContactStore(self._paths() / "contacts.json")

    def _communication(self):
        return CommunicationService(self._paths() / "messages.json")
