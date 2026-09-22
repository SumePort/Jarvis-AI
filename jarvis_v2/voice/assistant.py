"""Voice-facing personal assistant session for JARVIS V2."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from jarvis_v2.personal.assistant import PersonalAssistant, AssistantResult
from jarvis_v2.voice.runtime import VoiceRuntime, VoiceTurn


@dataclass
class VoiceAssistantResult:
    turn: VoiceTurn
    assistant: AssistantResult | None = None
    spoken: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class VoiceAssistant:
    """Connect wake -> STT -> identity-aware assistant -> TTS.

    The voice layer never bypasses PersonalAssistant authentication or policy.
    """

    def __init__(self, assistant: PersonalAssistant, voice: VoiceRuntime):
        self.assistant = assistant
        self.voice = voice

    def listen_and_handle(self) -> VoiceAssistantResult:
        if not self.voice.wait_for_wake():
            return VoiceAssistantResult(VoiceTurn("", wake_detected=False))

        turn = self.voice.listen_once()
        if not turn.transcript:
            self.voice.reset()
            return VoiceAssistantResult(turn)

        try:
            result = self.assistant.handle(turn.transcript)
            response = self._response_text(result)
            if response:
                self.voice.speak(response)
            return VoiceAssistantResult(turn, result, bool(response), {"identity_id": self.assistant.conversation.session.identity_id})
        finally:
            self.voice.reset()

    @staticmethod
    def _response_text(result: AssistantResult) -> str:
        if result.mode == "conversation" and result.conversation:
            return result.conversation.response
        if result.mode == "action" and result.plan:
            return VoiceAssistant._action_text(result.plan)
        return ""

    @staticmethod
    def _action_text(plan: dict[str, Any]) -> str:
        intent = plan.get("intent", "")
        if intent == "create_task":
            tasks = plan.get("tasks", [])
            if tasks:
                return f"Done. I've added {tasks[0].get('title', 'the task')} to your tasks."
        if intent == "list_tasks":
            tasks = plan.get("tasks", [])
            if not tasks:
                return "You have no pending tasks."
            titles = [t.get("title", "untitled task") for t in tasks[:5]]
            return "Your pending tasks are: " + "; ".join(titles)
        return "Done."

