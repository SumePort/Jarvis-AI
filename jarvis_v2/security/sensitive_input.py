"""Hard boundary for user-entered sensitive authentication."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import secrets
import time


class SensitiveInputKind(str, Enum):
    PAYMENT_AMOUNT = "payment_amount"
    PIN = "pin"
    OTP = "otp"
    PASSWORD = "password"
    CVV = "cvv"
    RECOVERY_CODE = "recovery_code"
    SECURITY_ANSWER = "security_answer"


@dataclass(frozen=True)
class SensitiveInputRequest:
    request_id: str
    kind: SensitiveInputKind
    instruction: str
    application: str | None
    expires_at: float


class SensitiveInputGate:
    """Create one-shot handoff requests without ever collecting the secret.

    JARVIS receives only completion/cancellation status. The trusted UI owns
    the actual input field and the secret value never enters model context,
    tool arguments, memory, audit details, or remote workers.
    """

    def __init__(self, ttl_seconds: float = 120.0) -> None:
        self.ttl_seconds = max(15.0, ttl_seconds)
        self._pending: dict[str, SensitiveInputRequest] = {}

    def request(self, kind: SensitiveInputKind, instruction: str,
                application: str | None = None) -> SensitiveInputRequest:
        if not instruction.strip():
            raise ValueError("Sensitive input instruction is required")
        now = time.time()
        request = SensitiveInputRequest(
            "input_" + secrets.token_hex(10), kind, instruction,
            application, now + self.ttl_seconds,
        )
        self._pending[request.request_id] = request
        return request

    def complete(self, request_id: str) -> SensitiveInputRequest:
        request = self._pending.pop(request_id, None)
        if request is None:
            raise PermissionError("Sensitive input request is unknown or already consumed")
        if time.time() > request.expires_at:
            raise PermissionError("Sensitive input request expired")
        return request

    def cancel(self, request_id: str) -> None:
        self._pending.pop(request_id, None)

    def pending(self) -> tuple[SensitiveInputRequest, ...]:
        now = time.time()
        expired = [key for key, value in self._pending.items() if value.expires_at < now]
        for key in expired:
            self._pending.pop(key, None)
        return tuple(self._pending.values())
