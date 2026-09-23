"""Low-latency local voice engine for JARVIS."""
from __future__ import annotations
import queue, threading, time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from jarvis_v2.voice.profile import JARVIS_MALE_PROFILE, VoiceProfile
from jarvis_v2.voice.providers import FasterWhisperSTT, PiperTTS, SpeechToText, TextToSpeech
@dataclass
class VoiceEngineConfig:
    wake_word: str = "hey jarvis"
    stt_model: str = "tiny"
    language: str | None = None
    silence_timeout: float = 0.8
    max_queue: int = 8
    profile: VoiceProfile = JARVIS_MALE_PROFILE
class LocalVoiceEngine:
    def __init__(self, config: VoiceEngineConfig | None = None, stt: SpeechToText | None = None, tts: TextToSpeech | None = None) -> None:
        self.config=config or VoiceEngineConfig(); self.stt=stt; self.tts=tts; self._stop=threading.Event(); self._interrupt=threading.Event(); self._audio_queue=queue.Queue(maxsize=self.config.max_queue)
    def stop(self): self._stop.set(); self._interrupt.set()
    def interrupt(self): self._interrupt.set()
    def clear_interrupt(self): self._interrupt.clear()
    def speak(self,text,output_path):
        if self.tts is None: self.tts=PiperTTS()
        self.clear_interrupt(); return self.tts.synthesize(text,output_path)
    def transcribe(self,audio_path):
        if self.stt is None: self.stt=FasterWhisperSTT(self.config.stt_model,self.config.language)
        return self.stt.transcribe(audio_path)
    def conversational_style_prompt(self):
        p=self.config.profile
        return f"Voice persona: {p.name}. Speak as a {p.age_style} {p.gender} assistant. Use a {p.timbre} voice with {p.accent}. Delivery is {p.delivery}. Use {p.pacing}. Keep responses conversational rather than theatrical. Do not imitate a named actor or copyrighted character performance."
    def run_turns(self,capture:Callable[[],str|None],respond:Callable[[str],str],play:Callable[[str],None]):
        while not self._stop.is_set():
            audio_path=capture()
            if not audio_path: time.sleep(0.02); continue
            text=self.transcribe(audio_path).strip()
            if not text: continue
            response=respond(text).strip()
            if not response: continue
            output=str(Path(audio_path).with_suffix(".jarvis.wav")); self.speak(response,output)
            if not self._interrupt.is_set(): play(output)
