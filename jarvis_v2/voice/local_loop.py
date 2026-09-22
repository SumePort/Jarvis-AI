"""Runnable local Vosk/Piper bridge for the JARVIS V2 agent runtime."""
from __future__ import annotations

import getpass
import os

from jarvis_v2.runtime.local import build_local_runtime
from jarvis_v2.voice.live_agent import LiveVoiceAgent
from jarvis_v2.voice.runtime import VoiceRuntime
from voice.stt import SpeechRecognizer
from voice.tts import speak
from voice.wake_word import WakeWord


class LocalWakeDetector:
    """Listen locally until the configured wake phrase is heard."""

    def __init__(self, recognizer: SpeechRecognizer, wake: WakeWord):
        self.recognizer = recognizer
        self.wake = wake

    def __call__(self) -> bool:
        transcript = self.recognizer.listen(timeout=12.0, silence_after_speech=0.7)
        if self.wake.matches(transcript):
            print("[JARVIS] Wake word detected.", flush=True)
            return True
        return False


def console_authenticate() -> bool:
    identity = os.getenv("JARVIS_IDENTITY", "default")
    credential = getpass.getpass(f"JARVIS credential for {identity}: ")
    # The runtime itself does not receive or store the credential. Hosts that
    # already have an identity service should replace this callback.
    expected = os.getenv("JARVIS_LOCAL_CREDENTIAL")
    if expected is None:
        print("[JARVIS] Set JARVIS_LOCAL_CREDENTIAL or provide an identity service.", flush=True)
        return False
    return credential == expected


def build_voice_agent() -> LiveVoiceAgent:
    recognizer = SpeechRecognizer()
    wake = WakeWord()
    voice = VoiceRuntime(
        LocalWakeDetector(recognizer, wake),
        lambda: recognizer.listen(),
        speak,
    )
    runtime, _ = build_local_runtime()
    return LiveVoiceAgent(runtime, voice, console_authenticate)


def main() -> None:
    print("=" * 64)
    print("JARVIS V2 — LOCAL VOICE AGENT")
    print("=" * 64)
    print(f"Wake word : {os.getenv('JARVIS_WAKE_WORD', 'hey jarvis')}")
    print("Brain     : local llama.cpp")
    print("STT       : local Vosk")
    print("TTS       : local Piper")
    print("Mode      : local-first")
    print()
    agent = build_voice_agent()
    agent.run_forever()


if __name__ == "__main__":
    main()
