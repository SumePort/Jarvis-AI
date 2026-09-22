from doom.policy import DataClass, can_leave_local_device, classify

def test_protected_tags_are_local_only():
    assert classify({"bank_pin"}) == DataClass.PROTECTED
    assert can_leave_local_device(DataClass.PROTECTED) is False
    assert can_leave_local_device(DataClass.PROTECTED, explicitly_authorized=True) is True

def test_normal_workspace_data_can_be_distributed():
    assert classify({"project", "source_code"}) == DataClass.NORMAL
    assert can_leave_local_device(DataClass.NORMAL) is True
