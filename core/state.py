from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class JarvisState:
    authenticated: bool=False
    online: bool=False
    current_project: str|None=None
    history: list[dict]=field(default_factory=list)
