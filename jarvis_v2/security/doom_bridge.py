"""Security bridge for DOOM protected-data boundaries."""
from __future__ import annotations
from jarvis_v2.core.types import DataClass
from jarvis_v2.doom import DoomResourceRouter
from .session import IdentitySession

class DoomSecurityBridge:
    def __init__(self, router: DoomResourceRouter) -> None:
        self.router=router

    def route(self, session: IdentitySession, task: str, capability: str,
              data_class: DataClass = DataClass.NORMAL, remote_authorized: bool = False):
        if not session.authenticated:
            raise PermissionError("JARVIS session is not authenticated")
        return self.router.route(task, capability, data_class, explicitly_authorized=remote_authorized)
