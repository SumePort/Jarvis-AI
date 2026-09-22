from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jarvis_v2.brain.provider import BrainProvider
from jarvis_v2.personal.conversation import JarvisConversation, ConversationResult
from jarvis_v2.personal.planner import PersonalPlanner

@dataclass
class AssistantResult:
    mode: str
    conversation: ConversationResult | None = None
    plan: dict[str, Any] | None = None

class PersonalAssistant:
    """Front door for personal requests: deterministic actions first, conversation otherwise."""
    def __init__(self, brain: BrainProvider, conversation: JarvisConversation | None = None, planner: PersonalPlanner | None = None):
        self.conversation=conversation or JarvisConversation(brain)
        self.planner=planner or PersonalPlanner(self.conversation.personal.tasks)
    def authenticate(self): self.conversation.authenticate()
    def logout(self): self.conversation.logout()
    def handle(self, text: str) -> AssistantResult:
        plan=self.planner.plan(text)
        if plan.intent != "conversation":
            return AssistantResult("action", plan=plan.to_dict())
        return AssistantResult("conversation", conversation=self.conversation.handle(text))
