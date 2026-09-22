from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable
import time


@dataclass
class EnvironmentObservation:
    timestamp: float
    snapshot: dict[str, Any]
    changes: list[dict[str, Any]] = field(default_factory=list)


class EnvironmentObserver:
    """Collects bounded before/after environment state and computes changes."""

    def __init__(self, collector: Callable[[], Any], max_changes: int = 100):
        self.collector = collector
        self.max_changes = max(1, max_changes)

    def capture(self) -> EnvironmentObservation:
        snapshot = self._normalize(self.collector())
        return EnvironmentObservation(time.time(), snapshot)

    def compare(self, before: EnvironmentObservation, after: EnvironmentObservation) -> EnvironmentObservation:
        changes = self._diff(before.snapshot, after.snapshot)
        after.changes = changes[:self.max_changes]
        return after

    def observe_change(self, before: EnvironmentObservation | None = None) -> EnvironmentObservation:
        after = self.capture()
        if before:
            return self.compare(before, after)
        return after

    @staticmethod
    def _normalize(value: Any) -> dict[str, Any]:
        if hasattr(value, "__dict__"):
            data = dict(value.__dict__)
            for key, item in list(data.items()):
                if isinstance(item, list):
                    data[key] = [dict(x) if hasattr(x, "__dict__") else x for x in item]
            return data
        return value if isinstance(value, dict) else {"value": value}

    @staticmethod
    def _diff(before: dict[str, Any], after: dict[str, Any]) -> list[dict[str, Any]]:
        changes = []
        for key in sorted(set(before) | set(after)):
            if before.get(key) == after.get(key):
                continue
            changes.append({
                "field": key,
                "before": before.get(key),
                "after": after.get(key),
            })
        return changes
