"""SQLite-backed local memory store."""
from __future__ import annotations
import json, sqlite3
from datetime import datetime, timezone
from pathlib import Path

class MemoryStore:
    def __init__(self, path: str = "data/jarvis.db"):
        p=Path(path); p.parent.mkdir(parents=True, exist_ok=True)
        self.conn=sqlite3.connect(p)
        self.conn.execute("CREATE TABLE IF NOT EXISTS conversations (id INTEGER PRIMARY KEY, ts TEXT, role TEXT, content TEXT)")
        self.conn.execute("CREATE TABLE IF NOT EXISTS project_notes (project TEXT PRIMARY KEY, snapshot TEXT, updated_at TEXT)")
        self.conn.commit()
    def add_message(self, role: str, content: str):
        self.conn.execute("INSERT INTO conversations(ts,role,content) VALUES(?,?,?)",
                          (datetime.now(timezone.utc).isoformat(),role,content))
        self.conn.commit()
    def recent(self, limit: int=20):
        rows=self.conn.execute("SELECT role,content,ts FROM conversations ORDER BY id DESC LIMIT ?",(limit,)).fetchall()
        return [{"role":r,"content":c,"timestamp":t} for r,c,t in reversed(rows)]
    def save_project(self, project: str, snapshot: dict):
        self.conn.execute("INSERT OR REPLACE INTO project_notes(project,snapshot,updated_at) VALUES(?,?,?)",
                          (project,json.dumps(snapshot,ensure_ascii=False),datetime.now(timezone.utc).isoformat()))
        self.conn.commit()
    def project(self, project: str):
        row=self.conn.execute("SELECT snapshot FROM project_notes WHERE project=?",(project,)).fetchone()
        return json.loads(row[0]) if row else None
