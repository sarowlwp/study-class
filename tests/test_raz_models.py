import pytest
from app.models.raz import RazBook


class TestRazBook:
    def test_directory_name_with_slash(self):
        """测试 id 包含斜杠时正确提取目录名"""
        book = RazBook(
            id="level-a/a-fish-sees",
            title="A Fish Sees",
            level="a",
            pages=[],
            cover="cover.jpg"
        )
        assert book.directory_name == "a-fish-sees"

    def test_directory_name_without_slash(self):
        """测试 id 不包含斜杠时返回原值"""
        book = RazBook(
            id="a-fish-sees",
            title="A Fish Sees",
            level="a",
            pages=[],
            cover="cover.jpg"
        )
        assert book.directory_name == "a-fish-sees"

    def test_validate_cover_valid(self):
        """测试有效的 cover 文件名通过校验"""
        book = RazBook(
            id="level-a/test",
            title="Test",
            level="a",
            pages=[],
            cover="cover.jpg"
        )
        assert book.validate_cover() is True

    def test_validate_cover_none(self):
        """测试 cover 为 None 时通过校验"""
        book = RazBook(
            id="level-a/test",
            title="Test",
            level="a",
            pages=[],
            cover=None
        )
        assert book.validate_cover() is True

    def test_validate_cover_invalid_path_traversal(self):
        """测试路径遍历字符被识别为无效"""
        book = RazBook(
            id="level-a/test",
            title="Test",
            level="a",
            pages=[],
            cover="../../../etc/passwd"
        )
        assert book.validate_cover() is False

    def test_validate_cover_invalid_extension(self):
        """测试不允许的扩展名被识别为无效"""
        book = RazBook(
            id="level-a/test",
            title="Test",
            level="a",
            pages=[],
            cover="cover.exe"
        )
        assert book.validate_cover() is False
