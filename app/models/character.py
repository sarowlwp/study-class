from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class QuizMode(str, Enum):
    CHAR_TO_PINYIN = "char_to_pinyin"
    PINYIN_TO_CHAR = "pinyin_to_char"


class ResultType(str, Enum):
    MASTERED = "mastered"
    FUZZY = "fuzzy"
    NOT_MASTERED = "not_mastered"


@dataclass
class Character:
    """汉字数据模型"""
    char: str
    pinyin: str
    meaning: str
    example: str
    lesson: str
    semester: str
    mastery_status: Optional[str] = field(default=None, repr=False)

    def to_dict(self, include_status: bool = True) -> dict:
        """转换为字典"""
        result = {
            "char": self.char,
            "pinyin": self.pinyin,
            "meaning": self.meaning,
            "example": self.example,
            "lesson": self.lesson,
            "semester": self.semester,
        }
        if include_status and self.mastery_status:
            result["mastery_status"] = self.mastery_status
        return result
