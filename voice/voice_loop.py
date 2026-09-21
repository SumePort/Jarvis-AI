"""Voice-first Jarvis assistant loop."""
from __future__ import annotations

import os
import time

from core.main import Jarvis
from security.authentication import AuthenticationManager
from .stt import SpeechRecognizer
from .tts import speak
from .wake_word import WakeWord


class VoiceLoop:
    def __init__(self, jarvis: Jarvis | None = None):
        self.jarvis = jarvis or Jarvis()
        self.wake = WakeWord()
        self.stt = SpeechRecognizer()
        self.running = True

    def run(self) -> None:
        print("=" * 60)
        print("JARVIS — VOICE MODE")
        print("=" * 60)
        print(f"Wake word : {self.wake.phrase.title()}")
        print(f"Mic       : {os.getenv('JARVIS_MIC_DEVICE', 'default')}")
        print("Say 'Hey Jarvis' to activate.")
        print("Press Ctrl+C to stop.")
        print("=" * 60)

        speak("Jarvis is ready.")

        while self.running:
            try:
                transcript = self.stt.listen(timeout=30.0, silence_after_speech=1.0)
                if not transcript:
                    continue

                print(f"[HEARD] {transcript}")
                if not self.wake.matches(transcript):
                    continue

                command = self.wake.strip(transcript)
                if not command:
                    speak("Yes?")
                    command = self.stt.listen(timeout=8.0, silence_after_speech=1.2)

                if not command:
                    continue

                print(f"[USER] {command}")
                try:
                    response = self.jarvis.handle(command)
                except SystemExit:
                    speak("Goodbye.")
                    break

                response = str(response or "").strip()
                print(f"[JARVIS] {response}")

                if response:
                    speak(response)

                time.sleep(0.35)

            except KeyboardInterrupt:
                break
            except Exception as exc:
                print(f"[VOICE ERROR] {exc}")
                speak("I ran into an error. Please try again.")
                time.sleep(1)

        print("Jarvis voice mode stopped.")


def main() -> None:
    if not AuthenticationManager().authenticate():
        print("Authentication failed. Jarvis locked.")
        return
    VoiceLoop().run()


if __name__ == "__main__":
    main()
