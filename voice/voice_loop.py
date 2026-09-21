"""Compatibility entry point for the LiveKit voice agent.

Use python -m voice.voice_loop or python -m voice.livekit_agent.
The old Vosk/Piper loop remains available in the repository as legacy code,
but LiveKit is now the primary realtime voice path.
"""
from __future__ import annotations

from .livekit_agent import main


if __name__ == "__main__":
    main()
