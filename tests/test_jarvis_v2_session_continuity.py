from pathlib import Path
import pytest

from jarvis_v2.doom.session_continuity import SessionContinuityStore, SessionContinuity


def test_session_snapshot_round_trip_and_identity_binding(tmp_path: Path):
    store = SessionContinuityStore(tmp_path)
    snap = store.create("shubham", "sumeport", [{"request": "hi"}], [{"role": "user", "text": "hi"}], "dev-pc")
    loaded = store.load("shubham", snap.session_id)
    assert loaded.identity_id == "shubham"
    assert loaded.device_id == "dev-pc"
    with pytest.raises(PermissionError):
        store.load("father", snap.session_id)


def test_snapshot_integrity_detects_tampering(tmp_path: Path):
    store = SessionContinuityStore(tmp_path)
    snap = store.create("shubham", None, [], [{"role": "user", "text": "hello"}])
    path = tmp_path / "shubham" / f"{snap.session_id}.json"
    raw = path.read_text()
    path.write_text(raw.replace("hello", "tampered"))
    with pytest.raises(PermissionError):
        store.load("shubham", snap.session_id)
