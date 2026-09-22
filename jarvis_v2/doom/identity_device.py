from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jarvis_v2.personal.identity import IdentityStore


@dataclass(frozen=True)
class DeviceIdentityContext:
    identity_id: str
    identity_name: str
    device_id: str


class IdentityDeviceBinder:
    """Resolves the active JARVIS identity for a registered device."""

    def __init__(self, identities: IdentityStore):
        self.identities = identities

    def bind(self, identity_id: str, device_id: str) -> DeviceIdentityContext:
        identity = self.identities.get(identity_id)
        if identity is None or not identity.active:
            raise PermissionError("Unknown or inactive identity")
        if not device_id:
            raise ValueError("device_id is required")
        return DeviceIdentityContext(identity.identity_id, identity.name, device_id)

    def context(self, identity: DeviceIdentityContext) -> dict[str, Any]:
        return {
            "identity_id": identity.identity_id,
            "identity_name": identity.identity_name,
            "device_id": identity.device_id,
        }
