# tests/test_speech_assessment.py
import os
import pytest
import asyncio
from unittest.mock import patch
from app.services.speech_assessment import (
    MockSpeechAssessor,
    SpeechAssessmentResult,
    WordScore,
)


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


class TestAzureSpeechAssessor:
    def test_init_raises_without_key(self):
        with patch.dict(os.environ, {"AZURE_SPEECH_KEY": "", "AZURE_SPEECH_REGION": ""}):
            with pytest.raises(ValueError, match="AZURE_SPEECH_KEY"):
                from app.services.speech_assessment import AzureSpeechAssessor
                AzureSpeechAssessor()

    def test_init_raises_without_region(self):
        with patch.dict(os.environ, {"AZURE_SPEECH_KEY": "test-key", "AZURE_SPEECH_REGION": ""}):
            with pytest.raises(ValueError, match="AZURE_SPEECH_REGION"):
                from app.services.speech_assessment import AzureSpeechAssessor
                AzureSpeechAssessor()

    def test_init_succeeds_with_both_env_vars(self):
        with patch.dict(os.environ, {"AZURE_SPEECH_KEY": "test-key", "AZURE_SPEECH_REGION": "eastasia"}):
            from app.services.speech_assessment import AzureSpeechAssessor
            assessor = AzureSpeechAssessor()
            assert assessor._key == "test-key"
            assert assessor._region == "eastasia"

    def test_map_score_to_level_excellent(self):
        with patch.dict(os.environ, {"AZURE_SPEECH_KEY": "test", "AZURE_SPEECH_REGION": "eastasia"}):
            from app.services.speech_assessment import AzureSpeechAssessor
            assessor = AzureSpeechAssessor()
            assert assessor._map_score_to_level(90) == ("excellent", "非常棒 🌟🌟")
            assert assessor._map_score_to_level(100) == ("excellent", "非常棒 🌟🌟")

    def test_map_score_to_level_great(self):
        with patch.dict(os.environ, {"AZURE_SPEECH_KEY": "test", "AZURE_SPEECH_REGION": "eastasia"}):
            from app.services.speech_assessment import AzureSpeechAssessor
            assessor = AzureSpeechAssessor()
            assert assessor._map_score_to_level(75) == ("great", "很好 🌟")
            assert assessor._map_score_to_level(89) == ("great", "很好 🌟")

    def test_map_score_to_level_good(self):
        with patch.dict(os.environ, {"AZURE_SPEECH_KEY": "test", "AZURE_SPEECH_REGION": "eastasia"}):
            from app.services.speech_assessment import AzureSpeechAssessor
            assessor = AzureSpeechAssessor()
            assert assessor._map_score_to_level(60) == ("good", "不错 👍")
            assert assessor._map_score_to_level(74) == ("good", "不错 👍")

    def test_map_score_to_level_keep_trying(self):
        with patch.dict(os.environ, {"AZURE_SPEECH_KEY": "test", "AZURE_SPEECH_REGION": "eastasia"}):
            from app.services.speech_assessment import AzureSpeechAssessor
            assessor = AzureSpeechAssessor()
            assert assessor._map_score_to_level(0) == ("keep_trying", "继续加油 💪")
            assert assessor._map_score_to_level(59) == ("keep_trying", "继续加油 💪")

    def test_map_word_score_good(self):
        with patch.dict(os.environ, {"AZURE_SPEECH_KEY": "test", "AZURE_SPEECH_REGION": "eastasia"}):
            from app.services.speech_assessment import AzureSpeechAssessor
            assessor = AzureSpeechAssessor()
            assert assessor._map_word_score(70) == "good"
            assert assessor._map_word_score(100) == "good"

    def test_map_word_score_weak(self):
        with patch.dict(os.environ, {"AZURE_SPEECH_KEY": "test", "AZURE_SPEECH_REGION": "eastasia"}):
            from app.services.speech_assessment import AzureSpeechAssessor
            assessor = AzureSpeechAssessor()
            assert assessor._map_word_score(0) == "weak"
            assert assessor._map_word_score(69) == "weak"


class TestGetAssessor:
    def test_returns_mock_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            from app.services.speech_assessment import get_assessor, MockSpeechAssessor
            assessor = get_assessor()
            assert isinstance(assessor, MockSpeechAssessor)

    def test_returns_mock_when_mock_specified(self):
        with patch.dict(os.environ, {"SPEECH_ASSESSOR": "mock"}):
            from app.services.speech_assessment import get_assessor, MockSpeechAssessor
            assessor = get_assessor()
            assert isinstance(assessor, MockSpeechAssessor)

    def test_returns_azure_when_azure_specified(self):
        with patch.dict(os.environ, {
            "SPEECH_ASSESSOR": "azure",
            "AZURE_SPEECH_KEY": "test-key",
            "AZURE_SPEECH_REGION": "eastasia"
        }):
            from app.services.speech_assessment import get_assessor, AzureSpeechAssessor
            assessor = get_assessor()
            assert isinstance(assessor, AzureSpeechAssessor)

    def test_returns_mock_for_invalid_provider(self):
        with patch.dict(os.environ, {"SPEECH_ASSESSOR": "invalid"}):
            from app.services.speech_assessment import get_assessor, MockSpeechAssessor
            assessor = get_assessor()
            assert isinstance(assessor, MockSpeechAssessor)
