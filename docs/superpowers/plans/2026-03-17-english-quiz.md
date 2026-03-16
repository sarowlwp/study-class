# 英语抽测卡功能实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现英语单词抽测卡功能模块，支持听音选词、看词选义、看义选词三种模式。

**Architecture:** 参考现有汉字抽测卡架构，独立实现英语模块。使用 Markdown 文件存储单词数据，内存存储抽测会话，复用现有记录存储逻辑。

**Tech Stack:** FastAPI, Jinja2, Tailwind CSS, Web Speech API

---

## 文件结构规划

### 新建文件
- `app/models/english_word.py` - 英语单词数据模型
- `app/services/english_service.py` - 英语单词数据服务
- `app/services/english_quiz_service.py` - 英语抽测服务
- `app/routers/english.py` - 英语路由（页面+API）
- `app/templates/english/index.html` - 英语首页
- `app/templates/english/quiz.html` - 英语抽测页面
- `app/templates/english/result.html` - 英语结果页面
- `app/templates/english/mistakes.html` - 英语错词本
- `data/english/grade3-autumn.md` - 示例数据文件

### 修改文件
- `app/config.py` - 添加 ENGLISH_DIR 配置
- `app/main.py` - 注册英语路由
- `app/templates/index.html` - 添加英语导航入口
- `app/models/__init__.py` - 导出英语模型
- `app/services/__init__.py` - 导出英语服务
- `app/routers/__init__.py` - 导出英语路由

---

## Task 1: 配置和基础设置

**Files:**
- Modify: `app/config.py`
- Modify: `app/models/__init__.py`
- Modify: `app/services/__init__.py`
- Modify: `app/routers/__init__.py`

### Step 1: 添加英语数据目录配置

```python
# app/config.py 中添加
ENGLISH_DIR = DATA_DIR / "english"
ENGLISH_DIR.mkdir(parents=True, exist_ok=True)
```

验证：
```bash
python -c "from app.config import ENGLISH_DIR; print(ENGLISH_DIR)"
# Expected: 输出目录路径，且目录已创建
```

### Step 2: 更新 models/__init__.py

```python
# app/models/__init__.py
from app.models.character import Character, QuizMode, ResultType
from app.models.record import QuizRecord, QuizSessionState
from app.models.english_word import EnglishWord, EnglishQuizMode, EnglishQuizRecord, EnglishQuizSessionState

__all__ = [
    "Character",
    "QuizMode",
    "ResultType",
    "QuizRecord",
    "QuizSessionState",
    "EnglishWord",
    "EnglishQuizMode",
    "EnglishQuizRecord",
    "EnglishQuizSessionState",
]
```

### Step 3: 更新 services/__init__.py

```python
# app/services/__init__.py
from app.services.character_service import CharacterService
from app.services.quiz_service import QuizService
from app.services.record_service import RecordService
from app.services.english_service import EnglishService
from app.services.english_quiz_service import EnglishQuizService

__all__ = [
    "CharacterService",
    "QuizService",
    "RecordService",
    "EnglishService",
    "EnglishQuizService",
]
```

### Step 4: 更新 routers/__init__.py

```python
# app/routers/__init__.py
from app.routers.pages import router as pages_router
from app.routers.api import router as api_router
from app.routers.english import router as english_router

__all__ = ["pages_router", "api_router", "english_router"]
```

### Step 5: Commit

```bash
git add app/config.py app/models/__init__.py app/services/__init__.py app/routers/__init__.py
git commit -m "chore: add english module configuration and exports"
```

---

## Task 2: 英语单词数据模型

**Files:**
- Create: `app/models/english_word.py`

### Step 1: 创建 EnglishWord 模型

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List


class EnglishQuizMode(str, Enum):
    """英语抽测模式"""
    AUDIO_TO_WORD = "audio_to_word"      # 听音选词
    WORD_TO_MEANING = "word_to_meaning"  # 看词选义
    MEANING_TO_WORD = "meaning_to_word"  # 看义选词


class ResultType(str, Enum):
    """评测结果类型（复用现有）"""
    MASTERED = "mastered"
    FUZZY = "fuzzy"
    NOT_MASTERED = "not_mastered"


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
```

### Step 2: Commit

```bash
git add app/models/english_word.py
git commit -m "feat(models): add english word data models"
```

---

## Task 3: 英语单词服务

**Files:**
- Create: `app/services/english_service.py`
- Create: `tests/test_english_service.py`

### Step 1: 创建测试文件

```python
# tests/test_english_service.py
import pytest
from pathlib import Path
from app.services.english_service import EnglishService
from app.models.english_word import EnglishWord


class TestEnglishService:
    def test_parse_file_not_found(self):
        service = EnglishService()
        result = service._parse_file("nonexistent.md")
        assert result == []

    def test_map_headers(self):
        service = EnglishService()
        headers = ["单词", "音标", "释义", "例句"]
        mapping = service._map_headers(headers)
        assert mapping["word"] == 0
        assert mapping["phonetic"] == 1
        assert mapping["meaning"] == 2
        assert mapping["example"] == 3
```

### Step 2: 运行测试（预期失败）

```bash
pytest tests/test_english_service.py -v
# Expected: ImportError or module not found
```

### Step 3: 创建 EnglishService

```python
# app/services/english_service.py
import re
from pathlib import Path
from typing import List, Dict, Optional

from app.config import ENGLISH_DIR
from app.models.english_word import EnglishWord


class EnglishService:
    """英语单词数据管理服务"""

    def __init__(self):
        self._cache: Dict[str, List[EnglishWord]] = {}

    def _parse_file(self, filename: str) -> List[EnglishWord]:
        """解析 Markdown 文件"""
        filepath = ENGLISH_DIR / filename
        if not filepath.exists():
            return []

        content = filepath.read_text(encoding="utf-8")
        words = []

        # 解析学期名称
        semester_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        semester = semester_match.group(1) if semester_match else filename

        # 解析单元和表格
        lesson_pattern = r"^##\s+(.+)$\n+\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|\n\|[-:|\s]+\|\n((?:\|[^\n]+\|\n?)+)"

        for match in re.finditer(lesson_pattern, content, re.MULTILINE):
            lesson_name = match.group(1).strip()
            table_content = match.group(8)

            # 解析表头
            headers = [
                match.group(2).strip().lower(),
                match.group(3).strip().lower(),
                match.group(4).strip().lower(),
                match.group(5).strip().lower(),
                match.group(6).strip().lower(),
                match.group(7).strip().lower(),
            ]
            field_map = self._map_headers(headers)

            # 解析表格行
            for line in table_content.strip().split("\n"):
                if not line.startswith("|"):
                    continue

                cells = [c.strip() for c in line.split("|")[1:-1]]
                if len(cells) < 6:
                    continue

                word = cells[field_map.get("word", 0)]
                phonetic = cells[field_map.get("phonetic", 1)]
                meaning = cells[field_map.get("meaning", 2)]
                example = cells[field_map.get("example", 3)]
                example_cn = cells[field_map.get("example_cn", 4)]
                image_keyword = cells[field_map.get("image_keyword", 5)]

                # 验证单词
                if not word or not word.isalpha():
                    continue

                words.append(
                    EnglishWord(
                        word=word,
                        phonetic=phonetic if phonetic else None,
                        meaning=meaning,
                        example=example if example else None,
                        example_cn=example_cn if example_cn else None,
                        lesson=lesson_name,
                        semester=semester,
                        image_keyword=image_keyword if image_keyword else None,
                    )
                )

        return words

    def _map_headers(self, headers: List[str]) -> Dict[str, int]:
        """映射表头到标准字段"""
        field_map = {}
        keywords = {
            "word": ["单词", "word"],
            "phonetic": ["音标", "phonetic", "发音"],
            "meaning": ["释义", "meaning", "意思", "中文"],
            "example": ["例句", "example", "例", "英文例句"],
            "example_cn": ["例句翻译", "example_cn", "翻译", "中文翻译"],
            "image_keyword": ["图片关键词", "image_keyword", "图片", "keyword"],
        }

        for i, header in enumerate(headers):
            for field, keys in keywords.items():
                if any(k in header for k in keys):
                    field_map[field] = i
                    break

        return field_map

    def get_semesters(self) -> List[Dict]:
        """获取所有年级列表"""
        semesters = []
        for filepath in ENGLISH_DIR.glob("*.md"):
            content = filepath.read_text(encoding="utf-8")
            match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            name = match.group(1) if match else filepath.stem

            words = self._parse_file(filepath.name)

            semesters.append({
                "id": filepath.stem,
                "name": name,
                "file": filepath.name,
                "total_words": len(words)
            })

        return sorted(semesters, key=lambda x: x["id"])

    def get_lessons(self, semester_id: str) -> List[Dict]:
        """获取指定年级的单元列表"""
        words = self._parse_file(f"{semester_id}.md")

        lessons = {}
        for word in words:
            if word.lesson not in lessons:
                lessons[word.lesson] = {"count": 0, "words": []}
            lessons[word.lesson]["count"] += 1
            lessons[word.lesson]["words"].append(word.word)

        return [
            {
                "id": f"lesson-{i+1}",
                "name": name,
                "word_count": data["count"],
            }
            for i, (name, data) in enumerate(lessons.items())
        ]

    def get_words(self, semester_id: str, lessons: Optional[List[str]] = None) -> List[EnglishWord]:
        """获取单词列表"""
        words = self._parse_file(f"{semester_id}.md")

        if lessons:
            words = [w for w in words if w.lesson in lessons]

        return words

    def get_all_words(self) -> List[EnglishWord]:
        """获取所有单词"""
        all_words = []
        for filepath in ENGLISH_DIR.glob("*.md"):
            all_words.extend(self._parse_file(filepath.name))
        return all_words
```

### Step 4: 运行测试（预期通过）

```bash
pytest tests/test_english_service.py -v
# Expected: 2 passed
```

### Step 5: Commit

```bash
git add app/services/english_service.py tests/test_english_service.py
git commit -m "feat(services): add english word service with markdown parsing"
```

---

## Task 4: 英语抽测服务

**Files:**
- Create: `app/services/english_quiz_service.py`
- Create: `tests/test_english_quiz_service.py`

### Step 1: 创建测试文件

```python
# tests/test_english_quiz_service.py
import pytest
from datetime import datetime
from app.services.english_quiz_service import EnglishQuizService
from app.services.english_service import EnglishService
from app.models.english_word import EnglishWord, EnglishQuizMode, ResultType


class TestEnglishQuizService:
    def test_generate_options(self):
        service = EnglishQuizService(None, None)
        correct = EnglishWord(word="cat", meaning="猫", lesson="Unit 1", semester="Grade 3")
        all_words = [
            correct,
            EnglishWord(word="dog", meaning="狗", lesson="Unit 1", semester="Grade 3"),
            EnglishWord(word="pig", meaning="猪", lesson="Unit 1", semester="Grade 3"),
            EnglishWord(word="cow", meaning="牛", lesson="Unit 1", semester="Grade 3"),
        ]

        options = service._generate_options(correct, all_words, 4)

        assert len(options) == 4
        assert any(opt["is_correct"] for opt in options)
        assert sum(1 for opt in options if opt["is_correct"]) == 1

    def test_generate_options_not_enough_words(self):
        service = EnglishQuizService(None, None)
        correct = EnglishWord(word="cat", meaning="猫", lesson="Unit 1", semester="Grade 3")
        all_words = [correct, EnglishWord(word="dog", meaning="狗", lesson="Unit 1", semester="Grade 3")]

        options = service._generate_options(correct, all_words, 4)

        assert len(options) == 2  # Only 2 available
```

### Step 2: 运行测试（预期失败）

```bash
pytest tests/test_english_quiz_service.py -v
# Expected: ImportError or AttributeError
```

### Step 3: 创建 EnglishQuizService

```python
# app/services/english_quiz_service.py
import random
import uuid
from datetime import datetime, date
from typing import Dict, List, Optional

from app.models.english_word import EnglishWord, EnglishQuizMode, EnglishQuizRecord, EnglishQuizSessionState, ResultType
from app.services.english_service import EnglishService
from app.services.record_service import RecordService


class EnglishQuizService:
    """英语抽测服务"""

    _sessions: Dict[str, EnglishQuizSessionState] = {}

    def __init__(self, english_service: EnglishService, record_service: RecordService):
        self.english_service = english_service
        self.record_service = record_service

    def _cleanup_expired_sessions(self):
        """清理过期会话（24小时）"""
        now = datetime.now()
        expired = [
            sid for sid, session in self._sessions.items()
            if (now - session.created_at).total_seconds() > 86400
        ]
        for sid in expired:
            del self._sessions[sid]

    def generate_quiz(
        self,
        semester_id: str,
        lessons: List[str],
        count: int,
        mode_mix: float = 0.33
    ) -> EnglishQuizSessionState:
        """生成抽测会话"""
        self._cleanup_expired_sessions()

        all_words = self.english_service.get_words(semester_id, lessons)

        if not all_words:
            raise ValueError("No words available")

        # 根据掌握度分组
        priority_groups = {
            "not_mastered": [],
            "fuzzy": [],
            "new": [],
            "mastered": []
        }

        for word in all_words:
            status = self.record_service.get_english_mastery_status(word.word, word.lesson)
            word.mastery_status = status
            priority_groups[status].append(word)

        # 按优先级选择
        selected = []
        priorities = ["not_mastered", "fuzzy", "new", "mastered"]

        for priority in priorities:
            words = priority_groups[priority]
            random.shuffle(words)
            needed = count - len(selected)
            if needed <= 0:
                break
            selected.extend(words[:needed])

        # 分配抽测模式
        quiz_items = []
        for word in selected:
            rand = random.random()
            if rand < mode_mix:
                mode = EnglishQuizMode.AUDIO_TO_WORD
            elif rand < mode_mix * 2:
                mode = EnglishQuizMode.WORD_TO_MEANING
            else:
                mode = EnglishQuizMode.MEANING_TO_WORD

            quiz_items.append({
                "word": word.word,
                "meaning": word.meaning,
                "phonetic": word.phonetic,
                "example": word.example,
                "example_cn": word.example_cn,
                "lesson": word.lesson,
                "mode": mode.value,
                "options": self._generate_options(word, all_words, min(4, len(all_words)))
            })

        session = EnglishQuizSessionState(
            session_id=str(uuid.uuid4())[:12],
            created_at=datetime.now(),
            total=len(quiz_items),
            lessons=lessons,
            words=quiz_items
        )

        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[EnglishQuizSessionState]:
        """获取会话状态"""
        self._cleanup_expired_sessions()
        return self._sessions.get(session_id)

    def submit_answer(self, session_id: str, index: int, answer: str) -> Dict:
        """提交答案，返回是否正确及正确答案"""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError("Session not found or expired")

        if index < 0 or index >= len(session.words):
            raise ValueError("Invalid index")

        word_data = session.words[index]
        correct_answer = word_data["word"]
        is_correct = answer.lower() == correct_answer.lower()

        # 记录结果
        result = ResultType.MASTERED if is_correct else ResultType.NOT_MASTERED
        record = EnglishQuizRecord(
            word=word_data["word"],
            meaning=word_data["meaning"],
            lesson=word_data["lesson"],
            mode=EnglishQuizMode(word_data["mode"]),
            result=result
        )
        session.add_record(record)
        session.current_index = max(session.current_index, index + 1)

        return {
            "is_correct": is_correct,
            "correct_answer": correct_answer,
            "your_answer": answer,
            "word": word_data
        }

    def finish_quiz(self, session_id: str) -> Dict:
        """完成抽测，保存记录"""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError("Session not found or expired")

        session.completed = True
        self.record_service.save_english_records(
            session.created_at.date(),
            session.records
        )
        return session.get_summary()

    def _generate_options(
        self,
        correct: EnglishWord,
        all_words: List[EnglishWord],
        option_count: int = 4
    ) -> List[Dict]:
        """生成选项，包含正确答案和干扰项"""
        # 过滤掉正确答案的候选干扰项
        distractors = [
            w for w in all_words
            if w.word != correct.word and w.meaning != correct.meaning
        ]

        # 随机选择干扰项
        selected_count = min(option_count - 1, len(distractors))
        selected = random.sample(distractors, selected_count) if distractors else []

        # 构建选项列表
        options = [
            {"word": correct.word, "meaning": correct.meaning, "phonetic": correct.phonetic, "is_correct": True}
        ]
        for word in selected:
            options.append({
                "word": word.word,
                "meaning": word.meaning,
                "phonetic": word.phonetic,
                "is_correct": False
            })

        # 随机打乱顺序
        random.shuffle(options)
        return options
```

### Step 4: 运行测试（预期通过）

```bash
pytest tests/test_english_quiz_service.py -v
# Expected: 2 passed
```

### Step 5: Commit

```bash
git add app/services/english_quiz_service.py tests/test_english_quiz_service.py
git commit -m "feat(services): add english quiz service with session management"
```

---

## Task 5: 扩展记录服务支持英语

**Files:**
- Modify: `app/services/record_service.py`

### Step 1: 添加英语记录方法

在 `app/services/record_service.py` 中添加以下方法（在现有类中）：

```python
def save_english_records(self, record_date: date, records: List):
    """保存英语评测记录"""
    from app.models.english_word import EnglishQuizRecord

    filename = RECORDS_DIR / f"english-{record_date.isoformat()}.md"

    # 统计
    counts = defaultdict(int)
    for r in records:
        counts[r.result.value] += 1

    # 生成 Markdown
    lines = [
        f"# {record_date.isoformat()} 英语评测记录\n",
        "## 统计",
        f"- 总数: {len(records)}",
        f"- 掌握: {counts['mastered']}",
        f"- 模糊: {counts['fuzzy']}",
        f"- 未掌握: {counts['not_mastered']}",
        f"- 正确率: {counts['mastered'] / len(records) * 100:.1f}%\n" if records else "- 正确率: 0%\n",
        "## 评测结果\n",
        "| 单词 | 释义 | 课文 | 模式 | 结果 | 时间 |",
        "|------|------|------|------|------|------|"
    ]

    for r in records:
        lines.append(
            f"| {r.word} | {r.meaning} | {r.lesson} | {r.mode.value} | {r.result.value} | {r.timestamp.strftime('%H:%M:%S')} |"
        )

    filename.write_text('\n'.join(lines), encoding='utf-8')

def get_english_mastery_status(self, word: str, lesson: str) -> str:
    """获取单词掌握状态"""
    from app.models.english_word import EnglishQuizMode, ResultType

    records = self.get_all_english_records()
    word_records = [r for r in records if r.word == word and r.lesson == lesson]

    if not word_records:
        return "new"

    word_records.sort(key=lambda r: r.timestamp, reverse=True)
    recent = word_records[:3]
    latest = recent[0].result

    if latest == ResultType.NOT_MASTERED:
        return "not_mastered"
    if latest == ResultType.FUZZY:
        return "fuzzy"

    mastered_count = sum(1 for r in recent if r.result == ResultType.MASTERED)
    if mastered_count >= 2:
        return "mastered"
    return "fuzzy"

def get_all_english_records(self) -> List:
    """获取所有英语评测记录"""
    from app.models.english_word import EnglishQuizRecord, EnglishQuizMode, ResultType

    records = []
    for filepath in sorted(RECORDS_DIR.glob("english-*.md")):
        records.extend(self._parse_english_record_file(filepath))
    return records

def _parse_english_record_file(self, filepath: Path) -> List:
    """解析英语记录文件"""
    from app.models.english_word import EnglishQuizRecord, EnglishQuizMode, ResultType

    content = filepath.read_text(encoding='utf-8')
    records = []

    table_match = re.search(
        r'## 评测结果\n+\|[^\n]+\|\n\|[-:|\s]+\|\n((?:\|[^\n]+\|\n?)+)',
        content
    )

    if table_match:
        for line in table_match.group(1).strip().split('\n'):
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if len(cells) >= 6:
                date_str = filepath.stem.replace("english-", "")
                time_str = cells[5]
                timestamp = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")

                records.append(EnglishQuizRecord(
                    word=cells[0],
                    meaning=cells[1],
                    lesson=cells[2],
                    mode=EnglishQuizMode(cells[3]),
                    result=ResultType(cells[4]),
                    timestamp=timestamp
                ))

    return records

def get_english_mistakes(self) -> List[Dict]:
    """获取英语错词本"""
    all_records = self.get_all_english_records()

    word_stats = defaultdict(lambda: {"count": 0, "last": None, "lesson": None, "meaning": None})

    for r in all_records:
        if r.result == ResultType.NOT_MASTERED:
            key = (r.word, r.lesson)
            word_stats[key]["count"] += 1
            word_stats[key]["last"] = r.timestamp
            word_stats[key]["lesson"] = r.lesson
            word_stats[key]["meaning"] = r.meaning

    mistakes = []
    for (word, lesson), stats in word_stats.items():
        mistakes.append({
            "word": word,
            "meaning": stats["meaning"],
            "lesson": stats["lesson"],
            "mistake_count": stats["count"],
            "last_tested": stats["last"].strftime("%Y-%m-%d") if stats["last"] else None
        })

    mistakes.sort(key=lambda x: x["mistake_count"], reverse=True)
    return mistakes
```

### Step 2: Commit

```bash
git add app/services/record_service.py
git commit -m "feat(services): extend record service to support english quiz records"
```

---

## Task 6: 英语路由

**Files:**
- Create: `app/routers/english.py`

### Step 1: 创建路由文件

```python
# app/routers/english.py
from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional

from app.config import BASE_DIR
from app.services.english_service import EnglishService
from app.services.english_quiz_service import EnglishQuizService
from app.services.record_service import RecordService

router = APIRouter()
templates = Jinja2Templates(directory=BASE_DIR / "app" / "templates")

# 服务实例
english_service = EnglishService()
record_service = RecordService()
english_quiz_service = EnglishQuizService(english_service, record_service)


class StartQuizRequest(BaseModel):
    semester_id: str
    lessons: List[str]
    count: int = 20


class SubmitAnswerRequest(BaseModel):
    session_id: str
    index: int
    answer: str


# ========== 页面路由 ==========

@router.get("/english")
async def english_index(request: Request):
    """英语抽测首页"""
    semesters = english_service.get_semesters()
    return templates.TemplateResponse("english/index.html", {
        "request": request,
        "semesters": semesters
    })


@router.get("/english/quiz")
async def english_quiz_page(request: Request, session: str):
    """英语抽测页面"""
    return templates.TemplateResponse("english/quiz.html", {
        "request": request,
        "session_id": session
    })


@router.get("/english/result")
async def english_result_page(request: Request, session: str):
    """英语结果页面"""
    return templates.TemplateResponse("english/result.html", {
        "request": request,
        "session_id": session
    })


@router.get("/english/mistakes")
async def english_mistakes_page(request: Request):
    """英语错词本"""
    return templates.TemplateResponse("english/mistakes.html", {
        "request": request
    })


# ========== API 路由 ==========

@router.get("/api/english/semesters")
async def api_english_semesters():
    """获取所有年级"""
    return english_service.get_semesters()


@router.get("/api/english/lessons")
async def api_english_lessons(semester: str):
    """获取单元列表"""
    return english_service.get_lessons(semester)


@router.post("/api/english/quiz/start")
async def api_start_quiz(request: StartQuizRequest):
    """开始抽测"""
    try:
        count = max(5, min(50, request.count))
        session = english_quiz_service.generate_quiz(
            semester_id=request.semester_id,
            lessons=request.lessons,
            count=count
        )
        return {"session_id": session.session_id, "total": session.total}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/english/quiz/session/{session_id}")
async def api_get_session(session_id: str):
    """获取会话状态"""
    session = english_quiz_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session.session_id,
        "total": session.total,
        "current_index": session.current_index,
        "words": session.words,
        "completed": session.completed
    }


@router.post("/api/english/quiz/submit")
async def api_submit_answer(request: SubmitAnswerRequest):
    """提交答案"""
    try:
        result = english_quiz_service.submit_answer(
            session_id=request.session_id,
            index=request.index,
            answer=request.answer
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/english/quiz/finish")
async def api_finish_quiz(request: dict):
    """完成抽测"""
    session_id = request.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    try:
        summary = english_quiz_service.finish_quiz(session_id)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/english/mistakes")
async def api_get_mistakes():
    """获取错词本"""
    return record_service.get_english_mistakes()


@router.get("/api/english/stats")
async def api_get_stats():
    """获取学习统计"""
    records = record_service.get_all_english_records()

    from collections import defaultdict
    from datetime import date

    daily_stats = defaultdict(lambda: {"total": 0, "mastered": 0})
    for r in records:
        date_str = r.timestamp.strftime("%Y-%m-%d")
        daily_stats[date_str]["total"] += 1
        if r.result.value == "mastered":
            daily_stats[date_str]["mastered"] += 1

    dates = sorted(daily_stats.keys(), reverse=True)
    streak = 0
    today = date.today().isoformat()
    yesterday = date.fromordinal(date.today().toordinal() - 1).isoformat()

    if dates and (dates[0] == today or dates[0] == yesterday):
        streak = 1
        for i in range(1, len(dates)):
            expected = date.fromordinal(date.fromisoformat(dates[i-1]).toordinal() - 1).isoformat()
            if dates[i] == expected:
                streak += 1
            else:
                break

    return {
        "total_records": len(records),
        "streak_days": streak,
        "daily_stats": [
            {"date": d, **stats}
            for d, stats in sorted(daily_stats.items())[-7:]
        ]
    }
```

### Step 2: Commit

```bash
git add app/routers/english.py
git commit -m "feat(routers): add english quiz routes (pages and api)"
```

---

## Task 7: 前端模板 - 首页

**Files:**
- Create: `app/templates/english/index.html`

### Step 1: 创建英语首页模板

```html
{% extends "base.html" %}

{% block title %}英语抽测 - 首页{% endblock %}

{% block content %}
<div class="max-w-4xl mx-auto">
    <h1 class="text-3xl font-bold text-gray-800 mb-8 text-center">🔤 英语单词抽测</h1>

    <div class="bg-white rounded-2xl shadow-lg p-8">
        <form id="quiz-form" class="space-y-6">
            <!-- 年级选择 -->
            <div>
                <label class="block text-gray-700 font-bold mb-2">选择年级</label>
                <select id="semester" name="semester" class="w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500" required>
                    <option value="">请选择年级</option>
                    {% for semester in semesters %}
                    <option value="{{ semester.id }}">{{ semester.name }} ({{ semester.total_words }}词)</option>
                    {% endfor %}
                </select>
            </div>

            <!-- 单元选择 -->
            <div>
                <label class="block text-gray-700 font-bold mb-2">选择单元</label>
                <div id="lessons-container" class="space-y-2">
                    <p class="text-gray-500">请先选择年级</p>
                </div>
            </div>

            <!-- 题目数量 -->
            <div>
                <label class="block text-gray-700 font-bold mb-2">抽测数量</label>
                <div class="flex items-center space-x-4">
                    <input type="range" id="count-slider" min="5" max="30" value="20" class="flex-1">
                    <span id="count-display" class="text-xl font-bold text-blue-600 w-12">20</span>
                </div>
            </div>

            <!-- 开始按钮 -->
            <button type="submit" class="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-4 px-8 rounded-xl text-lg shadow-lg transition">
                开始抽测
            </button>
        </form>
    </div>

    <!-- 快捷入口 -->
    <div class="mt-8 grid grid-cols-2 gap-4">
        <a href="/english/mistakes" class="bg-red-50 hover:bg-red-100 p-6 rounded-xl text-center transition">
            <div class="text-3xl mb-2">❌</div>
            <div class="font-bold text-red-700">错词本</div>
        </a>
        <a href="/" class="bg-gray-50 hover:bg-gray-100 p-6 rounded-xl text-center transition">
            <div class="text-3xl mb-2">📚</div>
            <div class="font-bold text-gray-700">返回首页</div>
        </a>
    </div>
</div>

<script>
const semesterSelect = document.getElementById('semester');
const lessonsContainer = document.getElementById('lessons-container');
const countSlider = document.getElementById('count-slider');
const countDisplay = document.getElementById('count-display');
const quizForm = document.getElementById('quiz-form');

// 数量滑块
countSlider.addEventListener('input', () => {
    countDisplay.textContent = countSlider.value;
});

// 年级选择变化时加载单元
semesterSelect.addEventListener('change', async () => {
    const semesterId = semesterSelect.value;
    if (!semesterId) {
        lessonsContainer.innerHTML = '<p class="text-gray-500">请先选择年级</p>';
        return;
    }

    try {
        const response = await fetch(`/api/english/lessons?semester=${semesterId}`);
        const lessons = await response.json();

        if (lessons.length === 0) {
            lessonsContainer.innerHTML = '<p class="text-red-500">该年级暂无单元数据</p>';
            return;
        }

        lessonsContainer.innerHTML = lessons.map((lesson, index) => `
            <label class="flex items-center space-x-3 p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
                <input type="checkbox" name="lessons" value="${lesson.name}" class="w-5 h-5 text-blue-500" ${index === 0 ? 'checked' : ''}>
                <span class="flex-1">${lesson.name}</span>
                <span class="text-gray-500 text-sm">${lesson.word_count}词</span>
            </label>
        `).join('');
    } catch (error) {
        lessonsContainer.innerHTML = '<p class="text-red-500">加载失败，请重试</p>';
    }
});

// 表单提交
quizForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const semesterId = semesterSelect.value;
    const checkedLessons = Array.from(document.querySelectorAll('input[name="lessons"]:checked')).map(cb => cb.value);
    const count = parseInt(countSlider.value);

    if (!semesterId) {
        alert('请选择年级');
        return;
    }

    if (checkedLessons.length === 0) {
        alert('请至少选择一个单元');
        return;
    }

    try {
        const response = await fetch('/api/english/quiz/start', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                semester_id: semesterId,
                lessons: checkedLessons,
                count: count
            })
        });

        if (!response.ok) {
            const error = await response.json();
            alert(error.detail || '启动失败');
            return;
        }

        const data = await response.json();
        window.location.href = `/english/quiz?session=${data.session_id}`;
    } catch (error) {
        alert('网络错误，请重试');
    }
});
</script>
{% endblock %}
```

### Step 2: Commit

```bash
git add app/templates/english/index.html
git commit -m "feat(templates): add english quiz index page"
```

---

## Task 8: 前端模板 - 抽测页面

**Files:**
- Create: `app/templates/english/quiz.html`

### Step 1: 创建抽测页面

```html
{% extends "base.html" %}

{% block title %}英语抽测 - 进行中{% endblock %}

{% block content %}
<div class="max-w-2xl mx-auto">
    <!-- 进度条 -->
    <div class="mb-6">
        <div class="flex justify-between text-sm text-gray-600 mb-2">
            <span>进度</span>
            <span id="progress-text">1 / 20</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-3">
            <div id="progress-bar" class="bg-blue-500 h-3 rounded-full transition-all duration-300" style="width: 5%"></div>
        </div>
    </div>

    <!-- 抽测卡片 -->
    <div class="bg-white rounded-2xl shadow-xl p-8 mb-6 min-h-[400px] flex flex-col">
        <div id="question-area" class="flex-1 flex flex-col items-center justify-center">
            <!-- 动态内容 -->
        </div>
        <div id="feedback-area" class="hidden mt-6 p-4 rounded-xl text-center">
            <!-- 反馈信息 -->
        </div>
    </div>

    <!-- 选项区域 -->
    <div id="options-area" class="grid gap-4">
        <!-- 动态选项 -->
    </div>

    <!-- 下一题按钮 -->
    <button id="next-btn" class="hidden w-full mt-6 bg-green-500 hover:bg-green-600 text-white font-bold py-4 px-8 rounded-xl text-lg shadow-lg transition">
        下一题 →
    </button>
</div>

<script>
const sessionId = '{{ session_id }}';
let currentIndex = 0;
let words = [];
let total = 0;
let hasAnswered = false;

// 检测浏览器是否支持语音合成
const speechSupported = 'speechSynthesis' in window;

async function loadSession() {
    const response = await fetch(`/api/english/quiz/session/${sessionId}`);
    if (!response.ok) {
        alert('会话已过期，请重新开始');
        window.location.href = '/english';
        return;
    }
    const data = await response.json();
    words = data.words;
    total = data.total;
    currentIndex = data.current_index || 0;
    updateProgress();
    showQuestion();
}

function updateProgress() {
    const percent = ((currentIndex + 1) / total) * 100;
    document.getElementById('progress-bar').style.width = `${percent}%`;
    document.getElementById('progress-text').textContent = `${currentIndex + 1} / ${total}`;
}

function speakWord(word) {
    if (!speechSupported) {
        alert('您的浏览器不支持语音播放');
        return;
    }
    const utterance = new SpeechSynthesisUtterance(word);
    utterance.lang = 'en-US';
    utterance.rate = 0.8;
    utterance.pitch = 1.0;
    speechSynthesis.speak(utterance);
}

function showQuestion() {
    hasAnswered = false;
    const word = words[currentIndex];
    const questionArea = document.getElementById('question-area');
    const optionsArea = document.getElementById('options-area');
    const feedbackArea = document.getElementById('feedback-area');
    const nextBtn = document.getElementById('next-btn');

    feedbackArea.classList.add('hidden');
    nextBtn.classList.add('hidden');

    // 根据模式显示不同内容
    if (word.mode === 'audio_to_word') {
        // 听音选词
        questionArea.innerHTML = `
            <button onclick="speakWord('${word.word}')" class="w-32 h-32 rounded-full bg-blue-100 hover:bg-blue-200 flex items-center justify-center mb-4 transition">
                <span class="text-5xl">🔊</span>
            </button>
            <p class="text-gray-600 text-lg">点击播放，选择听到的单词</p>
        `;
        // 自动播放一次（如果支持）
        setTimeout(() => speakWord(word.word), 500);
    } else if (word.mode === 'word_to_meaning') {
        // 看词选义
        questionArea.innerHTML = `
            <div class="text-5xl font-bold text-gray-800 mb-2">${word.word}</div>
            ${word.phonetic ? `<div class="text-xl text-gray-500 mb-4">${word.phonetic}</div>` : ''}
            <p class="text-gray-600">选择正确的中文释义</p>
        `;
    } else {
        // 看义选词
        questionArea.innerHTML = `
            <div class="text-6xl mb-4">${getEmoji(word.meaning)}</div>
            <div class="text-3xl font-bold text-gray-800 mb-2">${word.meaning}</div>
            <p class="text-gray-600">选择正确的英文单词</p>
        `;
    }

    // 显示选项
    renderOptions(word);
}

function getEmoji(meaning) {
    // 简单的 emoji 映射，实际可以更完善
    const emojiMap = {
        '猫': '🐱', '狗': '🐕', '猪': '🐷', '牛': '🐄',
        '鸟': '🐦', '鱼': '🐟', '马': '🐴', '羊': '🐑',
        '苹果': '🍎', '香蕉': '🍌', '橙子': '🍊', '西瓜': '🍉',
        '红色': '🔴', '蓝色': '🔵', '绿色': '🟢', '黄色': '🟡',
    };
    return emojiMap[meaning] || '📝';
}

function renderOptions(word) {
    const optionsArea = document.getElementById('options-area');
    const isAudioMode = word.mode === 'audio_to_word';
    const isWordMode = word.mode === 'meaning_to_word';

    optionsArea.innerHTML = word.options.map((opt, index) => {
        if (isAudioMode || isWordMode) {
            // 显示单词选项
            return `
                <button onclick="selectOption('${opt.word}', ${opt.is_correct})" class="option-btn bg-white border-2 border-gray-200 hover:border-blue-400 p-4 rounded-xl text-lg font-medium transition text-left" data-word="${opt.word}">
                    <div class="font-bold">${opt.word}</div>
                    ${opt.phonetic ? `<div class="text-sm text-gray-500">${opt.phonetic}</div>` : ''}
                </button>
            `;
        } else {
            // 显示中文选项
            return `
                <button onclick="selectOption('${opt.word}', ${opt.is_correct})" class="option-btn bg-white border-2 border-gray-200 hover:border-blue-400 p-4 rounded-xl text-xl font-medium transition" data-word="${opt.word}">
                    ${opt.meaning}
                </button>
            `;
        }
    }).join('');
}

async function selectOption(answer, isCorrect) {
    if (hasAnswered) return;
    hasAnswered = true;

    const word = words[currentIndex];
    const feedbackArea = document.getElementById('feedback-area');
    const nextBtn = document.getElementById('next-btn');

    // 禁用所有选项
    document.querySelectorAll('.option-btn').forEach(btn => {
        btn.disabled = true;
        const btnWord = btn.getAttribute('data-word');
        if (btnWord === word.word) {
            btn.classList.add('bg-green-100', 'border-green-500');
        } else if (btnWord === answer && !isCorrect) {
            btn.classList.add('bg-red-100', 'border-red-500');
        }
    });

    // 显示反馈
    if (isCorrect) {
        feedbackArea.className = 'mt-6 p-4 rounded-xl text-center bg-green-100 text-green-800';
        feedbackArea.innerHTML = '✅ 回答正确！';
    } else {
        feedbackArea.className = 'mt-6 p-4 rounded-xl text-center bg-red-100 text-red-800';
        feedbackArea.innerHTML = `❌ 回答错误，正确答案是：<span class="font-bold">${word.word}</span>`;
    }
    feedbackArea.classList.remove('hidden');

    // 提交答案
    await fetch('/api/english/quiz/submit', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            session_id: sessionId,
            index: currentIndex,
            answer: answer
        })
    });

    // 显示下一题按钮或完成
    if (currentIndex < total - 1) {
        nextBtn.classList.remove('hidden');
    } else {
        nextBtn.textContent = '完成抽测 ✅';
        nextBtn.classList.remove('hidden');
        nextBtn.onclick = finishQuiz;
    }
}

function nextQuestion() {
    currentIndex++;
    updateProgress();
    showQuestion();
}

document.getElementById('next-btn').addEventListener('click', nextQuestion);

async function finishQuiz() {
    await fetch('/api/english/quiz/finish', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({session_id: sessionId})
    });
    window.location.href = `/english/result?session=${sessionId}`;
}

// 键盘快捷键
document.addEventListener('keydown', (e) => {
    if (hasAnswered && e.key === 'Enter') {
        const nextBtn = document.getElementById('next-btn');
        if (!nextBtn.classList.contains('hidden')) {
            nextBtn.click();
        }
    }
});

loadSession();
</script>
{% endblock %}
```

### Step 2: Commit

```bash
git add app/templates/english/quiz.html
git commit -m "feat(templates): add english quiz page with three modes"
```

---

## Task 9: 前端模板 - 结果页和错词本

**Files:**
- Create: `app/templates/english/result.html`
- Create: `app/templates/english/mistakes.html`

### Step 1: 创建结果页面

```html
{% extends "base.html" %}

{% block title %}英语抽测 - 结果{% endblock %}

{% block content %}
<div class="max-w-2xl mx-auto">
    <h1 class="text-3xl font-bold text-gray-800 mb-8 text-center">📊 抽测结果</h1>

    <div id="result-container" class="bg-white rounded-2xl shadow-lg p-8">
        <!-- 动态加载结果 -->
        <div class="text-center text-gray-500">加载中...</div>
    </div>

    <div class="mt-8 grid grid-cols-2 gap-4">
        <a href="/english" class="bg-blue-500 hover:bg-blue-600 text-white text-center font-bold py-4 px-8 rounded-xl shadow-lg transition">
            再测一次
        </a>
        <a href="/" class="bg-gray-500 hover:bg-gray-600 text-white text-center font-bold py-4 px-8 rounded-xl shadow-lg transition">
            返回首页
        </a>
    </div>
</div>

<script>
const sessionId = new URLSearchParams(window.location.search).get('session');

async function loadResult() {
    const response = await fetch(`/api/english/quiz/session/${sessionId}`);
    if (!response.ok) {
        document.getElementById('result-container').innerHTML = '<div class="text-red-500 text-center">会话不存在或已过期</div>';
        return;
    }

    const data = await response.json();
    const container = document.getElementById('result-container');

    const mastered = data.records.filter(r => r.result === 'mastered').length;
    const fuzzy = data.records.filter(r => r.result === 'fuzzy').length;
    const notMastered = data.records.filter(r => r.result === 'not_mastered').length;
    const accuracy = data.total > 0 ? Math.round((mastered / data.total) * 100) : 0;

    container.innerHTML = `
        <!-- 统计卡片 -->
        <div class="grid grid-cols-3 gap-4 mb-8">
            <div class="bg-green-100 rounded-xl p-4 text-center">
                <div class="text-3xl font-bold text-green-600">${mastered}</div>
                <div class="text-green-700 text-sm">掌握</div>
            </div>
            <div class="bg-yellow-100 rounded-xl p-4 text-center">
                <div class="text-3xl font-bold text-yellow-600">${fuzzy}</div>
                <div class="text-yellow-700 text-sm">模糊</div>
            </div>
            <div class="bg-red-100 rounded-xl p-4 text-center">
                <div class="text-3xl font-bold text-red-600">${notMastered}</div>
                <div class="text-red-700 text-sm">未掌握</div>
            </div>
        </div>

        <!-- 正确率 -->
        <div class="mb-8">
            <div class="flex justify-between text-sm text-gray-600 mb-2">
                <span>正确率</span>
                <span class="font-bold">${accuracy}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-4">
                <div class="bg-blue-500 h-4 rounded-full transition-all duration-1000" style="width: ${accuracy}%"></div>
            </div>
        </div>

        <!-- 详细结果 -->
        <h2 class="font-bold text-gray-700 mb-4">详细结果</h2>
        <div class="space-y-2">
            ${data.records.map(r => `
                <div class="flex items-center justify-between p-3 rounded-lg ${
                    r.result === 'mastered' ? 'bg-green-50' :
                    r.result === 'fuzzy' ? 'bg-yellow-50' : 'bg-red-50'
                }">
                    <div>
                        <span class="font-bold">${r.word}</span>
                        <span class="text-gray-500 text-sm ml-2">${r.meaning}</span>
                    </div>
                    <span class="text-2xl">
                        ${r.result === 'mastered' ? '✅' : r.result === 'fuzzy' ? '⚠️' : '❌'}
                    </span>
                </div>
            `).join('')}
        </div>
    `;
}

loadResult();
</script>
{% endblock %}
```

### Step 2: 创建错词本页面

```html
{% extends "base.html" %}

{% block title %}英语错词本{% endblock %}

{% block content %}
<div class="max-w-4xl mx-auto">
    <h1 class="text-3xl font-bold text-gray-800 mb-8 text-center">❌ 英语错词本</h1>

    <div id="mistakes-container" class="bg-white rounded-2xl shadow-lg p-8">
        <div class="text-center text-gray-500">加载中...</div>
    </div>

    <div class="mt-8 text-center">
        <a href="/english" class="inline-block bg-blue-500 hover:bg-blue-600 text-white font-bold py-4 px-8 rounded-xl shadow-lg transition">
            去抽测
        </a>
    </div>
</div>

<script>
async function loadMistakes() {
    const response = await fetch('/api/english/mistakes');
    const mistakes = await response.json();
    const container = document.getElementById('mistakes-container');

    if (mistakes.length === 0) {
        container.innerHTML = `
            <div class="text-center py-12">
                <div class="text-6xl mb-4">🎉</div>
                <h2 class="text-xl font-bold text-gray-700 mb-2">太棒了！</h2>
                <p class="text-gray-500">你还没有错词，继续保持！</p>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <p class="text-gray-500 mb-4">共 ${mistakes.length} 个单词需要复习</p>
        <div class="space-y-3">
            ${mistakes.map(m => `
                <div class="flex items-center justify-between p-4 border rounded-xl hover:bg-gray-50">
                    <div class="flex items-center space-x-4">
                        <span class="text-2xl font-bold text-gray-800">${m.word}</span>
                        <span class="text-gray-500">${m.meaning}</span>
                        <span class="text-sm text-gray-400">${m.lesson}</span>
                    </div>
                    <div class="flex items-center space-x-4">
                        <span class="text-red-500 font-bold">错 ${m.mistake_count} 次</span>
                        <span class="text-gray-400 text-sm">${m.last_tested}</span>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

loadMistakes();
</script>
{% endblock %}
```

### Step 3: Commit

```bash
git add app/templates/english/result.html app/templates/english/mistakes.html
git commit -m "feat(templates): add english result and mistakes pages"
```

---

## Task 10: 主应用集成

**Files:**
- Modify: `app/main.py`
- Modify: `app/templates/index.html`

### Step 1: 注册英语路由

修改 `app/main.py`：

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR
from app.routers import pages, api
from app.routers import math_quiz
from app.routers import english  # 新增

app = FastAPI(
    title="语文学习小工具",
    description="帮助小学生每日学习汉字和英语",
    version="1.1.0"
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")
app.mount("/data/pdfs", StaticFiles(directory=BASE_DIR / "data" / "pdfs"), name="pdfs")
app.include_router(pages.router)
app.include_router(api.router, prefix="/api")
app.include_router(math_quiz.router)
app.include_router(english.router)  # 新增

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Step 2: 添加导航入口

在 `app/templates/index.html` 的导航栏中添加英语入口（在数学小测之后）：

```html
<!-- 找到数学小测链接，在其后添加 -->
<a href="/math-quiz" class="...">
    📐 数学每日小测
</a>
<a href="/english" class="bg-indigo-100 hover:bg-indigo-200 p-6 rounded-xl text-center transition">
    <div class="text-3xl mb-2">🔤</div>
    <div class="font-bold text-indigo-700">英语抽测</div>
    <div class="text-sm text-indigo-600 mt-1">单词听写练习</div>
</a>
```

### Step 3: Commit

```bash
git add app/main.py app/templates/index.html
git commit -m "feat: integrate english quiz into main app and navigation"
```

---

## Task 11: 示例数据

**Files:**
- Create: `data/english/grade3-autumn.md`

### Step 1: 创建示例数据文件

```markdown
# 三年级上册

## Unit 1: Hello

| 单词 | 音标 | 释义 | 例句 | 例句翻译 | 图片关键词 |
|------|------|------|------|----------|-----------|
| hello | /həˈləʊ/ | 你好 | Hello, I'm Tom. | 你好，我是汤姆。 | hello greeting |
| hi | /haɪ/ | 嗨 | Hi, Amy! | 嗨，艾米！ | hi greeting |
| I | /aɪ/ | 我 | I am a student. | 我是一名学生。 | student person |
| am | /æm/ | 是 | I am happy. | 我很开心。 | happy smile |
| name | /neɪm/ | 名字 | My name is Amy. | 我的名字叫艾米。 | name tag |

## Unit 2: Colours

| 单词 | 音标 | 释义 | 例句 | 例句翻译 | 图片关键词 |
|------|------|------|------|----------|-----------|
| red | /red/ | 红色 | I like red. | 我喜欢红色。 | red color |
| blue | /bluː/ | 蓝色 | The sky is blue. | 天空是蓝色的。 | blue color |
| green | /ɡriːn/ | 绿色 | The grass is green. | 草是绿色的。 | green color |
| yellow | /ˈjeləʊ/ | 黄色 | The banana is yellow. | 香蕉是黄色的。 | yellow color |

## Unit 3: Animals

| 单词 | 音标 | 释义 | 例句 | 例句翻译 | 图片关键词 |
|------|------|------|------|----------|-----------|
| cat | /kæt/ | 猫 | The cat is cute. | 这只猫很可爱。 | cat kitten |
| dog | /dɒɡ/ | 狗 | I have a dog. | 我有一只狗。 | dog puppy |
| bird | /bɜːd/ | 鸟 | The bird can fly. | 鸟会飞。 | bird flying |
| fish | /fɪʃ/ | 鱼 | The fish swims. | 鱼在游泳。 | fish water |
```

### Step 2: Commit

```bash
git add data/english/grade3-autumn.md
git commit -m "chore: add sample english word data for grade 3"
```

---

## Task 12: 最终测试和验证

### Step 1: 运行所有测试

```bash
pytest tests/ -v
# Expected: All tests pass (existing + new)
```

### Step 2: 启动应用测试

```bash
uvicorn app.main:app --reload
```

手动验证：
1. 首页显示英语抽测入口
2. 英语首页可以选择年级和单元
3. 开始抽测后显示题目
4. 三种模式正常切换
5. 答题后显示反馈
6. 完成后显示结果
7. 错词本记录错误单词

### Step 3: 最终 Commit

```bash
git add .
git commit -m "feat: complete english quiz module implementation

- Add EnglishWord, EnglishQuizMode, EnglishQuizRecord models
- Add EnglishService for word data management
- Add EnglishQuizService for quiz session management
- Add english routes (pages and API)
- Add frontend templates (index, quiz, result, mistakes)
- Integrate into main app and navigation
- Add sample data for grade 3"
```

---

## 验证清单

- [ ] 配置更新：ENGLISH_DIR 已添加
- [ ] 模型：EnglishWord, EnglishQuizMode, EnglishQuizRecord, EnglishQuizSessionState
- [ ] 服务：EnglishService, EnglishQuizService
- [ ] 路由：english.py 页面和 API
- [ ] 模板：index.html, quiz.html, result.html, mistakes.html
- [ ] 集成：main.py 注册路由，index.html 添加导航
- [ ] 数据：示例数据文件已创建
- [ ] 测试：所有单元测试通过
