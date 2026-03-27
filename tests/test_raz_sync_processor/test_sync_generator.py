"""同步生成器测试."""

import json
import pytest
from pathlib import Path

from scripts.raz_sync_processor.sync_generator import SyncGenerator
from scripts.raz_sync_processor.models import PageText, WordTiming


class TestSyncGenerator:
    """测试 SyncGenerator."""

    def test_init(self, tmp_path):
        """测试初始化."""
        generator = SyncGenerator(tmp_path)
        assert generator.output_dir == tmp_path

    def test_generate_word_timings_simple(self, tmp_path):
        """测试生成简化版 word_timings.json."""
        generator = SyncGenerator(tmp_path)

        words = [
            WordTiming("hello", 0.0, 0.5),
            WordTiming("world", 0.6, 1.0),
        ]

        generator.generate_word_timings_simple(words)

        json_path = tmp_path / "word_timings.json"
        assert json_path.exists()
        data = json.loads(json_path.read_text())
        assert data["total_words"] == 2
        assert len(data["timings"]) == 2
        assert data["timings"][0]["word"] == "hello"
        assert "start" in data["timings"][0]
        assert "end" in data["timings"][0]
        # 简化版没有 page 信息
        assert "page" not in data["timings"][0]

    def test_generate_pdf_text_json(self, tmp_path):
        """测试生成 pdf_text.json."""
        generator = SyncGenerator(tmp_path)

        pages = [
            PageText(1, "Hello world"),
            PageText(2, "How are you"),
        ]

        generator.generate_pdf_text_json(
            pages=pages,
            book_id="level-a/test",
            title="Test Book",
            level="a"
        )

        json_path = tmp_path / "pdf_text.json"
        assert json_path.exists()
        data = json.loads(json_path.read_text())
        assert data["id"] == "level-a/test"
        assert data["title"] == "Test Book"
        assert data["level"] == "a"
        assert data["page_count"] == 2
        assert len(data["pages"]) == 2

    def test_create_symlinks(self, tmp_path):
        """测试创建软链接."""
        generator = SyncGenerator(tmp_path)

        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "book.pdf").write_text("fake pdf")
        (source_dir / "book.mp3").write_text("fake audio")

        generator.create_symlinks(source_dir)

        assert (tmp_path / "book.pdf").exists()
        assert (tmp_path / "book.mp3").exists()

    def test_generate_reader_html(self, tmp_path):
        """测试生成阅读器 HTML."""
        generator = SyncGenerator(tmp_path)
        generator.generate_reader_html()

        html_path = tmp_path / "index.html"
        assert html_path.exists()
        content = html_path.read_text()
        assert "<!DOCTYPE html>" in content
