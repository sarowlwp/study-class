import pytest
from pathlib import Path
from app.services.english_service import EnglishService
from app.models.english_word import EnglishWord


class TestEnglishService:
    def test_parse_file_not_found(self):
        service = EnglishService()
        result = service._parse_file("nonexistent.md")
        assert result == []

    def test_map_headers(self):
        service = EnglishService()
        headers = ["单词", "音标", "释义", "例句", "例句翻译", "图片关键词"]
        mapping = service._map_headers(headers)
        assert mapping["word"] == 0
        assert mapping["phonetic"] == 1
        assert mapping["meaning"] == 2
        assert mapping["example"] == 3
        assert mapping["example_cn"] == 4
        assert mapping["image_keyword"] == 5
