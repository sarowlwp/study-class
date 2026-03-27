"""文本对齐器测试."""

import pytest
from scripts.raz_sync_processor.text_aligner import TextAligner
from scripts.raz_sync_processor.models import PageText, WordTiming, PageTiming


class TestTextAligner:
    """测试 TextAligner."""

    def test_init(self):
        """测试初始化."""
        aligner = TextAligner()
        assert aligner is not None

    def test_align_simple(self):
        """测试简单对齐."""
        aligner = TextAligner()

        pages = [
            PageText(1, "Hello world"),
            PageText(2, "How are you"),
        ]

        words = [
            WordTiming("hello", 0.0, 0.5),
            WordTiming("world", 0.6, 1.0),
            WordTiming("how", 1.5, 1.8),
            WordTiming("are", 1.9, 2.1),
            WordTiming("you", 2.2, 2.5),
        ]

        result = aligner.align(pages, words)

        assert len(result) == 2
        assert result[0].page_num == 1
        assert result[0].start_time == 0.0
        assert result[0].end_time == 1.0
        assert result[1].page_num == 2
        assert result[1].start_time == 1.5

    def test_normalize_text(self):
        """测试文本标准化."""
        aligner = TextAligner()
        assert aligner._normalize_text("Hello, World!") == "hello world"
        assert aligner._normalize_text("  spaces  ") == "spaces"

    def test_align_empty_pages(self):
        """测试空页面处理."""
        aligner = TextAligner()
        pages = [PageText(1, "Hello")]
        words = [WordTiming("hello", 0.0, 0.5)]
        result = aligner.align(pages, words)
        assert len(result) == 1
        assert result[0].start_time == 0.0
