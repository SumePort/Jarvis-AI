"""Device identity and bearer-token registry for the DOOM control plane."""
from __future__ import annotations
import hashlib
import hmac
import secrets
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class DeviceIdentity:
    device_id: str
    name: str
    token_hash: str
    enabled: bool = True

class IdentityRegistry:
    def __init__(self) -> None:
        self._devices: dict[str, DeviceIdentity] = {}

    @staticmethod
    def _hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def enroll(self, name: str) -> tuple[DeviceIdentity, str]:
        device_id = f"dev_{secrets.token_hex(12)}"
        token = secrets.token_urlsafe(32)
        identity = DeviceIdentity(device_id, name, self._hash(token))
        self._devices[device_id] = identity
        return identity, token

    def authenticate(self, device_id: str, token: str) -> bool:
        identity = self._devices.get(device_id)
        if not identity or not identity.enabled:
            return False
        return hmac.compare_digest(identity.token_hash, self._hash(token))

    def revoke(self, device_id: str) -> None:
        identity = self._devices.get(device_id)
        if identity:
            self._devices[device_id] = DeviceIdentity(identity.device_id, identity.name, identity.token_hash, False)

    def list_devices(self) -> list[DeviceIdentity]:
        return list(self._devices.values())
