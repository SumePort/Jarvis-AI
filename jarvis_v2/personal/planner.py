from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import re

from jarvis_v2.personal.tasks import PersonalTask, TaskStore

@dataclass
class PersonalPlan:
    intent: str
    tasks: list[PersonalTask] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> dict:
        return {"intent":self.intent,"tasks":[t.__dict__ for t in self.tasks],"explanation":self.explanation}

class PersonalPlanner:
    """Deterministic first-stage planner for common personal-assistant requests."""
    def __init__(self, tasks: TaskStore | None = None): self.tasks=tasks or TaskStore()
    def plan(self, request: str) -> PersonalPlan:
        text=request.strip(); lower=text.lower()
        if lower.startswith(("remind me to ","remember to ","add a task to ","add task ")):
            prefix=next(p for p in ("remind me to ","remember to ","add a task to ","add task ") if lower.startswith(p))
            title=text[len(prefix):].strip()
            due=None
            if " tomorrow" in lower:
                due=(datetime.now(timezone.utc)+timedelta(days=1)).date().isoformat()
                title=re.sub(r"\s+tomorrow\b","",title,flags=re.I).strip()
            task=self.tasks.add(title,due_at=due)
            return PersonalPlan("create_task",[task],"Created a personal task from the explicit request.")
        if lower in {"show my tasks","what are my tasks","show my pending tasks"}:
            return PersonalPlan("list_tasks",self.tasks.pending(),"Listed pending personal tasks.")
        return PersonalPlan("conversation",[],"No deterministic personal action matched; defer to the conversational brain.")
