"""High-level environment collector for JARVIS V2."""
from __future__ import annotations

from jarvis_v2.core.types import EnvironmentSnapshot
from .filesystem import FilesystemEnvironmentProvider
from .git import GitEnvironmentProvider
from .perception import CompositeEnvironment
from .windows import TerminalEnvironmentProvider, WindowsEnvironmentProvider


class JarvisEnvironment:
    """Collect a structured view of the current environment.

    This collector intentionally does not use screenshots. Visual perception can
    be added later as an additional provider when structured information cannot
    answer a question.
    """

    def __init__(self, roots: list[str] | None = None) -> None:
        roots = roots or []
        self._composite = CompositeEnvironment([
            WindowsEnvironmentProvider(),
            TerminalEnvironmentProvider(),
            FilesystemEnvironmentProvider(roots or None),
            GitEnvironmentProvider(roots or None),
        ])

    def snapshot(self) -> EnvironmentSnapshot:
        return self._composite.snapshot()
