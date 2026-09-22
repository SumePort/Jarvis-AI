import pytest
from jarvis_v2.doom.reconciliation import PersonalStateReconciler, ReconciliationLedger


def test_one_sided_change_is_merged():
    base = [{"id": "1", "title": "A", "status": "pending"}]
    local = [{"id": "1", "title": "A", "status": "completed"}]
    remote = base
    result = PersonalStateReconciler().merge("task", base, local, remote)
    assert result.merged[0]["status"] == "completed"
    assert not result.conflicts


def test_concurrent_field_changes_conflict():
    base = [{"id": "1", "title": "A", "status": "pending"}]
    local = [{"id": "1", "title": "Local", "status": "pending"}]
    remote = [{"id": "1", "title": "Remote", "status": "pending"}]
    result = PersonalStateReconciler().merge("task", base, local, remote)
    assert result.conflicts[0].fields == ["title"]


def test_conflict_resolution_is_explicit():
    ledger = ReconciliationLedger()
    record = ledger.record("shubham", "task", "1", "keep-local")
    assert record.resolution == "keep-local"
