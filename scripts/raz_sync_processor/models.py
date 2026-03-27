"""数据模型定义."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PageText:
    """单页文本."""
    page_num: int
    text: str


@dataclass
class WordTiming:
    """单词时间戳."""
    word: str
    start: float
    end: float


@dataclass
class PageTiming:
    """页面时间范围."""
    page_num: int
    start_time: float
    end_time: float
    text: str


@dataclass
class BookConfig:
    """书籍配置."""
    id: str
    title: str
    level: str
    pdf: str
    audio: str
    page_count: int
    pages: List[PageTiming] = field(default_factory=list)


@dataclass
class WordTimingWithLocation(WordTiming):
    """带位置信息的单词时间戳."""
    page: int
    char_start: int
    char_end: int
