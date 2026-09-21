"""Local Piper text-to-speech with Windows audio playback."""
from __future__ import annotations

import os
import subprocess
import tempfile


def speak(text: str) -> str:
    text = " ".join(str(text).split()).strip()
    if not text:
        return ""

    exe = os.getenv("PIPER_EXE")
    model = os.getenv("PIPER_MODEL")
    if not exe or not model:
        return "Piper is not configured."

    fd, output = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        subprocess.run(
            [exe, "--model", model, "--output_file", output],
            input=text,
            text=True,
            check=True,
            timeout=60,
        )
        import winsound
        winsound.PlaySound(output, winsound.SND_FILENAME)
        return "Spoken."
    except (subprocess.SubprocessError, OSError) as exc:
        return f"TTS error: {exc}"
    finally:
        try:
            os.unlink(output)
        except OSError:
            pass
