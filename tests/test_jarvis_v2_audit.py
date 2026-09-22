from jarvis_v2.audit import AuditLog

def test_audit_chain(tmp_path):
    log=AuditLog(tmp_path/"audit.jsonl")
    log.append("request.received","u","hello")
    log.append("plan.created","u","hello",{"steps":1})
    assert log.verify()

def test_tamper_detected(tmp_path):
    path=tmp_path/"audit.jsonl"; log=AuditLog(path)
    log.append("request.received", "u", "hello")
    raw=path.read_text(); path.write_text(raw.replace("hello", "tampered"))
    assert not log.verify()
