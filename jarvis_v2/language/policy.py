"""Multilingual JARVIS language layer for English, Hindi and Hinglish."""
from __future__ import annotations
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class LanguageResult:
    language: str
    confidence: float


class LanguageDetector:
    HINDI_SCRIPT = re.compile(r"[\u0900-\u097F]")
    HINGLISH = {
        "kya", "kaise", "kyun", "kyon", "mujhe", "aap", "tum", "hai", "hain",
        "kar", "karo", "batao", "bata", "chahiye", "mera", "meri", "yeh", "woh",
        "nahi", "nahin", "accha", "acha", "abhi", "kal", "aaj", "dekho", "banao",
    }

    def detect(self, text: str) -> LanguageResult:
        if self.HINDI_SCRIPT.search(text):
            return LanguageResult("hi", 0.99)
        words = {w.lower() for w in re.findall(r"[a-zA-Z]+", text)}
        score = len(words & self.HINGLISH) / max(1, len(words))
        if score >= 0.15:
            return LanguageResult("hinglish", min(0.98, 0.55 + score))
        return LanguageResult("en", 0.85)


class LanguagePolicy:
    """Selects response language without translating technical identifiers."""

    SUPPORTED = {"en", "hi", "hinglish"}

    def __init__(self, default: str = "en"):
        if default not in self.SUPPORTED:
            raise ValueError("Unsupported default language")
        self.default = default

    def choose(self, text: str, requested: str | None = None) -> LanguageResult:
        if requested in self.SUPPORTED:
            return LanguageResult(requested, 1.0)
        return LanguageDetector().detect(text)

    def instruction(self, result: LanguageResult) -> str:
        return {
            "en": "Respond in clear English.",
            "hi": "Respond in natural Hindi. Keep technical names, code, commands, and URLs unchanged.",
            "hinglish": "Respond in natural Roman-script Hinglish. Keep technical names, code, commands, and URLs unchanged.",
        }[result.language]
