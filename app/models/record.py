from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from app.models.character import QuizMode, ResultType


@dataclass
class QuizRecord:
    """单次评测记录"""
    char: str
    pinyin: str
    lesson: str
    mode: QuizMode
    result: ResultType
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class QuizSessionState:
    """抽测会话状态"""
    session_id: str
    created_at: datetime
    total: int
    lessons: List[str]
    current_index: int = 0
    characters: List[dict] = field(default_factory=list)
    records: List[QuizRecord] = field(default_factory=list)
    completed: bool = False

    def add_record(self, record: QuizRecord):
        """添加评测记录"""
        # Update existing record if char already exists
        for i, r in enumerate(self.records):
            if r.char == record.char:
                self.records[i] = record
                return
        self.records.append(record)

    def get_summary(self) -> dict:
        """获取评测摘要"""
        counts = {"mastered": 0, "fuzzy": 0, "not_mastered": 0}
        for r in self.records:
            counts[r.result.value] += 1
        return {
            "total": self.total,
            "completed": len(self.records),
            **counts
        }
