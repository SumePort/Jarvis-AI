from __future__ import annotations
from .wake_word import WakeWord

class VoiceLoop:
    def __init__(self):
        self.wake=WakeWord()
    def process_text(self,text: str):
        return text.split(self.wake.phrase,1)[1].strip() if self.wake.matches(text) else None
