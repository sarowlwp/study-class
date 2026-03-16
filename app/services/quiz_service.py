import random
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from app.models.character import Character, QuizMode, ResultType
from app.models.record import QuizRecord, QuizSessionState
from app.services.character_service import CharacterService
from app.services.record_service import RecordService


class QuizService:
    """抽测服务"""

    _sessions: Dict[str, QuizSessionState] = {}

    def __init__(self, character_service: CharacterService, record_service: RecordService):
        self.char_service = character_service
        self.record_service = record_service

    def generate_quiz(
        self,
        semester_id: str,
        lessons: List[str],
        count: int,
        mode_mix: float = 0.5
    ) -> QuizSessionState:
        """Generate a quiz session"""
        all_chars = self.char_service.get_characters(semester_id, lessons)

        if not all_chars:
            raise ValueError("No characters available")

        # Group by mastery status
        priority_groups = {
            "not_mastered": [],
            "fuzzy": [],
            "new": [],
            "mastered": []
        }

        for char in all_chars:
            status = self.record_service.get_mastery_status(char.char, char.lesson)
            char.mastery_status = status
            priority_groups[status].append(char)

        # Select by priority
        selected = []
        priorities = ["not_mastered", "fuzzy", "new", "mastered"]

        for priority in priorities:
            chars = priority_groups[priority]
            random.shuffle(chars)
            needed = count - len(selected)
            if needed <= 0:
                break
            selected.extend(chars[:needed])

        # Assign quiz modes
        quiz_items = []
        for char in selected:
            mode = QuizMode.CHAR_TO_PINYIN if random.random() < mode_mix else QuizMode.PINYIN_TO_CHAR
            quiz_items.append({
                "char": char.char,
                "pinyin": char.pinyin,
                "meaning": char.meaning,
                "example": char.example,
                "lesson": char.lesson,
                "mode": mode.value
            })

        session = QuizSessionState(
            session_id=str(uuid.uuid4())[:12],
            created_at=datetime.now(),
            total=len(quiz_items),
            lessons=lessons,
            characters=quiz_items
        )

        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[QuizSessionState]:
        """Get session state"""
        return self._sessions.get(session_id)

    def submit_result(self, session_id: str, index: int, result: ResultType) -> bool:
        """Submit quiz result for a character"""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError("Session not found or expired")

        if index < 0 or index >= len(session.characters):
            raise ValueError("Invalid index")

        char_data = session.characters[index]
        record = QuizRecord(
            char=char_data["char"],
            pinyin=char_data["pinyin"],
            lesson=char_data["lesson"],
            mode=QuizMode(char_data["mode"]),
            result=result
        )

        session.add_record(record)
        session.current_index = max(session.current_index, index + 1)
        return True

    def finish_quiz(self, session_id: str) -> Dict:
        """Finish quiz and save records"""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError("Session not found or expired")

        session.completed = True
        self.record_service.save_records(
            session.created_at.date(),
            session.records
        )
        return session.get_summary()
