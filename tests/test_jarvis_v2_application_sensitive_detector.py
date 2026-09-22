from jarvis_v2.tools.application_sensitive_detector import ApplicationSensitiveDetector
from jarvis_v2.tools.sensitive_detector import SensitiveStep


def test_upi_pin_is_sensitive():
    detector = ApplicationSensitiveDetector()
    assert detector.detect("Google Pay", "Enter UPI PIN to authorize payment") == SensitiveStep.PIN


def test_trading_final_authorization_is_sensitive():
    detector = ApplicationSensitiveDetector()
    assert detector.detect("broker", "Confirm order / final authorization") == SensitiveStep.FINAL_AUTHORIZATION
