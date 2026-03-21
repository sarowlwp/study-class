# tests/test_speech_assessment.py
import pytest
import asyncio
from app.services.speech_assessment import MockSpeechAssessor, SpeechAssessmentResult


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
