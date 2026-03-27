import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

from app.models.raz import RazBook, RazConfig, RazPage, RazPracticeRecord, RazSentence


class RazService:
    def __init__(self, raz_dir: Path, records_dir: Path, config_file: Path):
        self._raz_dir = raz_dir
        self._records_dir = records_dir
        self._config_file = config_file

    # ── 书库 ──────────────────────────────────────────────────────────────────

    def get_books(self, level: str) -> List[RazBook]:
        level_dir = self._raz_dir / f"level-{level}"
        if not level_dir.exists():
            return []
        books = []
        for book_dir in sorted(level_dir.iterdir()):
            book = self._load_book(book_dir)
            if book:
                books.append(book)
        return books

    def get_book(self, book_id: str) -> Optional[RazBook]:
        """book_id 格式: level-{x}/{dir_name}"""
        parts = book_id.split("/", 1)
        if len(parts) != 2:
            return None
        book_dir = self._raz_dir / parts[0] / parts[1]
        return self._load_book(book_dir)

    def _load_book(self, book_dir: Path) -> Optional[RazBook]:
        json_file = book_dir / "book.json"
        if not json_file.exists():
            return None
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))

            # 检查新格式（sentences 数组）
            if "sentences" in data:
                sentences = [
                    RazSentence(
                        start=s["start"],
                        end=s["end"],
                        text=s["text"],
                        page=s["page"],
                        confidence=s.get("confidence"),
                    )
                    for s in data.get("sentences", [])
                ]
                # 计算总页数
                total_pages = max((s.page for s in sentences), default=1)

                return RazBook(
                    id=data["id"],
                    title=data["title"],
                    level=data["level"],
                    pdf=data.get("pdf"),
                    audio=data.get("audio"),
                    video=data.get("video"),
                    cover=data.get("cover"),
                    total_pages=total_pages,
                    sentences=sentences,
                )

            # 旧格式兼容（pages 数组）
            pages = [
                RazPage(
                    page=p["page"],
                    pdf=p["pdf"],
                    audio=p["audio"],
                    sentences=p["sentences"],
                )
                for p in data.get("pages", [])
            ]
            return RazBook(
                id=data["id"],
                title=data["title"],
                level=data["level"],
                pages=pages,
                video=data.get("video"),
            )
        except Exception:
            return None

    # ── 配置 ──────────────────────────────────────────────────────────────────

    def get_config(self) -> RazConfig:
        if not self._config_file.exists():
            return RazConfig()
        try:
            data = json.loads(self._config_file.read_text(encoding="utf-8"))
            return RazConfig(
                current_level=data.get("current_level", "a"),
                daily_mode=data.get("daily_mode", "manual"),
                daily_count=data.get("daily_count", 10),
                current_session=data.get("current_session"),
            )
        except Exception:
            return RazConfig()

    def save_config(self, config: RazConfig) -> None:
        data = {
            "current_level": config.current_level,
            "daily_mode": config.daily_mode,
            "daily_count": config.daily_count,
            "current_session": config.current_session,
        }
        self._config_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── 记录 ──────────────────────────────────────────────────────────────────

    def save_record(self, record: RazPracticeRecord) -> None:
        self._records_dir.mkdir(parents=True, exist_ok=True)
        record_file = self._records_dir / f"{record.timestamp.date().isoformat()}.md"

        if record_file.exists():
            content = record_file.read_text(encoding="utf-8")
        else:
            content = f"# RAZ 练习记录 {record.timestamp.date().isoformat()}\n"

        book_section_header = f"## {record.book_title} (Level {record.level.upper()})"
        new_row = (
            f"| {record.page} | {record.sentence} "
            f"| {record.score} | {record.timestamp.strftime('%H:%M:%S')} |"
        )

        if book_section_header in content:
            content = content.rstrip("\n") + "\n" + new_row + "\n"
        else:
            table_header = (
                f"\n{book_section_header}\n\n"
                "| 页码 | 句子 | 评分 | 时间 |\n"
                "|------|------|------|------|\n"
            )
            content = content.rstrip("\n") + table_header + new_row + "\n"

        record_file.write_text(content, encoding="utf-8")

    def get_records_by_date(self, record_date: date) -> List[RazPracticeRecord]:
        record_file = self._records_dir / f"{record_date.isoformat()}.md"
        if not record_file.exists():
            return []
        return self._parse_records(record_file, record_date)

    def _parse_records(self, filepath: Path, record_date: date) -> List[RazPracticeRecord]:
        content = filepath.read_text(encoding="utf-8")
        records = []
        current_book_title = ""
        current_level = ""

        for line in content.splitlines():
            book_match = re.match(r"^## (.+?) \(Level ([A-Z]+)\)\s*$", line)
            if book_match:
                current_book_title = book_match.group(1)
                current_level = book_match.group(2).lower()
                continue

            if line.startswith("| 页码") or line.startswith("|---"):
                continue

            row_match = re.match(r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(\d+)\s*\|\s*(\d{2}:\d{2}:\d{2})\s*\|", line)
            if row_match and current_book_title:
                try:
                    page = int(row_match.group(1))
                    sentence = row_match.group(2).strip()
                    score = int(row_match.group(3))
                    time_str = row_match.group(4)
                    timestamp = datetime.strptime(
                        f"{record_date.isoformat()} {time_str}", "%Y-%m-%d %H:%M:%S"
                    )
                    records.append(RazPracticeRecord(
                        book_id="",
                        book_title=current_book_title,
                        level=current_level,
                        page=page,
                        sentence=sentence,
                        score=score,
                        timestamp=timestamp,
                    ))
                except (ValueError, IndexError):
                    continue

        return records
