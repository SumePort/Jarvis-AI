"""Bind JARVIS identity sessions to DOOM device sessions."""
from __future__ import annotations
from jarvis_v2.security.session import IdentitySession
from jarvis_v2.devices.session_manager import DeviceSessionManager


class DoomSessionBridge:
    def __init__(self, sessions: DeviceSessionManager | None = None) -> None:
        self.sessions = sessions or DeviceSessionManager()

    def bind(self, identity: IdentitySession):
        if not identity.authenticated or not identity.user_id or not identity.device_id:
            raise PermissionError("Authenticated identity/device required")
        return self.sessions.create(identity.user_id, identity.device_id)

    def validate(self, session_id: str, user_id: str, device_id: str) -> bool:
        session = self.sessions.get(session_id)
        return bool(session and session.active and session.user_id == user_id and session.device_id == device_id)
