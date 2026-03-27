"""文本对齐器：使用 LCS 算法对齐页面文本与转录文本."""

import re
import logging
from difflib import SequenceMatcher
from typing import List, Tuple, Optional

from .models import PageText, WordTiming, PageTiming

logger = logging.getLogger(__name__)


class TextAligner:
    """将页面文本与转录时间戳对齐."""

    def __init__(self, min_ratio: float = 0.8):
        """初始化对齐器.

        Args:
            min_ratio: 最小对齐比例阈值
        """
        self.min_ratio = min_ratio

    def align(
        self,
        pages: List[PageText],
        word_timings: List[WordTiming]
    ) -> List[PageTiming]:
        """对齐页面与时间戳.

        使用序列对齐算法找到每页在转录文本中的位置，
        然后映射到对应的时间范围。
        """
        if not pages or not word_timings:
            logger.warning("Empty input")
            return []

        logger.info(f"Aligning {len(pages)} pages with {len(word_timings)} words")

        # 准备文本 - 将页面文本拆分为单词列表
        page_word_lists = [
            self._normalize_text(p.text).split() for p in pages
        ]
        words = [w.word.lower() for w in word_timings]

        # 使用 LCS 对齐检查整体匹配度
        full_page_text = ' '.join([' '.join(pl) for pl in page_word_lists])
        full_word_text = ' '.join(words)
        matcher = SequenceMatcher(None, full_page_text, full_word_text)
        match_ratio = matcher.ratio()
        logger.info(f"Alignment ratio: {match_ratio:.2%}")

        if match_ratio < self.min_ratio:
            logger.warning(f"Low alignment ratio: {match_ratio:.2%}")

        # 查找每页的单词索引边界
        boundaries = self._find_page_word_boundaries(page_word_lists, words)

        # 构建结果
        page_timings = []
        for page, (start_idx, end_idx) in zip(pages, boundaries):
            start_idx = max(0, min(start_idx, len(word_timings) - 1))
            end_idx = max(0, min(end_idx, len(word_timings) - 1))

            start_time = word_timings[start_idx].start
            end_time = word_timings[end_idx].end

            page_timings.append(PageTiming(
                page_num=page.page_num,
                start_time=round(start_time, 3),
                end_time=round(end_time, 3),
                text=page.text
            ))

        return page_timings

    def _normalize_text(self, text: str) -> str:
        """标准化文本."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _find_page_word_boundaries(
        self,
        page_word_lists: List[List[str]],
        words: List[str]
    ) -> List[Tuple[int, int]]:
        """查找每页在单词列表中的索引边界.

        Returns:
            List of (start_word_idx, end_word_idx) tuples
        """
        boundaries = []
        current_word_idx = 0

        for page_words in page_word_lists:
            if not page_words:
                boundaries.append((current_word_idx, current_word_idx))
                continue

            # 查找这一页的第一个单词匹配位置
            start_idx = self._find_word_sequence(page_words, words, current_word_idx)

            if start_idx is not None:
                end_idx = min(start_idx + len(page_words) - 1, len(words) - 1)
                boundaries.append((start_idx, end_idx))
                current_word_idx = end_idx + 1
            else:
                # 回退：按比例估算
                total_page_words = sum(len(pl) for pl in page_word_lists)
                ratio = len(page_words) / total_page_words if total_page_words > 0 else 0
                start_idx = int(current_word_idx)
                end_idx = int(current_word_idx + len(words) * ratio) - 1
                end_idx = max(start_idx, min(end_idx, len(words) - 1))
                boundaries.append((start_idx, end_idx))
                current_word_idx = end_idx + 1

        return boundaries

    def _find_word_sequence(
        self,
        page_words: List[str],
        words: List[str],
        start_pos: int
    ) -> Optional[int]:
        """在单词列表中查找页面单词序列的起始位置.

        Args:
            page_words: 页面的单词列表
            words: 完整的转录单词列表
            start_pos: 开始搜索的单词索引

        Returns:
            匹配的起始单词索引，未找到返回 None
        """
        if not page_words or not words:
            return None

        # 从 start_pos 开始搜索
        search_start = max(0, start_pos - 2)

        for i in range(search_start, len(words)):
            # 检查从位置 i 开始的单词序列是否匹配
            match = True
            for j, pw in enumerate(page_words):
                if i + j >= len(words):
                    match = False
                    break
                if words[i + j] != pw:
                    match = False
                    break

            if match:
                return i

        # 尝试只匹配第一个单词
        if page_words:
            first_word = page_words[0]
            for i in range(search_start, len(words)):
                if words[i] == first_word:
                    return i

        return None
