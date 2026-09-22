"""Local visual perception boundary."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Any


@dataclass(frozen=True)
class VisualObservation:
    width: int
    height: int
    objects: tuple[dict[str, Any], ...] = ()
    text: tuple[dict[str, Any], ...] = ()
    source: str = "local"


class VisionProvider(Protocol):
    def analyze(self, image: bytes) -> VisualObservation: ...


class VisionService:
    def __init__(self, provider: VisionProvider | None = None) -> None:
        self.provider = provider

    def analyze(self, image: bytes) -> VisualObservation:
        if not self.provider:
            raise RuntimeError("No local vision provider configured")
        return self.provider.analyze(image)
