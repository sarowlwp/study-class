"""集成测试."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from scripts.raz_sync_processor.main import RazSyncProcessor
from scripts.raz_sync_processor.models import PageText, WordTiming


class TestIntegration:
    """集成测试."""

    @pytest.fixture
    def mock_processor(self):
        """创建带有模拟组件的处理器."""
        with patch('scripts.raz_sync_processor.pdf_processor.PDFProcessor') as mock_pdf_class, \
             patch('scripts.raz_sync_processor.audio_transcriber.AudioTranscriber') as mock_audio_class, \
             patch('scripts.raz_sync_processor.llm_mapper.LlmMapper') as mock_llm_class:

            # 创建处理器实例
            processor = RazSyncProcessor(model_size="tiny")

            # 替换实例的组件为 mock
            processor.pdf_processor = mock_pdf_class.return_value
            processor.audio_transcriber = mock_audio_class.return_value
            processor.llm_mapper = mock_llm_class.return_value

            yield processor, mock_pdf_class, mock_audio_class, mock_llm_class

    def test_process_success(self, tmp_path, mock_processor):
        """测试完整处理流程."""
        processor, _, _, mock_llm = mock_processor

        # 创建输入文件
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "book.pdf").write_text("fake pdf")
        (input_dir / "book.mp3").write_text("fake audio")

        output_dir = tmp_path / "output"

        # 配置模拟返回值
        processor.pdf_processor.needs_ocr.return_value = False
        processor.pdf_processor.extract_text_by_page.return_value = [
            PageText(1, "Hello world"),
            PageText(2, "How are you"),
        ]
        processor.pdf_processor.extract_cover_image.return_value = True

        processor.audio_transcriber.transcribe.return_value = [
            WordTiming("hello", 0.0, 0.5),
            WordTiming("world", 0.6, 1.0),
            WordTiming("how", 1.5, 1.8),
            WordTiming("are", 1.9, 2.1),
            WordTiming("you", 2.2, 2.5),
        ]

        # LLM mapper 生成 book.json
        mock_llm.return_value.generate_book_json.return_value = output_dir / "book.json"

        # 执行
        success = processor.process(input_dir, output_dir)

        # 验证
        assert success is True
        # LLM mapper 被调用
        mock_llm.return_value.generate_book_json.assert_called_once()

    def test_process_missing_pdf(self, tmp_path, mock_processor):
        """测试缺少 PDF 文件."""
        processor, _, _, _ = mock_processor

        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "book.mp3").write_text("fake audio")

        output_dir = tmp_path / "output"

        success = processor.process(input_dir, output_dir)
        assert success is False

    def test_process_missing_audio(self, tmp_path, mock_processor):
        """测试缺少音频文件."""
        processor, _, _, _ = mock_processor

        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "book.pdf").write_text("fake pdf")

        output_dir = tmp_path / "output"

        success = processor.process(input_dir, output_dir)
        assert success is False

    def test_process_empty_pages(self, tmp_path, mock_processor):
        """测试空页面处理."""
        processor, _, _, _ = mock_processor

        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "book.pdf").write_text("fake pdf")
        (input_dir / "book.mp3").write_text("fake audio")

        output_dir = tmp_path / "output"

        processor.pdf_processor.needs_ocr.return_value = False
        processor.pdf_processor.extract_text_by_page.return_value = []

        success = processor.process(input_dir, output_dir)
        assert success is False

    def test_process_llm_mapping_fails(self, tmp_path, mock_processor):
        """测试 LLM 映射失败的情况."""
        processor, _, _, mock_llm = mock_processor

        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "book.pdf").write_text("fake pdf")
        (input_dir / "book.mp3").write_text("fake audio")

        output_dir = tmp_path / "output"

        processor.pdf_processor.needs_ocr.return_value = False
        processor.pdf_processor.extract_text_by_page.return_value = [
            PageText(1, "Hello world"),
        ]
        processor.audio_transcriber.transcribe.return_value = [
            WordTiming("hello", 0.0, 0.5),
            WordTiming("world", 0.6, 1.0),
        ]

        # LLM mapper 返回 None 表示失败
        mock_llm.return_value.generate_book_json.return_value = None

        success = processor.process(input_dir, output_dir)
        assert success is False
