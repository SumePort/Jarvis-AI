"""A safe task handoff contract from JARVIS to DOOM."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from jarvis_v2.core.types import DataClass
from .router import RoutedTask

@dataclass
class DoomTaskEnvelope:
    routed: RoutedTask
    payload: dict[str, Any]

    def validate(self) -> None:
        if self.routed.data_class == DataClass.PROTECTED and not self.routed.authorized_remote and self.routed.worker_type != "local":
            raise PermissionError("Protected data cannot be handed to a remote DOOM worker")
