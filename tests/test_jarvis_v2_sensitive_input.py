from jarvis_v2.security.sensitive_input import SensitiveInputGate, SensitiveInputKind


def test_sensitive_input_is_one_shot():
    gate = SensitiveInputGate()
    request = gate.request(SensitiveInputKind.PIN, "Enter your UPI PIN in GPay", "GPay")
    completed = gate.complete(request.request_id)
    assert completed.kind == SensitiveInputKind.PIN
    try:
        gate.complete(request.request_id)
        assert False
    except PermissionError:
        assert True


def test_sensitive_input_request_contains_no_secret():
    gate = SensitiveInputGate()
    request = gate.request(SensitiveInputKind.OTP, "Enter the OTP in the trusted app")
    assert not hasattr(request, "value")
