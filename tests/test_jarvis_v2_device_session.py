from jarvis_v2.devices.session_manager import DeviceSessionManager

def test_device_session_is_identity_bound():
    m=DeviceSessionManager(); s=m.create("u","d")
    assert m.get(s.session_id).user_id=="u"
    assert m.get(s.session_id).device_id=="d"
    m.revoke(s.session_id); assert not m.get(s.session_id).active
