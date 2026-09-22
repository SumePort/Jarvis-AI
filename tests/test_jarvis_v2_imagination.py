from jarvis_v2.imagination.engine import ImaginationEngine
from jarvis_v2.imagination.models import PossibilityLevel

def test_unknown_is_not_impossible_without_model():
    result=ImaginationEngine().explore("build a new kind of display")
    assert result.hypotheses
    assert result.hypotheses[0].level == PossibilityLevel.EXPERIMENTALLY_UNKNOWN

def test_imagination_model_result():
    def model(prompt):
        return '{"known":["AR displays exist"],"constraints":["optics"],"hypotheses":[{"statement":"combine spatial tracking and directional optics","mechanism":"tracked optical projection","level":"plausible","evidence":["AR"],"uncertainties":["brightness"]}],"analogies":[],"experiments":[{"objective":"test visibility","hypothesis_id":"","materials":["display"],"procedure":["measure visibility"],"expected_observation":"tracked image","safety_notes":[],"success_criteria":["image visible"]}],"conclusion":"Test the hypothesis."}'
    result=ImaginationEngine(model).explore("new spatial display")
    assert result.hypotheses[0].level == PossibilityLevel.PLAUSIBLE
    assert result.experiments
