import re
from pathlib import Path
from typing import List, Dict, Optional

from app.config import CHARACTERS_DIR
from app.models.character import Character


class CharacterService:
    """汉字数据管理服务"""

    def __init__(self):
        self._cache: Dict[str, List[Character]] = {}

    def _parse_file(self, filename: str) -> List[Character]:
        """解析 Markdown 文件"""
        filepath = CHARACTERS_DIR / filename
        if not filepath.exists():
            return []

        content = filepath.read_text(encoding="utf-8")
        characters = []

        # Parse semester name
        semester_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        semester = semester_match.group(1) if semester_match else filename

        # Parse lessons and tables (support both ## and ### headers)
        lesson_pattern = r"^(#{2,3})\s+(.+)$\n+\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|\n\|[-:|\s]+\|\n((?:\|[^\n]+\|\n?)+)"

        for match in re.finditer(lesson_pattern, content, re.MULTILINE):
            header_level = match.group(1)  # ## or ###
            lesson_name = match.group(2).strip()
            table_content = match.group(7)

            # For level 2 headers (##), use as-is
            # For level 3 headers (###), prepend parent lesson name
            if header_level == "###":
                # Find parent level 2 header
                pos = match.start()
                before_content = content[:pos]
                parent_match = re.search(r"^##\s+(.+)$", before_content, re.MULTILINE)
                if parent_match:
                    parent_name = parent_match.group(1).strip()
                    lesson_name = f"{parent_name}：{lesson_name}"

            # Parse headers
            headers = [
                h.strip().lower()
                for h in [match.group(3), match.group(4), match.group(5), match.group(6)]
            ]
            field_map = self._map_headers(headers)

            # Parse table rows
            for line in table_content.strip().split("\n"):
                if not line.startswith("|"):
                    continue

                cells = [c.strip() for c in line.split("|")[1:-1]]
                if len(cells) < 4:
                    continue

                char = cells[field_map.get("char", 0)]
                pinyin = cells[field_map.get("pinyin", 1)]
                meaning = cells[field_map.get("meaning", 2)]
                example = cells[field_map.get("example", 3)]

                # Validate character
                if not char or len(char) != 1 or not "\u4e00" <= char <= "\u9fff":
                    continue

                characters.append(
                    Character(
                        char=char,
                        pinyin=pinyin,
                        meaning=meaning,
                        example=example,
                        lesson=lesson_name,
                        semester=semester,
                    )
                )

        return characters

    def _map_headers(self, headers: List[str]) -> Dict[str, int]:
        """Map table headers to standard fields"""
        field_map = {}
        keywords = {
            "char": ["汉字", "字", "char"],
            "pinyin": ["拼音", "pinyin", "拼音"],
            "meaning": ["释义", "意思", "meaning", "解释"],
            "example": ["例句", "例子", "example", "例"],
        }

        for i, header in enumerate(headers):
            for field, keys in keywords.items():
                if any(k in header for k in keys):
                    field_map[field] = i
                    break

        return field_map

    def get_semesters(self) -> List[Dict]:
        """Get all semesters"""
        semesters = []
        for filepath in CHARACTERS_DIR.glob("*.md"):
            content = filepath.read_text(encoding="utf-8")
            match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            name = match.group(1) if match else filepath.stem

            chars = self._parse_file(filepath.name)

            semesters.append(
                {"id": filepath.stem, "name": name, "file": filepath.name, "total_chars": len(chars)}
            )

        return semesters

    def get_lessons(self, semester_id: str) -> List[Dict]:
        """Get lessons for a semester"""
        chars = self._parse_file(f"{semester_id}.md")

        lessons = {}
        for char in chars:
            if char.lesson not in lessons:
                lessons[char.lesson] = {"count": 0, "mastered": 0}
            lessons[char.lesson]["count"] += 1

        return [
            {
                "id": f"lesson-{i+1}",
                "name": name,
                "char_count": data["count"],
                "mastered_count": data["mastered"],
            }
            for i, (name, data) in enumerate(lessons.items())
        ]

    def get_characters(self, semester_id: str, lessons: Optional[List[str]] = None) -> List[Character]:
        """Get characters for semester/lessons"""
        chars = self._parse_file(f"{semester_id}.md")

        if lessons:
            chars = [c for c in chars if c.lesson in lessons]

        return chars

    def get_all_characters(self) -> List[Character]:
        """Get all characters"""
        all_chars = []
        for filepath in CHARACTERS_DIR.glob("*.md"):
            all_chars.extend(self._parse_file(filepath.name))
        return all_chars
