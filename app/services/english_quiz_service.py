import random
import uuid
from datetime import datetime, date
from typing import Dict, List, Optional

from app.models.english_word import EnglishWord, EnglishQuizMode, EnglishQuizRecord, EnglishQuizSessionState
from app.models.character import ResultType
from app.services.english_service import EnglishService
from app.services.record_service import RecordService


class EnglishQuizService:
    """英语抽测服务"""

    _sessions: Dict[str, EnglishQuizSessionState] = {}

    def __init__(self, english_service: EnglishService, record_service: RecordService):
        self.english_service = english_service
        self.record_service = record_service

    def _cleanup_expired_sessions(self):
        """清理过期会话（24小时）"""
        now = datetime.now()
        expired = [
            sid for sid, session in self._sessions.items()
            if (now - session.created_at).total_seconds() > 86400
        ]
        for sid in expired:
            del self._sessions[sid]

    def generate_quiz(
        self,
        semester_id: str,
        lessons: List[str],
        count: int,
        mode_mix: float = 0.33
    ) -> EnglishQuizSessionState:
        """生成抽测会话"""
        self._cleanup_expired_sessions()

        all_words = self.english_service.get_words(semester_id, lessons)

        if not all_words:
            raise ValueError("No words available")

        # Group by mastery status
        priority_groups = {
            "not_mastered": [],
            "fuzzy": [],
            "new": [],
            "mastered": []
        }

        for word in all_words:
            status = self.record_service.get_english_mastery_status(word.word, word.lesson)
            word.mastery_status = status
            priority_groups[status].append(word)

        # Select by priority
        selected = []
        priorities = ["not_mastered", "fuzzy", "new", "mastered"]

        for priority in priorities:
            words = priority_groups[priority]
            random.shuffle(words)
            needed = count - len(selected)
            if needed <= 0:
                break
            selected.extend(words[:needed])

        # Assign quiz modes
        quiz_items = []
        for word in selected:
            rand = random.random()
            if rand < mode_mix:
                mode = EnglishQuizMode.AUDIO_TO_WORD
            elif rand < mode_mix * 2:
                mode = EnglishQuizMode.WORD_TO_MEANING
            else:
                mode = EnglishQuizMode.MEANING_TO_WORD

            quiz_items.append({
                "word": word.word,
                "meaning": word.meaning,
                "phonetic": word.phonetic,
                "example": word.example,
                "example_cn": word.example_cn,
                "lesson": word.lesson,
                "mode": mode.value,
                "options": self._generate_options(word, all_words, min(4, len(all_words)))
            })

        session = EnglishQuizSessionState(
            session_id=str(uuid.uuid4())[:12],
            created_at=datetime.now(),
            total=len(quiz_items),
            lessons=lessons,
            words=quiz_items
        )

        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[EnglishQuizSessionState]:
        """获取会话状态"""
        self._cleanup_expired_sessions()
        return self._sessions.get(session_id)

    def submit_answer(self, session_id: str, index: int, answer: str) -> Dict:
        """提交答案，返回是否正确及正确答案"""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError("Session not found or expired")

        if index < 0 or index >= len(session.words):
            raise ValueError("Invalid index")

        word_data = session.words[index]
        correct_answer = word_data["word"]
        is_correct = answer.lower() == correct_answer.lower()

        # Record result
        result = ResultType.MASTERED if is_correct else ResultType.NOT_MASTERED
        record = EnglishQuizRecord(
            word=word_data["word"],
            meaning=word_data["meaning"],
            lesson=word_data["lesson"],
            mode=EnglishQuizMode(word_data["mode"]),
            result=result
        )
        session.add_record(record)
        session.current_index = max(session.current_index, index + 1)

        return {
            "is_correct": is_correct,
            "correct_answer": correct_answer,
            "your_answer": answer,
            "word": word_data
        }

    def finish_quiz(self, session_id: str) -> Dict:
        """完成抽测，保存记录"""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError("Session not found or expired")

        session.completed = True
        self.record_service.save_english_records(
            session.created_at.date(),
            session.records
        )
        return session.get_summary()

    def _generate_options(
        self,
        correct: EnglishWord,
        all_words: List[EnglishWord],
        option_count: int = 4
    ) -> List[Dict]:
        """生成选项，包含正确答案和干扰项"""
        # Filter out correct answer from distractor candidates
        distractors = [
            w for w in all_words
            if w.word != correct.word and w.meaning != correct.meaning
        ]

        # Select distractors
        selected_count = min(option_count - 1, len(distractors))
        selected = random.sample(distractors, selected_count) if distractors else []

        # Build options list
        options = [
            {"word": correct.word, "meaning": correct.meaning, "phonetic": correct.phonetic, "is_correct": True}
        ]
        for word in selected:
            options.append({
                "word": word.word,
                "meaning": word.meaning,
                "phonetic": word.phonetic,
                "is_correct": False
            })

        # Shuffle
        random.shuffle(options)
        return options
