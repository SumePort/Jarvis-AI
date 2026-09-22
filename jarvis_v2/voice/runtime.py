"""Provider-neutral wake, speech-to-text and text-to-speech orchestration."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Any

@dataclass
class VoiceTurn:
    transcript: str
    response: str = ""
    wake_detected: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

class VoiceRuntime:
    def __init__(self, wake_detector: Callable[[], bool], stt: Callable[[], str], tts: Callable[[str], Any]) -> None:
        self.wake_detector=wake_detector
        self.stt=stt
        self.tts=tts
        self.active=False

    def wait_for_wake(self) -> bool:
        self.active=bool(self.wake_detector())
        return self.active

    def listen_once(self) -> VoiceTurn:
        if not self.active:
            return VoiceTurn("", wake_detected=False)
        transcript=self.stt().strip()
        return VoiceTurn(transcript, wake_detected=True)

    def speak(self, text: str) -> VoiceTurn:
        if text:
            self.tts(text)
        return VoiceTurn("", response=text, wake_detected=self.active)

    def reset(self) -> None:
        self.active=False
