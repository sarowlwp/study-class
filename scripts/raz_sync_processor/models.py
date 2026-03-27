"""数据模型定义."""

from dataclasses import dataclass


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
