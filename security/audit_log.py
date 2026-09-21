"""Append-only local audit log for Jarvis actions."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

class AuditLog:
    def __init__(self, path: str = "data/security/audit.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, action: str, status: str, detail: str = "") -> None:
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "status": status,
            "detail": detail,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
