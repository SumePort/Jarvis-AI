"""Operational local JARVIS launcher and capability lifecycle."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from jarvis_v2.runtime.local import build_local_runtime
from jarvis_v2.runtime.startup import StartupStatus
from jarvis_v2.voice.daemon import VoiceDaemon


@dataclass
class LocalJarvisHost:
    runtime: Any
    capabilities: Any
    browser_session: Any = None

    @classmethod
    def create(cls, model_url: str | None = None):
        runtime, capabilities = build_local_runtime(model_url)
        return cls(runtime, capabilities, runtime.services.get("browser_session"))

    def status(self, authenticated: bool = False) -> StartupStatus:
        services = getattr(self.runtime, "services", {})
        return StartupStatus(
            doom_ready=services.get("doom_sessions") is not None,
            runtime_ready=self.runtime is not None,
            voice_ready=services.get("voice_agent") is not None,
            authenticated=authenticated,
        )

    def close(self) -> None:
        if self.browser_session:
            self.browser_session.close()
            self.browser_session = None


def main() -> None:
    host = LocalJarvisHost.create()
    status = host.status()
    print("JARVIS V2")
    print(f"runtime={'ready' if status.runtime_ready else 'offline'}")
    print(f"doom={'ready' if status.doom_ready else 'offline'}")
    print(f"voice={'ready' if status.voice_ready else 'disabled'}")
    if not status.voice_ready and host.runtime.services.get("voice_error"):
        print(f"voice_error={host.runtime.services['voice_error']}")
    if status.voice_ready:
        print("wake=Hey Jarvis")
        print("voice=local Vosk + Piper")
        daemon = VoiceDaemon(host.runtime.services["voice_agent"])
        try:
            daemon.run_forever()
        except KeyboardInterrupt:
            daemon.stop()
        finally:
            host.close()
        return

    print("Set JARVIS_ENABLE_VOICE=1 and configure Vosk/Piper to enable voice.")
    print("Press Ctrl+C to stop.")
    try:
        while True:
            input()
    except (KeyboardInterrupt, EOFError):
        host.close()

if __name__ == "__main__":
    main()
