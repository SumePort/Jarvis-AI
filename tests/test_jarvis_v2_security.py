from jarvis_v2.core.types import ActionRisk, DataClass
from jarvis_v2.security import SecurityPolicy, IdentitySession

def test_security_requires_identity():
    d=SecurityPolicy().authorize(None, DataClass.NORMAL, ActionRisk.ALLOW)
    assert not d.allowed

def test_confirm_action_requires_confirmation():
    d=SecurityPolicy().authorize("u", DataClass.NORMAL, ActionRisk.CONFIRM, authenticated=True)
    assert d.requires_confirmation and not d.allowed

def test_authenticated_session_identity():
    s=IdentitySession("s1"); s.authenticate("user", "device")
    assert s.identity == "user@device"
