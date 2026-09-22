"""Encrypted PC-local vault for DOOM protected secrets."""
from __future__ import annotations
import base64
import json
import os
import secrets
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class VaultError(RuntimeError):
    pass

class LocalProtectedVault:
    """Store protected DOOM data encrypted on the local PC."""
    def __init__(self, root: Path) -> None:
        self.root = root
        self.key_file = root / "key.dpapi"
        self.data_file = root / "vault.json"

    def initialize(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        if not self.key_file.exists():
            self._write_key(secrets.token_bytes(32))
        if not self.data_file.exists():
            self.data_file.write_text("{}", encoding="utf-8")
        self._harden_permissions()

    def _write_key(self, key: bytes) -> None:
        if os.name == "nt":
            import win32crypt
            protected = win32crypt.CryptProtectData(key, "DOOM protected vault", None, None, None, 0)[1]
            self.key_file.write_bytes(protected)
        else:
            self.key_file.write_bytes(key)

    def _read_key(self) -> bytes:
        if not self.key_file.exists():
            self.initialize()
        blob = self.key_file.read_bytes()
        if os.name == "nt":
            import win32crypt
            return win32crypt.CryptUnprotectData(blob, None, None, None, 0)[1]
        return blob

    def _harden_permissions(self) -> None:
        try:
            os.chmod(self.key_file, 0o600)
            os.chmod(self.data_file, 0o600)
        except OSError:
            pass

    def put(self, name: str, value: str) -> None:
        if not name:
            raise VaultError("Secret name cannot be empty")
        key = self._read_key()
        nonce = secrets.token_bytes(12)
        ciphertext = AESGCM(key).encrypt(nonce, value.encode("utf-8"), name.encode("utf-8"))
        records = json.loads(self.data_file.read_text(encoding="utf-8")) if self.data_file.exists() else {}
        records[name] = {"nonce": base64.b64encode(nonce).decode("ascii"), "ciphertext": base64.b64encode(ciphertext).decode("ascii")}
        self.data_file.write_text(json.dumps(records, indent=2), encoding="utf-8")
        self._harden_permissions()

    def get(self, name: str) -> str:
        records = json.loads(self.data_file.read_text(encoding="utf-8"))
        record = records.get(name)
        if not record:
            raise KeyError(name)
        key = self._read_key()
        nonce = base64.b64decode(record["nonce"])
        ciphertext = base64.b64decode(record["ciphertext"])
        return AESGCM(key).decrypt(nonce, ciphertext, name.encode("utf-8")).decode("utf-8")
