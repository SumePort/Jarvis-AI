from pathlib import Path
import pytest

from jarvis_v2.doom.identity import DoomIdentityBridge
from jarvis_v2.doom.identity_device import IdentityDeviceBinder
from jarvis_v2.personal.identity import IdentityStore


def test_doom_identity_session_is_device_bound(tmp_path: Path):
    bridge = DoomIdentityBridge(tmp_path / "sessions.json")
    session, token = bridge.issue("shubham", "dev-pc", ttl_seconds=600)

    assert bridge.authenticate(token, identity_id="shubham", device_id="dev-pc").session_id == session.session_id
    with pytest.raises(PermissionError):
        bridge.authenticate(token, identity_id="father", device_id="dev-pc")
    with pytest.raises(PermissionError):
        bridge.authenticate(token, identity_id="shubham", device_id="dev-phone")


def test_device_binder_resolves_identity(tmp_path: Path):
    store = IdentityStore(tmp_path / "identities.json")
    store.register("shubham", "Shubham", "1111")
    bound = IdentityDeviceBinder(store).bind("shubham", "dev-pc")
    assert bound.identity_name == "Shubham"
    assert bound.device_id == "dev-pc"
