"""Persistent voice shell for the real JARVIS V2 agent runtime."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from jarvis_v2.runtime.agent_runtime import JarvisAgentRuntime, JarvisAgentResult
from jarvis_v2.voice.runtime import VoiceRuntime, VoiceTurn


@dataclass
class LiveVoiceResult:
    turn: VoiceTurn
    agent: JarvisAgentResult | None = None
    spoken: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class LiveVoiceAgent:
    """Persistent wake -> authenticate -> agent -> speak loop.

    Authentication is deliberately supplied by the host application; this class
    never accepts a password from the model or stores credentials.
    """

    def __init__(
        self,
        runtime: JarvisAgentRuntime,
        voice: VoiceRuntime,
        authenticate: Callable[[], bool],
        response: Callable[[JarvisAgentResult], str] | None = None,
    ) -> None:
        self.runtime = runtime
        self.voice = voice
        self.authenticate = authenticate
        self.response = response or self._default_response
        self.authenticated = False
        self.running = False

    def run_once(self) -> LiveVoiceResult:
        if not self.voice.wait_for_wake():
            return LiveVoiceResult(VoiceTurn("", wake_detected=False))

        try:
            if not self.authenticated:
                self.authenticated = bool(self.authenticate())
                if not self.authenticated:
                    self.voice.speak("Authentication failed.")
                    return LiveVoiceResult(
                        VoiceTurn("", wake_detected=True),
                        metadata={"authenticated": False},
                    )

            turn = self.voice.listen_once()
            if not turn.transcript:
                return LiveVoiceResult(turn, metadata={"authenticated": True})

            if turn.transcript.lower() in {"exit", "quit", "goodbye", "go to sleep"}:
                self.authenticated = False
                self.voice.speak("Going to sleep.")
                return LiveVoiceResult(turn, metadata={"authenticated": False, "sleep": True})

            result = self.runtime.run(turn.transcript)
            spoken_text = self.response(result)
            if spoken_text:
                self.voice.speak(spoken_text)
            return LiveVoiceResult(
                turn,
                result,
                bool(spoken_text),
                {"authenticated": True},
            )
        finally:
            self.voice.reset()

    def run_forever(self, stop: Callable[[], bool] | None = None) -> None:
        self.running = True
        try:
            while self.running and not (stop and stop()):
                self.run_once()
        finally:
            self.running = False
            self.voice.reset()

    def stop(self) -> None:
        self.running = False

    @staticmethod
    def _default_response(result: JarvisAgentResult) -> str:
        if result.blocked:
            return result.reason or "I couldn't perform that action."
        execution = result.execution
        if execution is None:
            return "I couldn't complete that request."
        verifications = getattr(execution, "verifications", [])
        if verifications:
            latest = verifications[-1]
            if latest.success:
                return latest.message or "Done."
            if getattr(latest, "message", None):
                return latest.message
        return "I couldn't complete that request."
