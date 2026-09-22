"""High-assurance broker for using protected secrets without exposing them to JARVIS."""
from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Callable

from doom.vault import LocalProtectedVault


@dataclass(frozen=True)
class SecretUseRequest:
    secret_name: str
    purpose: str
    identity_id: str
    device_id: str
    confirmation_token: str
    expires_at: float


class ProtectedSecretBroker:
    """Mediates one-shot secret use.

    The secret value never enters model context, observations, audit payloads,
    tool arguments, or remote DOOM workers. A trusted local adapter receives it
    only at the final operation boundary.
    """

    def __init__(self, vault: LocalProtectedVault, confirmation_ttl: float = 60.0):
        self.vault = vault
        self.confirmation_ttl = max(5.0, confirmation_ttl)

    def authorize(self, secret_name: str, purpose: str, identity_id: str,
                  device_id: str, confirmation_token: str) -> SecretUseRequest:
        if not all(x and x.strip() for x in (secret_name, purpose, identity_id, device_id, confirmation_token)):
            raise PermissionError("Complete protected-secret authorization is required")
        return SecretUseRequest(
            secret_name=secret_name,
            purpose=purpose,
            identity_id=identity_id,
            device_id=device_id,
            confirmation_token=confirmation_token,
            expires_at=time.time() + self.confirmation_ttl,
        )

    def use_once(self, request: SecretUseRequest,
                 trusted_local_operation: Callable[[str], object]) -> object:
        if time.time() > request.expires_at:
            raise PermissionError("Protected-secret authorization expired")
        secret = self.vault.get(request.secret_name)
        try:
            return trusted_local_operation(secret)
        finally:
            # Do not retain or return the secret from this broker.
            secret = None
