from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List

from app.models.character import ResultType


class EnglishQuizMode(str, Enum):
    """英语抽测模式"""
    AUDIO_TO_WORD = "audio_to_word"      # 听音选词
    WORD_TO_MEANING = "word_to_meaning"  # 看词选义
    MEANING_TO_WORD = "meaning_to_word"  # 看义选词


@dataclass
class EnglishWord:
    """英语单词数据模型"""
    word: str                           # 英文单词
    meaning: str                        # 中文释义
    phonetic: Optional[str] = None      # 音标
    example: Optional[str] = None       # 例句（英文）
    example_cn: Optional[str] = None    # 例句翻译
    lesson: str = ""                    # 所属单元
    semester: str = ""                  # 年级/册别
    image_keyword: Optional[str] = None # 图片搜索关键词
    mastery_status: Optional[str] = field(default=None, repr=False)

    def to_dict(self, include_status: bool = False) -> dict:
        """转换为字典"""
        result = {
            "word": self.word,
            "meaning": self.meaning,
            "phonetic": self.phonetic,
            "example": self.example,
            "example_cn": self.example_cn,
            "lesson": self.lesson,
            "semester": self.semester,
            "image_keyword": self.image_keyword,
        }
        if include_status and self.mastery_status:
            result["mastery_status"] = self.mastery_status
        return result


@dataclass
class EnglishQuizRecord:
    """英语评测记录"""
    word: str
    meaning: str
    lesson: str
    mode: EnglishQuizMode
    result: ResultType
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EnglishQuizSessionState:
    """英语抽测会话状态"""
    session_id: str
    created_at: datetime
    total: int
    lessons: List[str]
    current_index: int = 0
    words: List[dict] = field(default_factory=list)
    records: List[EnglishQuizRecord] = field(default_factory=list)
    completed: bool = False

    def add_record(self, record: EnglishQuizRecord):
        """添加评测记录"""
        for i, r in enumerate(self.records):
            if r.word == record.word and r.lesson == record.lesson:
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
