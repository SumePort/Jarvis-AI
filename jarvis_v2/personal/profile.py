from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import json

@dataclass
class PersonalProfile:
    name: str | None = None
    preferences: dict[str, str] = field(default_factory=dict)
    routines: dict[str, str] = field(default_factory=dict)
    goals: list[str] = field(default_factory=list)
    important_notes: list[str] = field(default_factory=list)

class PersonalProfileStore:
    def __init__(self, path: str | Path = "data/jarvis_v2/personal_profile.json"):
        self.path=Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
    def load(self) -> PersonalProfile:
        if not self.path.exists(): return PersonalProfile()
        try: return PersonalProfile(**json.loads(self.path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, TypeError): return PersonalProfile()
    def save(self, profile: PersonalProfile) -> PersonalProfile:
        self.path.write_text(json.dumps(asdict(profile), indent=2, ensure_ascii=False), encoding="utf-8")
        return profile
    def set_preference(self, key: str, value: str) -> PersonalProfile:
        p=self.load(); p.preferences[key]=value; return self.save(p)
    def add_goal(self, goal: str) -> PersonalProfile:
        p=self.load();
        if goal not in p.goals: p.goals.append(goal)
        return self.save(p)
    def add_note(self, note: str) -> PersonalProfile:
        p=self.load(); p.important_notes.append(note); p.important_notes=p.important_notes[-100:]; return self.save(p)
