import re
from datetime import date, timedelta
from pathlib import Path
from typing import Optional
import math

from app.models.raz import RazConfig
from app.services.raz_service import RazService


class RazPracticeService:
    def __init__(self, raz_service: RazService, records_dir: Path):
        self._raz_service = raz_service
        self._records_dir = records_dir

    def get_today_count(self, today: date) -> int:
        """统计今日已完成句子数（record 文件中的数据行数）。"""
        record_file = self._records_dir / f"{today.isoformat()}.md"
        if not record_file.exists():
            return 0
        content = record_file.read_text(encoding="utf-8")
        count = 0
        for line in content.splitlines():
            if re.match(r"^\|\s*\d+\s*\|", line) and not line.startswith("| 页码"):
                count += 1
        return count

    def is_daily_goal_met(self, today: date, config: RazConfig) -> bool:
        target = config.daily_count
        if config.daily_mode == "smart":
            target = self.get_smart_recommendation(reference_date=today)
        return self.get_today_count(today) >= target

    def get_smart_recommendation(self, reference_date: date) -> int:
        """近7天平均完成句数 × 完成率，无历史时默认10。"""
        counts = []
        for i in range(1, 8):
            d = reference_date - timedelta(days=i)
            counts.append(self.get_today_count(d))

        days_with_data = [c for c in counts if c > 0]
        if not days_with_data:
            return 10

        avg = sum(days_with_data) / len(days_with_data)
        completion_rate = len(days_with_data) / 7
        return max(5, math.ceil(avg * completion_rate))

    def update_session(self, book_id: str, page: int, sentence_index: int) -> None:
        """持久化当前练习断点到 raz-config.json。"""
        config = self._raz_service.get_config()
        config.current_session = {
            "book_id": book_id,
            "page": page,
            "sentence_index": sentence_index,
        }
        self._raz_service.save_config(config)
