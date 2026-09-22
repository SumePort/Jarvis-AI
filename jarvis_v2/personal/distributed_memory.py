from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
import hashlib
import json
import time
import uuid
from typing import Any

from jarvis_v2.memory.store import MemoryRecord


@dataclass
class MemoryVersion:
    version_id: str
    memory_id: str
    identity_id: str
    device_id: str
    operation: str
    record: dict[str, Any] | None
    timestamp: float = field(default_factory=time.time)
    base_version: str | None = None


@dataclass
class MemoryConflict:
    memory_id: str
    local: dict[str, Any]
    remote: dict[str, Any]
    fields: list[str]


class DistributedMemoryStore:
    """Identity-scoped memory replication with append-only versions.

    Memory contents remain identity-scoped. No protected credential material is
    replicated by this layer. Conflicting edits are surfaced, never guessed.
    """

    def __init__(self, identity_id: str, device_id: str, path: str | Path):
        if not identity_id or not device_id:
            raise ValueError("identity_id and device_id are required")
        self.identity_id = identity_id
        self.device_id = device_id
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: MemoryRecord, operation: str = "upsert", base_version: str | None = None) -> MemoryVersion:
        payload = asdict(record)
        payload["metadata"] = dict(payload.get("metadata", {}))
        payload["metadata"].setdefault("identity_id", self.identity_id)
        version = MemoryVersion(str(uuid.uuid4()), record.id, self.identity_id, self.device_id,
                                operation, payload, base_version=base_version)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(version), ensure_ascii=False) + "\n")
        return version

    def versions(self, memory_id: str | None = None) -> list[MemoryVersion]:
        if not self.path.exists():
            return []
        result = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try:
                item = MemoryVersion(**json.loads(line))
                if item.identity_id == self.identity_id and (memory_id is None or item.memory_id == memory_id):
                    result.append(item)
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
        return result

    def export(self, since: float = 0.0) -> list[dict[str, Any]]:
        return [asdict(v) for v in self.versions() if v.timestamp > since]

    def import_versions(self, versions: list[dict[str, Any]]) -> int:
        existing = {v.version_id for v in self.versions()}
        added = 0
        with self.path.open("a", encoding="utf-8") as handle:
            for raw in versions:
                if raw.get("identity_id") != self.identity_id or raw.get("version_id") in existing:
                    continue
                handle.write(json.dumps(raw, ensure_ascii=False) + "\n")
                existing.add(raw["version_id"])
                added += 1
        return added

    def latest(self, memory_id: str) -> MemoryVersion | None:
        items = self.versions(memory_id)
        return max(items, key=lambda x: x.timestamp) if items else None


class MemoryReconciler:
    def reconcile(self, local: MemoryVersion | None, remote: MemoryVersion | None) -> tuple[MemoryVersion | None, MemoryConflict | None]:
        if local is None: return remote, None
        if remote is None: return local, None
        if local.version_id == remote.version_id: return local, None
        if local.record == remote.record:
            return max((local, remote), key=lambda x: x.timestamp), None
        left = local.record or {}
        right = remote.record or {}
        fields = sorted(k for k in set(left) | set(right) if left.get(k) != right.get(k))
        return None, MemoryConflict(local.memory_id, left, right, fields)
