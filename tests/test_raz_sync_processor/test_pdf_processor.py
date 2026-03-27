"""PDF 处理器测试."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Mock fitz 模块 before importing PDFProcessor
fitz_mock = MagicMock()
with patch.dict(sys.modules, {"fitz": fitz_mock}):
    from scripts.raz_sync_processor.pdf_processor import PDFProcessor
    from scripts.raz_sync_processor.models import PageText


class TestPDFProcessor:
    """测试 PDFProcessor."""

    def test_init_default(self):
        """测试默认初始化."""
        processor = PDFProcessor()
        assert processor.dpi == 300

    def test_init_custom_dpi(self):
        """测试自定义 DPI."""
        processor = PDFProcessor(dpi=150)
        assert processor.dpi == 150

    def test_extract_text_by_page(self):
        """测试文本提取."""
        # 使用模块级别的 fitz_mock
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Hello World"

        mock_doc = MagicMock()
        mock_doc.__len__ = Mock(return_value=2)
        mock_doc.__getitem__ = Mock(side_effect=[mock_page, mock_page])
        mock_doc.close = Mock()

        fitz_mock.open.return_value = mock_doc

        processor = PDFProcessor()
        result = processor.extract_text_by_page(Path("test.pdf"))

        assert len(result) == 2
        assert result[0].page_num == 1
        assert result[0].text == "Hello World"

    def test_normalize_text(self):
        """测试文本标准化."""
        processor = PDFProcessor()
        assert processor._normalize_text("Hello!") == "hello"
        assert processor._normalize_text("hello, world.") == "hello world"
