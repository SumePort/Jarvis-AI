from jarvis_v2.doom.session_bridge import DoomSessionBridge
from jarvis_v2.security.session import IdentitySession

def test_doom_session_binds_identity_and_device():
    identity=IdentitySession("s"); identity.authenticate("u","d")
    bridge=DoomSessionBridge(); s=bridge.bind(identity)
    assert bridge.validate(s.session_id,"u","d")
    assert not bridge.validate(s.session_id,"other","d")
