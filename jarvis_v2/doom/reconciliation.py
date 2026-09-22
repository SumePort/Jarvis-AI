from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any
import copy
import time


@dataclass
class StateConflict:
    entity_type: str
    entity_id: str
    local: dict[str, Any]
    remote: dict[str, Any]
    fields: list[str] = field(default_factory=list)


@dataclass
class StateMergeResult:
    entity_type: str
    merged: list[dict[str, Any]] = field(default_factory=list)
    conflicts: list[StateConflict] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)


class PersonalStateReconciler:
    """Deterministic three-way reconciliation for identity-scoped state.

    The reconciler never guesses when both devices changed the same field.
    It uses the common base to identify one-sided changes and emits explicit
    conflicts for true concurrent edits.
    """

    def merge(self, entity_type: str, base: list[Any], local: list[Any], remote: list[Any],
              key: str = "id") -> StateMergeResult:
        def rows(values):
            return {str(getattr(x, key, None) if not isinstance(x, dict) else x.get(key)): self._dict(x) for x in values}
        b, l, r = rows(base), rows(local), rows(remote)
        result = StateMergeResult(entity_type)
        for entity_id in sorted(set(b) | set(l) | set(r)):
            bv, lv, rv = b.get(entity_id), l.get(entity_id), r.get(entity_id)
            if lv == rv:
                if lv is not None: result.merged.append(copy.deepcopy(lv))
                else: result.deleted.append(entity_id)
                continue
            if lv == bv and rv is not None:
                result.merged.append(copy.deepcopy(rv)); continue
            if rv == bv and lv is not None:
                result.merged.append(copy.deepcopy(lv)); continue
            if lv is None or rv is None:
                result.conflicts.append(StateConflict(entity_type, entity_id, lv or {}, rv or {}, ["existence"]))
                continue
            changed = sorted(k for k in set(lv) | set(rv) if lv.get(k) != rv.get(k))
            if not changed:
                result.merged.append(copy.deepcopy(lv))
            else:
                result.conflicts.append(StateConflict(entity_type, entity_id, lv, rv, changed))
        return result

    @staticmethod
    def _dict(value: Any) -> dict[str, Any] | None:
        if value is None:
            return None
        if isinstance(value, dict):
            return dict(value)
        return asdict(value)


@dataclass
class ReconciliationRecord:
    identity_id: str
    entity_type: str
    entity_id: str
    resolution: str
    timestamp: float = field(default_factory=time.time)


class ReconciliationLedger:
    """Append-only record of explicit conflict resolutions."""

    def __init__(self):
        self.records: list[ReconciliationRecord] = []

    def record(self, identity_id: str, entity_type: str, entity_id: str, resolution: str) -> ReconciliationRecord:
        if not identity_id or not entity_id or not resolution:
            raise ValueError("identity_id, entity_id and resolution are required")
        item = ReconciliationRecord(identity_id, entity_type, entity_id, resolution)
        self.records.append(item)
        return item
