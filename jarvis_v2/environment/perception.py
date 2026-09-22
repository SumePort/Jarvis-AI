"""Provider-neutral environment perception.

Structured sources are preferred. Vision is an evidence source, not the
canonical representation of the computer environment.
"""
from __future__ import annotations

from typing import Protocol
import time

from jarvis_v2.core.types import EnvironmentSnapshot


class EnvironmentProvider(Protocol):
    def snapshot(self) -> EnvironmentSnapshot: ...


class CompositeEnvironment:
    def __init__(self, providers: list[EnvironmentProvider] | None = None) -> None:
        self.providers = providers or []

    def snapshot(self) -> EnvironmentSnapshot:
        merged = EnvironmentSnapshot(timestamp=time.time())
        for provider in self.providers:
            current = provider.snapshot()
            merged.devices.extend(current.devices)
            merged.applications.extend(current.applications)
            merged.windows.extend(current.windows)
            merged.workspaces.extend(current.workspaces)
            merged.processes.extend(current.processes)
            merged.repositories.extend(current.repositories)
            merged.browser_pages.extend(current.browser_pages)
            merged.filesystem.extend(current.filesystem)
            merged.visual_evidence.extend(current.visual_evidence)
            merged.metadata.update(current.metadata)
        return merged
