# tests/test_speech_assessment.py
import pytest
import asyncio
from app.services.speech_assessment import MockSpeechAssessor, SpeechAssessmentResult


from app.services.speech_assessment import WordScore, SpeechAssessmentResult


def test_word_score_has_status_field():
    ws = WordScore(word="hello", score=85)
    assert ws.word == "hello"
    assert ws.score == 85
    assert ws.status == "good"  # default value


def test_word_score_status_can_be_weak():
    ws = WordScore(word="hello", score=55, status="weak")
    assert ws.status == "weak"


class TestMockSpeechAssessor:
    @pytest.mark.asyncio
    async def test_assess_returns_result(self):
        assessor = MockSpeechAssessor()
        result = await assessor.assess(b"fake_audio", "Hello world.")
        assert isinstance(result, SpeechAssessmentResult)
        assert 0 <= result.score <= 100
        assert isinstance(result.feedback, str)

    @pytest.mark.asyncio
    async def test_assess_accepts_any_audio_bytes(self):
        assessor = MockSpeechAssessor()
        result = await assessor.assess(b"", "Short.")
        assert result.score >= 0
