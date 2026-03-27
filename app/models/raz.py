from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class RazSentence:
    start: float      # 秒
    end: float        # 秒
    text: str
    page: int
    confidence: Optional[float] = None


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
    pdf: Optional[str] = None
    audio: Optional[str] = None
    video: Optional[str] = None
    cover: Optional[str] = None
    total_pages: int = 0
    sentences: List[RazSentence] = field(default_factory=list)
    # 旧格式兼容
    pages: List[RazPage] = field(default_factory=list)


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
