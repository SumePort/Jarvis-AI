"""Local Piper text-to-speech with Windows audio playback."""
from __future__ import annotations

import os
import subprocess
import tempfile
import wave


def speak(text: str) -> str:
    text = " ".join(str(text).split()).strip()
    if not text:
        return ""

    exe = os.getenv("PIPER_EXE")
    model = os.getenv("PIPER_MODEL")
    if not exe or not model:
        return "Piper is not configured."

    output = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    output.close()
    try:
        subprocess.run(
            [exe, "--model", model, "--output_file", output.name],
            input=text,
            text=True,
            check=True,
            timeout=60,
        )
        _play_wav(output.name)
        return "Spoken."
    except (subprocess.SubprocessError, OSError, ValueError) as exc:
        return f"TTS error: {exc}"
    finally:
        try:
            os.unlink(output.name)
        except OSError:
            pass


def _play_wav(path: str) -> None:
    import winsound
    winsound.PlaySound(path, winsound.SND_FILENAME)
