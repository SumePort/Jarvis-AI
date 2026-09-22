from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import hashlib
import json
import time
import uuid
from typing import Any


@dataclass
class SessionSnapshot:
    session_id: str
    identity_id: str
    active_project: str | None
    history: list[dict[str, Any]]
    turns: list[dict[str, Any]]
    updated_at: float
    revision: int = 1
    device_id: str | None = None
    checksum: str = ""


class SessionContinuityStore:
    """Identity-scoped session snapshots for moving a JARVIS conversation between devices."""

    def __init__(self, root: str | Path = "data/jarvis_v2/session_continuity"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, identity_id: str, session_id: str) -> Path:
        safe_i = "".join(c if c.isalnum() or c in "-_" else "_" for c in identity_id)
        safe_s = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_id)
        return self.root / safe_i / f"{safe_s}.json"

    def save(self, snapshot: SessionSnapshot) -> SessionSnapshot:
        payload = asdict(snapshot)
        payload["checksum"] = ""
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        snapshot.checksum = hashlib.sha256(canonical.encode()).hexdigest()
        path = self._path(snapshot.identity_id, snapshot.session_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(snapshot), indent=2), encoding="utf-8")
        return snapshot

    def create(self, identity_id: str, active_project: str | None, history: list[dict[str, Any]],
               turns: list[dict[str, Any]], device_id: str | None = None) -> SessionSnapshot:
        return self.save(SessionSnapshot(str(uuid.uuid4()), identity_id, active_project,
                                          history[-50:], turns[-20:], time.time(), 1, device_id))

    def load(self, identity_id: str, session_id: str) -> SessionSnapshot:
        path = self._path(identity_id, session_id)
        if not path.is_file():
            candidates = list(self.root.glob(f"*/{session_id}.json"))
            if not candidates:
                raise FileNotFoundError("Session continuity snapshot not found")
            path = candidates[0]
        snapshot = SessionSnapshot(**json.loads(path.read_text(encoding="utf-8")))
        supplied = snapshot.checksum
        payload = asdict(snapshot)
        payload["checksum"] = ""
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        expected = hashlib.sha256(canonical.encode()).hexdigest()
        if supplied != expected:
            raise PermissionError("Session snapshot integrity check failed")
        if snapshot.identity_id != identity_id:
            raise PermissionError("Session belongs to another identity")
        return snapshot

    def latest(self, identity_id: str) -> SessionSnapshot | None:
        directory = self.root / "".join(c if c.isalnum() or c in "-_" else "_" for c in identity_id)
        files = list(directory.glob("*.json")) if directory.exists() else []
        if not files:
            return None
        return self.load(identity_id, max(files, key=lambda p: p.stat().st_mtime).stem)


class SessionContinuity:
    """Converts a live conversation into a portable, bounded continuation state."""

    def __init__(self, store: SessionContinuityStore):
        self.store = store

    def checkpoint(self, conversation: Any, device_id: str | None = None) -> SessionSnapshot:
        session = conversation.session
        if not session.authenticated or not session.identity_id:
            raise PermissionError("Authenticated identity required")
        return self.store.create(session.identity_id, session.active_project,
                                 session.history, [t.to_dict() for t in conversation.turns], device_id)

    def resume(self, conversation: Any, snapshot: SessionSnapshot, device_id: str | None = None) -> None:
        session = conversation.session
        if not session.authenticated or session.identity_id != snapshot.identity_id:
            raise PermissionError("Authenticated identity does not match session snapshot")
        session.session_id = snapshot.session_id
        session.active_project = snapshot.active_project
        session.history = list(snapshot.history[-50:])
        conversation.turns = [
            type(conversation.turns[0])(**t) if conversation.turns else self._turn_type(**t)
            for t in snapshot.turns[-20:]
        ]

    @staticmethod
    def _turn_type(**kwargs):
        from jarvis_v2.personal.conversation import ConversationTurn
        return ConversationTurn(**kwargs)
