from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import hmac
import json
import os


@dataclass
class PersonalIdentity:
    identity_id: str
    name: str
    credential_salt: str | None = None
    credential_hash: str | None = None
    active: bool = True

    @property
    def has_credential(self) -> bool:
        return bool(self.credential_hash)


class IdentityStore:
    """Local identity registry with salted PBKDF2 credentials."""

    def __init__(self, path: str | Path = "data/jarvis_v2/identities.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict[str, PersonalIdentity]:
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return {k: PersonalIdentity(**v) for k, v in raw.items()}
        except (OSError, json.JSONDecodeError, TypeError):
            return {}

    def _save(self, identities: dict[str, PersonalIdentity]) -> None:
        self.path.write_text(
            json.dumps({k: asdict(v) for k, v in identities.items()}, indent=2),
            encoding="utf-8",
        )

    def register(self, identity_id: str, name: str, credential: str | None = None) -> PersonalIdentity:
        identity_id = identity_id.strip()
        name = name.strip()
        if not identity_id or not name:
            raise ValueError("identity_id and name are required")
        identities = self._load()
        if identity_id in identities:
            raise ValueError(f"Identity already exists: {identity_id}")

        salt = os.urandom(16)
        digest = None
        salt_hex = None
        if credential is not None:
            salt_hex = salt.hex()
            digest = hashlib.pbkdf2_hmac(
                "sha256", credential.encode("utf-8"), salt, 310_000
            ).hex()

        identity = PersonalIdentity(identity_id, name, salt_hex, digest)
        identities[identity_id] = identity
        self._save(identities)
        return identity

    def ensure_default(self) -> PersonalIdentity:
        identities = self._load()
        if "default" not in identities:
            identities["default"] = PersonalIdentity("default", "User")
            self._save(identities)
        return identities["default"]

    def get(self, identity_id: str) -> PersonalIdentity | None:
        return self._load().get(identity_id)

    def authenticate(self, identity_id: str, credential: str | None = None) -> PersonalIdentity:
        identity = self.get(identity_id)
        if identity is None or not identity.active:
            raise PermissionError("Unknown or inactive identity")
        if identity.credential_hash:
            if credential is None or not identity.credential_salt:
                raise PermissionError("Credential required")
            digest = hashlib.pbkdf2_hmac(
                "sha256",
                credential.encode("utf-8"),
                bytes.fromhex(identity.credential_salt),
                310_000,
            ).hex()
            if not hmac.compare_digest(digest, identity.credential_hash):
                raise PermissionError("Invalid credential")
        return identity

    def all(self) -> list[PersonalIdentity]:
        return list(self._load().values())


class IdentityDataPaths:
    """Deterministic per-identity paths for personal data isolation."""

    def __init__(self, identity_id: str, root: str | Path = "data/jarvis_v2/users"):
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in identity_id)
        if not safe:
            raise ValueError("Invalid identity_id")
        self.root = Path(root) / safe
        self.root.mkdir(parents=True, exist_ok=True)

    @property
    def profile(self) -> Path:
        return self.root / "profile.json"

    @property
    def tasks(self) -> Path:
        return self.root / "tasks.json"

    @property
    def memory(self) -> Path:
        return self.root / "memory.jsonl"
