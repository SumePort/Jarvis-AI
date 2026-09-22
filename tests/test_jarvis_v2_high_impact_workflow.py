from jarvis_v2.runtime.high_impact_workflow import HighImpactWorkflow, WorkflowState


def test_pin_screen_pauses_workflow():
    flow = HighImpactWorkflow()
    transition = flow.inspect_ui("GPay: Enter your UPI PIN", "GPay")
    assert transition.state == WorkflowState.WAITING_FOR_USER
    assert transition.request_id
    assert "PIN" in transition.message or "pin" in transition.message.lower()


def test_workflow_resumes_only_matching_request():
    flow = HighImpactWorkflow()
    transition = flow.inspect_ui("Enter OTP", "GPay")
    resumed = flow.resume(transition.request_id)
    assert resumed.state == WorkflowState.RUNNING


def test_normal_screen_does_not_pause():
    flow = HighImpactWorkflow()
    transition = flow.inspect_ui("Choose contact Rahul", "GPay")
    assert transition.state == WorkflowState.RUNNING
