"""Identity-bound JARVIS session state."""
from __future__ import annotations
from dataclasses import dataclass, field
import time

@dataclass
class IdentitySession:
    session_id: str
    user_id: str | None = None
    device_id: str | None = None
    authenticated: bool = False
    created_at: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)

    def authenticate(self, user_id: str, device_id: str) -> None:
        self.user_id=user_id
        self.device_id=device_id
        self.authenticated=True

    def revoke(self) -> None:
        self.authenticated=False

    @property
    def identity(self) -> str | None:
        if self.user_id and self.device_id:
            return f"{self.user_id}@{self.device_id}"
        return self.user_id or self.device_id
