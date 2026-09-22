from __future__ import annotations

from jarvis_v2.personal.memory import PersonalMemory

class PersonalMemoryExtractor:
    """Conservative explicit-memory extractor; it never treats arbitrary conversation as durable memory."""
    DURABLE_PREFIXES={
        "remember that ": "important",
        "remember this: ": "important",
        "my preference is ": "preference",
        "i prefer ": "preference",
        "my goal is ": "goal",
        "my routine is ": "routine",
    }
    def __init__(self, memory: PersonalMemory): self.memory=memory
    def extract(self, text: str):
        normalized=text.strip()
        lowered=normalized.lower()
        for prefix, kind in self.DURABLE_PREFIXES.items():
            if lowered.startswith(prefix):
                value=normalized[len(prefix):].strip()
                if value: return self.memory.remember(value, kind=kind, source="explicit_user")
        return None
