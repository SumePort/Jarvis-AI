from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import time
import uuid

from jarvis_v2.brain.provider import BrainProvider, BrainResponse
from jarvis_v2.personal.context import PersonalContext
from jarvis_v2.personal.memory import PersonalMemory
from jarvis_v2.personal.memory_extractor import PersonalMemoryExtractor
from jarvis_v2.personal.identity import IdentityDataPaths, IdentityStore
from jarvis_v2.runtime.session import JarvisSession


@dataclass
class ConversationTurn:
    role: str
    text: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"role": self.role, "text": self.text, "timestamp": self.timestamp, "metadata": self.metadata}


@dataclass
class ConversationResult:
    session_id: str
    user_text: str
    response: str
    turn: ConversationTurn
    context: dict[str, Any]
    brain_metadata: dict[str, Any] = field(default_factory=dict)


class JarvisConversation:
    """Multi-turn assistant loop with identity-scoped personal state."""

    def __init__(
        self,
        brain: BrainProvider,
        session: JarvisSession | None = None,
        personal: PersonalContext | None = None,
        memory: PersonalMemory | None = None,
        identity_store: IdentityStore | None = None,
    ):
        self.brain = brain
        self.session = session or JarvisSession(str(uuid.uuid4()), authenticated=False)
        self.identity_store = identity_store or IdentityStore()
        self.personal = personal or PersonalContext()
        self.memory = memory or PersonalMemory(self.personal.memory)
        self.extractor = PersonalMemoryExtractor(self.memory)
        self.turns: list[ConversationTurn] = []

    def authenticate(self, identity_id: str = "default", credential: str | None = None) -> None:
        if identity_id == "default" and self.identity_store.get("default") is None:
            identity = self.identity_store.ensure_default()
        else:
            identity = self.identity_store.authenticate(identity_id, credential)
        self.session.authenticated = True
        self.session.identity_id = identity.identity_id
        self.session.identity_name = identity.name
        self.bind_identity(identity.identity_id)

    def bind_identity(self, identity_id: str) -> None:
        paths = IdentityDataPaths(identity_id)
        self.personal = PersonalContext(
            memory=__import__("jarvis_v2.memory.store", fromlist=["MemoryStore"]).MemoryStore(paths.memory),
            profile=__import__("jarvis_v2.personal.profile", fromlist=["PersonalProfileStore"]).PersonalProfileStore(paths.profile),
            tasks=__import__("jarvis_v2.personal.tasks", fromlist=["TaskStore"]).TaskStore(paths.tasks),
        )
        self.memory = PersonalMemory(self.personal.memory)
        self.extractor = PersonalMemoryExtractor(self.memory)
        self.turns.clear()

    def logout(self) -> None:
        self.session.authenticated = False
        self.session.identity_id = None
        self.session.identity_name = None
        self.turns.clear()

    def _context(self, text: str) -> dict[str, Any]:
        personal = self.personal.build(text)
        conversation = [t.to_dict() for t in self.turns[-20:]]
        return {
            "identity": {
                "id": self.session.identity_id,
                "name": self.session.identity_name,
            },
            "personal": personal,
            "conversation": conversation,
            "session": {
                "id": self.session.session_id,
                "authenticated": self.session.authenticated,
                "active_project": self.session.active_project,
            },
            "request": text,
        }

    def handle(self, text: str) -> ConversationResult:
        if not self.session.authenticated:
            raise PermissionError("JARVIS session is not authenticated")
        text = text.strip()
        if not text:
            raise ValueError("Conversation input cannot be empty")
        user_turn = ConversationTurn("user", text)
        self.turns.append(user_turn)
        self.extractor.extract(text)
        context = self._context(text)
        response: BrainResponse = self.brain.respond(text, context, [])
        answer = response.text.strip()
        assistant_turn = ConversationTurn("assistant", answer, metadata=response.metadata)
        self.turns.append(assistant_turn)
        self.session.add_turn(text, {"response": answer, "metadata": response.metadata})
        return ConversationResult(self.session.session_id, text, answer, assistant_turn, context, response.metadata)
