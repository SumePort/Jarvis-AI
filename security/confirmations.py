"""Interactive confirmation gate for actions classified as CONFIRM."""
from __future__ import annotations

def confirm(action: str, description: str) -> bool:
    answer = input(f"CONFIRM required [{action}]: {description}\nProceed? [y/N]: ").strip().lower()
    return answer in {"y", "yes"}
