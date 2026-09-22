from pathlib import Path
from jarvis_v2.security.policy import SecurityPolicy
from jarvis_v2.security.protected_broker import ProtectedSecretBroker
from jarvis_v2.core.types import ActionRisk, DataClass
from doom.vault import LocalProtectedVault


def test_protected_data_requires_confirmation():
    policy = SecurityPolicy()
    denied = policy.authorize("user", DataClass.PROTECTED, ActionRisk.ALLOW, True, False)
    assert not denied.allowed
    assert denied.requires_confirmation

    allowed = policy.authorize("user", DataClass.PROTECTED, ActionRisk.ALLOW, True, True)
    assert allowed.allowed


def test_secret_never_returns_from_broker(tmp_path: Path):
    vault = LocalProtectedVault(tmp_path)
    vault.initialize()
    vault.put("upi_pin", "1234")
    broker = ProtectedSecretBroker(vault)
    request = broker.authorize("upi_pin", "local payment confirmation", "user", "pc", "confirmed")
    seen = []
    result = broker.use_once(request, lambda secret: seen.append(secret) or "ok")
    assert result == "ok"
    assert seen == ["1234"]
