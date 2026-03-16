import re
from pathlib import Path
from typing import List, Dict, Optional

from app.config import ENGLISH_DIR
from app.models.english_word import EnglishWord


class EnglishService:
    """英语单词数据管理服务"""

    def __init__(self):
        self._cache: Dict[str, List[EnglishWord]] = {}

    def _parse_file(self, filename: str) -> List[EnglishWord]:
        """解析 Markdown 文件"""
        filepath = ENGLISH_DIR / filename
        if not filepath.exists():
            return []

        content = filepath.read_text(encoding="utf-8")
        words = []

        # Parse semester name
        semester_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        semester = semester_match.group(1) if semester_match else filename

        # Parse lessons and tables
        lesson_pattern = r"^##\s+(.+)$\n+\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|\n\|[-:|\s]+\|\n((?:\|[^\n]+\|\n?)+)"

        for match in re.finditer(lesson_pattern, content, re.MULTILINE):
            lesson_name = match.group(1).strip()
            table_content = match.group(8)

            # Parse headers
            headers = [
                match.group(2).strip().lower(),
                match.group(3).strip().lower(),
                match.group(4).strip().lower(),
                match.group(5).strip().lower(),
                match.group(6).strip().lower(),
                match.group(7).strip().lower(),
            ]
            field_map = self._map_headers(headers)

            # Parse table rows
            for line in table_content.strip().split("\n"):
                if not line.startswith("|"):
                    continue

                cells = [c.strip() for c in line.split("|")[1:-1]]
                if len(cells) < 6:
                    continue

                word = cells[field_map.get("word", 0)]
                phonetic = cells[field_map.get("phonetic", 1)]
                meaning = cells[field_map.get("meaning", 2)]
                example = cells[field_map.get("example", 3)]
                example_cn = cells[field_map.get("example_cn", 4)]
                image_keyword = cells[field_map.get("image_keyword", 5)]

                # Validate word
                if not word or not word.isalpha():
                    continue

                words.append(
                    EnglishWord(
                        word=word,
                        phonetic=phonetic if phonetic else None,
                        meaning=meaning,
                        example=example if example else None,
                        example_cn=example_cn if example_cn else None,
                        lesson=lesson_name,
                        semester=semester,
                        image_keyword=image_keyword if image_keyword else None,
                    )
                )

        return words

    def _map_headers(self, headers: List[str]) -> Dict[str, int]:
        """映射表头到标准字段"""
        field_map = {}
        # Order matters: more specific patterns first
        keywords = {
            "word": ["单词", "word"],
            "phonetic": ["音标", "phonetic", "发音"],
            "meaning": ["释义", "meaning", "意思", "中文"],
            "example_cn": ["例句翻译", "example_cn", "中文翻译", "翻译"],
            "example": ["例句", "example", "英文例句", "例"],
            "image_keyword": ["图片关键词", "image_keyword", "图片", "keyword"],
        }

        for i, header in enumerate(headers):
            for field, keys in keywords.items():
                if any(k in header for k in keys):
                    field_map[field] = i
                    break

        return field_map

    def get_semesters(self) -> List[Dict]:
        """获取所有年级列表"""
        semesters = []
        for filepath in ENGLISH_DIR.glob("*.md"):
            content = filepath.read_text(encoding="utf-8")
            match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            name = match.group(1) if match else filepath.stem

            words = self._parse_file(filepath.name)

            semesters.append({
                "id": filepath.stem,
                "name": name,
                "file": filepath.name,
                "total_words": len(words)
            })

        return sorted(semesters, key=lambda x: x["id"])

    def get_lessons(self, semester_id: str) -> List[Dict]:
        """获取指定年级的单元列表"""
        words = self._parse_file(f"{semester_id}.md")

        lessons = {}
        for word in words:
            if word.lesson not in lessons:
                lessons[word.lesson] = {"count": 0, "words": []}
            lessons[word.lesson]["count"] += 1
            lessons[word.lesson]["words"].append(word.word)

        return [
            {
                "id": f"lesson-{i+1}",
                "name": name,
                "word_count": data["count"],
            }
            for i, (name, data) in enumerate(lessons.items())
        ]

    def get_words(self, semester_id: str, lessons: Optional[List[str]] = None) -> List[EnglishWord]:
        """获取单词列表"""
        words = self._parse_file(f"{semester_id}.md")

        if lessons:
            words = [w for w in words if w.lesson in lessons]

        return words

    def get_all_words(self) -> List[EnglishWord]:
        """获取所有单词"""
        all_words = []
        for filepath in ENGLISH_DIR.glob("*.md"):
            all_words.extend(self._parse_file(filepath.name))
        return all_words
