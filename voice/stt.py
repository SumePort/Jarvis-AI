"""Optional Vosk adapter; kept independent from the core."""
from __future__ import annotations

def transcribe_file(wav_path: str, model_path: str) -> str:
    try:
        import wave, json
        from vosk import Model, KaldiRecognizer
    except ImportError as exc:
        raise RuntimeError("Install vosk to enable local speech recognition.") from exc
    wf=wave.open(wav_path,"rb")
    rec=KaldiRecognizer(Model(model_path),wf.getframerate())
    parts=[]
    while True:
        data=wf.readframes(4000)
        if not data: break
        if rec.AcceptWaveform(data):
            parts.append(json.loads(rec.Result()).get("text",""))
    parts.append(json.loads(rec.FinalResult()).get("text",""))
    return " ".join(x for x in parts if x).strip()
