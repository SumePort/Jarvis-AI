from jarvis_v2.diagnostics import DiagnosticAnalyzer
from jarvis_v2.diagnostics.correlation import DiagnosticCorrelator

def test_diagnostic_parsing():
    text='Traceback (most recent call last):\n  File "app.py", line 12, in run\nERROR database failed\nWARNING retrying'
    events=DiagnosticAnalyzer().analyze_text(text)
    assert any(e.kind=="stack_frame" and e.line==12 for e in events)
    assert DiagnosticAnalyzer().summarize(events)["errors"] >= 2

def test_diagnostic_correlation():
    events=DiagnosticAnalyzer().analyze_text('  File "app.py", line 2')
    links=DiagnosticCorrelator().correlate(events, {"C:/project/app.py"})
    assert links
