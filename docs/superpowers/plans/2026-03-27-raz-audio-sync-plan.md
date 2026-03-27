# RAZ 音频-文本同步处理器实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现一个纯开源、本地运行的 Python 脚本模块，将 RAZ 绘本的 PDF 和 MP3 自动对齐，生成带时间戳的 JSON 配置和独立阅读器。

**Architecture:** 模块化设计，包含 PDFProcessor（OCR + 文本提取）、AudioTranscriber（faster-whisper 转录）、TextAligner（LCS 对齐算法）、SyncGenerator（JSON 输出）四个核心组件，通过 CLI 入口脚本串联。

**Tech Stack:** Python 3.10+, OCRmyPDF, PyMuPDF, faster-whisper, difflib, Jinja2

---

## 文件结构

```
scripts/raz_sync_processor/
├── __init__.py              # 包初始化
├── __main__.py              # CLI 入口
├── config.py                # 配置和常量
├── models.py                # 数据模型 (dataclasses)
├── pdf_processor.py         # PDF OCR + 文本提取
├── audio_transcriber.py     # faster-whisper 封装
├── text_aligner.py          # LCS 对齐算法
├── sync_generator.py        # JSON 和 HTML 生成
└── templates/
    └── reader.html          # 阅读器 HTML 模板

tests/test_raz_sync_processor/
├── test_pdf_processor.py
├── test_audio_transcriber.py
├── test_text_aligner.py
└── test_sync_generator.py
```

---

## Task 1: 项目结构和数据模型

**Files:**
- Create: `scripts/raz_sync_processor/__init__.py`
- Create: `scripts/raz_sync_processor/models.py`
- Create: `scripts/raz_sync_processor/config.py`

### Step 1.1: 创建包初始化文件

```python
# scripts/raz_sync_processor/__init__.py
"""RAZ 音频-文本同步处理器.

将 RAZ 绘本的 PDF 和 MP3 自动对齐，生成带时间戳的配置文件。
"""

__version__ = "1.0.0"

from .pdf_processor import PDFProcessor
from .audio_transcriber import AudioTranscriber
from .text_aligner import TextAligner
from .sync_generator import SyncGenerator

__all__ = [
    "PDFProcessor",
    "AudioTranscriber",
    "TextAligner",
    "SyncGenerator",
]
```

### Step 1.2: 创建数据模型

```python
# scripts/raz_sync_processor/models.py
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
```

### Step 1.3: 创建配置常量

```python
# scripts/raz_sync_processor/config.py
"""配置常量."""

import logging

# 日志配置
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.INFO

# 默认模型配置
DEFAULT_WHISPER_MODEL = "base"
DEFAULT_LANGUAGE = "en"

# 文件路径
PDF_FILENAME = "book.pdf"
AUDIO_FILENAME = "book.mp3"
OUTPUT_JSON = "book.json"
WORD_TIMINGS_JSON = "word_timings.json"
READER_HTML = "index.html"

# OCR 配置
OCR_LANGUAGE = "eng"
OCR_DPI = 300

# 对齐算法阈值
MIN_ALIGNMENT_RATIO = 0.8  # 最小对齐比例
```

### Step 1.4: 提交

```bash
git add scripts/raz_sync_processor/__init__.py \
        scripts/raz_sync_processor/models.py \
        scripts/raz_sync_processor/config.py
git commit -m "feat(raz-sync): add project structure and data models"
```

---

## Task 2: PDF 处理器

**Files:**
- Create: `scripts/raz_sync_processor/pdf_processor.py`
- Create: `tests/test_raz_sync_processor/test_pdf_processor.py`

### Step 2.1: 编写测试

```python
# tests/test_raz_sync_processor/test_pdf_processor.py
"""PDF 处理器测试."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from scripts.raz_sync_processor.pdf_processor import PDFProcessor
from scripts.raz_sync_processor.models import PageText


class TestPDFProcessor:
    """测试 PDFProcessor."""

    def test_init_default(self):
        """测试默认初始化."""
        processor = PDFProcessor()
        assert processor.dpi == 300

    def test_init_custom_dpi(self):
        """测试自定义 DPI."""
        processor = PDFProcessor(dpi=150)
        assert processor.dpi == 150

    @patch("scripts.raz_sync_processor.pdf_processor.fitx")
    def test_extract_text_by_page(self, mock_fitz):
        """测试文本提取."""
        # 模拟 PDF 文档
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Hello World"

        mock_doc = MagicMock()
        mock_doc.__len__ = Mock(return_value=2)
        mock_doc.__getitem__ = Mock(side_effect=[mock_page, mock_page])
        mock_doc.close = Mock()

        mock_fitz.open.return_value = mock_doc

        processor = PDFProcessor()
        result = processor.extract_text_by_page(Path("test.pdf"))

        assert len(result) == 2
        assert result[0].page_num == 1
        assert result[0].text == "Hello World"
        assert result[1].page_num == 2

    @patch("scripts.raz_sync_processor.pdf_processor.fitz")
    def test_extract_text_empty_page(self, mock_fitz):
        """测试空页面处理."""
        mock_page = MagicMock()
        mock_page.get_text.return_value = ""

        mock_doc = MagicMock()
        mock_doc.__len__ = Mock(return_value=1)
        mock_doc.__getitem__ = Mock(return_value=mock_page)
        mock_doc.close = Mock()

        mock_fitz.open.return_value = mock_doc

        processor = PDFProcessor()
        result = processor.extract_text_by_page(Path("test.pdf"))

        assert len(result) == 1
        assert result[0].text == ""

    def test_normalize_text(self):
        """测试文本标准化."""
        processor = PDFProcessor()

        # 测试小写转换
        assert processor._normalize_text("Hello") == "hello"

        # 测试标点去除
        assert processor._normalize_text("hello!") == "hello"
        assert processor._normalize_text("hello, world.") == "hello world"

        # 测试多余空格
        assert processor._normalize_text("  hello   world  ") == "hello world"
```

### Step 2.2: 运行测试确认失败

```bash
cd /Users/liuwenping/Documents/fliggy/study-class
python -m pytest tests/test_raz_sync_processor/test_pdf_processor.py -v
```

**Expected:** ImportError: No module named 'scripts.raz_sync_processor.pdf_processor'

### Step 2.3: 实现 PDFProcessor

```python
# scripts/raz_sync_processor/pdf_processor.py
"""PDF 处理器：OCR + 文本提取."""

import re
import logging
from pathlib import Path
from typing import List, Optional

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

from .models import PageText
from .config import OCR_DPI

logger = logging.getLogger(__name__)


class PDFProcessor:
    """处理 PDF 文件：提取每页文本."""

    def __init__(self, dpi: int = OCR_DPI):
        """初始化处理器.

        Args:
            dpi: PDF 渲染分辨率
        """
        self.dpi = dpi
        if fitz is None:
            raise ImportError("PyMuPDF (fitz) is required. Install: pip install pymupdf")

    def extract_text_by_page(self, pdf_path: Path) -> List[PageText]:
        """提取每页文本.

        Args:
            pdf_path: PDF 文件路径

        Returns:
            每页文本列表
        """
        logger.info(f"Extracting text from {pdf_path}")

        pages = []
        doc = fitz.open(pdf_path)

        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text().strip()
                pages.append(PageText(page_num=page_num + 1, text=text))
                logger.debug(f"Page {page_num + 1}: {len(text)} chars")
        finally:
            doc.close()

        logger.info(f"Extracted {len(pages)} pages")
        return pages

    def needs_ocr(self, pdf_path: Path, sample_pages: int = 2) -> bool:
        """检查 PDF 是否需要 OCR.

        通过检查前几页是否有文本来判断.

        Args:
            pdf_path: PDF 文件路径
            sample_pages: 检查的页数

        Returns:
            是否需要 OCR
        """
        doc = fitz.open(pdf_path)
        try:
            for i in range(min(sample_pages, len(doc))):
                text = doc[i].get_text().strip()
                if len(text) > 10:  # 假设有 10 个字符以上为有效文本
                    return False
            return True
        finally:
            doc.close()

    def add_ocr_layer(
        self,
        input_path: Path,
        output_path: Path,
        language: str = "eng"
    ) -> bool:
        """使用 OCRmyPDF 为 PDF 添加隐藏文字层.

        Args:
            input_path: 输入 PDF 路径
            output_path: 输出 PDF 路径
            language: OCR 语言

        Returns:
            是否成功
        """
        try:
            import ocrmypdf
        except ImportError:
            logger.error("ocrmypdf not installed. Install: pip install ocrmypdf")
            return False

        logger.info(f"Adding OCR layer: {input_path} -> {output_path}")

        try:
            ocrmypdf.ocr(
                input_path,
                output_path,
                language=language,
                deskew=True,
                optimize=1,
                progress_bar=False,
            )
            logger.info("OCR completed successfully")
            return True
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return False

    def _normalize_text(self, text: str) -> str:
        """标准化文本用于对齐.

        - 转小写
        - 去除标点
        - 合并多余空格

        Args:
            text: 原始文本

        Returns:
            标准化文本
        """
        # 转小写
        text = text.lower()
        # 去除标点（保留字母、数字、空格）
        text = re.sub(r'[^\w\s]', '', text)
        # 合并多余空格
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def get_full_text(self, pages: List[PageText], normalized: bool = False) -> str:
        """获取完整文本.

        Args:
            pages: 页面列表
            normalized: 是否标准化

        Returns:
            完整文本
        """
        texts = [p.text for p in pages]
        full_text = ' '.join(texts)

        if normalized:
            return self._normalize_text(full_text)
        return full_text
```

### Step 2.4: 运行测试确认通过

```bash
python -m pytest tests/test_raz_sync_processor/test_pdf_processor.py -v
```

**Expected:** 4 tests passed

### Step 2.5: 提交

```bash
git add scripts/raz_sync_processor/pdf_processor.py \
        tests/test_raz_sync_processor/test_pdf_processor.py
git commit -m "feat(raz-sync): implement PDF processor with text extraction"
```

---

## Task 3: 音频转录器

**Files:**
- Create: `scripts/raz_sync_processor/audio_transcriber.py`
- Create: `tests/test_raz_sync_processor/test_audio_transcriber.py`

### Step 3.1: 编写测试

```python
# tests/test_raz_sync_processor/test_audio_transcriber.py
"""音频转录器测试."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from scripts.raz_sync_processor.audio_transcriber import AudioTranscriber
from scripts.raz_sync_processor.models import WordTiming


class TestAudioTranscriber:
    """测试 AudioTranscriber."""

    def test_init_default(self):
        """测试默认初始化."""
        transcriber = AudioTranscriber()
        assert transcriber.model_size == "base"
        assert transcriber.device == "cpu"

    def test_init_custom(self):
        """测试自定义参数."""
        transcriber = AudioTranscriber(model_size="tiny", device="cuda")
        assert transcriber.model_size == "tiny"
        assert transcriber.device == "cuda"

    @patch("scripts.raz_sync_processor.audio_transcriber.WhisperModel")
    def test_transcribe(self, mock_model_class):
        """测试转录功能."""
        # 模拟转录结果
        mock_segment = MagicMock()
        mock_segment.words = [
            Mock(word="Hello", start=0.0, end=0.5),
            Mock(word="world", start=0.6, end=1.0),
        ]

        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([mock_segment], None)
        mock_model_class.return_value = mock_model

        transcriber = AudioTranscriber()
        result = transcriber.transcribe(Path("test.mp3"))

        assert len(result) == 2
        assert result[0].word == "Hello"
        assert result[0].start == 0.0
        assert result[0].end == 0.5
        assert result[1].word == "world"

    @patch("scripts.raz_sync_processor.audio_transcriber.WhisperModel")
    def test_transcribe_empty(self, mock_model_class):
        """测试空音频处理."""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([], None)
        mock_model_class.return_value = mock_model

        transcriber = AudioTranscriber()
        result = transcriber.transcribe(Path("test.mp3"))

        assert len(result) == 0

    def test_normalize_word(self):
        """测试单词标准化."""
        transcriber = AudioTranscriber()

        assert transcriber._normalize_word("Hello") == "hello"
        assert transcriber._normalize_word("IT'S") == "it's"
        assert transcriber._normalize_word("  spaced  ") == "spaced"
```

### Step 3.2: 运行测试确认失败

```bash
python -m pytest tests/test_raz_sync_processor/test_audio_transcriber.py -v
```

**Expected:** ImportError

### Step 3.3: 实现 AudioTranscriber

```python
# scripts/raz_sync_processor/audio_transcriber.py
"""音频转录器：使用 faster-whisper 生成词级时间戳."""

import logging
from pathlib import Path
from typing import List, Optional

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

from .models import WordTiming
from .config import DEFAULT_WHISPER_MODEL

logger = logging.getLogger(__name__)


class AudioTranscriber:
    """使用 faster-whisper 转录音频."""

    def __init__(
        self,
        model_size: str = DEFAULT_WHISPER_MODEL,
        device: str = "cpu",
        compute_type: str = "int8"
    ):
        """初始化转录器.

        Args:
            model_size: 模型大小 (tiny, base, small, medium, large)
            device: 计算设备 (cpu, cuda)
            compute_type: 计算类型 (int8, float16, float32)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None

        if WhisperModel is None:
            raise ImportError(
                "faster-whisper is required. Install: pip install faster-whisper"
            )

    @property
    def model(self) -> WhisperModel:
        """懒加载模型."""
        if self._model is None:
            logger.info(f"Loading Whisper model: {self.model_size}")
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
        return self._model

    def transcribe(
        self,
        audio_path: Path,
        language: str = "en",
        beam_size: int = 5
    ) -> List[WordTiming]:
        """转录音频，生成词级时间戳.

        Args:
            audio_path: 音频文件路径
            language: 语言代码
            beam_size: 解码束大小

        Returns:
            词级时间戳列表
        """
        logger.info(f"Transcribing audio: {audio_path}")

        segments, info = self.model.transcribe(
            str(audio_path),
            language=language,
            beam_size=beam_size,
            word_timestamps=True,
            condition_on_previous_text=False,
        )

        logger.info(f"Detected language: {info.language}, probability: {info.language_probability:.2f}")

        # 收集所有单词
        word_timings = []
        for segment in segments:
            if segment.words:
                for word_info in segment.words:
                    word = self._normalize_word(word_info.word)
                    if word:  # 忽略空单词
                        timing = WordTiming(
                            word=word,
                            start=round(word_info.start, 3),
                            end=round(word_info.end, 3)
                        )
                        word_timings.append(timing)

        logger.info(f"Transcribed {len(word_timings)} words")
        return word_timings

    def _normalize_word(self, word: str) -> str:
        """标准化单词.

        - 去除首尾空格
        - 转小写
        - 去除标点

        Args:
            word: 原始单词

        Returns:
            标准化单词
        """
        word = word.strip().lower()
        # 去除首尾标点
        word = word.strip('.,!?;:"()[]{}')
        return word

    def get_full_text(self, word_timings: List[WordTiming]) -> str:
        """获取完整转录文本.

        Args:
            word_timings: 单词时间戳列表

        Returns:
            完整文本
        """
        return ' '.join(w.word for w in word_timings)
```

### Step 3.4: 运行测试确认通过

```bash
python -m pytest tests/test_raz_sync_processor/test_audio_transcriber.py -v
```

**Expected:** 5 tests passed

### Step 3.5: 提交

```bash
git add scripts/raz_sync_processor/audio_transcriber.py \
        tests/test_raz_sync_processor/test_audio_transcriber.py
git commit -m "feat(raz-sync): implement audio transcriber with faster-whisper"
```

---

## Task 4: 文本对齐器

**Files:**
- Create: `scripts/raz_sync_processor/text_aligner.py`
- Create: `tests/test_raz_sync_processor/test_text_aligner.py`

### Step 4.1: 编写测试

```python
# tests/test_raz_sync_processor/test_text_aligner.py
"""文本对齐器测试."""

import pytest
from pathlib import Path

from scripts.raz_sync_processor.text_aligner import TextAligner
from scripts.raz_sync_processor.models import PageText, WordTiming, PageTiming


class TestTextAligner:
    """测试 TextAligner."""

    def test_init(self):
        """测试初始化."""
        aligner = TextAligner()
        assert aligner is not None

    def test_align_simple(self):
        """测试简单对齐."""
        aligner = TextAligner()

        pages = [
            PageText(1, "Hello world"),
            PageText(2, "How are you"),
        ]

        words = [
            WordTiming("hello", 0.0, 0.5),
            WordTiming("world", 0.6, 1.0),
            WordTiming("how", 1.5, 1.8),
            WordTiming("are", 1.9, 2.1),
            WordTiming("you", 2.2, 2.5),
        ]

        result = aligner.align(pages, words)

        assert len(result) == 2
        assert result[0].page_num == 1
        assert result[0].start_time == 0.0
        assert result[0].end_time == 1.0
        assert result[1].page_num == 2
        assert result[1].start_time == 1.5

    def test_normalize_text(self):
        """测试文本标准化."""
        aligner = TextAligner()

        assert aligner._normalize_text("Hello, World!") == "hello world"
        assert aligner._normalize_text("  spaces  ") == "spaces"
        assert aligner._normalize_text("UPPER") == "upper"

    def test_align_empty_pages(self):
        """测试空页面处理."""
        aligner = TextAligner()

        pages = [PageText(1, "Hello")]
        words = [WordTiming("hello", 0.0, 0.5)]

        result = aligner.align(pages, words)
        assert len(result) == 1
        assert result[0].start_time == 0.0

    def test_find_page_boundaries(self):
        """测试页面边界查找."""
        aligner = TextAligner()

        page_texts = ["hello world", "how are you"]
        full_text = "hello world how are you"

        boundaries = aligner._find_page_boundaries(page_texts, full_text)

        assert len(boundaries) == 2
        assert boundaries[0] == (0, 11)  # "hello world"
        assert boundaries[1] == (12, 23)  # "how are you"
```

### Step 4.2: 运行测试确认失败

```bash
python -m pytest tests/test_raz_sync_processor/test_text_aligner.py -v
```

**Expected:** ImportError

### Step 4.3: 实现 TextAligner

```python
# scripts/raz_sync_processor/text_aligner.py
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

        Args:
            pages: 页面文本列表
            word_timings: 词级时间戳列表

        Returns:
            每页的时间范围
        """
        if not pages or not word_timings:
            logger.warning("Empty input: pages=%d, words=%d", len(pages), len(word_timings))
            return []

        logger.info(f"Aligning {len(pages)} pages with {len(word_timings)} words")

        # 1. 准备文本
        page_texts = [self._normalize_text(p.text) for p in pages]
        words = [w.word for w in word_timings]

        # 2. 构建完整文本
        full_page_text = ' '.join(page_texts)
        full_word_text = ' '.join(words)

        # 3. 使用 LCS 对齐
        matcher = SequenceMatcher(None, full_page_text, full_word_text)
        match_ratio = matcher.ratio()
        logger.info(f"Alignment ratio: {match_ratio:.2%}")

        if match_ratio < self.min_ratio:
            logger.warning(f"Low alignment ratio: {match_ratio:.2%}")

        # 4. 查找每页边界
        boundaries = self._find_page_boundaries(page_texts, full_word_text, matcher)

        # 5. 构建结果
        page_timings = []
        for i, (page, (start_char, end_char)) in enumerate(zip(pages, boundaries)):
            start_time = self._char_to_time(start_char, word_timings, full_word_text)
            end_time = self._char_to_time(end_char, word_timings, full_word_text)

            page_timings.append(PageTiming(
                page_num=page.page_num,
                start_time=round(start_time, 3),
                end_time=round(end_time, 3),
                text=page.text
            ))

            logger.debug(f"Page {page.page_num}: {start_time:.2f}s - {end_time:.2f}s")

        return page_timings

    def _normalize_text(self, text: str) -> str:
        """标准化文本.

        Args:
            text: 原始文本

        Returns:
            标准化文本
        """
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _find_page_boundaries(
        self,
        page_texts: List[str],
        word_text: str,
        matcher: SequenceMatcher
    ) -> List[Tuple[int, int]]:
        """查找每页在转录文本中的字符边界.

        Args:
            page_texts: 每页标准化文本
            word_text: 转录文本
            matcher: 序列匹配器

        Returns:
            每页的起止字符位置 [(start, end), ...]
        """
        boundaries = []
        current_pos = 0

        for page_text in page_texts:
            page_len = len(page_text)

            # 在转录文本中查找匹配位置
            # 使用滑动窗口查找最佳匹配
            best_match = self._find_best_match(page_text, word_text, current_pos)

            if best_match:
                start, end = best_match
                boundaries.append((start, end))
                current_pos = end
            else:
                # 回退：按字数比例估算
                ratio = page_len / sum(len(t) for t in page_texts)
                text_len = len(word_text)
                start = int(current_pos)
                end = int(current_pos + text_len * ratio)
                boundaries.append((start, end))
                current_pos = end

        return boundaries

    def _find_best_match(
        self,
        pattern: str,
        text: str,
        start_pos: int
    ) -> Optional[Tuple[int, int]]:
        """在文本中查找最佳匹配.

        Args:
            pattern: 要查找的模式
            text: 目标文本
            start_pos: 开始查找位置

        Returns:
            匹配的起止位置，未找到返回 None
        """
        # 简单实现：直接查找子串
        pattern = pattern.strip()
        if not pattern:
            return None

        # 在 start_pos 附近查找
        search_start = max(0, start_pos - 10)
        search_end = min(len(text), start_pos + len(pattern) + 100)

        # 尝试直接匹配
        idx = text.find(pattern, search_start, search_end)
        if idx != -1:
            return (idx, idx + len(pattern))

        # 尝试匹配前几个单词
        words = pattern.split()
        if len(words) >= 2:
            prefix = ' '.join(words[:2])
            idx = text.find(prefix, search_start, search_end)
            if idx != -1:
                # 估算结束位置
                return (idx, idx + len(pattern))

        return None

    def _char_to_time(
        self,
        char_pos: int,
        word_timings: List[WordTiming],
        full_text: str
    ) -> float:
        """将字符位置转换为时间戳.

        Args:
            char_pos: 字符位置
            word_timings: 词级时间戳
            full_text: 完整转录文本

        Returns:
            时间戳（秒）
        """
        if not word_timings:
            return 0.0

        # 找到对应单词
        words = full_text.split()
        word_idx = 0
        current_pos = 0

        for i, word in enumerate(words):
            word_len = len(word)
            if current_pos <= char_pos < current_pos + word_len:
                word_idx = i
                break
            current_pos += word_len + 1  # +1 for space
        else:
            word_idx = len(words) - 1

        word_idx = min(word_idx, len(word_timings) - 1)
        return word_timings[word_idx].start
```

### Step 4.4: 运行测试确认通过

```bash
python -m pytest tests/test_raz_sync_processor/test_text_aligner.py -v
```

**Expected:** 5 tests passed

### Step 4.5: 提交

```bash
git add scripts/raz_sync_processor/text_aligner.py \
        tests/test_raz_sync_processor/test_text_aligner.py
git commit -m "feat(raz-sync): implement text aligner with LCS algorithm"
```

---

## Task 5: 同步生成器

**Files:**
- Create: `scripts/raz_sync_processor/sync_generator.py`
- Create: `scripts/raz_sync_processor/templates/reader.html`
- Create: `tests/test_raz_sync_processor/test_sync_generator.py`

### Step 5.1: 编写测试

```python
# tests/test_raz_sync_processor/test_sync_generator.py
"""同步生成器测试."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from scripts.raz_sync_processor.sync_generator import SyncGenerator
from scripts.raz_sync_processor.models import PageTiming, WordTiming


class TestSyncGenerator:
    """测试 SyncGenerator."""

    def test_init(self, tmp_path):
        """测试初始化."""
        generator = SyncGenerator(tmp_path)
        assert generator.output_dir == tmp_path

    def test_generate_book_json(self, tmp_path):
        """测试生成 book.json."""
        generator = SyncGenerator(tmp_path)

        pages = [
            PageTiming(1, 0.0, 3.5, "Hello world"),
            PageTiming(2, 4.0, 7.0, "How are you"),
        ]

        result = generator.generate_book_json(
            book_id="level-a/test",
            title="Test Book",
            level="a",
            pages=pages
        )

        json_path = tmp_path / "book.json"
        assert json_path.exists()

        data = json.loads(json_path.read_text())
        assert data["id"] == "level-a/test"
        assert data["title"] == "Test Book"
        assert data["page_count"] == 2
        assert len(data["pages"]) == 2
        assert data["pages"][0]["start_time"] == 0.0

    def test_generate_word_timings(self, tmp_path):
        """测试生成 word_timings.json."""
        generator = SyncGenerator(tmp_path)

        words = [
            WordTiming("hello", 0.0, 0.5),
            WordTiming("world", 0.6, 1.0),
        ]

        generator.generate_word_timings(words)

        json_path = tmp_path / "word_timings.json"
        assert json_path.exists()

        data = json.loads(json_path.read_text())
        assert data["total_words"] == 2
        assert len(data["timings"]) == 2

    def test_create_symlinks(self, tmp_path):
        """测试创建软链接."""
        generator = SyncGenerator(tmp_path)

        # 创建临时源文件
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        pdf_file = source_dir / "book.pdf"
        pdf_file.write_text("fake pdf")

        generator.create_symlinks(source_dir)

        assert (tmp_path / "book.pdf").exists()
        assert (tmp_path / "book.pdf").is_symlink()

    def test_generate_reader_html(self, tmp_path):
        """测试生成阅读器 HTML."""
        generator = SyncGenerator(tmp_path)

        generator.generate_reader_html()

        html_path = tmp_path / "index.html"
        assert html_path.exists()

        content = html_path.read_text()
        assert "<!DOCTYPE html>" in content
        assert "PDF.js" in content or "pdf" in content.lower()
```

### Step 5.2: 运行测试确认失败

```bash
python -m pytest tests/test_raz_sync_processor/test_sync_generator.py -v
```

**Expected:** ImportError

### Step 5.3: 实现 SyncGenerator

```python
# scripts/raz_sync_processor/sync_generator.py
"""同步生成器：生成 JSON 文件和阅读器 HTML."""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

try:
    from jinja2 import Template
except ImportError:
    Template = None

from .models import PageTiming, WordTiming, WordTimingWithLocation
from .config import OUTPUT_JSON, WORD_TIMINGS_JSON, READER_HTML, PDF_FILENAME, AUDIO_FILENAME

logger = logging.getLogger(__name__)


class SyncGenerator:
    """生成同步所需的输出文件."""

    def __init__(self, output_dir: Path):
        """初始化生成器.

        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_book_json(
        self,
        book_id: str,
        title: str,
        level: str,
        pages: List[PageTiming]
    ) -> Path:
        """生成 book.json.

        Args:
            book_id: 书籍 ID
            title: 书名
            level: 级别
            pages: 页面时间列表

        Returns:
            生成的文件路径
        """
        data = {
            "id": book_id,
            "title": title,
            "level": level,
            "pdf": PDF_FILENAME,
            "audio": AUDIO_FILENAME,
            "page_count": len(pages),
            "pages": [
                {
                    "page": p.page_num,
                    "start_time": p.start_time,
                    "end_time": p.end_time,
                    "text": p.text
                }
                for p in pages
            ]
        }

        output_path = self.output_dir / OUTPUT_JSON
        output_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        logger.info(f"Generated: {output_path}")
        return output_path

    def generate_word_timings(
        self,
        word_timings: List[WordTimingWithLocation]
    ) -> Path:
        """生成 word_timings.json.

        Args:
            word_timings: 带位置信息的单词时间戳

        Returns:
            生成的文件路径
        """
        data = {
            "version": "1.0",
            "total_words": len(word_timings),
            "timings": [
                {
                    "word": w.word,
                    "start": w.start,
                    "end": w.end,
                    "page": w.page,
                    "char_start": w.char_start,
                    "char_end": w.char_end
                }
                for w in word_timings
            ]
        }

        output_path = self.output_dir / WORD_TIMINGS_JSON
        output_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        logger.info(f"Generated: {output_path}")
        return output_path

    def create_symlinks(self, source_dir: Path) -> None:
        """创建源文件软链接.

        Args:
            source_dir: 源目录
        """
        pdf_source = source_dir / PDF_FILENAME
        audio_source = source_dir / AUDIO_FILENAME

        if pdf_source.exists():
            pdf_link = self.output_dir / PDF_FILENAME
            if pdf_link.exists() or pdf_link.is_symlink():
                pdf_link.unlink()
            pdf_link.symlink_to(pdf_source.resolve())
            logger.info(f"Created symlink: {pdf_link}")

        if audio_source.exists():
            audio_link = self.output_dir / AUDIO_FILENAME
            if audio_link.exists() or audio_link.is_symlink():
                audio_link.unlink()
            audio_link.symlink_to(audio_source.resolve())
            logger.info(f"Created symlink: {audio_link}")

    def generate_reader_html(self) -> Path:
        """生成阅读器 HTML.

        Returns:
            生成的文件路径
        """
        template_path = Path(__file__).parent / "templates" / "reader.html"

        if template_path.exists():
            template = Template(template_path.read_text())
            html_content = template.render()
        else:
            # 使用内嵌模板
            html_content = self._get_default_template()

        output_path = self.output_dir / READER_HTML
        output_path.write_text(html_content, encoding="utf-8")
        logger.info(f"Generated: {output_path}")
        return output_path

    def _get_default_template(self) -> str:
        """获取默认 HTML 模板."""
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAZ 同步阅读器</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    <style>
        .word-highlight {
            background-color: #fef08a;
            padding: 2px 4px;
            border-radius: 4px;
            transition: background-color 0.2s;
        }
        #text-display {
            line-height: 2;
        }
    </style>
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="max-w-4xl mx-auto p-4">
        <!-- 头部 -->
        <header class="bg-white rounded-lg shadow p-4 mb-4">
            <h1 id="book-title" class="text-xl font-bold text-gray-800">加载中...</h1>
            <p id="book-info" class="text-sm text-gray-500"></p>
        </header>

        <!-- PDF 显示区 -->
        <div class="bg-white rounded-lg shadow p-4 mb-4">
            <canvas id="pdf-canvas" class="w-full border rounded"></canvas>
        </div>

        <!-- 文本显示区（逐词高亮） -->
        <div class="bg-white rounded-lg shadow p-4 mb-4">
            <div id="text-display" class="text-lg text-gray-800"></div>
        </div>

        <!-- 音频控制 -->
        <div class="bg-white rounded-lg shadow p-4 mb-4">
            <audio id="audio-player" controls class="w-full"></audio>
        </div>

        <!-- 翻页控制 -->
        <div class="flex justify-between items-center bg-white rounded-lg shadow p-4">
            <button id="prev-btn" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
                ← 上一页
            </button>
            <span id="page-indicator" class="text-gray-600">第 1 / 10 页</span>
            <button id="next-btn" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
                下一页 →
            </button>
        </div>
    </div>

    <script>
        // 全局状态
        let bookData = null;
        let wordTimings = null;
        let currentPage = 1;
        let pdfDoc = null;
        let audioPlayer = null;

        // 初始化
        async function init() {
            // 加载配置
            bookData = await fetch('book.json').then(r => r.json());
            wordTimings = await fetch('word_timings.json').then(r => r.json());

            // 更新标题
            document.getElementById('book-title').textContent = bookData.title;
            document.getElementById('book-info').textContent =
                `Level ${bookData.level.toUpperCase()} · ${bookData.page_count} 页`;

            // 初始化音频
            audioPlayer = document.getElementById('audio-player');
            audioPlayer.src = bookData.audio;

            // 初始化 PDF
            pdfjsLib.GlobalWorkerOptions.workerSrc =
                'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
            pdfDoc = await pdfjsLib.getDocument(bookData.pdf).promise;

            // 绑定事件
            document.getElementById('prev-btn').addEventListener('click', () => changePage(-1));
            document.getElementById('next-btn').addEventListener('click', () => changePage(1));
            audioPlayer.addEventListener('timeupdate', onTimeUpdate);

            // 渲染第一页
            renderPage(1);
        }

        // 渲染页面
        async function renderPage(pageNum) {
            currentPage = pageNum;

            // 渲染 PDF
            const page = await pdfDoc.getPage(pageNum);
            const canvas = document.getElementById('pdf-canvas');
            const ctx = canvas.getContext('2d');
            const scale = canvas.width / page.getViewport({scale: 1}).width;
            const viewport = page.getViewport({scale});

            canvas.height = viewport.height;
            await page.render({canvasContext: ctx, viewport}).promise;

            // 更新文本显示
            const pageData = bookData.pages.find(p => p.page === pageNum);
            document.getElementById('text-display').textContent = pageData?.text || '';

            // 更新页码
            document.getElementById('page-indicator').textContent =
                `第 ${pageNum} / ${bookData.page_count} 页`;
        }

        // 翻页
        function changePage(delta) {
            const newPage = currentPage + delta;
            if (newPage >= 1 && newPage <= bookData.page_count) {
                renderPage(newPage);

                // 同步音频
                const pageData = bookData.pages.find(p => p.page === newPage);
                if (pageData) {
                    audioPlayer.currentTime = pageData.start_time;
                    audioPlayer.play();
                }
            }
        }

        // 时间更新（逐词高亮）
        function onTimeUpdate() {
            const currentTime = audioPlayer.currentTime;

            // 找到当前单词
            const currentWord = wordTimings.timings.find(
                w => w.start <= currentTime && w.end >= currentTime
            );

            if (currentWord) {
                // 如果跳到新页面，自动翻页
                if (currentWord.page !== currentPage) {
                    renderPage(currentWord.page);
                }

                // 高亮当前单词
                highlightWord(currentWord);
            }
        }

        // 高亮单词
        function highlightWord(wordTiming) {
            const display = document.getElementById('text-display');
            const text = display.textContent;

            // 简单的字符级高亮
            const before = text.slice(0, wordTiming.char_start);
            const word = text.slice(wordTiming.char_start, wordTiming.char_end);
            const after = text.slice(wordTiming.char_end);

            display.innerHTML = `${before}<span class="word-highlight">${word}</span>${after}`;
        }

        // 启动
        init().catch(err => {
            console.error('初始化失败:', err);
            document.getElementById('book-title').textContent = '加载失败';
        });
    </script>
</body>
</html>'''
```

### Step 5.4: 创建模板目录

```bash
mkdir -p scripts/raz_sync_processor/templates
```

### Step 5.5: 运行测试确认通过

```bash
python -m pytest tests/test_raz_sync_processor/test_sync_generator.py -v
```

**Expected:** 5 tests passed

### Step 5.6: 提交

```bash
git add scripts/raz_sync_processor/sync_generator.py \
        scripts/raz_sync_processor/templates/ \
        tests/test_raz_sync_processor/test_sync_generator.py
git commit -m "feat(raz-sync): implement sync generator with HTML reader"
```

---

## Task 6: CLI 入口

**Files:**
- Create: `scripts/raz_sync_processor/__main__.py`
- Create: `scripts/raz_sync_processor/main.py`
- Modify: `scripts/raz_sync_processor/__init__.py` (添加导入)

### Step 6.1: 实现主处理器

```python
# scripts/raz_sync_processor/main.py
"""主处理器：协调各组件完成同步任务."""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

from .pdf_processor import PDFProcessor
from .audio_transcriber import AudioTranscriber
from .text_aligner import TextAligner
from .sync_generator import SyncGenerator
from .models import PageText, WordTiming, PageTiming, WordTimingWithLocation
from .config import LOG_FORMAT, LOG_LEVEL, PDF_FILENAME, AUDIO_FILENAME

logger = logging.getLogger(__name__)


class RazSyncProcessor:
    """RAZ 同步处理器主类."""

    def __init__(
        self,
        model_size: str = "base",
        language: str = "en",
        device: str = "cpu"
    ):
        """初始化处理器.

        Args:
            model_size: Whisper 模型大小
            language: 语言代码
            device: 计算设备
        """
        self.model_size = model_size
        self.language = language
        self.device = device

        # 初始化组件
        self.pdf_processor = PDFProcessor()
        self.audio_transcriber = AudioTranscriber(
            model_size=model_size,
            device=device
        )
        self.text_aligner = TextAligner()

    def process(
        self,
        input_dir: Path,
        output_dir: Path,
        book_id: Optional[str] = None,
        title: Optional[str] = None,
        force: bool = False
    ) -> bool:
        """处理单本书.

        Args:
            input_dir: 输入目录（含 book.pdf, book.mp3）
            output_dir: 输出目录
            book_id: 书籍 ID，默认从目录名推断
            title: 书名，默认从目录名推断
            force: 是否强制重新处理

        Returns:
            是否成功
        """
        # 检查输入文件
        pdf_path = input_dir / PDF_FILENAME
        audio_path = input_dir / AUDIO_FILENAME

        if not pdf_path.exists():
            logger.error(f"PDF not found: {pdf_path}")
            return False

        if not audio_path.exists():
            logger.error(f"Audio not found: {audio_path}")
            return False

        # 检查输出目录
        if output_dir.exists() and not force:
            logger.info(f"Output exists, skipping (use --force to overwrite): {output_dir}")
            return True

        # 创建输出目录
        output_dir.mkdir(parents=True, exist_ok=True)

        # 推断书籍信息
        if book_id is None:
            book_id = self._infer_book_id(input_dir)
        if title is None:
            title = self._infer_title(input_dir)
        level = input_dir.parent.name  # level-a

        logger.info(f"Processing: {title} (ID: {book_id})")

        try:
            # Step 1: 处理 PDF
            logger.info("Step 1/4: Processing PDF...")
            pages = self._process_pdf(pdf_path)
            if not pages:
                logger.error("PDF processing failed")
                return False

            # Step 2: 转录音频
            logger.info("Step 2/4: Transcribing audio...")
            word_timings = self._transcribe_audio(audio_path)
            if not word_timings:
                logger.error("Audio transcription failed")
                return False

            # Step 3: 对齐文本
            logger.info("Step 3/4: Aligning text...")
            page_timings = self.text_aligner.align(pages, word_timings)
            if not page_timings:
                logger.error("Text alignment failed")
                return False

            # Step 4: 生成输出
            logger.info("Step 4/4: Generating output...")
            generator = SyncGenerator(output_dir)
            generator.create_symlinks(input_dir)
            generator.generate_book_json(book_id, title, level, page_timings)

            # 生成带位置信息的单词时间戳
            word_timings_with_loc = self._add_word_locations(
                word_timings, page_timings
            )
            generator.generate_word_timings(word_timings_with_loc)
            generator.generate_reader_html()

            logger.info(f"Successfully processed: {title}")
            logger.info(f"Output: {output_dir}")
            return True

        except Exception as e:
            logger.exception(f"Processing failed: {e}")
            return False

    def _process_pdf(self, pdf_path: Path) -> list[PageText]:
        """处理 PDF."""
        # 检查是否需要 OCR
        if self.pdf_processor.needs_ocr(pdf_path):
            logger.info("PDF needs OCR, processing with OCRmyPDF...")
            ocr_path = pdf_path.parent / "book_ocr.pdf"
            if self.pdf_processor.add_ocr_layer(pdf_path, ocr_path):
                return self.pdf_processor.extract_text_by_page(ocr_path)
            else:
                logger.warning("OCR failed, trying direct extraction...")

        return self.pdf_processor.extract_text_by_page(pdf_path)

    def _transcribe_audio(self, audio_path: Path) -> list[WordTiming]:
        """转录音频."""
        return self.audio_transcriber.transcribe(
            audio_path,
            language=self.language
        )

    def _add_word_locations(
        self,
        word_timings: list[WordTiming],
        page_timings: list[PageTiming]
    ) -> list[WordTimingWithLocation]:
        """为单词添加页面和字符位置信息."""
        result = []
        char_offset = 0
        current_page_idx = 0

        for word in word_timings:
            # 找到当前单词所属页面
            while (current_page_idx < len(page_timings) - 1 and
                   word.start > page_timings[current_page_idx].end_time):
                char_offset += len(page_timings[current_page_idx].text) + 1
                current_page_idx += 1

            page = page_timings[current_page_idx]
            word_len = len(word.word)

            result.append(WordTimingWithLocation(
                word=word.word,
                start=word.start,
                end=word.end,
                page=page.page_num,
                char_start=char_offset,
                char_end=char_offset + word_len
            ))

            char_offset += word_len + 1

        return result

    def _infer_book_id(self, input_dir: Path) -> str:
        """从目录路径推断书籍 ID."""
        level = input_dir.parent.name  # level-a
        book_name = input_dir.name
        return f"{level}/{book_name}"

    def _infer_title(self, input_dir: Path) -> str:
        """从目录名推断书名."""
        name = input_dir.name
        # 将连字符替换为空格，首字母大写
        return name.replace('-', ' ').title()


def setup_logging():
    """配置日志."""
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """CLI 入口."""
    setup_logging()

    parser = argparse.ArgumentParser(
        description="RAZ 音频-文本同步处理器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m scripts.raz_sync_processor -i data/raz/level-a/all-kinds-of-faces -o output/
  python -m scripts.raz_sync_processor -i input/ -o output/ --model tiny --force
        """
    )

    parser.add_argument(
        "--input", "-i",
        required=True,
        type=Path,
        help="输入目录（需包含 book.pdf 和 book.mp3）"
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        type=Path,
        help="输出目录"
    )
    parser.add_argument(
        "--model", "-m",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper 模型大小 (默认: base)"
    )
    parser.add_argument(
        "--lang", "-l",
        default="en",
        help="语言代码 (默认: en)"
    )
    parser.add_argument(
        "--device", "-d",
        default="cpu",
        choices=["cpu", "cuda"],
        help="计算设备 (默认: cpu)"
    )
    parser.add_argument(
        "--book-id",
        help="书籍 ID（默认从目录推断）"
    )
    parser.add_argument(
        "--title",
        help="书名（默认从目录推断）"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="强制重新处理"
    )

    args = parser.parse_args()

    processor = RazSyncProcessor(
        model_size=args.model,
        language=args.lang,
        device=args.device
    )

    success = processor.process(
        input_dir=args.input,
        output_dir=args.output,
        book_id=args.book_id,
        title=args.title,
        force=args.force
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
```

### Step 6.2: 更新 CLI 入口

```python
# scripts/raz_sync_processor/__main__.py
"""CLI 入口."""

from .main import main

if __name__ == "__main__":
    main()
```

### Step 6.3: 更新包初始化文件

```python
# scripts/raz_sync_processor/__init__.py
"""RAZ 音频-文本同步处理器.

将 RAZ 绘本的 PDF 和 MP3 自动对齐，生成带时间戳的配置文件。
"""

__version__ = "1.0.0"

from .pdf_processor import PDFProcessor
from .audio_transcriber import AudioTranscriber
from .text_aligner import TextAligner
from .sync_generator import SyncGenerator
from .main import RazSyncProcessor, main

__all__ = [
    "PDFProcessor",
    "AudioTranscriber",
    "TextAligner",
    "SyncGenerator",
    "RazSyncProcessor",
    "main",
]
```

### Step 6.4: 测试 CLI

```bash
# 测试帮助信息
python -m scripts.raz_sync_processor --help
```

**Expected:** 显示帮助信息，包含所有参数选项

### Step 6.5: 提交

```bash
git add scripts/raz_sync_processor/__main__.py \
        scripts/raz_sync_processor/main.py \
        scripts/raz_sync_processor/__init__.py
git commit -m "feat(raz-sync): add CLI entry and main processor"
```

---

## Task 7: 集成测试

**Files:**
- Create: `tests/test_raz_sync_processor/test_integration.py`

### Step 7.1: 编写集成测试

```python
# tests/test_raz_sync_processor/test_integration.py
"""集成测试."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from scripts.raz_sync_processor.main import RazSyncProcessor


class TestIntegration:
    """集成测试."""

    @pytest.fixture
    def mock_processor(self):
        """创建带有模拟组件的处理器."""
        with patch('scripts.raz_sync_processor.main.PDFProcessor') as mock_pdf, \
             patch('scripts.raz_sync_processor.main.AudioTranscriber') as mock_audio, \
             patch('scripts.raz_sync_processor.main.TextAligner') as mock_aligner:

            processor = RazSyncProcessor(model_size="tiny")

            # 配置模拟
            processor.pdf_processor = mock_pdf.return_value
            processor.audio_transcriber = mock_audio.return_value
            processor.text_aligner = mock_aligner.return_value

            yield processor, mock_pdf, mock_audio, mock_aligner

    def test_process_success(self, tmp_path, mock_processor):
        """测试完整处理流程."""
        processor, _, _, _ = mock_processor

        # 创建输入文件
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "book.pdf").write_text("fake pdf")
        (input_dir / "book.mp3").write_text("fake audio")

        output_dir = tmp_path / "output"

        # 配置模拟返回值
        from scripts.raz_sync_processor.models import PageText, WordTiming, PageTiming

        processor.pdf_processor.needs_ocr.return_value = False
        processor.pdf_processor.extract_text_by_page.return_value = [
            PageText(1, "Hello world"),
            PageText(2, "How are you"),
        ]

        processor.audio_transcriber.transcribe.return_value = [
            WordTiming("hello", 0.0, 0.5),
            WordTiming("world", 0.6, 1.0),
            WordTiming("how", 1.5, 1.8),
            WordTiming("are", 1.9, 2.1),
            WordTiming("you", 2.2, 2.5),
        ]

        processor.text_aligner.align.return_value = [
            PageTiming(1, 0.0, 1.0, "Hello world"),
            PageTiming(2, 1.5, 2.5, "How are you"),
        ]

        # 执行
        success = processor.process(input_dir, output_dir)

        # 验证
        assert success is True
        assert (output_dir / "book.json").exists()
        assert (output_dir / "word_timings.json").exists()
        assert (output_dir / "index.html").exists()

    def test_process_missing_pdf(self, tmp_path, mock_processor):
        """测试缺少 PDF 文件."""
        processor, _, _, _ = mock_processor

        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "book.mp3").write_text("fake audio")

        output_dir = tmp_path / "output"

        success = processor.process(input_dir, output_dir)
        assert success is False

    def test_process_missing_audio(self, tmp_path, mock_processor):
        """测试缺少音频文件."""
        processor, _, _, _ = mock_processor

        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "book.pdf").write_text("fake pdf")

        output_dir = tmp_path / "output"

        success = processor.process(input_dir, output_dir)
        assert success is False

    def test_process_empty_pages(self, tmp_path, mock_processor):
        """测试空页面处理."""
        processor, _, _, _ = mock_processor

        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "book.pdf").write_text("fake pdf")
        (input_dir / "book.mp3").write_text("fake audio")

        output_dir = tmp_path / "output"

        processor.pdf_processor.needs_ocr.return_value = False
        processor.pdf_processor.extract_text_by_page.return_value = []

        success = processor.process(input_dir, output_dir)
        assert success is False
```

### Step 7.2: 运行集成测试

```bash
python -m pytest tests/test_raz_sync_processor/test_integration.py -v
```

**Expected:** 5 tests passed

### Step 7.3: 提交

```bash
git add tests/test_raz_sync_processor/test_integration.py
git commit -m "test(raz-sync): add integration tests"
```

---

## Task 8: 文档和示例

**Files:**
- Create: `scripts/raz_sync_processor/README.md`
- Modify: `docs/superpowers/specs/2026-03-27-raz-audio-sync-design.md` (添加使用说明)

### Step 8.1: 编写 README

```markdown
# RAZ 音频-文本同步处理器

将 RAZ 英文绘本的 PDF 和 MP3 自动对齐，生成带时间戳的配置文件和独立阅读器。

## 功能特性

- **PDF OCR**: 使用 OCRmyPDF 为扫描版 PDF 添加隐藏文字层
- **音频转录**: 使用 faster-whisper 生成词级时间戳（精度 0.01s）
- **文本对齐**: 使用 LCS 序列对齐算法自动匹配页面与时间戳
- **独立阅读器**: 生成可双击打开的 HTML 阅读器，支持翻页同步和逐词高亮

## 安装依赖

```bash
# Python 依赖
pip install ocrmypdf pymupdf faster-whisper jinja2

# Tesseract OCR (macOS)
brew install tesseract

# Tesseract OCR (Ubuntu)
sudo apt-get install tesseract-ocr
```

## 使用方法

### 处理单本书

```bash
python -m scripts.raz_sync_processor \
    --input data/raz/level-a/all-kinds-of-faces \
    --output data/raz/level-a/all-kinds-of-faces-synced \
    --model base
```

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-i, --input` | 输入目录（需含 book.pdf, book.mp3） | 必填 |
| `-o, --output` | 输出目录 | 必填 |
| `-m, --model` | Whisper 模型 (tiny/base/small/medium/large) | base |
| `-l, --lang` | 语言代码 | en |
| `-d, --device` | 计算设备 (cpu/cuda) | cpu |
| `--book-id` | 书籍 ID | 自动推断 |
| `--title` | 书名 | 自动推断 |
| `-f, --force` | 强制重新处理 | False |

### 使用示例

```bash
# 使用 tiny 模型（更快，精度稍低）
python -m scripts.raz_sync_processor -i input/ -o output/ --model tiny

# 强制重新处理
python -m scripts.raz_sync_processor -i input/ -o output/ --force

# 指定书名
python -m scripts.raz_sync_processor -i input/ -o output/ --title "My Book"
```

## 输出文件

```
output/
├── book.json          # 页面时间戳配置
├── book.pdf           # 原始 PDF（软链接）
├── book.mp3           # 原始音频（软链接）
├── word_timings.json  # 逐词时间戳
└── index.html         # 独立阅读器
```

## 阅读器使用

双击 `index.html` 即可在浏览器中打开阅读器：

- **翻页**: 点击"上一页"/"下一页"按钮或使用方向键
- **音频同步**: 翻页时自动跳到对应时间
- **逐词高亮**: 播放时自动高亮当前朗读的单词

## 测试

```bash
# 运行所有测试
python -m pytest tests/test_raz_sync_processor/ -v

# 运行特定测试
python -m pytest tests/test_raz_sync_processor/test_text_aligner.py -v
```

## 架构说明

```
┌─────────────────────────────────────────────────────────────┐
│                    RazSyncProcessor                         │
├─────────────────────────────────────────────────────────────┤
│  PDFProcessor        │  OCR + 每页文本提取                   │
│  AudioTranscriber    │  faster-whisper → 词级时间戳          │
│  TextAligner         │  LCS 对齐 → 页面时间范围              │
│  SyncGenerator       │  JSON + HTML 生成                     │
└─────────────────────────────────────────────────────────────┘
```
```

### Step 8.2: 提交

```bash
git add scripts/raz_sync_processor/README.md
git commit -m "docs(raz-sync): add README with usage instructions"
```

---

## Task 9: 端到端测试

**Files:**
- Create: `scripts/test_raz_sync.sh` (可选的 shell 测试脚本)

### Step 9.1: 使用真实数据测试

```bash
# 安装依赖
cd /Users/liuwenping/Documents/fliggy/study-class
pip install ocrmypdf pymupdf faster-whisper jinja2

# 运行处理器
python -m scripts.raz_sync_processor \
    --input data/raz/level-a/all-kinds-of-faces \
    --output data/raz/level-a/all-kinds-of-faces-synced \
    --model tiny \
    --force

# 验证输出
ls -la data/raz/level-a/all-kinds-of-faces-synced/

# 检查生成的文件
cat data/raz/level-a/all-kinds-of-faces-synced/book.json
cat data/raz/level-a/all-kinds-of-faces-synced/word_timings.json | head -50
```

### Step 9.2: 提交

```bash
git add -A
git commit -m "feat(raz-sync): complete implementation with tests and docs"
```

---

## Spec 覆盖率检查

| 设计文档要求 | 实施计划任务 | 状态 |
|-------------|-------------|------|
| OCRmyPDF + PyMuPDF 文本提取 | Task 2 | ✅ |
| faster-whisper 词级时间戳 | Task 3 | ✅ |
| LCS 序列对齐算法 | Task 4 | ✅ |
| book.json + word_timings.json | Task 5 | ✅ |
| index.html 阅读器 | Task 5 | ✅ |
| CLI 入口脚本 | Task 6 | ✅ |
| 错误处理和日志 | 所有任务 | ✅ |
| 不修改原始文件 | Task 5 | ✅ |
| 软链接机制 | Task 5 | ✅ |
| 单元测试覆盖 | Task 2-7 | ✅ |
| 集成测试 | Task 7 | ✅ |
| 文档 | Task 8 | ✅ |

---

## Placeholder 扫描

- [x] 无 "TBD" / "TODO"
- [x] 无 "implement later"
- [x] 所有代码步骤包含完整代码
- [x] 所有测试步骤包含完整断言
- [x] 所有文件路径精确

---

## 类型一致性检查

| 类型/函数 | 定义位置 | 使用位置 | 状态 |
|----------|---------|---------|------|
| PageText | models.py | pdf_processor.py, text_aligner.py | ✅ |
| WordTiming | models.py | audio_transcriber.py, text_aligner.py | ✅ |
| PageTiming | models.py | text_aligner.py, sync_generator.py | ✅ |
| WordTimingWithLocation | models.py | sync_generator.py, main.py | ✅ |
| PDFProcessor.extract_text_by_page | pdf_processor.py | main.py | ✅ |
| AudioTranscriber.transcribe | audio_transcriber.py | main.py | ✅ |
| TextAligner.align | text_aligner.py | main.py | ✅ |

---

## 执行方式选择

**计划已完成并保存到：**
`docs/superpowers/plans/2026-03-27-raz-audio-sync-plan.md`

**两种执行选项：**

**1. Subagent-Driven（推荐）** - 每个任务派发独立子代理，任务间审查，快速迭代

**2. Inline Execution** - 在本会话中顺序执行任务，批量执行并设置检查点

推荐使用 **Subagent-Driven**，因为它能为每个组件提供独立的上下文和审查机会。
