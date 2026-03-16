import re
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict

from app.config import RECORDS_DIR
from app.models.record import QuizRecord, QuizMode, ResultType


class RecordService:
    """评测记录管理服务"""

    def save_records(self, record_date: date, records: List[QuizRecord]):
        """Save quiz records to markdown file"""
        filename = RECORDS_DIR / f"{record_date.isoformat()}.md"

        # Calculate stats
        counts = defaultdict(int)
        for r in records:
            counts[r.result.value] += 1

        # Generate markdown content
        lines = [
            f"# {record_date.isoformat()} 评测记录\n",
            "## 统计",
            f"- 总数: {len(records)}",
            f"- 掌握: {counts['mastered']}",
            f"- 模糊: {counts['fuzzy']}",
            f"- 未掌握: {counts['not_mastered']}",
            f"- 正确率: {counts['mastered'] / len(records) * 100:.1f}%\n" if records else "- 正确率: 0%\n",
            "## 评测结果\n",
            "| 汉字 | 拼音 | 课文 | 模式 | 结果 | 时间 |",
            "|------|------|------|------|------|------|"
        ]

        for r in records:
            lines.append(
                f"| {r.char} | {r.pinyin} | {r.lesson} | {r.mode.value} | {r.result.value} | {r.timestamp.strftime('%H:%M:%S')} |"
            )

        filename.write_text('\n'.join(lines), encoding='utf-8')

    def get_records_by_date(self, record_date: date) -> List[QuizRecord]:
        """Get records for a specific date"""
        filename = RECORDS_DIR / f"{record_date.isoformat()}.md"
        if not filename.exists():
            return []
        return self._parse_record_file(filename)

    def _parse_record_file(self, filepath: Path) -> List[QuizRecord]:
        """Parse a record file"""
        content = filepath.read_text(encoding='utf-8')
        records = []

        table_match = re.search(
            r'## 评测结果\n+\|[^\n]+\|\n\|[-:|\s]+\|\n((?:\|[^\n]+\|\n?)+)',
            content
        )

        if table_match:
            for line in table_match.group(1).strip().split('\n'):
                cells = [c.strip() for c in line.split('|')[1:-1]]
                if len(cells) >= 6:
                    date_str = filepath.stem
                    time_str = cells[5]
                    timestamp = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")

                    records.append(QuizRecord(
                        char=cells[0],
                        pinyin=cells[1],
                        lesson=cells[2],
                        mode=QuizMode(cells[3]),
                        result=ResultType(cells[4]),
                        timestamp=timestamp
                    ))

        return records

    def get_all_records(self) -> List[QuizRecord]:
        """Get all historical records"""
        all_records = []
        for filepath in sorted(RECORDS_DIR.glob("*.md")):
            all_records.extend(self._parse_record_file(filepath))
        return all_records

    def get_mastery_status(self, char: str, lesson: str) -> str:
        """
        Calculate mastery status based on history
        Returns: 'new' | 'mastered' | 'fuzzy' | 'not_mastered'
        """
        records = [
            r for r in self.get_all_records()
            if r.char == char and r.lesson == lesson
        ]

        if not records:
            return "new"

        records.sort(key=lambda r: r.timestamp, reverse=True)
        recent = records[:3]
        latest = recent[0].result

        if latest == ResultType.NOT_MASTERED:
            return "not_mastered"
        if latest == ResultType.FUZZY:
            return "fuzzy"

        mastered_count = sum(1 for r in recent if r.result == ResultType.MASTERED)
        if mastered_count >= 2:
            return "mastered"
        return "fuzzy"

    def get_mistakes(self, semester_id: Optional[str] = None) -> List[Dict]:
        """Get mistake book (all not_mastered characters)"""
        all_records = self.get_all_records()

        char_stats = defaultdict(lambda: {"count": 0, "last": None, "lesson": None, "pinyin": None})

        for r in all_records:
            if r.result == ResultType.NOT_MASTERED:
                key = (r.char, r.lesson)
                char_stats[key]["count"] += 1
                char_stats[key]["last"] = r.timestamp
                char_stats[key]["lesson"] = r.lesson
                char_stats[key]["pinyin"] = r.pinyin

        mistakes = []
        for (char, lesson), stats in char_stats.items():
            mistakes.append({
                "char": char,
                "pinyin": stats["pinyin"],
                "lesson": stats["lesson"],
                "mistake_count": stats["count"],
                "last_tested": stats["last"].strftime("%Y-%m-%d") if stats["last"] else None
            })

        mistakes.sort(key=lambda x: x["mistake_count"], reverse=True)
        return mistakes

    def get_stats(self, semester_id: Optional[str] = None) -> Dict:
        """Get learning statistics"""
        records = self.get_all_records()

        daily_stats = defaultdict(lambda: {"total": 0, "mastered": 0})
        for r in records:
            date_str = r.timestamp.strftime("%Y-%m-%d")
            daily_stats[date_str]["total"] += 1
            if r.result == ResultType.MASTERED:
                daily_stats[date_str]["mastered"] += 1

        dates = sorted(daily_stats.keys(), reverse=True)
        streak = 0
        today = date.today().isoformat()
        yesterday = date.fromordinal(date.today().toordinal() - 1).isoformat()

        if dates and (dates[0] == today or dates[0] == yesterday):
            streak = 1
            for i in range(1, len(dates)):
                expected = date.fromordinal(date.fromisoformat(dates[i-1]).toordinal() - 1).isoformat()
                if dates[i] == expected:
                    streak += 1
                else:
                    break

        return {
            "total_records": len(records),
            "streak_days": streak,
            "daily_stats": [
                {"date": d, **stats}
                for d, stats in sorted(daily_stats.items())[-7:]
            ]
        }

    def save_english_records(self, record_date: date, records: List):
        """保存英语评测记录"""
        from app.models.english_word import EnglishQuizMode, ResultType

        filename = RECORDS_DIR / f"english-{record_date.isoformat()}.md"

        # Calculate stats
        counts = defaultdict(int)
        for r in records:
            counts[r.result.value] += 1

        # Generate markdown content
        lines = [
            f"# {record_date.isoformat()} 英语评测记录\n",
            "## 统计",
            f"- 总数: {len(records)}",
            f"- 掌握: {counts['mastered']}",
            f"- 模糊: {counts['fuzzy']}",
            f"- 未掌握: {counts['not_mastered']}",
            f"- 正确率: {counts['mastered'] / len(records) * 100:.1f}%\n" if records else "- 正确率: 0%\n",
            "## 评测结果\n",
            "| 单词 | 释义 | 课文 | 模式 | 结果 | 时间 |",
            "|------|------|------|------|------|------|"
        ]

        for r in records:
            lines.append(
                f"| {r.word} | {r.meaning} | {r.lesson} | {r.mode.value} | {r.result.value} | {r.timestamp.strftime('%H:%M:%S')} |"
            )

        filename.write_text('\n'.join(lines), encoding='utf-8')

    def get_english_mastery_status(self, word: str, lesson: str) -> str:
        """获取单词掌握状态"""
        from app.models.english_word import EnglishQuizMode, ResultType

        records = self.get_all_english_records()
        word_records = [r for r in records if r.word == word and r.lesson == lesson]

        if not word_records:
            return "new"

        word_records.sort(key=lambda r: r.timestamp, reverse=True)
        recent = word_records[:3]
        latest = recent[0].result

        if latest == ResultType.NOT_MASTERED:
            return "not_mastered"
        if latest == ResultType.FUZZY:
            return "fuzzy"

        mastered_count = sum(1 for r in recent if r.result == ResultType.MASTERED)
        if mastered_count >= 2:
            return "mastered"
        return "fuzzy"

    def get_all_english_records(self) -> List:
        """获取所有英语评测记录"""
        from app.models.english_word import EnglishQuizRecord, EnglishQuizMode, ResultType

        records = []
        for filepath in sorted(RECORDS_DIR.glob("english-*.md")):
            records.extend(self._parse_english_record_file(filepath))
        return records

    def _parse_english_record_file(self, filepath: Path) -> List:
        """解析英语记录文件"""
        from app.models.english_word import EnglishQuizRecord, EnglishQuizMode, ResultType

        content = filepath.read_text(encoding='utf-8')
        records = []

        table_match = re.search(
            r'## 评测结果\n+\|[^\n]+\|\n\|[-:|\s]+\|\n((?:\|[^\n]+\|\n?)+)',
            content
        )

        if table_match:
            for line in table_match.group(1).strip().split('\n'):
                cells = [c.strip() for c in line.split('|')[1:-1]]
                if len(cells) >= 6:
                    date_str = filepath.stem.replace("english-", "")
                    time_str = cells[5]
                    timestamp = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")

                    records.append(EnglishQuizRecord(
                        word=cells[0],
                        meaning=cells[1],
                        lesson=cells[2],
                        mode=EnglishQuizMode(cells[3]),
                        result=ResultType(cells[4]),
                        timestamp=timestamp
                    ))

        return records

    def get_english_mistakes(self) -> List[Dict]:
        """获取英语错词本"""
        all_records = self.get_all_english_records()

        word_stats = defaultdict(lambda: {"count": 0, "last": None, "lesson": None, "meaning": None})

        for r in all_records:
            if r.result == ResultType.NOT_MASTERED:
                key = (r.word, r.lesson)
                word_stats[key]["count"] += 1
                word_stats[key]["last"] = r.timestamp
                word_stats[key]["lesson"] = r.lesson
                word_stats[key]["meaning"] = r.meaning

        mistakes = []
        for (word, lesson), stats in word_stats.items():
            mistakes.append({
                "word": word,
                "meaning": stats["meaning"],
                "lesson": stats["lesson"],
                "mistake_count": stats["count"],
                "last_tested": stats["last"].strftime("%Y-%m-%d") if stats["last"] else None
            })

        mistakes.sort(key=lambda x: x["mistake_count"], reverse=True)
        return mistakes
