from jarvis_v2.security.transaction_firewall import TransactionFirewall


def test_approval_is_bound_to_exact_transaction(tmp_path):
    firewall = TransactionFirewall(approval_ttl=30)
    intent = firewall.prepare("user", "pc", "payment", "100", "merchant", "Pay merchant 100")
    approval = firewall.approve(intent, "user", "pc", "confirm payment")
    assert firewall.execute(intent, approval, lambda: "ok") == "ok"


def test_changed_transaction_cannot_use_old_approval(tmp_path):
    firewall = TransactionFirewall(approval_ttl=30)
    intent = firewall.prepare("user", "pc", "payment", "100", "merchant", "Pay merchant 100")
    approval = firewall.approve(intent, "user", "pc", "confirm payment")
    changed = type(intent)(
        intent.transaction_id, intent.identity_id, intent.device_id,
        intent.operation, "1000", intent.destination, intent.summary,
        intent.intent_hash, intent.expires_at,
    )
    try:
        firewall.execute(changed, approval, lambda: "bad")
        assert False
    except PermissionError:
        assert True
