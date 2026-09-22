"""Single-process local JARVIS startup coordinator."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class StartupStatus:
    doom_ready: bool
    runtime_ready: bool
    voice_ready: bool
    authenticated: bool


class JarvisStartup:
    def __init__(self, doom_check, runtime_check, voice_check) -> None:
        self.doom_check = doom_check
        self.runtime_check = runtime_check
        self.voice_check = voice_check

    def status(self, authenticated: bool = False) -> StartupStatus:
        return StartupStatus(
            bool(self.doom_check()),
            bool(self.runtime_check()),
            bool(self.voice_check()),
            authenticated,
        )
