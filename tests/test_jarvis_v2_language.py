from jarvis_v2.language.policy import LanguageDetector


def test_hindi_detection():
    assert LanguageDetector().detect("मुझे नई AI technology के बारे में बताओ").language == "hi"


def test_hinglish_detection():
    assert LanguageDetector().detect("mujhe new AI technology ke baare mein batao").language == "hinglish"
