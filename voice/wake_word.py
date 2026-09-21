"""Wake-word matching for Jarvis speech transcripts."""
from __future__ import annotations

import os


class WakeWord:
    def __init__(self, phrase: str | None = None):
        self.phrase = (phrase or os.getenv("JARVIS_WAKE_WORD", "hey jarvis")).strip().lower()

    def matches(self, text: str) -> bool:
        normalized = " ".join(text.lower().split())
        return self.phrase in normalized

    def strip(self, text: str) -> str:
        normalized = " ".join(text.split()).strip()
        lower = normalized.lower()
        index = lower.find(self.phrase)
        if index < 0:
            return ""
        return normalized[index + len(self.phrase):].strip(" ,.!?")
