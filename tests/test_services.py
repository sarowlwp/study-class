import pytest
from datetime import datetime

from app.models.record import QuizRecord, ResultType
from app.services.character_service import CharacterService
from app.services.record_service import RecordService
from app.services.quiz_service import QuizService


@pytest.fixture
def character_service():
    return CharacterService()


@pytest.fixture
def record_service():
    return RecordService()


@pytest.fixture
def quiz_service(character_service, record_service):
    return QuizService(character_service, record_service)


class TestCharacterService:
    def test_parse_markdown_file(self, character_service):
        characters = character_service._parse_file("grade1-spring.md")
        assert len(characters) > 0
        assert characters[0].char == "春"
        assert characters[0].semester == "一年级下册"
        assert characters[0].lesson == "第一课：春天来了"

    def test_get_semesters(self, character_service):
        semesters = character_service.get_semesters()
        assert isinstance(semesters, list)
        assert len(semesters) >= 1
        assert "grade1-spring" in [s["id"] for s in semesters]

    def test_get_lessons(self, character_service):
        lessons = character_service.get_lessons("grade1-spring")
        assert len(lessons) == 2
        assert lessons[0]["name"] == "第一课：春天来了"
        assert lessons[0]["char_count"] == 4

    def test_get_characters_by_lessons(self, character_service):
        chars = character_service.get_characters("grade1-spring", ["第一课：春天来了"])
        assert len(chars) == 4
        assert all(c.lesson == "第一课：春天来了" for c in chars)

    def test_get_characters_all(self, character_service):
        chars = character_service.get_characters("grade1-spring")
        assert len(chars) == 8  # 4 + 4 from two lessons


class TestQuizService:
    def test_generate_quiz(self, quiz_service):
        session = quiz_service.generate_quiz("grade1-spring", ["第一课：春天来了"], 4)
        assert session.total == 4
        assert len(session.characters) == 4
        assert session.session_id is not None

    def test_submit_result(self, quiz_service):
        session = quiz_service.generate_quiz("grade1-spring", ["第一课：春天来了"], 2)
        quiz_service.submit_result(session.session_id, 0, ResultType.MASTERED)
        assert len(session.records) == 1
        assert session.records[0].result == ResultType.MASTERED

    def test_finish_quiz(self, quiz_service):
        session = quiz_service.generate_quiz("grade1-spring", ["第一课：春天来了"], 2)
        quiz_service.submit_result(session.session_id, 0, ResultType.MASTERED)
        quiz_service.submit_result(session.session_id, 1, ResultType.NOT_MASTERED)
        summary = quiz_service.finish_quiz(session.session_id)
        assert summary["total"] == 2
        assert summary["mastered"] == 1
        assert summary["not_mastered"] == 1


class TestRecordService:
    def test_save_and_load_records(self, record_service):
        from datetime import datetime
        from app.models.record import QuizMode
        records = [
            QuizRecord(
                char="春", pinyin="chūn", lesson="第一课",
                mode=QuizMode.CHAR_TO_PINYIN, result=ResultType.MASTERED,
                timestamp=datetime(2026, 3, 16, 10, 0, 0)
            )
        ]
        record_service.save_records(datetime(2026, 3, 16).date(), records)
        loaded = record_service.get_records_by_date(datetime(2026, 3, 16).date())
        assert len(loaded) == 1
        assert loaded[0].char == "春"
