from pathlib import Path
from jarvis_v2.perception import InputKind, PerceptionPipeline

def test_text_and_environment_are_normalized():
    p=PerceptionPipeline()
    result=p.fuse(p.text("understand SumePort"), p.environment({"project":"SumePort"}))
    assert [x.kind for x in result.percepts] == [InputKind.TEXT, InputKind.ENVIRONMENT]

def test_document_is_bounded(tmp_path: Path):
    f=tmp_path/"readme.txt"; f.write_text("hello", encoding="utf-8")
    assert PerceptionPipeline().document(str(f)).percepts[0].text == "hello"
