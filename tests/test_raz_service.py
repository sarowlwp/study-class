# tests/test_raz_service.py
import json
import pytest
from pathlib import Path
from datetime import date, datetime

from app.services.raz_service import RazService
from app.models.raz import RazBook, RazConfig, RazPracticeRecord


@pytest.fixture
def tmp_raz_dir(tmp_path):
    """创建临时 RAZ 书库目录"""
    book_dir = tmp_path / "level-a" / "my-book"
    book_dir.mkdir(parents=True)
    book_json = {
        "id": "level-a/my-book",
        "title": "My Book",
        "level": "a",
        "video": None,
        "pdf": "book.pdf",
        "audio": "audio.mp3",
        "sentences": [
            {"text": "Hello world.", "page": 1},
            {"text": "Goodbye world.", "page": 1}
        ]
    }
    (book_dir / "book.json").write_text(json.dumps(book_json), encoding="utf-8")
    return tmp_path


@pytest.fixture
def tmp_records_dir(tmp_path):
    return tmp_path / "records"


@pytest.fixture
def service(tmp_raz_dir, tmp_records_dir):
    tmp_records_dir.mkdir()
    config_file = tmp_raz_dir.parent / "raz-config.json"
    return RazService(raz_dir=tmp_raz_dir, records_dir=tmp_records_dir, config_file=config_file)


class TestRazService:
    def test_get_books_returns_books_for_level(self, service):
        books = service.get_books(level="a")
        assert len(books) == 1
        assert books[0].title == "My Book"
        assert books[0].id == "level-a/my-book"

    def test_get_books_empty_for_missing_level(self, service):
        books = service.get_books(level="z")
        assert books == []

    def test_get_book_by_id(self, service):
        book = service.get_book("level-a/my-book")
        assert book is not None
        # 每条 sentence 作为一页（测试数据有 2 条 sentences）
        assert len(book.pages) == 2
        assert book.pages[0].page == 1
        assert book.pages[0].pdf == "book.pdf"
        assert book.pages[0].audio == "audio.mp3"
        assert book.pages[0].sentences == ["Hello world."]
        assert book.pages[1].page == 2
        assert book.pages[1].sentences == ["Goodbye world."]

    def test_get_book_returns_none_for_missing(self, service):
        book = service.get_book("level-a/nonexistent")
        assert book is None

    def test_get_config_returns_default_when_no_file(self, service):
        config = service.get_config()
        assert config.current_level == "a"
        assert config.daily_mode == "manual"
        assert config.daily_count == 10

    def test_save_and_load_config(self, service):
        from app.models.raz import RazConfig
        config = RazConfig(current_level="b", daily_mode="smart", daily_count=15)
        service.save_config(config)
        loaded = service.get_config()
        assert loaded.current_level == "b"
        assert loaded.daily_count == 15

    def test_save_record(self, service):
        record = RazPracticeRecord(
            book_id="level-a/my-book",
            book_title="My Book",
            level="a",
            page=1,
            sentence="Hello world.",
            score=85,
            timestamp=datetime(2026, 3, 21, 9, 15, 0),
        )
        service.save_record(record)
        records = service.get_records_by_date(date(2026, 3, 21))
        assert len(records) == 1
        assert records[0].score == 85
        assert records[0].sentence == "Hello world."

    def test_get_records_returns_empty_for_missing_date(self, service):
        records = service.get_records_by_date(date(2020, 1, 1))
        assert records == []

    def test_malformed_record_line_is_skipped(self, service, tmp_records_dir):
        """格式错误的行不应导致崩溃"""
        record_file = tmp_records_dir / "2026-03-21.md"
        record_file.write_text(
            "# RAZ 练习记录 2026-03-21\n\n## My Book (Level A)\n\n"
            "| 页码 | 句子 | 评分 | 时间 |\n|------|------|------|------|\n"
            "| 1 | Hello world. | 85 | 09:15:00 |\n"
            "| BROKEN LINE WITHOUT PROPER FORMAT\n"
            "| 1 | Goodbye world. | 90 | 09:16:00 |\n",
            encoding="utf-8"
        )
        records = service.get_records_by_date(date(2026, 3, 21))
        assert len(records) == 2  # 跳过损坏行，读到2条


class TestLoadBookCover:
    """测试 _load_book 读取 cover 字段"""

    def test_load_book_with_cover(self, tmp_path):
        """测试 _load_book 正确读取 cover 字段"""
        book_dir = tmp_path / "level-a" / "test-book"
        book_dir.mkdir(parents=True)
        book_json = {
            "id": "level-a/test-book",
            "title": "Test Book",
            "level": "a",
            "cover": "cover.jpg",
            "video": None,
            "pdf": "book.pdf",
            "audio": "audio.mp3",
            "sentences": []
        }
        (book_dir / "book.json").write_text(json.dumps(book_json), encoding="utf-8")

        service = RazService(
            raz_dir=tmp_path,
            records_dir=tmp_path / "records",
            config_file=tmp_path / "config.json"
        )

        book = service._load_book(book_dir)
        assert book is not None
        assert book.cover == "cover.jpg"

    def test_load_book_without_cover(self, tmp_path):
        """测试 _load_book 处理无 cover 字段的情况"""
        book_dir = tmp_path / "level-a" / "test-book"
        book_dir.mkdir(parents=True)
        book_json = {
            "id": "level-a/test-book",
            "title": "Test Book",
            "level": "a",
            "video": None,
            "pdf": "book.pdf",
            "audio": "audio.mp3",
            "sentences": []
        }
        (book_dir / "book.json").write_text(json.dumps(book_json), encoding="utf-8")

        service = RazService(
            raz_dir=tmp_path,
            records_dir=tmp_path / "records",
            config_file=tmp_path / "config.json"
        )

        book = service._load_book(book_dir)
        assert book is not None
        assert book.cover is None

    def test_load_book_with_invalid_cover(self, tmp_path):
        """测试 _load_book 对非法 cover 字段重置为 None"""
        book_dir = tmp_path / "level-a" / "test-book"
        book_dir.mkdir(parents=True)
        book_json = {
            "id": "level-a/test-book",
            "title": "Test Book",
            "level": "a",
            "cover": "../../../etc/passwd",
            "video": None,
            "pdf": "book.pdf",
            "audio": "audio.mp3",
            "sentences": []
        }
        (book_dir / "book.json").write_text(json.dumps(book_json), encoding="utf-8")

        service = RazService(
            raz_dir=tmp_path,
            records_dir=tmp_path / "records",
            config_file=tmp_path / "config.json"
        )

        book = service._load_book(book_dir)
        assert book is not None
        assert book.cover is None
