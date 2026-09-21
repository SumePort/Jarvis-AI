"""Local microphone speech recognition using Vosk + sounddevice."""
from __future__ import annotations

import json
import os
import time

import sounddevice as sd


class SpeechRecognizer:
    def __init__(self, model_path: str | None = None, sample_rate: int = 16000):
        from vosk import KaldiRecognizer, Model

        self.model_path = model_path or os.getenv("VOSK_MODEL_PATH", "models/vosk-model-small-en-us-0.15")
        self.sample_rate = sample_rate
        self.model = Model(self.model_path)
        self.KaldiRecognizer = KaldiRecognizer

    @staticmethod
    def _rms(data: bytes) -> float:
        import array
        samples = array.array("h")
        samples.frombytes(data)
        if not samples:
            return 0.0
        return (sum(x * x for x in samples) / len(samples)) ** 0.5

    def listen(self, timeout: float = 8.0, silence_after_speech: float = 1.15) -> str:
        recognizer = self.KaldiRecognizer(self.model, self.sample_rate)
        recognizer.SetWords(True)
        chunks: list[str] = []
        started = False
        started_at = time.monotonic()
        last_voice = started_at
        speech_threshold = float(os.getenv("JARVIS_VOICE_THRESHOLD", "450"))

        def callback(indata, frames, time_info, status):
            if status:
                print(f"[MIC] {status}", flush=True)
            recognizer.AcceptWaveform(bytes(indata))

        with sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=8000,
            dtype="int16",
            channels=1,
            device=self._device(),
            callback=callback,
        ):
            while time.monotonic() - started_at < timeout:
                time.sleep(0.08)
                partial = json.loads(recognizer.PartialResult()).get("partial", "").strip()
                if partial:
                    started = True
                    last_voice = time.monotonic()
                # RMS is checked independently so silence can end a sentence.
                if started and time.monotonic() - last_voice >= silence_after_speech:
                    break

        final = json.loads(recognizer.FinalResult()).get("text", "").strip()
        return " ".join(chunks + ([final] if final else [])).strip()

    @staticmethod
    def _device():
        value = os.getenv("JARVIS_MIC_DEVICE", "").strip()
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            return value


def transcribe_file(wav_path: str, model_path: str) -> str:
    try:
        import wave
        from vosk import Model, KaldiRecognizer
    except ImportError as exc:
        raise RuntimeError("Install vosk to enable local speech recognition.") from exc
    with wave.open(wav_path, "rb") as wf:
        rec = KaldiRecognizer(Model(model_path), wf.getframerate())
        parts = []
        while True:
            data = wf.readframes(4000)
            if not data:
                break
            if rec.AcceptWaveform(data):
                parts.append(json.loads(rec.Result()).get("text", ""))
        parts.append(json.loads(rec.FinalResult()).get("text", ""))
    return " ".join(x for x in parts if x).strip()
