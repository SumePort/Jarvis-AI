"""Local Vosk/Piper voice adapter for the JARVIS V2 runtime."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from voice.stt import SpeechRecognizer
from voice.tts import speak as piper_speak
from voice.wake_word import WakeWord

from jarvis_v2.voice.runtime import VoiceRuntime, VoiceTurn


@dataclass
class LocalVoiceConfig:
    model_path: str | None = None
    sample_rate: int = 16000
    wake_word: str = "hey jarvis"
    listen_timeout: float = 8.0
    silence_after_speech: float = 1.15


class LocalWakeWordRuntime(VoiceRuntime):
    """Real microphone runtime using local Vosk STT and Piper TTS.

    Vosk listens continuously in short utterance windows. The wake phrase is
    detected locally; the first utterance can also contain the command, which
    avoids making the user repeat themselves after saying "Hey Jarvis".
    """

    def __init__(
        self,
        recognizer: SpeechRecognizer,
        wake_word: WakeWord,
        tts: Callable[[str], object] = piper_speak,
        listen_timeout: float = 8.0,
        silence_after_speech: float = 1.15,
    ) -> None:
        self.recognizer = recognizer
        self.wake_word = wake_word
        self.listen_timeout = listen_timeout
        self.silence_after_speech = silence_after_speech
        self._pending_command = ""
        super().__init__(self._detect_wake, self._listen_command, tts)

    def _detect_wake(self) -> bool:
        transcript = self.recognizer.listen(
            timeout=self.listen_timeout,
            silence_after_speech=self.silence_after_speech,
        )
        if not transcript:
            return False
        command = self.wake_word.strip(transcript)
        if not command:
            return False
        self._pending_command = command
        return True

    def _listen_command(self) -> str:
        if self._pending_command:
            command = self._pending_command
            self._pending_command = ""
            return command
        return self.recognizer.listen(
            timeout=self.listen_timeout,
            silence_after_speech=self.silence_after_speech,
        )

    def reset(self) -> None:
        self._pending_command = ""
        super().reset()


def build_local_voice(
    config: LocalVoiceConfig | None = None,
) -> LocalWakeWordRuntime:
    config = config or LocalVoiceConfig()
    recognizer = SpeechRecognizer(
        model_path=config.model_path,
        sample_rate=config.sample_rate,
    )
    return LocalWakeWordRuntime(
        recognizer=recognizer,
        wake_word=WakeWord(config.wake_word),
        listen_timeout=config.listen_timeout,
        silence_after_speech=config.silence_after_speech,
    )
