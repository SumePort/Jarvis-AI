from security.permissions import PermissionEngine
from security.security_policy import PolicyDecision


def test_safe_action_is_allowed():
    assert PermissionEngine().check("open_app").decision == PolicyDecision.ALLOW


def test_destructive_action_requires_confirmation():
    assert PermissionEngine().check("delete_file").decision == PolicyDecision.CONFIRM


def test_unknown_action_is_not_implicitly_allowed():
    assert PermissionEngine().check("unknown_action").decision == PolicyDecision.RESTRICT
