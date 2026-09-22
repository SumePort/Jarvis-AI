"""Device/session continuity with explicit identity binding."""
from __future__ import annotations
from dataclasses import dataclass
import secrets
import time


@dataclass
class DeviceSession:
    session_id: str
    user_id: str
    device_id: str
    created_at: float
    active: bool = True


class DeviceSessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, DeviceSession] = {}

    def create(self, user_id: str, device_id: str) -> DeviceSession:
        session = DeviceSession("sess_" + secrets.token_hex(12), user_id, device_id, time.time())
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> DeviceSession | None:
        return self._sessions.get(session_id)

    def revoke(self, session_id: str) -> None:
        session = self._sessions.get(session_id)
        if session:
            session.active = False
