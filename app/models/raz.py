from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class RazPage:
    page: int
    pdf: str
    audio: str
    sentences: List[str]


@dataclass
class RazBook:
    id: str           # 全局唯一，格式：level-{x}/{dir_name}，如 level-a/the-big-red-barn
    title: str
    level: str
    pages: List[RazPage]
    video: Optional[str] = None


@dataclass
class RazConfig:
    current_level: str = "a"
    daily_mode: str = "manual"   # "manual" | "smart"
    daily_count: int = 10
    current_session: Optional[dict] = None  # {book_id, page, sentence_index}


@dataclass
class RazPracticeRecord:
    book_id: str
    book_title: str
    level: str
    page: int
    sentence: str
    score: int
    timestamp: datetime
