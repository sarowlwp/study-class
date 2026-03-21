# RAZ 英语跟读练习 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为现有小学学习工具新增 RAZ 分级阅读逐句跟读练习模块，支持语音播放、录音跟读、阿里云发音评测，以及每日学习量定制。

**Architecture:** 延续项目现有 FastAPI + 文件存储风格，新增 `app/services/speech_assessment.py` 抽象发音评测层（Protocol），通过环境变量切换具体实现（阿里云 / Mock）。书库数据存于 `data/raz/{level}/{book}/book.json`，每日练习记录写入 `data/raz-records/YYYY-MM-DD.md`。

**Tech Stack:** FastAPI, Python 3.10+, Jinja2, Tailwind CSS, 原生 JavaScript (MediaRecorder API), 阿里云智能语音交互 SDK, pydub (音频格式转换), pytest

---

## File Map

| 文件 | 操作 | 职责 |
|------|------|------|
| `app/models/raz.py` | 新建 | RAZ 数据模型：Book, Page, RazConfig, PracticeRecord |
| `app/config.py` | 修改 | 新增 RAZ_DIR, RAZ_RECORDS_DIR 路径常量 |
| `app/services/raz_service.py` | 新建 | 扫描书库、解析 book.json、读写配置、读写记录 |
| `app/services/speech_assessment.py` | 新建 | SpeechAssessor Protocol + MockSpeechAssessor + AliyunSpeechAssessor |
| `app/services/raz_practice_service.py` | 新建 | 每日任务计算、智能推荐、会话状态持久化 |
| `app/routers/raz.py` | 新建 | 页面路由 + API 路由 |
| `app/main.py` | 修改 | 注册 raz router，挂载 raz static 目录 |
| `app/templates/base.html` | 修改 | 导航栏新增 RAZ 跟读入口 |
| `app/templates/raz/index.html` | 新建 | 书库首页（按 Level 浏览） |
| `app/templates/raz/book.html` | 新建 | 书详情页（视频预览 + 开始练习） |
| `app/templates/raz/practice.html` | 新建 | 逐句练习页（核心功能） |
| `app/templates/raz/progress.html` | 新建 | 进度总览页 |
| `tests/test_raz_service.py` | 新建 | RazService 单元测试 |
| `tests/test_raz_practice_service.py` | 新建 | RazPracticeService 单元测试 |
| `tests/test_speech_assessment.py` | 新建 | SpeechAssessor Mock 单元测试 |
| `data/raz/level-a/sample-book/` | 新建 | 示例书数据（供测试和开发用） |
| `requirements.txt` | 修改 | 新增 pydub |

---

## Task 1: 数据模型与配置

**Files:**
- Create: `app/models/raz.py`
- Modify: `app/config.py`

- [ ] **Step 1: 在 `app/config.py` 新增 RAZ 路径常量**

```python
# 在现有常量后追加：
RAZ_DIR = DATA_DIR / "raz"
RAZ_RECORDS_DIR = DATA_DIR / "raz-records"
RAZ_CONFIG_FILE = DATA_DIR / "raz-config.json"

RAZ_DIR.mkdir(parents=True, exist_ok=True)
RAZ_RECORDS_DIR.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 2: 新建 `app/models/raz.py`**

```python
from dataclasses import dataclass, field
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
```

- [ ] **Step 3: 验证导入无错误**

```bash
cd /path/to/study-class
python -c "from app.models.raz import RazBook, RazConfig, RazPage, RazPracticeRecord; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add app/config.py app/models/raz.py
git commit -m "feat(raz): add data models and config paths"
```

---

## Task 2: 示例书数据

**Files:**
- Create: `data/raz/level-a/sample-book/book.json`

- [ ] **Step 1: 创建示例书目录和 book.json**

```bash
mkdir -p data/raz/level-a/sample-book
```

```json
// data/raz/level-a/sample-book/book.json
{
  "id": "level-a/sample-book",
  "title": "A Sample Book",
  "level": "a",
  "video": null,
  "pages": [
    {
      "page": 1,
      "pdf": "page01.pdf",
      "audio": "page01.mp3",
      "sentences": [
        "This is a big red barn.",
        "Animals live here."
      ]
    },
    {
      "page": 2,
      "pdf": "page02.pdf",
      "audio": "page02.mp3",
      "sentences": [
        "The cow says moo.",
        "The horse says neigh."
      ]
    }
  ]
}
```

注意：pdf 和 mp3 文件本次不放入仓库（真实内容为用户自备），仅 book.json 作为结构示例。

- [ ] **Step 2: 创建占位文件（供测试用）**

```bash
touch data/raz/level-a/sample-book/page01.pdf
touch data/raz/level-a/sample-book/page01.mp3
touch data/raz/level-a/sample-book/page02.pdf
touch data/raz/level-a/sample-book/page02.mp3
```

- [ ] **Step 3: Commit**

```bash
git add data/raz/level-a/sample-book/book.json
git commit -m "feat(raz): add sample book data for development"
```

---

## Task 3: RazService（书库管理）

**Files:**
- Create: `app/services/raz_service.py`
- Create: `tests/test_raz_service.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_raz_service.py
import json
import pytest
from pathlib import Path
from datetime import date, datetime

from app.services.raz_service import RazService
from app.models.raz import RazBook, RazConfig, RazPracticeRecord


@pytest.fixture
def tmp_raz_dir(tmp_path):
    """创建临时 RAZ 书库目录"""
    book_dir = tmp_path / "level-a" / "my-book"
    book_dir.mkdir(parents=True)
    book_json = {
        "id": "level-a/my-book",
        "title": "My Book",
        "level": "a",
        "video": None,
        "pages": [
            {
                "page": 1,
                "pdf": "page01.pdf",
                "audio": "page01.mp3",
                "sentences": ["Hello world.", "Goodbye world."]
            }
        ]
    }
    (book_dir / "book.json").write_text(json.dumps(book_json), encoding="utf-8")
    return tmp_path


@pytest.fixture
def tmp_records_dir(tmp_path):
    return tmp_path / "records"


@pytest.fixture
def service(tmp_raz_dir, tmp_records_dir):
    tmp_records_dir.mkdir()
    config_file = tmp_raz_dir.parent / "raz-config.json"
    return RazService(raz_dir=tmp_raz_dir, records_dir=tmp_records_dir, config_file=config_file)


class TestRazService:
    def test_get_books_returns_books_for_level(self, service):
        books = service.get_books(level="a")
        assert len(books) == 1
        assert books[0].title == "My Book"
        assert books[0].id == "level-a/my-book"

    def test_get_books_empty_for_missing_level(self, service):
        books = service.get_books(level="z")
        assert books == []

    def test_get_book_by_id(self, service):
        book = service.get_book("level-a/my-book")
        assert book is not None
        assert len(book.pages) == 1
        assert book.pages[0].sentences == ["Hello world.", "Goodbye world."]

    def test_get_book_returns_none_for_missing(self, service):
        book = service.get_book("level-a/nonexistent")
        assert book is None

    def test_get_config_returns_default_when_no_file(self, service):
        config = service.get_config()
        assert config.current_level == "a"
        assert config.daily_mode == "manual"
        assert config.daily_count == 10

    def test_save_and_load_config(self, service):
        from app.models.raz import RazConfig
        config = RazConfig(current_level="b", daily_mode="smart", daily_count=15)
        service.save_config(config)
        loaded = service.get_config()
        assert loaded.current_level == "b"
        assert loaded.daily_count == 15

    def test_save_record(self, service):
        record = RazPracticeRecord(
            book_id="level-a/my-book",
            book_title="My Book",
            level="a",
            page=1,
            sentence="Hello world.",
            score=85,
            timestamp=datetime(2026, 3, 21, 9, 15, 0),
        )
        service.save_record(record)
        records = service.get_records_by_date(date(2026, 3, 21))
        assert len(records) == 1
        assert records[0].score == 85
        assert records[0].sentence == "Hello world."

    def test_get_records_returns_empty_for_missing_date(self, service):
        records = service.get_records_by_date(date(2020, 1, 1))
        assert records == []

    def test_malformed_record_line_is_skipped(self, service, tmp_records_dir):
        """格式错误的行不应导致崩溃"""
        record_file = tmp_records_dir / "2026-03-21.md"
        record_file.write_text(
            "# RAZ 练习记录 2026-03-21\n\n## My Book (Level A)\n\n"
            "| 页码 | 句子 | 评分 | 时间 |\n|------|------|------|------|\n"
            "| 1 | Hello world. | 85 | 09:15:00 |\n"
            "| BROKEN LINE WITHOUT PROPER FORMAT\n"
            "| 1 | Goodbye world. | 90 | 09:16:00 |\n",
            encoding="utf-8"
        )
        records = service.get_records_by_date(date(2026, 3, 21))
        assert len(records) == 2  # 跳过损坏行，读到2条
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_raz_service.py -v
```

Expected: 所有测试 FAIL（`RazService` 不存在）

- [ ] **Step 3: 实现 `app/services/raz_service.py`**

```python
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

from app.models.raz import RazBook, RazConfig, RazPage, RazPracticeRecord


class RazService:
    def __init__(self, raz_dir: Path, records_dir: Path, config_file: Path):
        self._raz_dir = raz_dir
        self._records_dir = records_dir
        self._config_file = config_file

    # ── 书库 ──────────────────────────────────────────────────────────────────

    def get_books(self, level: str) -> List[RazBook]:
        level_dir = self._raz_dir / f"level-{level}"
        if not level_dir.exists():
            return []
        books = []
        for book_dir in sorted(level_dir.iterdir()):
            book = self._load_book(book_dir)
            if book:
                books.append(book)
        return books

    def get_book(self, book_id: str) -> Optional[RazBook]:
        """book_id 格式: level-{x}/{dir_name}"""
        parts = book_id.split("/", 1)
        if len(parts) != 2:
            return None
        book_dir = self._raz_dir / parts[0] / parts[1]
        return self._load_book(book_dir)

    def _load_book(self, book_dir: Path) -> Optional[RazBook]:
        json_file = book_dir / "book.json"
        if not json_file.exists():
            return None
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            pages = [
                RazPage(
                    page=p["page"],
                    pdf=p["pdf"],
                    audio=p["audio"],
                    sentences=p["sentences"],
                )
                for p in data.get("pages", [])
            ]
            return RazBook(
                id=data["id"],
                title=data["title"],
                level=data["level"],
                pages=pages,
                video=data.get("video"),
            )
        except Exception:
            return None

    # ── 配置 ──────────────────────────────────────────────────────────────────

    def get_config(self) -> RazConfig:
        if not self._config_file.exists():
            return RazConfig()
        try:
            data = json.loads(self._config_file.read_text(encoding="utf-8"))
            return RazConfig(
                current_level=data.get("current_level", "a"),
                daily_mode=data.get("daily_mode", "manual"),
                daily_count=data.get("daily_count", 10),
                current_session=data.get("current_session"),
            )
        except Exception:
            return RazConfig()

    def save_config(self, config: RazConfig) -> None:
        data = {
            "current_level": config.current_level,
            "daily_mode": config.daily_mode,
            "daily_count": config.daily_count,
            "current_session": config.current_session,
        }
        self._config_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── 记录 ──────────────────────────────────────────────────────────────────

    def save_record(self, record: RazPracticeRecord) -> None:
        self._records_dir.mkdir(parents=True, exist_ok=True)
        record_file = self._records_dir / f"{record.timestamp.date().isoformat()}.md"

        # 追加模式：若文件已有该书的 section，直接追加行；否则新建 section
        if record_file.exists():
            content = record_file.read_text(encoding="utf-8")
        else:
            content = f"# RAZ 练习记录 {record.timestamp.date().isoformat()}\n"

        book_section_header = f"## {record.book_title} (Level {record.level.upper()})"
        new_row = (
            f"| {record.page} | {record.sentence} "
            f"| {record.score} | {record.timestamp.strftime('%H:%M:%S')} |"
        )

        if book_section_header in content:
            content = content.rstrip("\n") + "\n" + new_row + "\n"
        else:
            table_header = (
                f"\n{book_section_header}\n\n"
                "| 页码 | 句子 | 评分 | 时间 |\n"
                "|------|------|------|------|\n"
            )
            content = content.rstrip("\n") + table_header + new_row + "\n"

        record_file.write_text(content, encoding="utf-8")

    def get_records_by_date(self, record_date: date) -> List[RazPracticeRecord]:
        record_file = self._records_dir / f"{record_date.isoformat()}.md"
        if not record_file.exists():
            return []
        return self._parse_records(record_file, record_date)

    def _parse_records(self, filepath: Path, record_date: date) -> List[RazPracticeRecord]:
        content = filepath.read_text(encoding="utf-8")
        records = []
        current_book_title = ""
        current_level = ""

        for line in content.splitlines():
            # 检测 book section header: ## Title (Level X)
            book_match = re.match(r"^## (.+?) \(Level ([A-Z]+)\)\s*$", line)
            if book_match:
                current_book_title = book_match.group(1)
                current_level = book_match.group(2).lower()
                continue

            # 跳过表头和分隔行
            if line.startswith("| 页码") or line.startswith("|---"):
                continue

            # 解析数据行：| page | sentence | score | time |
            row_match = re.match(r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(\d+)\s*\|\s*(\d{2}:\d{2}:\d{2})\s*\|", line)
            if row_match and current_book_title:
                try:
                    page = int(row_match.group(1))
                    sentence = row_match.group(2).strip()
                    score = int(row_match.group(3))
                    time_str = row_match.group(4)
                    timestamp = datetime.strptime(
                        f"{record_date.isoformat()} {time_str}", "%Y-%m-%d %H:%M:%S"
                    )
                    records.append(RazPracticeRecord(
                        book_id="",  # 记录中不存 book_id，仅存 title
                        book_title=current_book_title,
                        level=current_level,
                        page=page,
                        sentence=sentence,
                        score=score,
                        timestamp=timestamp,
                    ))
                except (ValueError, IndexError):
                    continue  # 跳过格式错误的行

        return records
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_raz_service.py -v
```

Expected: 所有测试 PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/raz_service.py tests/test_raz_service.py data/raz/level-a/sample-book/book.json
git commit -m "feat(raz): implement RazService with book library, config, and record management"
```

---

## Task 4: 发音评测抽象层

**Files:**
- Create: `app/services/speech_assessment.py`
- Create: `tests/test_speech_assessment.py`
- Modify: `requirements.txt`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_speech_assessment.py
import pytest
import asyncio
from app.services.speech_assessment import MockSpeechAssessor, SpeechAssessmentResult


class TestMockSpeechAssessor:
    @pytest.mark.asyncio
    async def test_assess_returns_result(self):
        assessor = MockSpeechAssessor()
        result = await assessor.assess(b"fake_audio", "Hello world.")
        assert isinstance(result, SpeechAssessmentResult)
        assert 0 <= result.score <= 100
        assert isinstance(result.feedback, str)

    @pytest.mark.asyncio
    async def test_assess_accepts_any_audio_bytes(self):
        assessor = MockSpeechAssessor()
        result = await assessor.assess(b"", "Short.")
        assert result.score >= 0
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_speech_assessment.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现 `app/services/speech_assessment.py`**

```python
import os
import random
from dataclasses import dataclass, field
from typing import Protocol, List, runtime_checkable


@dataclass
class WordScore:
    word: str
    score: int  # 0-100


@dataclass
class SpeechAssessmentResult:
    score: int                                    # 0-100 整体评分
    word_scores: List[WordScore] = field(default_factory=list)
    feedback: str = ""


@runtime_checkable
class SpeechAssessor(Protocol):
    async def assess(self, audio_bytes: bytes, text: str) -> SpeechAssessmentResult:
        ...


class MockSpeechAssessor:
    """开发/测试用：返回随机评分，不调用任何外部服务"""

    async def assess(self, audio_bytes: bytes, text: str) -> SpeechAssessmentResult:
        score = random.randint(60, 100)
        if score >= 90:
            feedback = "优秀！发音非常标准。"
        elif score >= 70:
            feedback = "良好，继续练习！"
        else:
            feedback = "需要加油，多听多读。"
        return SpeechAssessmentResult(score=score, feedback=feedback)


class AliyunSpeechAssessor:
    """阿里云智能语音交互发音评测实现。

    需要环境变量：
      ALIYUN_ACCESS_KEY_ID
      ALIYUN_ACCESS_KEY_SECRET
      ALIYUN_NLS_APP_KEY

    阿里云 NLS 文档：https://help.aliyun.com/product/30413.html
    具体使用的产品：英语口语评测（nls-speech-assessment）
    音频格式要求：PCM/WAV，16kHz，16bit，单声道
    """

    def __init__(self):
        self._access_key_id = os.environ.get("ALIYUN_ACCESS_KEY_ID", "")
        self._access_key_secret = os.environ.get("ALIYUN_ACCESS_KEY_SECRET", "")
        self._app_key = os.environ.get("ALIYUN_NLS_APP_KEY", "")

    async def assess(self, audio_bytes: bytes, text: str) -> SpeechAssessmentResult:
        """提交 WAV 音频到阿里云发音评测接口，返回评分结果。

        audio_bytes 应为 WAV 格式（16kHz, 16bit, mono）。
        调用方负责在提交前完成格式转换（WebM → WAV）。
        """
        # TODO: 根据实际申请的阿里云产品 SDK 实现调用逻辑
        # 参考：aliyun-python-sdk-core + nls SDK
        # pip install aliyun-python-sdk-core nls-python-sdk
        raise NotImplementedError(
            "AliyunSpeechAssessor 需根据实际申请的阿里云产品配置实现。"
            "请参考 docs/superpowers/specs/2026-03-21-raz-shadowing-design.md 第5节。"
        )


def get_assessor() -> SpeechAssessor:
    """根据环境变量 SPEECH_ASSESSOR 返回对应实现。"""
    provider = os.environ.get("SPEECH_ASSESSOR", "mock").lower()
    if provider == "aliyun":
        return AliyunSpeechAssessor()
    return MockSpeechAssessor()
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_speech_assessment.py -v
```

Expected: PASS

- [ ] **Step 5: 在 requirements.txt 新增 pydub（供阿里云实现使用，WebM→WAV 转换）**

在 `requirements.txt` 末尾追加：
```
pydub==0.25.1
```

注意：pydub 需要系统安装 ffmpeg（`brew install ffmpeg` 或 `apt install ffmpeg`）。

- [ ] **Step 6: Commit**

```bash
git add app/services/speech_assessment.py tests/test_speech_assessment.py requirements.txt
git commit -m "feat(raz): add speech assessment abstraction layer with Mock and Aliyun implementations"
```

---

## Task 5: RazPracticeService（每日任务与会话）

**Files:**
- Create: `app/services/raz_practice_service.py`
- Create: `tests/test_raz_practice_service.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_raz_practice_service.py
import json
import pytest
from datetime import date, datetime, timedelta
from pathlib import Path

from app.services.raz_practice_service import RazPracticeService
from app.services.raz_service import RazService
from app.models.raz import RazConfig, RazPracticeRecord


@pytest.fixture
def tmp_dirs(tmp_path):
    raz_dir = tmp_path / "raz"
    records_dir = tmp_path / "records"
    records_dir.mkdir(parents=True)
    config_file = tmp_path / "raz-config.json"
    return raz_dir, records_dir, config_file


@pytest.fixture
def raz_service(tmp_dirs):
    raz_dir, records_dir, config_file = tmp_dirs
    return RazService(raz_dir=raz_dir, records_dir=records_dir, config_file=config_file)


@pytest.fixture
def practice_service(raz_service, tmp_dirs):
    _, records_dir, _ = tmp_dirs
    return RazPracticeService(raz_service=raz_service, records_dir=records_dir)


def _write_records(records_dir: Path, record_date: date, count: int):
    content = f"# RAZ 练习记录 {record_date.isoformat()}\n\n## Test Book (Level A)\n\n"
    content += "| 页码 | 句子 | 评分 | 时间 |\n|------|------|------|------|\n"
    for i in range(count):
        content += f"| 1 | Sentence {i}. | 80 | 0{i % 10}:00:00 |\n"
    (records_dir / f"{record_date.isoformat()}.md").write_text(content, encoding="utf-8")


class TestRazPracticeService:
    def test_get_today_count_zero_when_no_records(self, practice_service):
        count = practice_service.get_today_count(date(2099, 1, 1))
        assert count == 0

    def test_get_today_count_matches_record_rows(self, practice_service, tmp_dirs):
        _, records_dir, _ = tmp_dirs
        today = date(2026, 3, 21)
        _write_records(records_dir, today, 7)
        count = practice_service.get_today_count(today)
        assert count == 7

    def test_is_daily_goal_met_manual_mode(self, practice_service, tmp_dirs):
        _, records_dir, _ = tmp_dirs
        today = date(2026, 3, 21)
        _write_records(records_dir, today, 10)
        config = RazConfig(daily_mode="manual", daily_count=10)
        assert practice_service.is_daily_goal_met(today, config) is True

    def test_is_daily_goal_not_met(self, practice_service, tmp_dirs):
        _, records_dir, _ = tmp_dirs
        today = date(2026, 3, 21)
        _write_records(records_dir, today, 5)
        config = RazConfig(daily_mode="manual", daily_count=10)
        assert practice_service.is_daily_goal_met(today, config) is False

    def test_smart_recommend_defaults_to_10_with_no_history(self, practice_service):
        recommended = practice_service.get_smart_recommendation(reference_date=date(2026, 3, 21))
        assert recommended == 10

    def test_smart_recommend_uses_7_day_average(self, practice_service, tmp_dirs):
        _, records_dir, _ = tmp_dirs
        today = date(2026, 3, 21)
        for i in range(7):
            _write_records(records_dir, today - timedelta(days=i + 1), 8)
        recommended = practice_service.get_smart_recommendation(reference_date=today)
        assert recommended > 0

    def test_update_session(self, practice_service, raz_service):
        practice_service.update_session(book_id="level-a/my-book", page=2, sentence_index=1)
        config = raz_service.get_config()
        assert config.current_session == {
            "book_id": "level-a/my-book",
            "page": 2,
            "sentence_index": 1,
        }
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_raz_practice_service.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现 `app/services/raz_practice_service.py`**

```python
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Optional
import math

from app.models.raz import RazConfig
from app.services.raz_service import RazService


class RazPracticeService:
    def __init__(self, raz_service: RazService, records_dir: Path):
        self._raz_service = raz_service
        self._records_dir = records_dir

    def get_today_count(self, today: date) -> int:
        """统计今日已完成句子数（record 文件中的数据行数）。"""
        record_file = self._records_dir / f"{today.isoformat()}.md"
        if not record_file.exists():
            return 0
        content = record_file.read_text(encoding="utf-8")
        count = 0
        for line in content.splitlines():
            if re.match(r"^\|\s*\d+\s*\|", line) and not line.startswith("| 页码"):
                count += 1
        return count

    def is_daily_goal_met(self, today: date, config: RazConfig) -> bool:
        target = config.daily_count
        if config.daily_mode == "smart":
            target = self.get_smart_recommendation(reference_date=today)
        return self.get_today_count(today) >= target

    def get_smart_recommendation(self, reference_date: date) -> int:
        """近7天平均完成句数 × 完成率，无历史时默认10。"""
        counts = []
        for i in range(1, 8):
            d = reference_date - timedelta(days=i)
            counts.append(self.get_today_count(d))

        days_with_data = [c for c in counts if c > 0]
        if not days_with_data:
            return 10

        avg = sum(days_with_data) / len(days_with_data)
        completion_rate = len(days_with_data) / 7
        return max(5, math.ceil(avg * completion_rate))

    def update_session(self, book_id: str, page: int, sentence_index: int) -> None:
        """持久化当前练习断点到 raz-config.json。"""
        config = self._raz_service.get_config()
        config.current_session = {
            "book_id": book_id,
            "page": page,
            "sentence_index": sentence_index,
        }
        self._raz_service.save_config(config)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_raz_practice_service.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/raz_practice_service.py tests/test_raz_practice_service.py
git commit -m "feat(raz): implement RazPracticeService with daily task and session persistence"
```

---

## Task 6: RAZ Router（后端路由与 API）

**Files:**
- Create: `app/routers/raz.py`
- Modify: `app/main.py`
- Modify: `app/config.py`（确认 RAZ_DIR 已挂载）

- [ ] **Step 1: 新建 `app/routers/raz.py`**

```python
import os
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.config import BASE_DIR, RAZ_DIR, RAZ_RECORDS_DIR, RAZ_CONFIG_FILE
from app.models.raz import RazConfig, RazPracticeRecord
from app.services.raz_service import RazService
from app.services.raz_practice_service import RazPracticeService
from app.services.speech_assessment import get_assessor
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory=BASE_DIR / "app" / "templates")

raz_service = RazService(raz_dir=RAZ_DIR, records_dir=RAZ_RECORDS_DIR, config_file=RAZ_CONFIG_FILE)
practice_service = RazPracticeService(raz_service=raz_service, records_dir=RAZ_RECORDS_DIR)
assessor = get_assessor()


# ── 页面路由 ──────────────────────────────────────────────────────────────────

@router.get("/raz")
async def raz_index(request: Request):
    config = raz_service.get_config()
    books = raz_service.get_books(config.current_level)
    today_count = practice_service.get_today_count(date.today())
    goal_met = practice_service.is_daily_goal_met(date.today(), config)
    return templates.TemplateResponse("raz/index.html", {
        "request": request,
        "books": books,
        "config": config,
        "today_count": today_count,
        "goal_met": goal_met,
    })


@router.get("/raz/book/{level}/{book_dir}")
async def raz_book(request: Request, level: str, book_dir: str):
    book_id = f"level-{level}/{book_dir}"
    book = raz_service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return templates.TemplateResponse("raz/book.html", {
        "request": request,
        "book": book,
    })


@router.get("/raz/practice/{level}/{book_dir}")
async def raz_practice(request: Request, level: str, book_dir: str):
    book_id = f"level-{level}/{book_dir}"
    book = raz_service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    config = raz_service.get_config()
    return templates.TemplateResponse("raz/practice.html", {
        "request": request,
        "book": book,
        "config": config,
    })


@router.get("/raz/progress")
async def raz_progress(request: Request):
    config = raz_service.get_config()
    records = raz_service.get_records_by_date(date.today())
    return templates.TemplateResponse("raz/progress.html", {
        "request": request,
        "config": config,
        "today_records": records,
        "today_count": len(records),
    })


# ── API 路由 ──────────────────────────────────────────────────────────────────

@router.get("/api/raz/books")
async def api_get_books(level: Optional[str] = None):
    config = raz_service.get_config()
    target_level = level or config.current_level
    books = raz_service.get_books(target_level)
    return [{"id": b.id, "title": b.title, "level": b.level, "page_count": len(b.pages)} for b in books]


@router.get("/api/raz/book/{level}/{book_dir}")
async def api_get_book(level: str, book_dir: str):
    book_id = f"level-{level}/{book_dir}"
    book = raz_service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return {
        "id": book.id,
        "title": book.title,
        "level": book.level,
        "video": book.video,
        "pages": [
            {"page": p.page, "pdf": p.pdf, "audio": p.audio, "sentences": p.sentences}
            for p in book.pages
        ],
    }


@router.post("/api/raz/assess")
async def api_assess(
    audio: UploadFile = File(...),
    text: str = Form(...),
    book_id: str = Form(...),
    book_title: str = Form(...),
    level: str = Form(...),
    page: int = Form(...),
):
    audio_bytes = await audio.read()
    if len(audio_bytes) < 1000:  # 粗略判断录音过短（约 0.5s）
        raise HTTPException(status_code=400, detail="录音过短，请重新录制")

    result = await assessor.assess(audio_bytes, text)

    # 写入记录
    record = RazPracticeRecord(
        book_id=book_id,
        book_title=book_title,
        level=level,
        page=page,
        sentence=text,
        score=result.score,
        timestamp=datetime.now(),
    )
    raz_service.save_record(record)

    return {
        "score": result.score,
        "feedback": result.feedback,
        "word_scores": [{"word": w.word, "score": w.score} for w in result.word_scores],
    }


class UpdateSessionRequest(BaseModel):
    book_id: str
    page: int
    sentence_index: int


@router.post("/api/raz/session")
async def api_update_session(req: UpdateSessionRequest):
    practice_service.update_session(req.book_id, req.page, req.sentence_index)
    return {"ok": True}


class UpdateConfigRequest(BaseModel):
    current_level: Optional[str] = None
    daily_mode: Optional[str] = None
    daily_count: Optional[int] = None


@router.post("/api/raz/config")
async def api_update_config(req: UpdateConfigRequest):
    config = raz_service.get_config()
    if req.current_level is not None:
        config.current_level = req.current_level
    if req.daily_mode is not None:
        config.daily_mode = req.daily_mode
    if req.daily_count is not None:
        config.daily_count = max(1, req.daily_count)
    raz_service.save_config(config)
    return {"ok": True}


@router.get("/api/raz/config")
async def api_get_config():
    config = raz_service.get_config()
    today = date.today()
    today_count = practice_service.get_today_count(today)
    smart_rec = practice_service.get_smart_recommendation(reference_date=today)
    return {
        "current_level": config.current_level,
        "daily_mode": config.daily_mode,
        "daily_count": config.daily_count,
        "current_session": config.current_session,
        "today_count": today_count,
        "smart_recommendation": smart_rec,
    }


# ── 静态文件（书库 PDF/MP3/MP4） ───────────────────────────────────────────────

@router.get("/raz/media/{level}/{book_dir}/{filename}")
async def raz_media(level: str, book_dir: str, filename: str):
    """安全地提供书库媒体文件。路径参数严格校验，防止路径穿越。"""
    # 校验参数：只允许字母、数字、连字符、下划线、点
    import re as _re
    safe_pattern = _re.compile(r'^[a-zA-Z0-9_\-\.]+$')
    if not all(safe_pattern.match(p) for p in [level, book_dir, filename]):
        raise HTTPException(status_code=400, detail="Invalid path")

    file_path = RAZ_DIR / f"level-{level}" / book_dir / filename
    # 确认路径在 RAZ_DIR 内（二次防护）
    try:
        file_path.resolve().relative_to(RAZ_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)
```

- [ ] **Step 2: 在 `app/main.py` 注册 raz router**

在 `from app.routers import english` 后追加：
```python
from app.routers import raz
```

在 `app.include_router(english.router)` 后追加：
```python
app.include_router(raz.router)
```

- [ ] **Step 3: 启动应用验证无报错**

```bash
uvicorn app.main:app --reload
```

访问 http://localhost:8000/raz，Expected：页面加载（模板暂未创建时会报 TemplateNotFound，正常）

- [ ] **Step 4: Commit**

```bash
git add app/routers/raz.py app/main.py
git commit -m "feat(raz): add RAZ router with page routes and API endpoints"
```

---

## Task 7: 模板 - 书库首页与书详情页

**Files:**
- Create: `app/templates/raz/index.html`
- Create: `app/templates/raz/book.html`

- [ ] **Step 1: 新建 `app/templates/raz/index.html`**

```html
{% extends "base.html" %}
{% block title %}RAZ 跟读练习{% endblock %}
{% block content %}
<div class="max-w-4xl mx-auto px-4 py-6">

  <!-- 顶部：今日进度 + 设置 -->
  <div class="flex items-center justify-between mb-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-800">📖 RAZ 跟读练习</h1>
      <p class="text-gray-500 mt-1">
        今日已练习 <span id="today-count" class="font-bold text-blue-600">{{ today_count }}</span> 句
        {% if goal_met %}
        <span class="ml-2 text-green-600 font-bold">✅ 今日任务完成！</span>
        {% endif %}
      </p>
    </div>
    <div class="flex items-center gap-3">
      <!-- Level 切换 -->
      <label class="text-sm text-gray-600">当前 Level：</label>
      <select id="level-select" class="border rounded px-2 py-1 text-sm">
        {% for lv in ['aa','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z'] %}
        <option value="{{ lv }}" {% if lv == config.current_level %}selected{% endif %}>
          Level {{ lv | upper }}
        </option>
        {% endfor %}
      </select>
      <!-- 每日目标 -->
      <input id="daily-count" type="number" min="1" max="100"
             value="{{ config.daily_count }}"
             class="border rounded px-2 py-1 text-sm w-16" title="每日目标句数">
      <button onclick="saveConfig()" class="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600">保存</button>
      <a href="/raz/progress" class="text-gray-500 hover:text-gray-700 text-sm">📊 进度</a>
    </div>
  </div>

  <!-- 书库列表 -->
  {% if books %}
  <div class="grid grid-cols-2 md:grid-cols-3 gap-4" id="book-list">
    {% for book in books %}
    <a href="/raz/book/{{ book.level }}/{{ book.id.split('/')[-1] }}"
       class="block bg-white rounded-xl shadow hover:shadow-md transition p-4 border border-gray-100">
      <div class="text-4xl text-center mb-2">📚</div>
      <p class="text-center font-semibold text-gray-700 text-sm">{{ book.title }}</p>
      <p class="text-center text-xs text-gray-400 mt-1">{{ book.pages | length }} 页</p>
    </a>
    {% endfor %}
  </div>
  {% else %}
  <div class="text-center text-gray-400 py-16">
    <p class="text-5xl mb-4">📂</p>
    <p>当前 Level 暂无书籍</p>
    <p class="text-sm mt-2">请将书库文件放入 <code>data/raz/level-{{ config.current_level }}/</code></p>
  </div>
  {% endif %}
</div>

<script>
async function saveConfig() {
  const level = document.getElementById('level-select').value;
  const count = parseInt(document.getElementById('daily-count').value) || 10;
  await fetch('/api/raz/config', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({current_level: level, daily_count: count})
  });
  window.location.reload();
}
</script>
{% endblock %}
```

- [ ] **Step 2: 新建 `app/templates/raz/book.html`**

```html
{% extends "base.html" %}
{% block title %}{{ book.title }} - RAZ 跟读{% endblock %}
{% block content %}
<div class="max-w-2xl mx-auto px-4 py-6">
  <a href="/raz" class="text-blue-500 hover:underline text-sm">← 返回书库</a>

  <div class="mt-4 bg-white rounded-xl shadow p-6">
    <h1 class="text-xl font-bold text-gray-800 mb-1">{{ book.title }}</h1>
    <p class="text-sm text-gray-400 mb-4">Level {{ book.level | upper }} · {{ book.pages | length }} 页</p>

    {% if book.video %}
    <div class="mb-6">
      <p class="text-sm font-semibold text-gray-600 mb-2">📽 整本书视频预览</p>
      <video controls class="w-full rounded-lg border">
        <source src="/raz/media/{{ book.level }}/{{ book.id.split('/')[-1] }}/{{ book.video }}">
      </video>
    </div>
    {% endif %}

    <div class="bg-blue-50 rounded-lg p-4 mb-6">
      <p class="text-sm text-gray-600 mb-1">本书共 <strong>{{ book.pages | length }}</strong> 页，练习方式：</p>
      <ul class="text-sm text-gray-600 list-disc list-inside space-y-1">
        <li>每页展示 PDF 内容 + 播放参考音频</li>
        <li>逐句录音跟读，AI 即时评分</li>
        <li>可重录或跳过</li>
      </ul>
    </div>

    <a href="/raz/practice/{{ book.level }}/{{ book.id.split('/')[-1] }}"
       class="block w-full bg-green-500 hover:bg-green-600 text-white text-center font-bold py-3 rounded-xl text-lg transition">
      🎤 开始练习
    </a>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 3: 访问书库页验证渲染**

启动服务后访问 http://localhost:8000/raz，Expected：书库页正常渲染，显示 sample-book。

- [ ] **Step 4: Commit**

```bash
git add app/templates/raz/
git commit -m "feat(raz): add book library and book detail templates"
```

---

## Task 8: 模板 - 逐句练习页（核心功能）

**Files:**
- Create: `app/templates/raz/practice.html`

这是功能最复杂的页面，包含 PDF 展示、音频播放、浏览器录音、API 提交评分的完整前端逻辑。

- [ ] **Step 1: 新建 `app/templates/raz/practice.html`**

```html
{% extends "base.html" %}
{% block title %}练习 - {{ book.title }}{% endblock %}
{% block content %}
<div class="max-w-3xl mx-auto px-4 py-4">

  <!-- 顶部导航 -->
  <div class="flex items-center justify-between mb-4">
    <a href="/raz/book/{{ book.level }}/{{ book.id.split('/')[-1] }}" class="text-blue-500 hover:underline text-sm">← 返回</a>
    <p class="text-gray-600 text-sm font-semibold">{{ book.title }}</p>
    <span id="progress-label" class="text-xs text-gray-400"></span>
  </div>

  <!-- 当前页 PDF 展示 -->
  <div class="bg-white rounded-xl shadow mb-4 overflow-hidden">
    <iframe id="page-pdf" src="" class="w-full h-64 md:h-80 border-0"></iframe>
  </div>

  <!-- 音频播放器（隐藏控件，由按钮触发） -->
  <audio id="ref-audio" preload="none"></audio>

  <!-- 句子卡片 -->
  <div class="bg-white rounded-xl shadow p-5 mb-4">
    <p class="text-xs text-gray-400 mb-2">当前句子</p>
    <p id="current-sentence" class="text-xl font-semibold text-gray-800 leading-relaxed"></p>
  </div>

  <!-- 操作按钮区 -->
  <div class="flex gap-3 justify-center mb-4 flex-wrap">
    <button id="btn-play" onclick="playRef()"
            class="bg-blue-100 hover:bg-blue-200 text-blue-700 font-semibold px-5 py-2 rounded-lg flex items-center gap-2">
      🔊 听示范
    </button>
    <button id="btn-record" onclick="toggleRecord()"
            class="bg-red-500 hover:bg-red-600 text-white font-semibold px-5 py-2 rounded-lg flex items-center gap-2">
      🎤 开始录音
    </button>
    <button id="btn-skip" onclick="nextSentence(true)"
            class="bg-gray-100 hover:bg-gray-200 text-gray-600 font-semibold px-4 py-2 rounded-lg">
      跳过
    </button>
  </div>

  <!-- 评分结果区 -->
  <div id="score-area" class="hidden bg-white rounded-xl shadow p-5 mb-4 text-center">
    <div id="score-badge" class="text-5xl font-bold mb-2"></div>
    <div id="score-feedback" class="text-gray-600 mb-4"></div>
    <button onclick="nextSentence(false)"
            class="bg-green-500 hover:bg-green-600 text-white font-semibold px-6 py-2 rounded-lg mr-2">
      下一句 →
    </button>
    <button onclick="retryRecord()"
            class="bg-yellow-100 hover:bg-yellow-200 text-yellow-700 font-semibold px-4 py-2 rounded-lg">
      重录
    </button>
  </div>

  <!-- 今日完成提示 -->
  <div id="goal-banner" class="hidden bg-green-50 border border-green-200 rounded-xl p-4 text-center mb-4">
    <p class="text-green-700 font-bold text-lg">🎉 今日目标完成！</p>
    <p class="text-green-600 text-sm mt-1">可以继续练习，或<a href="/raz" class="underline">返回书库</a></p>
  </div>

</div>

<script>
// ── 状态 ─────────────────────────────────────────────────────────────────────
const BOOK_DATA = {{ book | tojson }};
const BOOK_LEVEL = "{{ book.level }}";
const BOOK_DIR = "{{ book.id.split('/')[-1] }}";
const DAILY_COUNT = {{ config.daily_count }};
const DAILY_MODE = "{{ config.daily_mode }}";

let currentPageIdx = 0;
let currentSentIdx = 0;
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

// ── 初始化 ───────────────────────────────────────────────────────────────────
function init() {
  // 尝试从 config.current_session 恢复断点
  const session = {{ (config.current_session or {})|tojson }};
  if (session.book_id === BOOK_DATA.id) {
    const pageIdx = BOOK_DATA.pages.findIndex(p => p.page === session.page);
    if (pageIdx >= 0) {
      currentPageIdx = pageIdx;
      currentSentIdx = Math.min(session.sentence_index || 0, BOOK_DATA.pages[pageIdx].sentences.length - 1);
    }
  }
  renderCurrent();
}

function renderCurrent() {
  const page = BOOK_DATA.pages[currentPageIdx];
  if (!page) { showFinished(); return; }

  const sentence = page.sentences[currentSentIdx];

  // 更新 PDF
  document.getElementById('page-pdf').src =
    `/raz/media/${BOOK_LEVEL}/${BOOK_DIR}/${page.pdf}`;

  // 更新参考音频（不自动播放）
  document.getElementById('ref-audio').src =
    `/raz/media/${BOOK_LEVEL}/${BOOK_DIR}/${page.audio}`;

  // 更新句子文本
  document.getElementById('current-sentence').textContent = sentence;

  // 更新进度标签
  const totalSents = BOOK_DATA.pages.reduce((s, p) => s + p.sentences.length, 0);
  let done = 0;
  for (let i = 0; i < currentPageIdx; i++) done += BOOK_DATA.pages[i].sentences.length;
  done += currentSentIdx;
  document.getElementById('progress-label').textContent = `${done + 1} / ${totalSents}`;

  // 隐藏评分区
  document.getElementById('score-area').classList.add('hidden');
  document.getElementById('btn-record').textContent = '🎤 开始录音';
  document.getElementById('btn-record').disabled = false;

  // 保存断点
  saveSession();
}

// ── 播放参考音频 ──────────────────────────────────────────────────────────────
function playRef() {
  document.getElementById('ref-audio').play();
}

// ── 录音 ─────────────────────────────────────────────────────────────────────
async function toggleRecord() {
  if (isRecording) {
    stopRecord();
  } else {
    await startRecord();
  }
}

async function startRecord() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
    mediaRecorder.onstop = submitAudio;
    mediaRecorder.start();
    isRecording = true;
    document.getElementById('btn-record').textContent = '⏹ 停止录音';
    document.getElementById('btn-record').classList.replace('bg-red-500', 'bg-orange-500');
  } catch (e) {
    alert('无法获取麦克风权限，请在浏览器设置中允许访问麦克风。');
  }
}

function stopRecord() {
  if (mediaRecorder && isRecording) {
    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach(t => t.stop());
    isRecording = false;
    document.getElementById('btn-record').textContent = '⏳ 评分中...';
    document.getElementById('btn-record').disabled = true;
  }
}

async function submitAudio() {
  const page = BOOK_DATA.pages[currentPageIdx];
  const sentence = page.sentences[currentSentIdx];

  const blob = new Blob(audioChunks, { type: 'audio/webm' });
  const fd = new FormData();
  fd.append('audio', blob, 'recording.webm');
  fd.append('text', sentence);
  fd.append('book_id', BOOK_DATA.id);
  fd.append('book_title', BOOK_DATA.title);
  fd.append('level', BOOK_LEVEL);
  fd.append('page', String(page.page));

  try {
    const res = await fetch('/api/raz/assess', { method: 'POST', body: fd });
    if (res.ok) {
      const data = await res.json();
      showScore(data.score, data.feedback);
    } else {
      const err = await res.json();
      if (err.detail && err.detail.includes('过短')) {
        alert('录音过短，请重新录制。');
      } else {
        showScoreError();
      }
    }
  } catch {
    showScoreError();
  }
}

function showScore(score, feedback) {
  const area = document.getElementById('score-area');
  const badge = document.getElementById('score-badge');
  const feedbackEl = document.getElementById('score-feedback');
  area.classList.remove('hidden');

  if (score >= 90) {
    badge.textContent = `${score} 优`;
    badge.className = 'text-5xl font-bold mb-2 text-green-600';
  } else if (score >= 70) {
    badge.textContent = `${score} 良`;
    badge.className = 'text-5xl font-bold mb-2 text-yellow-500';
  } else {
    badge.textContent = `${score} 加油`;
    badge.className = 'text-5xl font-bold mb-2 text-red-500';
  }
  feedbackEl.textContent = feedback;
}

function showScoreError() {
  document.getElementById('score-area').classList.remove('hidden');
  document.getElementById('score-badge').textContent = '⚠️';
  document.getElementById('score-feedback').textContent = '评分失败，可重试或跳过。';
  document.getElementById('btn-record').textContent = '🎤 开始录音';
  document.getElementById('btn-record').disabled = false;
  document.getElementById('btn-record').classList.replace('bg-orange-500', 'bg-red-500');
}

// ── 导航 ─────────────────────────────────────────────────────────────────────
function nextSentence(skip) {
  const page = BOOK_DATA.pages[currentPageIdx];
  if (currentSentIdx + 1 < page.sentences.length) {
    currentSentIdx++;
  } else if (currentPageIdx + 1 < BOOK_DATA.pages.length) {
    currentPageIdx++;
    currentSentIdx = 0;
  } else {
    showFinished();
    return;
  }
  renderCurrent();
  checkDailyGoal();
}

function retryRecord() {
  document.getElementById('score-area').classList.add('hidden');
  document.getElementById('btn-record').textContent = '🎤 开始录音';
  document.getElementById('btn-record').disabled = false;
  document.getElementById('btn-record').className =
    'bg-red-500 hover:bg-red-600 text-white font-semibold px-5 py-2 rounded-lg flex items-center gap-2';
}

function showFinished() {
  document.getElementById('current-sentence').textContent = '🎉 本书练习完成！';
  document.getElementById('btn-record').disabled = true;
  document.getElementById('btn-play').disabled = true;
}

async function checkDailyGoal() {
  try {
    const res = await fetch('/api/raz/config');
    const data = await res.json();
    if (data.today_count >= DAILY_COUNT) {
      document.getElementById('goal-banner').classList.remove('hidden');
    }
  } catch {}
}

async function saveSession() {
  const page = BOOK_DATA.pages[currentPageIdx];
  await fetch('/api/raz/session', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      book_id: BOOK_DATA.id,
      page: page.page,
      sentence_index: currentSentIdx,
    })
  });
}

init();
</script>
{% endblock %}
```

- [ ] **Step 2: 手动测试练习页**

访问 http://localhost:8000/raz/practice/a/sample-book

验证：
- PDF iframe 加载（占位文件显示空白正常）
- 音频参考无报错
- 点击"🎤 开始录音"能弹出麦克风权限请求
- 录音后显示评分（Mock 返回随机分数）
- 点击"下一句"正常跳转

- [ ] **Step 3: Commit**

```bash
git add app/templates/raz/practice.html
git commit -m "feat(raz): add sentence practice template with recording and scoring"
```

---

## Task 9: 模板 - 进度总览页 + 导航栏

**Files:**
- Create: `app/templates/raz/progress.html`
- Modify: `app/templates/base.html`

- [ ] **Step 1: 新建 `app/templates/raz/progress.html`**

```html
{% extends "base.html" %}
{% block title %}RAZ 练习进度{% endblock %}
{% block content %}
<div class="max-w-2xl mx-auto px-4 py-6">
  <a href="/raz" class="text-blue-500 hover:underline text-sm">← 返回书库</a>
  <h1 class="text-2xl font-bold text-gray-800 mt-4 mb-6">📊 今日练习进度</h1>

  <div class="bg-white rounded-xl shadow p-5 mb-6">
    <p class="text-gray-600">今日已完成
      <span class="text-3xl font-bold text-blue-600 mx-2">{{ today_count }}</span>
      句
    </p>
    <p class="text-sm text-gray-400 mt-1">
      目标：{{ config.daily_count }} 句（{{ config.daily_mode == 'smart' and '智能推荐' or '手动设置' }}）
    </p>
  </div>

  {% if today_records %}
  <div class="bg-white rounded-xl shadow p-5">
    <h2 class="font-semibold text-gray-700 mb-3">今日练习记录</h2>
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="text-gray-500 border-b">
          <tr>
            <th class="text-left py-1 pr-3">句子</th>
            <th class="text-center py-1 px-2">评分</th>
            <th class="text-right py-1 pl-2">时间</th>
          </tr>
        </thead>
        <tbody>
          {% for r in today_records %}
          <tr class="border-b border-gray-50">
            <td class="py-1 pr-3 text-gray-700">{{ r.sentence }}</td>
            <td class="text-center py-1 px-2">
              <span class="font-bold {% if r.score >= 90 %}text-green-600{% elif r.score >= 70 %}text-yellow-500{% else %}text-red-500{% endif %}">
                {{ r.score }}
              </span>
            </td>
            <td class="text-right py-1 pl-2 text-gray-400">{{ r.timestamp.strftime('%H:%M') }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
  {% else %}
  <div class="text-center text-gray-400 py-10">今日暂无练习记录</div>
  {% endif %}
</div>
{% endblock %}
```

- [ ] **Step 2: 在 `app/templates/base.html` 导航栏新增 RAZ 入口**

找到导航栏中英语入口附近，追加 RAZ 入口。定位现有导航项（通常包含"英语"字样的 `<a>` 标签），在其后追加：

```html
<a href="/raz" class="...">📖 RAZ 跟读</a>
```

具体 class 与已有导航项保持一致（与其他 `<a>` 使用相同样式）。

- [ ] **Step 3: 整体测试**

```bash
pytest tests/ -v
```

Expected: 所有测试 PASS

访问各页面验证：
- http://localhost:8000/raz — 书库首页（含 sample-book）
- http://localhost:8000/raz/book/a/sample-book — 书详情
- http://localhost:8000/raz/practice/a/sample-book — 练习页（录音 + Mock 评分）
- http://localhost:8000/raz/progress — 进度页

- [ ] **Step 4: 最终 Commit**

```bash
git add app/templates/raz/progress.html app/templates/base.html
git commit -m "feat(raz): add progress page and navigation entry"
```

---

## 完成后的验证清单

- [ ] `pytest tests/ -v` 全部通过
- [ ] 书库首页正确展示 level-a 的书籍列表
- [ ] Level 切换后页面刷新显示对应书籍
- [ ] 练习页：听示范音频 → 录音 → 显示 Mock 评分 → 下一句流程畅通
- [ ] 刷新练习页后，从最后断点继续（current_session 生效）
- [ ] 今日进度页正确显示已练习句数和记录
- [ ] `SPEECH_ASSESSOR=mock` 环境变量生效（默认 mock）
- [ ] `data/raz-records/YYYY-MM-DD.md` 文件在练习后自动生成

---

## 注意事项

1. **阿里云 实现**：`AliyunSpeechAssessor.assess()` 目前抛出 `NotImplementedError`，需根据实际申请的阿里云产品（英语口语评测）补充实现。配置环境变量 `SPEECH_ASSESSOR=aliyun` 后启用。

2. **真实书库内容**：将 PDF 和 MP3 文件放入 `data/raz/level-{x}/{book-dir}/`，并创建对应 `book.json`，格式参考 `data/raz/level-a/sample-book/book.json`。

3. **pydub / ffmpeg**：如 AliyunSpeechAssessor 需要 WAV 格式转换，需在系统安装 ffmpeg：
   - macOS: `brew install ffmpeg`
   - Ubuntu: `apt install ffmpeg`
