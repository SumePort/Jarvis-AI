"""Wake-word interface placeholder for local engines."""
from __future__ import annotations

class WakeWord:
    def __init__(self, phrase: str="hey jarvis"):
        self.phrase=phrase.lower()
    def matches(self,text: str) -> bool:
        return self.phrase in text.lower()
