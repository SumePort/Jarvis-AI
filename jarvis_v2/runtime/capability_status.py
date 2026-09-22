"""Report which JARVIS capabilities are configured vs unavailable."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilityStatus:
    name: str
    configured: bool
    detail: str


class CapabilityStatusReporter:
    def report(self, **providers) -> tuple[CapabilityStatus, ...]:
        return tuple(
            CapabilityStatus(name, provider is not None,
                             "configured" if provider is not None else "provider not configured")
            for name, provider in providers.items()
        )
