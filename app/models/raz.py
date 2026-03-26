from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import re


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
    cover: Optional[str] = None  # 新增: 封面文件名

    @property
    def directory_name(self) -> str:
        """返回书籍目录名，用于构建资源路径。

        id 格式为 level-{x}/{dir_name}，如 level-a/a-fish-sees
        """
        return self.id.split("/")[-1] if "/" in self.id else self.id

    def validate_cover(self) -> bool:
        """校验 cover 字段是否为安全的文件名。

        仅允许：字母、数字、下划线、连字符、点
        扩展名白名单：jpg, jpeg, png, gif, webp
        """
        if not self.cover:
            return True
        return bool(re.match(
            r"^[a-zA-Z0-9_\-\.]+\.(jpg|jpeg|png|gif|webp)$",
            self.cover,
            re.IGNORECASE
        ))


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
