"""One-shot broker for protected secrets kept inside the local trust boundary.

The broker never exposes secret values to callers as return data. A secret is
resolved from the local vault only for the duration of a caller-provided
trusted operation, then discarded.
"""
from __future__ import annotations

from dataclasses import dataclass
import secrets
import time
from typing import Callable, TypeVar

from doom.vault import LocalProtectedVault

T = TypeVar("T")


@dataclass(frozen=True)
class ProtectedSecretRequest:
    request_id: str
    secret_name: str
    purpose: str
    user_id: str
    device_id: str
    expires_at: float


class ProtectedSecretBroker:
    """Authorize and execute one protected-secret operation locally."""

    def __init__(self, vault: LocalProtectedVault, ttl_seconds: float = 120.0) -> None:
        self.vault = vault
        self.ttl_seconds = max(15.0, ttl_seconds)
        self._pending: dict[str, ProtectedSecretRequest] = {}

    def authorize(
        self,
        secret_name: str,
        purpose: str,
        user_id: str,
        device_id: str,
        confirmation: str,
    ) -> ProtectedSecretRequest:
        if not secret_name.strip():
            raise ValueError("Secret name is required")
        if not purpose.strip():
            raise ValueError("Purpose is required")
        if not user_id or not device_id:
            raise PermissionError("Authenticated user and device are required")
        if confirmation.strip().lower() != "confirmed":
            raise PermissionError("Explicit confirmation required")

        request = ProtectedSecretRequest(
            request_id="secret_" + secrets.token_hex(10),
            secret_name=secret_name,
            purpose=purpose,
            user_id=user_id,
            device_id=device_id,
            expires_at=time.time() + self.ttl_seconds,
        )
        self._pending[request.request_id] = request
        return request

    def use_once(
        self,
        request: ProtectedSecretRequest,
        operation: Callable[[str], T],
    ) -> T:
        pending = self._pending.pop(request.request_id, None)
        if pending is None:
            raise PermissionError("Protected secret request is unknown or already consumed")
        if time.time() > pending.expires_at:
            raise PermissionError("Protected secret request expired")

        secret = self.vault.get(pending.secret_name)
        try:
            return operation(secret)
        finally:
            secret = None
