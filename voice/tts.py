"""Optional local TTS adapter. Uses Piper executable when configured."""
from __future__ import annotations
import os, subprocess

def speak(text: str) -> str:
    exe=os.getenv("PIPER_EXE")
    model=os.getenv("PIPER_MODEL")
    if not exe or not model:
        return "Piper is not configured; text response returned instead."
    subprocess.run([exe,"--model",model],input=text,text=True,check=False)
    return "Spoken."
