"""集成测试."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from scripts.raz_sync_processor.main import RazSyncProcessor
from scripts.raz_sync_processor.models import PageText, WordTiming, PageTiming


class TestIntegration:
    """集成测试."""

    @pytest.fixture
    def mock_processor(self):
        """创建带有模拟组件的处理器."""
        with patch('scripts.raz_sync_processor.main.PDFProcessor') as mock_pdf, \
             patch('scripts.raz_sync_processor.main.AudioTranscriber') as mock_audio, \
             patch('scripts.raz_sync_processor.main.TextAligner') as mock_aligner:

            processor = RazSyncProcessor(model_size="tiny")
            processor.pdf_processor = mock_pdf.return_value
            processor.audio_transcriber = mock_audio.return_value
            processor.text_aligner = mock_aligner.return_value

            yield processor, mock_pdf, mock_audio, mock_aligner

    def test_process_success(self, tmp_path, mock_processor):
        """测试完整处理流程."""
        processor, _, _, _ = mock_processor

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

        processor.audio_transcriber.transcribe.return_value = [
            WordTiming("hello", 0.0, 0.5),
            WordTiming("world", 0.6, 1.0),
            WordTiming("how", 1.5, 1.8),
            WordTiming("are", 1.9, 2.1),
            WordTiming("you", 2.2, 2.5),
        ]

        processor.text_aligner.align.return_value = [
            PageTiming(1, 0.0, 1.0, "Hello world"),
            PageTiming(2, 1.5, 2.5, "How are you"),
        ]

        # 执行
        success = processor.process(input_dir, output_dir)

        # 验证
        assert success is True
        assert (output_dir / "book.json").exists()
        assert (output_dir / "word_timings.json").exists()
        assert (output_dir / "index.html").exists()

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

    def test_book_json_content(self, tmp_path, mock_processor):
        """测试生成的 book.json 内容."""
        processor, _, _, _ = mock_processor

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
        processor.text_aligner.align.return_value = [
            PageTiming(1, 0.0, 1.0, "Hello world"),
        ]

        processor.process(input_dir, output_dir)

        # 验证 JSON 内容
        book_json = json.loads((output_dir / "book.json").read_text())
        assert book_json["title"] == "Input"
        assert book_json["page_count"] == 1
        assert len(book_json["pages"]) == 1
        assert book_json["pages"][0]["text"] == "Hello world"
