from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
import uuid


@dataclass
class Contact:
    id: str
    name: str
    phone: str | None = None
    email: str | None = None
    notes: str = ""


class ContactStore:
    """Identity-scoped local contacts."""

    def __init__(self, path: str | Path = "data/jarvis_v2/contacts.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def all(self) -> list[Contact]:
        if not self.path.exists():
            return []
        try:
            return [Contact(**x) for x in json.loads(self.path.read_text(encoding="utf-8"))]
        except (OSError, json.JSONDecodeError, TypeError):
            return []

    def _save(self, contacts: list[Contact]) -> None:
        self.path.write_text(json.dumps([asdict(c) for c in contacts], indent=2), encoding="utf-8")

    def add(self, name: str, phone: str | None = None, email: str | None = None, notes: str = "") -> Contact:
        contact = Contact(str(uuid.uuid4()), name.strip(), phone, email, notes)
        contacts = self.all()
        contacts.append(contact)
        self._save(contacts)
        return contact

    def find(self, query: str) -> list[Contact]:
        q = query.strip().lower()
        return [c for c in self.all() if q in c.name.lower() or (c.email and q in c.email.lower()) or (c.phone and q in c.phone)]


class MessageStatus:
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"


@dataclass
class MessageRequest:
    id: str
    channel: str
    recipient: str
    body: str
    status: str = MessageStatus.QUEUED
    provider: str | None = None


class CommunicationService:
    """Provider-neutral communication queue.

    Sending is intentionally confirmation-gated: this layer never sends by itself.
    """

    def __init__(self, path: str | Path = "data/jarvis_v2/messages.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> list[MessageRequest]:
        if not self.path.exists():
            return []
        try:
            return [MessageRequest(**x) for x in json.loads(self.path.read_text(encoding="utf-8"))]
        except (OSError, json.JSONDecodeError, TypeError):
            return []

    def _save(self, messages: list[MessageRequest]) -> None:
        self.path.write_text(json.dumps([asdict(m) for m in messages], indent=2), encoding="utf-8")

    def prepare(self, channel: str, recipient: str, body: str, provider: str | None = None) -> MessageRequest:
        message = MessageRequest(str(uuid.uuid4()), channel, recipient, body, provider=provider)
        messages = self._load()
        messages.append(message)
        self._save(messages)
        return message

    def confirm_and_mark_sent(self, message_id: str) -> MessageRequest:
        messages = self._load()
        for message in messages:
            if message.id == message_id:
                if message.status != MessageStatus.QUEUED:
                    raise ValueError("Message is not awaiting confirmation")
                message.status = MessageStatus.SENT
                self._save(messages)
                return message
        raise KeyError(message_id)
