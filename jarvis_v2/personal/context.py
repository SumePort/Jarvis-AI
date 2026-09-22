from __future__ import annotations

from jarvis_v2.memory.store import MemoryStore
from jarvis_v2.personal.profile import PersonalProfileStore
from jarvis_v2.personal.tasks import TaskStore

class PersonalContext:
    """Build bounded personal context for JARVIS reasoning."""
    def __init__(self, memory: MemoryStore | None = None, profile: PersonalProfileStore | None = None, tasks: TaskStore | None = None):
        self.memory=memory or MemoryStore(); self.profile=profile or PersonalProfileStore(); self.tasks=tasks or TaskStore()
    def build(self, request: str) -> dict:
        p=self.profile.load()
        return {
            "profile": {"name":p.name,"preferences":p.preferences,"routines":p.routines,"goals":p.goals,"important_notes":p.important_notes[-20:]},
            "relevant_memory":[m.__dict__ for m in self.memory.search(request, limit=8)],
            "pending_tasks":[t.__dict__ for t in self.tasks.pending()[:20]],
        }
