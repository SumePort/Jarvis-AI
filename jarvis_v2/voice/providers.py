"""Local STT/TTS provider boundaries for JARVIS."""
from __future__ import annotations
import os, subprocess
from pathlib import Path
from typing import Protocol
class SpeechToText(Protocol):
    def transcribe(self, audio_path: str) -> str: ...
class TextToSpeech(Protocol):
    def synthesize(self, text: str, output_path: str) -> str: ...
class FasterWhisperSTT:
    def __init__(self, model_size: str = "tiny", language: str | None = None) -> None: self.model_size, self.language, self._model = model_size, language, None
    def _load(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
        return self._model
    def transcribe(self, audio_path: str) -> str:
        segments, _ = self._load().transcribe(audio_path, language=self.language, vad_filter=True, beam_size=1)
        return " ".join(s.text.strip() for s in segments if s.text.strip()).strip()
class PiperTTS:
    def __init__(self, executable: str | None = None, model: str | None = None) -> None:
        self.executable = executable or os.getenv("PIPER_EXE", "piper"); self.model = model or os.getenv("PIPER_MODEL")
        if not self.model: raise RuntimeError("PIPER_MODEL is not configured")
    def synthesize(self, text: str, output_path: str) -> str:
        out=Path(output_path); out.parent.mkdir(parents=True, exist_ok=True)
        p=subprocess.run([self.executable,"--model",self.model,"--output_file",str(out)],input=text,text=True,capture_output=True)
        if p.returncode != 0: raise RuntimeError(p.stderr.strip() or "Piper synthesis failed")
        return str(out)
