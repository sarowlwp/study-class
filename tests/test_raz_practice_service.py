# tests/test_raz_practice_service.py
import json
import pytest
from datetime import date, datetime, timedelta
from pathlib import Path

from app.services.raz_practice_service import RazPracticeService
from app.services.raz_service import RazService
from app.models.raz import RazConfig, RazPracticeRecord


@pytest.fixture
def tmp_dirs(tmp_path):
    raz_dir = tmp_path / "raz"
    records_dir = tmp_path / "records"
    records_dir.mkdir(parents=True)
    config_file = tmp_path / "raz-config.json"
    return raz_dir, records_dir, config_file


@pytest.fixture
def raz_service(tmp_dirs):
    raz_dir, records_dir, config_file = tmp_dirs
    return RazService(raz_dir=raz_dir, records_dir=records_dir, config_file=config_file)


@pytest.fixture
def practice_service(raz_service, tmp_dirs):
    _, records_dir, _ = tmp_dirs
    return RazPracticeService(raz_service=raz_service, records_dir=records_dir)


def _write_records(records_dir: Path, record_date: date, count: int):
    content = f"# RAZ 练习记录 {record_date.isoformat()}\n\n## Test Book (Level A)\n\n"
    content += "| 页码 | 句子 | 评分 | 时间 |\n|------|------|------|------|\n"
    for i in range(count):
        content += f"| 1 | Sentence {i}. | 80 | 0{i % 10}:00:00 |\n"
    (records_dir / f"{record_date.isoformat()}.md").write_text(content, encoding="utf-8")


class TestRazPracticeService:
    def test_get_today_count_zero_when_no_records(self, practice_service):
        count = practice_service.get_today_count(date(2099, 1, 1))
        assert count == 0

    def test_get_today_count_matches_record_rows(self, practice_service, tmp_dirs):
        _, records_dir, _ = tmp_dirs
        today = date(2026, 3, 21)
        _write_records(records_dir, today, 7)
        count = practice_service.get_today_count(today)
        assert count == 7

    def test_is_daily_goal_met_manual_mode(self, practice_service, tmp_dirs):
        _, records_dir, _ = tmp_dirs
        today = date(2026, 3, 21)
        _write_records(records_dir, today, 10)
        config = RazConfig(daily_mode="manual", daily_count=10)
        assert practice_service.is_daily_goal_met(today, config) is True

    def test_is_daily_goal_not_met(self, practice_service, tmp_dirs):
        _, records_dir, _ = tmp_dirs
        today = date(2026, 3, 21)
        _write_records(records_dir, today, 5)
        config = RazConfig(daily_mode="manual", daily_count=10)
        assert practice_service.is_daily_goal_met(today, config) is False

    def test_smart_recommend_defaults_to_10_with_no_history(self, practice_service):
        recommended = practice_service.get_smart_recommendation(reference_date=date(2026, 3, 21))
        assert recommended == 10

    def test_smart_recommend_uses_7_day_average(self, practice_service, tmp_dirs):
        _, records_dir, _ = tmp_dirs
        today = date(2026, 3, 21)
        for i in range(7):
            _write_records(records_dir, today - timedelta(days=i + 1), 8)
        recommended = practice_service.get_smart_recommendation(reference_date=today)
        assert recommended > 0

    def test_update_session(self, practice_service, raz_service):
        practice_service.update_session(book_id="level-a/my-book", page=2, sentence_index=1)
        config = raz_service.get_config()
        assert config.current_session == {
            "book_id": "level-a/my-book",
            "page": 2,
            "sentence_index": 1,
        }
