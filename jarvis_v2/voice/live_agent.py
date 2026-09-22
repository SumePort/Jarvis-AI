"""Authenticated persistent voice session for JARVIS V2."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Any
import uuid

from jarvis_v2.voice.runtime import VoiceRuntime
from jarvis_v2.personal.assistant import PersonalAssistant
from jarvis_v2.security.session import IdentitySession
from jarvis_v2.doom.session_bridge import DoomSessionBridge


@dataclass
class LiveVoiceResult:
    status: str
    message: str = ""
    identity: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class LiveVoiceAgent:
    """Wake -> authenticate -> assist -> speak, with DOOM device binding.

    The authentication callback owns credential handling. Credentials never
    enter the transcript, model context, audit events, or this result object.
    """

    def __init__(
        self,
        assistant: PersonalAssistant,
        voice: VoiceRuntime,
        authenticate: Callable[[], tuple[str, str]] ,
        doom_sessions: DoomSessionBridge,
    ):
        self.assistant = assistant
        self.voice = voice
        self.authenticate_callback = authenticate
        self.doom_sessions = doom_sessions
        self.identity_session: IdentitySession | None = None
        self.doom_session_id: str | None = None

    def authenticate_session(self) -> LiveVoiceResult:
        user_id, device_id = self.authenticate_callback()
        if not user_id or not device_id:
            raise PermissionError("Authentication did not provide identity and device")
        session = IdentitySession("voice_" + uuid.uuid4().hex)
        session.authenticate(user_id, device_id)
        doom = self.doom_sessions.bind(session)
        self.identity_session = session
        self.doom_session_id = doom.session_id
        self.assistant.authenticate(user_id)
        return LiveVoiceResult("authenticated", "Authentication successful.", session.identity)

    def run_once(self) -> LiveVoiceResult:
        if not self.voice.wait_for_wake():
            return LiveVoiceResult("sleeping")
        turn = self.voice.listen_once()
        if not turn.transcript:
            return LiveVoiceResult("empty")
        command = turn.transcript.strip()
        if command.lower() in {"exit", "quit", "goodbye", "go to sleep"}:
            self.logout()
            return LiveVoiceResult("sleeping", "Going to sleep.")
        if not self.identity_session or not self.identity_session.authenticated:
            self.authenticate_session()
        try:
            result = self.assistant.handle(command)
            response = self._response(result)
            if response:
                self.voice.speak(response)
            return LiveVoiceResult("handled", response, self.identity_session.identity if self.identity_session else None)
        except PermissionError as exc:
            message = str(exc)
            self.voice.speak(message)
            return LiveVoiceResult("blocked", message)
        finally:
            self.voice.reset()

    def logout(self) -> None:
        if self.identity_session:
            self.identity_session.revoke()
        if self.doom_session_id:
            self.doom_sessions.sessions.revoke(self.doom_session_id)
        try:
            self.assistant.logout()
        finally:
            self.identity_session = None
            self.doom_session_id = None
            self.voice.reset()

    @staticmethod
    def _response(result) -> str:
        if result.mode == "conversation" and result.conversation:
            return result.conversation.response
        if result.mode == "action":
            return "Done."
        return ""
