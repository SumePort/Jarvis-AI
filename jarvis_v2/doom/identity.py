from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import hmac
import json
import os
import time
import uuid


@dataclass
class DoomIdentitySession:
    session_id: str
    identity_id: str
    device_id: str
    issued_at: float
    expires_at: float
    token_hash: str


class DoomIdentityBridge:
    """Binds an authenticated JARVIS identity to a DOOM device session.

    The raw session token is returned only at creation time. Only its hash is
    persisted, allowing multiple devices to represent the same user identity
    without sharing personal data directly between clients.
    """

    def __init__(self, path: str | Path = "data/jarvis_v2/doom_identity_sessions.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> list[DoomIdentitySession]:
        if not self.path.exists():
            return []
        try:
            return [DoomIdentitySession(**x) for x in json.loads(self.path.read_text(encoding="utf-8"))]
        except (OSError, json.JSONDecodeError, TypeError):
            return []

    def _save(self, sessions: list[DoomIdentitySession]) -> None:
        self.path.write_text(json.dumps([asdict(s) for s in sessions], indent=2), encoding="utf-8")

    def issue(self, identity_id: str, device_id: str, ttl_seconds: int = 3600) -> tuple[DoomIdentitySession, str]:
        if not identity_id or not device_id:
            raise ValueError("identity_id and device_id are required")
        raw = uuid.uuid4().hex + os.urandom(16).hex()
        now = time.time()
        session = DoomIdentitySession(
            session_id=str(uuid.uuid4()),
            identity_id=identity_id,
            device_id=device_id,
            issued_at=now,
            expires_at=now + max(60, ttl_seconds),
            token_hash=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        )
        sessions = [s for s in self._load() if s.expires_at > now]
        sessions.append(session)
        self._save(sessions)
        return session, raw

    def authenticate(self, token: str, identity_id: str | None = None, device_id: str | None = None) -> DoomIdentitySession:
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        now = time.time()
        for session in self._load():
            if session.expires_at <= now:
                continue
            if identity_id and session.identity_id != identity_id:
                continue
            if device_id and session.device_id != device_id:
                continue
            if hmac.compare_digest(digest, session.token_hash):
                return session
        raise PermissionError("Invalid or expired DOOM identity session")
