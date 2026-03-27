"""音频转录器测试."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


class TestAudioTranscriber:
    """测试 AudioTranscriber."""

    @patch("scripts.raz_sync_processor.audio_transcriber.WhisperModel")
    def test_init_default(self, mock_model_class):
        """测试默认初始化."""
        from scripts.raz_sync_processor.audio_transcriber import AudioTranscriber
        transcriber = AudioTranscriber()
        assert transcriber.model_size == "base"
        assert transcriber.device == "cpu"

    @patch("scripts.raz_sync_processor.audio_transcriber.WhisperModel")
    def test_init_custom(self, mock_model_class):
        """测试自定义参数."""
        from scripts.raz_sync_processor.audio_transcriber import AudioTranscriber
        transcriber = AudioTranscriber(model_size="tiny", device="cuda")
        assert transcriber.model_size == "tiny"
        assert transcriber.device == "cuda"

    @patch("scripts.raz_sync_processor.audio_transcriber.WhisperModel")
    def test_transcribe(self, mock_model_class):
        """测试转录功能."""
        from scripts.raz_sync_processor.audio_transcriber import AudioTranscriber

        mock_segment = MagicMock()
        mock_segment.words = [
            Mock(word="Hello", start=0.0, end=0.5),
            Mock(word="world", start=0.6, end=1.0),
        ]

        mock_info = MagicMock()
        mock_info.language = "en"

        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment], mock_info)
        mock_model_class.return_value = mock_model

        transcriber = AudioTranscriber()
        result = transcriber.transcribe(Path("test.mp3"))

        assert len(result) == 2
        assert result[0].word == "hello"  # 标准化为小写
        assert result[0].start == 0.0
        assert result[0].end == 0.5

    @patch("scripts.raz_sync_processor.audio_transcriber.WhisperModel")
    def test_normalize_word(self, mock_model_class):
        """测试单词标准化."""
        from scripts.raz_sync_processor.audio_transcriber import AudioTranscriber
        transcriber = AudioTranscriber()
        assert transcriber._normalize_word("Hello") == "hello"
        assert transcriber._normalize_word("IT'S") == "it's"
