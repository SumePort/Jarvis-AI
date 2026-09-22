"""Provider-neutral object storage contracts and local implementation."""
from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Protocol

class ObjectStore(Protocol):
    def has(self, digest: str) -> bool: ...
    def put(self, digest: str, source: Path) -> None: ...
    def get(self, digest: str, destination: Path) -> None: ...

def _validate_digest(digest: str) -> None:
    if len(digest) != 64: raise ValueError("Invalid object digest.")
    int(digest, 16)

class LocalObjectStore:
    def __init__(self, root: Path) -> None:
        self.root = root
    def _object_path(self, digest: str) -> Path:
        _validate_digest(digest)
        return self.root / digest[:2] / digest[2:4] / digest
    def has(self, digest: str) -> bool:
        return self._object_path(digest).is_file()
    def put(self, digest: str, source: Path) -> None:
        target = self._object_path(digest)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists(): return
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        if actual != digest: raise ValueError("Object content does not match its SHA-256 digest.")
        target.write_bytes(source.read_bytes())
    def get(self, digest: str, destination: Path) -> None:
        source = self._object_path(digest)
        if not source.is_file(): raise FileNotFoundError(digest)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
