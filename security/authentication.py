"""Local password authentication for Jarvis.

The password is stored as a salted PBKDF2 hash, never plaintext.
This is a local session gate, not protection against someone with full
administrator access to the machine or repository.
"""
from __future__ import annotations

import getpass
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path

DEFAULT_PATH = Path("data/security/credential.json")
ITERATIONS = 310_000


class AuthenticationManager:
    def __init__(self, path: str | os.PathLike[str] = DEFAULT_PATH, max_attempts: int = 5):
        self.path = Path(path)
        self.max_attempts = max_attempts

    def _hash(self, password: str, salt: bytes) -> str:
        return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS).hex()

    def is_configured(self) -> bool:
        return self.path.exists()

    def setup(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        while True:
            first = getpass.getpass("Create Jarvis password: ")
            second = getpass.getpass("Confirm password: ")
            if first and hmac.compare_digest(first, second):
                break
            print("Passwords do not match or are empty.")
        salt = secrets.token_bytes(32)
        payload = {"salt": salt.hex(), "hash": self._hash(first, salt), "iterations": ITERATIONS}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass
        print("Jarvis password configured.")

    def authenticate(self) -> bool:
        if not self.is_configured():
            self.setup()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        salt = bytes.fromhex(data["salt"])
        expected = data["hash"]
        attempts = 0
        while attempts < self.max_attempts:
            password = getpass.getpass("Jarvis password: ")
            actual = self._hash(password, salt)
            if hmac.compare_digest(actual, expected):
                return True
            attempts += 1
            print(f"Invalid password. Attempts remaining: {self.max_attempts - attempts}")
            time.sleep(min(attempts, 3))
        return False
