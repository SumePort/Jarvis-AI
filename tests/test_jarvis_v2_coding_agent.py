from pathlib import Path

from jarvis_v2.code.coding_agent import CodingAgentRequest, ProjectCodingAgent


def test_coding_agent_requires_confirmation(tmp_path: Path):
    source = tmp_path / "calc.py"
    source.write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    (tmp_path / "test_calc.py").write_text(
        "from calc import add\n\ndef test_add():\n    assert add(2, 3) == 5\n", encoding="utf-8"
    )

    def proposer(*args):
        raise AssertionError("proposal must not be requested before confirmation")

    result = ProjectCodingAgent(tmp_path, proposer).run(
        CodingAgentRequest("Fix add", str(tmp_path), confirmed=False)
    )
    assert not result.success
    assert "confirmation" in result.message.lower()


def test_coding_agent_repairs_and_verifies(tmp_path: Path):
    source = tmp_path / "calc.py"
    source.write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    (tmp_path / "test_calc.py").write_text(
        "from calc import add\n\ndef test_add():\n    assert add(2, 3) == 5\n", encoding="utf-8"
    )

    def proposer(request, failure, candidates):
        original = source.read_text(encoding="utf-8")
        proposed = original.replace("return a - b", "return a + b")
        return agent.repair.propose_text_patch(source, proposed, "Fix addition operator.", 0.99)

    agent = ProjectCodingAgent(tmp_path, proposer)
    result = agent.run(CodingAgentRequest("Fix add", str(tmp_path), confirmed=True))
    assert result.success
    assert "return a + b" in source.read_text(encoding="utf-8")
    assert result.repair_cycles[-1].verified
