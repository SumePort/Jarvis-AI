"""Original JARVIS male cinematic voice profile."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class VoiceProfile:
    name: str
    language: str
    gender: str
    age_style: str
    accent: str
    timbre: str
    pacing: str
    delivery: str
    emotional_range: tuple[str, ...]

JARVIS_MALE_PROFILE = VoiceProfile(
    name="jarvis-male-cinematic", language="en", gender="male",
    age_style="mature adult",
    accent="neutral British-inspired, not an actor imitation",
    timbre="warm, low-mid baritone, clear and controlled",
    pacing="measured conversational pace with short natural pauses",
    delivery="calm, precise, intelligent, lightly dry, reassuring",
    emotional_range=("calm", "focused", "warm", "concerned", "amused", "urgent"),
)
