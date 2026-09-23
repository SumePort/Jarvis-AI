from jarvis_v2.voice.chatgpt_background import JarvisAction, parse_actions


def test_parse_jarvis_action():
    text = (
        "I'll do that. "
        '[[JARVIS_ACTION]]{"command":"open Chrome","spoken":"Opening Chrome."}'
        "[[/JARVIS_ACTION]]"
    )
    assert parse_actions(text) == [
        JarvisAction("open Chrome", "Opening Chrome.")
    ]


def test_parse_multiple_actions():
    text = (
        '[[JARVIS_ACTION]]{"command":"open Chrome"}[[/JARVIS_ACTION]] '
        '[[JARVIS_ACTION]]{"command":"open Notepad"}[[/JARVIS_ACTION]]'
    )
    assert [a.command for a in parse_actions(text)] == [
        "open Chrome",
        "open Notepad",
    ]


def test_parse_normal_conversation():
    assert parse_actions("Sure, let's talk about AI.") == []
