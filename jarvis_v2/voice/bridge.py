"""Bridge voice turns into the unified perception pipeline."""
from __future__ import annotations
from jarvis_v2.perception import PerceptionPipeline, PerceptionResult
from .runtime import VoiceTurn

class VoicePerceptionBridge:
    def __init__(self, perception: PerceptionPipeline | None = None) -> None:
        self.perception=perception or PerceptionPipeline()

    def to_perception(self, turn: VoiceTurn) -> PerceptionResult:
        result=self.perception.text(turn.transcript)
        result.percepts[0].source="voice"
        result.percepts[0].metadata["wake_detected"]=turn.wake_detected
        return result
