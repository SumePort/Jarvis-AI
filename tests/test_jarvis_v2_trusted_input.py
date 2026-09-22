from jarvis_v2.tools.trusted_input import TrustedInputHandoff


def test_handoff_never_accepts_secret():
    handoff = TrustedInputHandoff()
    result = handoff.request_user_input("pin", "Enter your UPI PIN in GPay", "GPay")
    assert result["status"] == "WAITING_FOR_USER"
    assert "value" not in result
    assert "pin" == result["kind"]


def test_handoff_is_resumable_once():
    handoff = TrustedInputHandoff()
    result = handoff.request_user_input("otp", "Enter the OTP in the trusted app")
    resumed = handoff.resume_after_user_input(result["request_id"])
    assert resumed["status"] == "USER_INPUT_COMPLETED"
    try:
        handoff.resume_after_user_input(result["request_id"])
        assert False
    except PermissionError:
        assert True
