from datetime import datetime

import pytest

from app.models.character import Character, QuizMode, ResultType
from app.models.record import QuizRecord, QuizSessionState


def test_character_creation():
    char = Character(
        char="春",
        pinyin="chūn",
        meaning="春季，一年的第一季",
        example="春天来了，花儿开了。",
        lesson="第一课：春天来了",
        semester="一年级下册"
    )
    assert char.char == "春"
    assert char.pinyin == "chūn"
    assert char.mastery_status is None


def test_character_to_dict():
    char = Character(
        char="春",
        pinyin="chūn",
        meaning="春季",
        example="春天来了。",
        lesson="第一课",
        semester="一年级下册"
    )
    data = char.to_dict()
    assert data["char"] == "春"
    assert data["pinyin"] == "chūn"
    assert "mastery_status" not in data  # Not included when None


def test_character_to_dict_with_status():
    char = Character(
        char="春",
        pinyin="chūn",
        meaning="春季",
        example="春天来了。",
        lesson="第一课",
        semester="一年级下册",
        mastery_status="mastered"
    )
    data = char.to_dict()
    assert data["mastery_status"] == "mastered"


def test_quiz_record_creation():
    record = QuizRecord(
        char="春",
        pinyin="chūn",
        lesson="第一课",
        mode=QuizMode.CHAR_TO_PINYIN,
        result=ResultType.MASTERED,
        timestamp=datetime(2026, 3, 16, 19, 30, 0)
    )
    assert record.char == "春"
    assert record.result == ResultType.MASTERED
    assert record.mode == QuizMode.CHAR_TO_PINYIN


def test_quiz_session_creation():
    session = QuizSessionState(
        session_id="abc123",
        created_at=datetime.now(),
        total=20,
        lessons=["第一课", "第二课"]
    )
    assert session.session_id == "abc123"
    assert session.current_index == 0
    assert len(session.records) == 0
    assert not session.completed


def test_quiz_session_add_record():
    session = QuizSessionState(
        session_id="abc123",
        created_at=datetime.now(),
        total=20,
        lessons=["第一课"]
    )

    record = QuizRecord(
        char="春",
        pinyin="chūn",
        lesson="第一课",
        mode=QuizMode.CHAR_TO_PINYIN,
        result=ResultType.MASTERED
    )

    session.add_record(record)
    assert len(session.records) == 1
    assert session.records[0].result == ResultType.MASTERED


def test_quiz_session_add_record_update_existing():
    """测试添加重复记录会更新而不是追加"""
    session = QuizSessionState(
        session_id="abc123",
        created_at=datetime.now(),
        total=20,
        lessons=["第一课"]
    )

    record1 = QuizRecord(
        char="春",
        pinyin="chūn",
        lesson="第一课",
        mode=QuizMode.CHAR_TO_PINYIN,
        result=ResultType.NOT_MASTERED
    )

    record2 = QuizRecord(
        char="春",
        pinyin="chūn",
        lesson="第一课",
        mode=QuizMode.CHAR_TO_PINYIN,
        result=ResultType.MASTERED
    )

    session.add_record(record1)
    session.add_record(record2)

    assert len(session.records) == 1
    assert session.records[0].result == ResultType.MASTERED


def test_quiz_session_get_summary():
    session = QuizSessionState(
        session_id="abc123",
        created_at=datetime.now(),
        total=20,
        lessons=["第一课"]
    )

    session.add_record(QuizRecord("春", "chūn", "第一课", QuizMode.CHAR_TO_PINYIN, ResultType.MASTERED))
    session.add_record(QuizRecord("来", "lái", "第一课", QuizMode.CHAR_TO_PINYIN, ResultType.FUZZY))
    session.add_record(QuizRecord("花", "huā", "第一课", QuizMode.CHAR_TO_PINYIN, ResultType.NOT_MASTERED))

    summary = session.get_summary()
    assert summary["total"] == 20
    assert summary["completed"] == 3
    assert summary["mastered"] == 1
    assert summary["fuzzy"] == 1
    assert summary["not_mastered"] == 1
