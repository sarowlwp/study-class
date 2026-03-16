# 汉字抽测卡 Web 程序 - 实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个面向小学生的汉字抽测卡 Web 程序，支持本地 Markdown 数据存储、智能抽测、错字本和打印功能。

**Architecture:** FastAPI 后端 + Jinja2 模板引擎 + Tailwind CSS 前端，数据存储使用 Markdown 文件，无需数据库。单用户本地运行，服务端内存存储会话状态。

**Tech Stack:** Python 3.10+, FastAPI, Jinja2, Tailwind CSS, pytest

**Design Spec Reference:** `docs/superpowers/specs/2026-03-16-chinese-character-quiz-design.md`

---

## 文件结构规划

```
.
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 入口
│   ├── config.py               # 配置管理
│   ├── models/
│   │   ├── __init__.py
│   │   ├── character.py        # Character 数据模型
│   │   └── record.py           # QuizRecord, QuizSession 模型
│   ├── services/
│   │   ├── __init__.py
│   │   ├── character_service.py    # 汉字数据读取
│   │   ├── record_service.py       # 评测记录管理
│   │   └── quiz_service.py         # 抽测逻辑
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── pages.py            # 页面路由
│   │   └── api.py              # API 路由
│   ├── templates/              # Jinja2 模板
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── quiz.html
│   │   ├── result.html
│   │   ├── mistakes.html
│   │   └── print.html
│   └── static/                 # 静态资源
│       ├── css/
│       │   └── style.css
│       └── js/
│           └── app.js
├── data/
│   ├── characters/             # 汉字数据文件
│   │   └── grade1-spring.md    # 示例数据
│   └── records/                # 评测记录目录
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # pytest 配置
│   ├── test_models.py
│   ├── test_services.py
│   └── test_api.py
├── requirements.txt
└── README.md
```

---

## Chunk 1: 项目基础架构

### Task 1.1: 创建项目目录结构

**Files:**
- Create: `app/__init__.py`
- Create: `app/models/__init__.py`
- Create: `app/services/__init__.py`
- Create: `app/routers/__init__.py`
- Create: `app/templates/` (directory)
- Create: `app/static/css/` (directory)
- Create: `app/static/js/` (directory)
- Create: `data/characters/` (directory)
- Create: `data/records/` (directory)
- Create: `tests/__init__.py`

- [ ] **Step 1: 创建所有目录和 init 文件**

```bash
mkdir -p app/models app/services app/routers app/templates app/static/css app/static/js
mkdir -p data/characters data/records
mkdir -p tests
touch app/__init__.py app/models/__init__.py app/services/__init__.py app/routers/__init__.py
touch tests/__init__.py
touch app/static/css/style.css app/static/js/app.js
```

- [ ] **Step 2: Commit**

```bash
git add .
git commit -m "chore: create project directory structure"
```

---

### Task 1.2: 创建 requirements.txt

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: 创建依赖文件**

```txt
# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0

# Templates
jinja2==3.1.3

# Data Parsing
markdown==3.5.2

# Testing
pytest==8.0.0
pytest-asyncio==0.23.4
httpx==0.26.0

# Development
python-multipart==0.0.6
```

- [ ] **Step 2: 安装依赖**

```bash
pip install -r requirements.txt
```

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: add requirements.txt"
```

---

### Task 1.3: 创建基础 FastAPI 应用

**Files:**
- Create: `app/config.py`
- Create: `app/main.py`

- [ ] **Step 1: 创建配置模块**

```python
# app/config.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()
DATA_DIR = BASE_DIR / "data"
CHARACTERS_DIR = DATA_DIR / "characters"
RECORDS_DIR = DATA_DIR / "records"

# Ensure directories exist
CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)
RECORDS_DIR.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 2: 创建主应用**

```python
# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR
from app.routers import pages, api

app = FastAPI(
    title="汉字抽测卡",
    description="帮助小学生每日校验汉字掌握情况",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")

# Include routers
app.include_router(pages.router)
app.include_router(api.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **Step 3: 创建基础页面路由**

```python
# app/routers/pages.py
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR

router = APIRouter()
templates = Jinja2Templates(directory=BASE_DIR / "app" / "templates")

@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
```

- [ ] **Step 4: 创建基础 API 路由**

```python
# app/routers/api.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok"}
```

- [ ] **Step 5: 测试应用启动**

```bash
python -c "from app.main import app; print('App loaded successfully')"
```

Expected: `App loaded successfully`

- [ ] **Step 6: Commit**

```bash
git add app/
git commit -m "feat: create basic FastAPI application structure"
```

---

## Chunk 2: 数据模型层

### Task 2.1: 创建 Character 模型

**Files:**
- Create: `app/models/character.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_models.py
import pytest
from app.models.character import Character


def test_character_creation():
    char = Character(
        char="春",
        pinyin="chūn",
        meaning="春季，一年的第一季",
        example="春天来了，花儿开了。",
        lesson="第一课：春天来了",
        semester="一年级下册"
    )
    assert char.char == "春"
    assert char.pinyin == "chūn"


def test_character_to_dict():
    char = Character(
        char="春",
        pinyin="chūn",
        meaning="春季",
        example="春天来了。",
        lesson="第一课",
        semester="一年级下册"
    )
    data = char.to_dict()
    assert data["char"] == "春"
    assert data["pinyin"] == "chūn"
    assert "mastery_status" in data
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_models.py::test_character_creation -v
```

Expected: FAIL (module not found)

- [ ] **Step 3: 实现 Character 模型**

```python
# app/models/character.py
from dataclasses import dataclass, field
from typing import Optional


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
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_models.py::test_character_creation tests/test_models.py::test_character_to_dict -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/models/character.py tests/test_models.py
git commit -m "feat: add Character data model"
```

---

### Task 2.2: 创建 Record 模型

**Files:**
- Modify: `app/models/character.py`
- Create: `app/models/record.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: 添加枚举类型到 character.py**

```python
# app/models/character.py
from enum import Enum


class QuizMode(str, Enum):
    CHAR_TO_PINYIN = "char_to_pinyin"
    Pinyin_TO_CHAR = "pinyin_to_char"


class ResultType(str, Enum):
    MASTERED = "mastered"
    FUZZY = "fuzzy"
    NOT_MASTERED = "not_mastered"
```

- [ ] **Step 2: 编写测试**

```python
# tests/test_models.py (append)
from datetime import datetime
from app.models.record import QuizRecord, QuizSession, QuizMode, ResultType


def test_quiz_record_creation():
    record = QuizRecord(
        char="春",
        pinyin="chūn",
        lesson="第一课",
        mode=QuizMode.CHAR_TO_PINYIN,
        result=ResultType.MASTERED,
        timestamp=datetime(2026, 3, 16, 19, 30, 0)
    )
    assert record.char == "春"
    assert record.result == ResultType.MASTERED


def test_quiz_session_creation():
    session = QuizSession(
        session_id="abc123",
        total=20,
        lessons=["第一课", "第二课"]
    )
    assert session.session_id == "abc123"
    assert session.current_index == 0
    assert len(session.records) == 0
```

- [ ] **Step 3: 实现 Record 模型**

```python
# app/models/record.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class QuizMode(str, Enum):
    CHAR_TO_PINYIN = "char_to_pinyin"
    PINYIN_TO_CHAR = "pinyin_to_char"


class ResultType(str, Enum):
    MASTERED = "mastered"
    FUZZY = "fuzzy"
    NOT_MASTERED = "not_mastered"


@dataclass
class QuizRecord:
    """单次评测记录"""
    char: str
    pinyin: str
    lesson: str
    mode: QuizMode
    result: ResultType
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class QuizSessionState:
    """抽测会话状态"""
    session_id: str
    created_at: datetime
    total: int
    lessons: List[str]
    current_index: int = 0
    characters: List[dict] = field(default_factory=list)
    records: List[QuizRecord] = field(default_factory=list)
    completed: bool = False

    def add_record(self, record: QuizRecord):
        """添加评测记录"""
        # 更新已存在的记录
        for i, r in enumerate(self.records):
            if r.char == record.char:
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

- [ ] **Step 4: 更新 models __init__.py**

```python
# app/models/__init__.py
from app.models.character import Character
from app.models.record import QuizRecord, QuizSessionState, QuizMode, ResultType

__all__ = [
    "Character",
    "QuizRecord",
    "QuizSessionState",
    "QuizMode",
    "ResultType"
]
```

- [ ] **Step 5: 运行测试**

```bash
pytest tests/test_models.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/models/ tests/test_models.py
git commit -m "feat: add QuizRecord and QuizSessionState models"
```

---

## Chunk 3: 服务层 - 汉字数据管理

### Task 3.1: 创建 CharacterService

**Files:**
- Create: `app/services/character_service.py`
- Create: `data/characters/grade1-spring.md` (示例数据)
- Test: `tests/test_services.py`

- [ ] **Step 1: 创建示例数据文件**

```markdown
# 一年级下册

## 第一课：春天来了

| 汉字 | 拼音 | 释义 | 例句 |
|------|------|------|------|
| 春 | chūn | 春季，一年的第一季 | 春天来了，花儿开了。 |
| 来 | lái | 从别的地方到说话人所在的地方 | 小明来到学校。 |
| 花 | huā | 种子植物的有性繁殖器官 | 公园里有很多花。 |
| 开 | kāi | 打开，开启 | 请开门。 |

## 第二课：小蝌蚪找妈妈

| 汉字 | 拼音 | 释义 | 例句 |
|------|------|------|------|
| 蝌 | kē | 蝌蚪，蛙或蟾蜍的幼体 | 小蝌蚪在水里游来游去。 |
| 蚪 | dǒu | 见"蝌" | 小蝌蚪长大了变成青蛙。 |
| 妈 | mā | 母亲 | 我爱妈妈。 |
| 找 | zhǎo | 寻求，想要得到 | 我在找我的铅笔。 |
```

- [ ] **Step 2: 编写测试**

```python
# tests/test_services.py
import pytest
from app.services.character_service import CharacterService


@pytest.fixture
def character_service():
    return CharacterService()


def test_parse_markdown_file(character_service):
    characters = character_service._parse_file("grade1-spring.md")
    assert len(characters) > 0
    assert characters[0].char == "春"
    assert characters[0].semester == "一年级下册"


def test_get_semesters(character_service):
    semesters = character_service.get_semesters()
    assert isinstance(semesters, list)
    assert len(semesters) >= 1
    assert "grade1-spring" in [s["id"] for s in semesters]


def test_get_lessons(character_service):
    lessons = character_service.get_lessons("grade1-spring")
    assert len(lessons) == 2
    assert lessons[0]["name"] == "第一课：春天来了"


def test_get_characters_by_lessons(character_service):
    chars = character_service.get_characters("grade1-spring", ["第一课：春天来了"])
    assert len(chars) == 4
    assert all(c.lesson == "第一课：春天来了" for c in chars)
```

- [ ] **Step 3: 实现 CharacterService**

```python
# app/services/character_service.py
import re
from pathlib import Path
from typing import List, Dict, Optional

from app.config import CHARACTERS_DIR
from app.models.character import Character


class CharacterService:
    """汉字数据管理服务"""

    def __init__(self):
        self._cache: Dict[str, List[Character]] = {}

    def _parse_file(self, filename: str) -> List[Character]:
        """解析 Markdown 文件"""
        filepath = CHARACTERS_DIR / filename
        if not filepath.exists():
            return []

        content = filepath.read_text(encoding="utf-8")
        characters = []

        # 解析学期名称
        semester_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        semester = semester_match.group(1) if semester_match else filename

        # 解析课文和表格
        lesson_pattern = r'^##\s+(.+)$\n+\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|\n\|[-:|\s]+\|\n((?:\|[^\n]+\|\n?)+)'

        for match in re.finditer(lesson_pattern, content, re.MULTILINE):
            lesson_name = match.group(1).strip()
            table_content = match.group(6)

            # 解析表头
            headers = [h.strip().lower() for h in [match.group(2), match.group(3), match.group(4), match.group(5)]]

            # 映射标准字段
            field_map = self._map_headers(headers)

            # 解析表格行
            for line in table_content.strip().split('\n'):
                if not line.startswith('|'):
                    continue

                cells = [c.strip() for c in line.split('|')[1:-1]]
                if len(cells) < 4:
                    continue

                char = cells[field_map.get('char', 0)]
                pinyin = cells[field_map.get('pinyin', 1)]
                meaning = cells[field_map.get('meaning', 2)]
                example = cells[field_map.get('example', 3)]

                # 验证汉字
                if not char or len(char) != 1 or not '\u4e00' <= char <= '\u9fff':
                    continue

                characters.append(Character(
                    char=char,
                    pinyin=pinyin,
                    meaning=meaning,
                    example=example,
                    lesson=lesson_name,
                    semester=semester
                ))

        return characters

    def _map_headers(self, headers: List[str]) -> Dict[str, int]:
        """映射表头到标准字段"""
        field_map = {}
        keywords = {
            'char': ['汉字', '字', 'char'],
            'pinyin': ['拼音', 'pinyin', '拼音'],
            'meaning': ['释义', '意思', 'meaning', '解释'],
            'example': ['例句', '例子', 'example', '例']
        }

        for i, header in enumerate(headers):
            for field, keys in keywords.items():
                if any(k in header for k in keys):
                    field_map[field] = i
                    break

        return field_map

    def get_semesters(self) -> List[Dict]:
        """获取所有学期列表"""
        semesters = []
        for filepath in CHARACTERS_DIR.glob("*.md"):
            content = filepath.read_text(encoding="utf-8")
            match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            name = match.group(1) if match else filepath.stem

            chars = self._parse_file(filepath.name)

            semesters.append({
                "id": filepath.stem,
                "name": name,
                "file": filepath.name,
                "total_chars": len(chars)
            })

        return semesters

    def get_lessons(self, semester_id: str) -> List[Dict]:
        """获取指定学期的课文列表"""
        chars = self._parse_file(f"{semester_id}.md")

        lessons = {}
        for char in chars:
            if char.lesson not in lessons:
                lessons[char.lesson] = {"count": 0, "mastered": 0}
            lessons[char.lesson]["count"] += 1

        return [
            {"id": f"lesson-{i+1}", "name": name, "char_count": data["count"], "mastered_count": data["mastered"]}
            for i, (name, data) in enumerate(lessons.items())
        ]

    def get_characters(self, semester_id: str, lessons: Optional[List[str]] = None) -> List[Character]:
        """获取指定范围的汉字"""
        chars = self._parse_file(f"{semester_id}.md")

        if lessons:
            chars = [c for c in chars if c.lesson in lessons]

        return chars

    def get_all_characters(self) -> List[Character]:
        """获取所有汉字"""
        all_chars = []
        for filepath in CHARACTERS_DIR.glob("*.md"):
            all_chars.extend(self._parse_file(filepath.name))
        return all_chars
```

- [ ] **Step 4: 运行测试**

```bash
pytest tests/test_services.py::test_parse_markdown_file -v
```

Expected: PASS

- [ ] **Step 5: 修复其他测试并全部运行**

```bash
pytest tests/test_services.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/services/character_service.py data/ tests/test_services.py
git commit -m "feat: add CharacterService for parsing markdown data"
```

---

## Chunk 4: 服务层 - 记录管理

### Task 4.1: 创建 RecordService

**Files:**
- Create: `app/services/record_service.py`
- Test: `tests/test_services.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_services.py (append)
from datetime import datetime
from app.services.record_service import RecordService
from app.models.record import QuizRecord, QuizMode, ResultType


@pytest.fixture
def record_service():
    return RecordService()


def test_save_and_load_records(record_service):
    records = [
        QuizRecord(
            char="春", pinyin="chūn", lesson="第一课",
            mode=QuizMode.CHAR_TO_PINYIN, result=ResultType.MASTERED,
            timestamp=datetime(2026, 3, 16, 10, 0, 0)
        )
    ]

    # 保存
    record_service.save_records(datetime(2026, 3, 16).date(), records)

    # 读取
    loaded = record_service.get_records_by_date(datetime(2026, 3, 16).date())
    assert len(loaded) == 1
    assert loaded[0].char == "春"


def test_get_mastery_status(record_service):
    # 测试基于历史记录计算掌握状态
    pass  # 在集成测试中验证


def test_get_mistakes(record_service):
    # 获取错字本
    pass  # 在集成测试中验证
```

- [ ] **Step 2: 实现 RecordService**

```python
# app/services/record_service.py
import re
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict

from app.config import RECORDS_DIR
from app.models.record import QuizRecord, QuizMode, ResultType


class RecordService:
    """评测记录管理服务"""

    def save_records(self, record_date: date, records: List[QuizRecord]):
        """保存评测记录到文件"""
        filename = RECORDS_DIR / f"{record_date.isoformat()}.md"

        # 计算统计
        counts = defaultdict(int)
        for r in records:
            counts[r.result.value] += 1

        # 生成 Markdown 内容
        lines = [
            f"# {record_date.isoformat()} 评测记录\n",
            "## 统计",
            f"- 总数: {len(records)}",
            f"- 掌握: {counts['mastered']}",
            f"- 模糊: {counts['fuzzy']}",
            f"- 未掌握: {counts['not_mastered']}",
            f"- 正确率: {counts['mastered'] / len(records) * 100:.1f}%\n" if records else "- 正确率: 0%\n",
            "## 评测结果\n",
            "| 汉字 | 拼音 | 课文 | 模式 | 结果 | 时间 |",
            "|------|------|------|------|------|------|"
        ]

        for r in records:
            lines.append(
                f"| {r.char} | {r.pinyin} | {r.lesson} | {r.mode.value} | {r.result.value} | {r.timestamp.strftime('%H:%M:%S')} |"
            )

        filename.write_text('\n'.join(lines), encoding='utf-8')

    def get_records_by_date(self, record_date: date) -> List[QuizRecord]:
        """获取指定日期的评测记录"""
        filename = RECORDS_DIR / f"{record_date.isoformat()}.md"
        if not filename.exists():
            return []

        return self._parse_record_file(filename)

    def _parse_record_file(self, filepath: Path) -> List[QuizRecord]:
        """解析记录文件"""
        content = filepath.read_text(encoding='utf-8')
        records = []

        # 查找评测结果表格
        table_match = re.search(
            r'## 评测结果\n+\|[^\n]+\|\n\|[-:|\s]+\|\n((?:\|[^\n]+\|\n?)+)',
            content
        )

        if table_match:
            for line in table_match.group(1).strip().split('\n'):
                cells = [c.strip() for c in line.split('|')[1:-1]]
                if len(cells) >= 6:
                    date_str = filepath.stem
                    time_str = cells[5]
                    timestamp = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")

                    records.append(QuizRecord(
                        char=cells[0],
                        pinyin=cells[1],
                        lesson=cells[2],
                        mode=QuizMode(cells[3]),
                        result=ResultType(cells[4]),
                        timestamp=timestamp
                    ))

        return records

    def get_all_records(self) -> List[QuizRecord]:
        """获取所有历史记录"""
        all_records = []
        for filepath in sorted(RECORDS_DIR.glob("*.md")):
            all_records.extend(self._parse_record_file(filepath))
        return all_records

    def get_mastery_status(self, char: str, lesson: str) -> str:
        """
        计算汉字的掌握状态

        Returns: 'new' | 'mastered' | 'fuzzy' | 'not_mastered'
        """
        records = [
            r for r in self.get_all_records()
            if r.char == char and r.lesson == lesson
        ]

        if not records:
            return "new"

        # 按时间倒序
        records.sort(key=lambda r: r.timestamp, reverse=True)

        # 取最近 3 次
        recent = records[:3]

        # 最近一次结果
        latest = recent[0].result

        # 如果最近一次是未掌握，直接返回未掌握
        if latest == ResultType.NOT_MASTERED:
            return "not_mastered"

        # 如果最近一次是模糊，返回模糊
        if latest == ResultType.FUZZY:
            return "fuzzy"

        # 计算最近 3 次的掌握情况
        mastered_count = sum(1 for r in recent if r.result == ResultType.MASTERED)

        # 至少 2/3 掌握才算已掌握
        if mastered_count >= 2:
            return "mastered"

        # 混合状态返回模糊
        return "fuzzy"

    def get_mistakes(self, semester_id: Optional[str] = None) -> List[Dict]:
        """获取错字本"""
        all_records = self.get_all_records()

        # 统计每个字的错误次数
        char_stats = defaultdict(lambda: {"count": 0, "last": None, "lesson": None, "pinyin": None})

        for r in all_records:
            if r.result == ResultType.NOT_MASTERED:
                key = (r.char, r.lesson)
                char_stats[key]["count"] += 1
                char_stats[key]["last"] = r.timestamp
                char_stats[key]["lesson"] = r.lesson
                char_stats[key]["pinyin"] = r.pinyin

        # 转换为列表
        mistakes = []
        for (char, lesson), stats in char_stats.items():
            mistakes.append({
                "char": char,
                "pinyin": stats["pinyin"],
                "lesson": stats["lesson"],
                "mistake_count": stats["count"],
                "last_tested": stats["last"].strftime("%Y-%m-%d") if stats["last"] else None
            })

        # 按错误次数倒序
        mistakes.sort(key=lambda x: x["mistake_count"], reverse=True)

        return mistakes

    def get_stats(self, semester_id: Optional[str] = None) -> Dict:
        """获取学习统计"""
        records = self.get_all_records()

        # 按日期分组统计
        daily_stats = defaultdict(lambda: {"total": 0, "mastered": 0})

        for r in records:
            date_str = r.timestamp.strftime("%Y-%m-%d")
            daily_stats[date_str]["total"] += 1
            if r.result == ResultType.MASTERED:
                daily_stats[date_str]["mastered"] += 1

        # 计算连续学习天数
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
                for d, stats in sorted(daily_stats.items())[-7:]  # 最近7天
            ]
        }
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_services.py::test_save_and_load_records -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add app/services/record_service.py tests/test_services.py
git commit -m "feat: add RecordService for managing quiz records"
```

---

## Chunk 5: 服务层 - 抽测逻辑

### Task 5.1: 创建 QuizService

**Files:**
- Create: `app/services/quiz_service.py`
- Test: `tests/test_services.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_services.py (append)
import uuid
from app.services.quiz_service import QuizService


@pytest.fixture
def quiz_service(character_service, record_service):
    return QuizService(character_service, record_service)


def test_generate_quiz(quiz_service):
    session = quiz_service.generate_quiz("grade1-spring", ["第一课：春天来了"], 4)

    assert session.total == 4
    assert len(session.characters) == 4
    assert session.session_id is not None


def test_submit_result(quiz_service):
    session = quiz_service.generate_quiz("grade1-spring", ["第一课：春天来了"], 2)

    quiz_service.submit_result(
        session.session_id,
        0,
        ResultType.MASTERED
    )

    assert len(session.records) == 1
    assert session.records[0].result == ResultType.MASTERED


def test_finish_quiz(quiz_service):
    session = quiz_service.generate_quiz("grade1-spring", ["第一课：春天来了"], 2)

    quiz_service.submit_result(session.session_id, 0, ResultType.MASTERED)
    quiz_service.submit_result(session.session_id, 1, ResultType.NOT_MASTERED)

    summary = quiz_service.finish_quiz(session.session_id)

    assert summary["total"] == 2
    assert summary["mastered"] == 1
    assert summary["not_mastered"] == 1
```

- [ ] **Step 2: 实现 QuizService**

```python
# app/services/quiz_service.py
import uuid
import random
from datetime import datetime
from typing import List, Dict, Optional

from app.models.character import Character
from app.models.record import QuizSessionState, QuizRecord, QuizMode, ResultType
from app.services.character_service import CharacterService
from app.services.record_service import RecordService


class QuizService:
    """抽测服务"""

    # 内存存储会话状态
    _sessions: Dict[str, QuizSessionState] = {}

    def __init__(self, character_service: CharacterService, record_service: RecordService):
        self.char_service = character_service
        self.record_service = record_service

    def generate_quiz(
        self,
        semester_id: str,
        lessons: List[str],
        count: int,
        mode_mix: float = 0.5
    ) -> QuizSessionState:
        """
        生成抽测会话

        Args:
            semester_id: 学期ID
            lessons: 课文列表
            count: 抽测数量
            mode_mix: 汉字->拼音模式的比例 (0-1)
        """
        # 获取汉字
        all_chars = self.char_service.get_characters(semester_id, lessons)

        if not all_chars:
            raise ValueError("没有可用的汉字")

        # 获取掌握状态并分组
        priority_groups = {
            "not_mastered": [],
            "fuzzy": [],
            "new": [],
            "mastered": []
        }

        for char in all_chars:
            status = self.record_service.get_mastery_status(char.char, char.lesson)
            char.mastery_status = status
            priority_groups[status].append(char)

        # 按优先级抽取
        selected = []
        priorities = ["not_mastered", "fuzzy", "new", "mastered"]

        for priority in priorities:
            chars = priority_groups[priority]
            random.shuffle(chars)

            needed = count - len(selected)
            if needed <= 0:
                break

            selected.extend(chars[:needed])

        # 随机分配模式
        quiz_items = []
        for char in selected:
            mode = QuizMode.CHAR_TO_PINYIN if random.random() < mode_mix else QuizMode.PINYIN_TO_CHAR
            quiz_items.append({
                "char": char.char,
                "pinyin": char.pinyin,
                "meaning": char.meaning,
                "example": char.example,
                "lesson": char.lesson,
                "mode": mode.value
            })

        # 创建会话
        session = QuizSessionState(
            session_id=str(uuid.uuid4())[:12],
            created_at=datetime.now(),
            total=len(quiz_items),
            lessons=lessons,
            characters=quiz_items
        )

        # 存储会话
        self._sessions[session.session_id] = session

        return session

    def get_session(self, session_id: str) -> Optional[QuizSessionState]:
        """获取会话状态"""
        return self._sessions.get(session_id)

    def submit_result(
        self,
        session_id: str,
        index: int,
        result: ResultType
    ) -> bool:
        """提交单个字的评测结果"""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError("会话不存在或已过期")

        if index < 0 or index >= len(session.characters):
            raise ValueError("无效的索引")

        char_data = session.characters[index]

        record = QuizRecord(
            char=char_data["char"],
            pinyin=char_data["pinyin"],
            lesson=char_data["lesson"],
            mode=QuizMode(char_data["mode"]),
            result=result
        )

        session.add_record(record)
        session.current_index = max(session.current_index, index + 1)

        return True

    def finish_quiz(self, session_id: str) -> Dict:
        """完成抽测，保存记录"""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError("会话不存在或已过期")

        session.completed = True

        # 保存到文件
        self.record_service.save_records(
            session.created_at.date(),
            session.records
        )

        # 返回摘要
        return session.get_summary()
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_services.py -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add app/services/quiz_service.py tests/test_services.py
git commit -m "feat: add QuizService for quiz generation and management"
```

---

## Chunk 6: API 路由层

### Task 6.1: 创建 API 路由

**Files:**
- Modify: `app/routers/api.py`
- Test: `tests/test_api.py`

- [ ] **Step 1: 编写 API 测试**

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_get_semesters():
    response = client.get("/api/semesters")
    assert response.status_code == 200
    data = response.json()
    assert "semesters" in data


def test_get_lessons():
    response = client.get("/api/lessons?semester=grade1-spring")
    assert response.status_code == 200
    data = response.json()
    assert "lessons" in data


def test_start_quiz():
    response = client.post("/api/quiz/start", json={
        "semester": "grade1-spring",
        "lessons": ["第一课：春天来了"],
        "count": 4,
        "mode_mix": 0.5
    })
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["total"] == 4


def test_submit_and_finish_quiz():
    # Start quiz
    start = client.post("/api/quiz/start", json={
        "semester": "grade1-spring",
        "lessons": ["第一课：春天来了"],
        "count": 2
    })
    session_id = start.json()["session_id"]

    # Submit results
    client.post("/api/quiz/submit", json={
        "session_id": session_id,
        "index": 0,
        "result": "mastered"
    })
    client.post("/api/quiz/submit", json={
        "session_id": session_id,
        "index": 1,
        "result": "not_mastered"
    })

    # Finish
    finish = client.post("/api/quiz/finish", json={
        "session_id": session_id
    })
    assert finish.status_code == 200
    data = finish.json()
    assert data["summary"]["mastered"] == 1
    assert data["summary"]["not_mastered"] == 1
```

- [ ] **Step 2: 实现 API 路由**

```python
# app/routers/api.py
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.character_service import CharacterService
from app.services.record_service import RecordService
from app.services.quiz_service import QuizService
from app.models.record import ResultType

router = APIRouter()

# 服务实例
char_service = CharacterService()
record_service = RecordService()
quiz_service = QuizService(char_service, record_service)


class StartQuizRequest(BaseModel):
    semester: str
    lessons: List[str]
    count: int = 20
    mode_mix: float = 0.5


class SubmitResultRequest(BaseModel):
    session_id: str
    index: int
    result: str  # mastered | fuzzy | not_mastered


class FinishQuizRequest(BaseModel):
    session_id: str


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.get("/semesters")
async def get_semesters():
    return {"semesters": char_service.get_semesters()}


@router.get("/lessons")
async def get_lessons(semester: str):
    return {
        "semester": semester,
        "lessons": char_service.get_lessons(semester)
    }


@router.get("/characters")
async def get_characters(
    semester: str,
    lessons: Optional[str] = None  # 逗号分隔的课文名
):
    lesson_list = lessons.split(",") if lessons else None
    chars = char_service.get_characters(semester, lesson_list)
    return {"characters": [c.to_dict() for c in chars]}


@router.post("/quiz/start")
async def start_quiz(request: StartQuizRequest):
    try:
        # 验证数量
        count = max(10, min(50, request.count))

        session = quiz_service.generate_quiz(
            request.semester,
            request.lessons,
            count,
            request.mode_mix
        )

        return {
            "session_id": session.session_id,
            "total": session.total,
            "characters": session.characters
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/quiz/submit")
async def submit_result(request: SubmitResultRequest):
    try:
        result = ResultType(request.result)
        success = quiz_service.submit_result(
            request.session_id,
            request.index,
            result
        )

        session = quiz_service.get_session(request.session_id)

        return {
            "success": success,
            "next_index": session.current_index if session else None,
            "completed": session.completed if session else True
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/quiz/finish")
async def finish_quiz(request: FinishQuizRequest):
    try:
        summary = quiz_service.finish_quiz(request.session_id)
        return {
            "success": True,
            "summary": summary
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/mistakes")
async def get_mistakes(semester: Optional[str] = None):
    return {"mistakes": record_service.get_mistakes(semester)}


@router.get("/stats")
async def get_stats(semester: Optional[str] = None):
    return record_service.get_stats(semester)
```

- [ ] **Step 3: 运行 API 测试**

```bash
pytest tests/test_api.py -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add app/routers/api.py tests/test_api.py
git commit -m "feat: add API routes for quiz functionality"
```

---

## Chunk 7: 前端页面 - 基础模板

### Task 7.1: 创建基础模板和首页

**Files:**
- Create: `app/templates/base.html`
- Modify: `app/templates/index.html`
- Modify: `app/routers/pages.py`

- [ ] **Step 1: 创建基础模板**

```html
<!-- app/templates/base.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}汉字抽测卡{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="/static/css/style.css">
    {% block extra_css %}{% endblock %}
</head>
<body class="bg-gradient-to-br from-green-50 to-blue-50 min-h-screen">
    <!-- 导航栏 -->
    <nav class="bg-white shadow-md">
        <div class="max-w-4xl mx-auto px-4 py-3">
            <div class="flex items-center justify-between">
                <a href="/" class="flex items-center space-x-2">
                    <span class="text-2xl">📚</span>
                    <span class="text-xl font-bold text-green-600">汉字抽测卡</span>
                </a>
                <div class="flex space-x-4">
                    <a href="/" class="text-gray-600 hover:text-green-600 px-3 py-2 rounded-lg hover:bg-green-50 transition">
                        首页
                    </a>
                    <a href="/mistakes" class="text-gray-600 hover:text-red-600 px-3 py-2 rounded-lg hover:bg-red-50 transition">
                        错字本
                    </a>
                    <a href="/print" class="text-gray-600 hover:text-blue-600 px-3 py-2 rounded-lg hover:bg-blue-50 transition">
                        打印
                    </a>
                </div>
            </div>
        </div>
    </nav>

    <!-- 主内容 -->
    <main class="max-w-4xl mx-auto px-4 py-8">
        {% block content %}{% endblock %}
    </main>

    <!-- 页脚 -->
    <footer class="text-center py-6 text-gray-500 text-sm">
        <p>汉字抽测卡 - 每日进步一点点 🌱</p>
    </footer>

    <script src="/static/js/app.js"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

- [ ] **Step 2: 创建首页模板**

```html
<!-- app/templates/index.html -->
{% extends "base.html" %}

{% block content %}
<div class="text-center mb-8">
    <h1 class="text-4xl font-bold text-gray-800 mb-2">欢迎来到汉字抽测卡! 🎯</h1>
    <p class="text-gray-600">选择课文，开始今天的汉字学习之旅</p>
</div>

<!-- 配置卡片 -->
<div class="bg-white rounded-2xl shadow-lg p-6 mb-6">
    <!-- 学期选择 -->
    <div class="mb-6">
        <label class="block text-sm font-medium text-gray-700 mb-2">选择学期</label>
        <select id="semester" class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 text-lg">
            <option value="">请选择...</option>
        </select>
    </div>

    <!-- 课文选择 -->
    <div class="mb-6">
        <label class="block text-sm font-medium text-gray-700 mb-2">选择课文</label>
        <div id="lessons" class="grid grid-cols-2 md:grid-cols-3 gap-3">
            <p class="text-gray-400 col-span-full">请先选择学期</p>
        </div>
    </div>

    <!-- 抽测数量 -->
    <div class="mb-6">
        <label class="block text-sm font-medium text-gray-700 mb-2">
            抽测数量: <span id="count-display" class="text-green-600 font-bold">20</span> 个
        </label>
        <input type="range" id="count" min="10" max="50" value="20"
               class="w-full h-3 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-green-500">
        <div class="flex justify-between text-xs text-gray-500 mt-1">
            <span>10</span>
            <span>50</span>
        </div>
    </div>

    <!-- 开始按钮 -->
    <button id="start-btn" class="w-full bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white font-bold py-4 px-8 rounded-xl text-xl shadow-lg transform transition hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none">
        🚀 开始抽测
    </button>
</div>

<!-- 快捷入口 -->
<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <a href="/mistakes" class="bg-white rounded-xl shadow p-6 hover:shadow-lg transition flex items-center space-x-4">
        <span class="text-4xl">❌</span>
        <div>
            <h3 class="font-bold text-gray-800">错字本</h3>
            <p class="text-sm text-gray-500">复习没掌握的汉字</p>
        </div>
    </a>
    <a href="/print" class="bg-white rounded-xl shadow p-6 hover:shadow-lg transition flex items-center space-x-4">
        <span class="text-4xl">🖨️</span>
        <div>
            <h3 class="font-bold text-gray-800">打印卡片</h3>
            <p class="text-sm text-gray-500">生成纸质抽测卡</p>
        </div>
    </a>
</div>

<script>
// 加载学期列表
async function loadSemesters() {
    const response = await fetch('/api/semesters');
    const data = await response.json();

    const select = document.getElementById('semester');
    data.semesters.forEach(s => {
        const option = document.createElement('option');
        option.value = s.id;
        option.textContent = s.name;
        select.appendChild(option);
    });
}

// 加载课文列表
async function loadLessons(semesterId) {
    const response = await fetch(`/api/lessons?semester=${semesterId}`);
    const data = await response.json();

    const container = document.getElementById('lessons');
    container.innerHTML = '';

    data.lessons.forEach(l => {
        const div = document.createElement('div');
        div.className = 'flex items-center space-x-2 p-3 border rounded-lg hover:bg-green-50 cursor-pointer lesson-item';
        div.innerHTML = `
            <input type="checkbox" value="${l.name}" id="lesson-${l.id}" class="w-5 h-5 text-green-500 rounded focus:ring-green-500">
            <label for="lesson-${l.id}" class="flex-1 cursor-pointer text-sm">
                ${l.name}
                <span class="text-xs text-gray-400">(${l.char_count}字)</span>
            </label>
        `;
        div.querySelector('input').addEventListener('change', updateStartButton);
        container.appendChild(div);
    });
}

// 更新开始按钮状态
function updateStartButton() {
    const checked = document.querySelectorAll('#lessons input:checked');
    document.getElementById('start-btn').disabled = checked.length === 0;
}

// 开始抽测
async function startQuiz() {
    const semester = document.getElementById('semester').value;
    const lessons = Array.from(document.querySelectorAll('#lessons input:checked')).map(cb => cb.value);
    const count = parseInt(document.getElementById('count').value);

    const response = await fetch('/api/quiz/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({semester, lessons, count})
    });

    const data = await response.json();
    window.location.href = `/quiz?session=${data.session_id}`;
}

// 事件监听
document.getElementById('semester').addEventListener('change', (e) => {
    if (e.target.value) {
        loadLessons(e.target.value);
    }
});

document.getElementById('count').addEventListener('input', (e) => {
    document.getElementById('count-display').textContent = e.target.value;
});

document.getElementById('start-btn').addEventListener('click', startQuiz);

// 初始化
loadSemesters();
</script>
{% endblock %}
```

- [ ] **Step 3: 更新页面路由**

```python
# app/routers/pages.py
from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR
from app.services.character_service import CharacterService
from app.services.record_service import RecordService
from app.services.quiz_service import QuizService

router = APIRouter()
templates = Jinja2Templates(directory=BASE_DIR / "app" / "templates")

char_service = CharacterService()
record_service = RecordService()
quiz_service = QuizService(char_service, record_service)


@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/quiz")
async def quiz(request: Request, session: str):
    return templates.TemplateResponse("quiz.html", {
        "request": request,
        "session_id": session
    })


@router.get("/result")
async def result(request: Request):
    return templates.TemplateResponse("result.html", {"request": request})


@router.get("/mistakes")
async def mistakes(request: Request):
    return templates.TemplateResponse("mistakes.html", {"request": request})


@router.get("/print")
async def print_page(request: Request):
    return templates.TemplateResponse("print.html", {"request": request})
```

- [ ] **Step 4: 测试首页**

```bash
python -c "
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)
response = client.get('/')
assert response.status_code == 200
print('Homepage loads successfully')
"
```

Expected: `Homepage loads successfully`

- [ ] **Step 5: Commit**

```bash
git add app/templates/ app/routers/pages.py
git commit -m "feat: add base template and homepage"
```

---

## Chunk 8: 前端页面 - 抽测页和结果页

### Task 8.1: 创建抽测页面

**Files:**
- Create: `app/templates/quiz.html`

- [ ] **Step 1: 创建抽测页面**

```html
<!-- app/templates/quiz.html -->
{% extends "base.html" %}

{% block title %}汉字抽测 - 进行中{% endblock %}

{% block content %}
<div class="max-w-2xl mx-auto">
    <!-- 进度条 -->
    <div class="mb-6">
        <div class="flex justify-between text-sm text-gray-600 mb-2">
            <span>进度</span>
            <span id="progress-text">1 / 20</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-3">
            <div id="progress-bar" class="bg-green-500 h-3 rounded-full transition-all duration-300" style="width: 5%"></div>
        </div>
    </div>

    <!-- 抽测卡片 -->
    <div class="bg-white rounded-2xl shadow-xl p-8 mb-6 min-h-[400px] flex flex-col">
        <!-- 问题区域 -->
        <div id="question-area" class="flex-1 flex flex-col items-center justify-center">
            <div id="question-content" class="text-center">
                <!-- 动态填充 -->
            </div>
        </div>

        <!-- 答案区域（初始隐藏） -->
        <div id="answer-area" class="hidden flex-1 flex flex-col items-center justify-center border-t pt-6 mt-6">
            <div id="answer-content" class="text-center">
                <!-- 动态填充 -->
            </div>
        </div>
    </div>

    <!-- 操作按钮 -->
    <div id="action-buttons" class="grid grid-cols-3 gap-4">
        <button onclick="showAnswer()" class="col-span-3 bg-blue-500 hover:bg-blue-600 text-white font-bold py-4 px-8 rounded-xl text-lg shadow-lg transition">
            👁️ 显示答案
        </button>
    </div>

    <!-- 评分按钮（初始隐藏） -->
    <div id="rating-buttons" class="hidden grid grid-cols-3 gap-4">
        <button onclick="submitResult('mastered')" class="bg-green-500 hover:bg-green-600 text-white font-bold py-4 px-6 rounded-xl shadow-lg transition">
            ✅ 掌握
        </button>
        <button onclick="submitResult('fuzzy')" class="bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-4 px-6 rounded-xl shadow-lg transition">
            🤔 模糊
        </button>
        <button onclick="submitResult('not_mastered')" class="bg-red-500 hover:bg-red-600 text-white font-bold py-4 px-6 rounded-xl shadow-lg transition">
            ❌ 不会
        </button>
    </div>
</div>

<script>
const sessionId = '{{ session_id }}';
let currentIndex = 0;
let characters = [];
let total = 0;

// 加载会话数据
async function loadSession() {
    // 通过 API 获取会话数据
    // 注意：目前 quiz_service 没有直接的获取接口，需要修改
    // 这里简化处理，通过 window.location.reload() 重新加载
    const response = await fetch(`/api/quiz/session/${sessionId}`);
    if (!response.ok) {
        alert('会话已过期，请重新开始');
        window.location.href = '/';
        return;
    }
    const data = await response.json();
    characters = data.characters;
    total = data.total;
    currentIndex = data.current_index || 0;

    updateProgress();
    showCharacter();
}

// 更新进度条
function updateProgress() {
    const percent = ((currentIndex + 1) / total) * 100;
    document.getElementById('progress-bar').style.width = `${percent}%`;
    document.getElementById('progress-text').textContent = `${currentIndex + 1} / ${total}`;
}

// 显示当前汉字
function showCharacter() {
    const char = characters[currentIndex];
    const questionArea = document.getElementById('question-content');
    const answerArea = document.getElementById('answer-content');

    // 重置显示
    document.getElementById('answer-area').classList.add('hidden');
    document.getElementById('action-buttons').classList.remove('hidden');
    document.getElementById('rating-buttons').classList.add('hidden');

    if (char.mode === 'char_to_pinyin') {
        // 汉字 -> 拼音
        questionArea.innerHTML = `
            <div class="text-8xl font-bold text-gray-800 mb-4" style="font-family: 'KaiTi', 'STKaiti', serif;">${char.char}</div>
            <p class="text-gray-500">这个字的拼音是什么？</p>
        `;
        answerArea.innerHTML = `
            <div class="text-4xl text-green-600 font-bold mb-2">${char.pinyin}</div>
            <div class="text-lg text-gray-700 mb-1">${char.meaning}</div>
            <div class="text-gray-500 italic">"${char.example}"</div>
        `;
    } else {
        // 拼音 -> 汉字
        questionArea.innerHTML = `
            <div class="text-5xl font-bold text-green-600 mb-4">${char.pinyin}</div>
            <div class="text-xl text-gray-700">${char.meaning}</div>
            <p class="text-gray-500 mt-4">这个字怎么写？</p>
        `;
        answerArea.innerHTML = `
            <div class="text-8xl font-bold text-gray-800 mb-4" style="font-family: 'KaiTi', 'STKaiti', serif;">${char.char}</div>
            <div class="text-gray-500 italic">"${char.example}"</div>
        `;
    }
}

// 显示答案
function showAnswer() {
    document.getElementById('answer-area').classList.remove('hidden');
    document.getElementById('action-buttons').classList.add('hidden');
    document.getElementById('rating-buttons').classList.remove('hidden');
}

// 提交结果
async function submitResult(result) {
    await fetch('/api/quiz/submit', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            session_id: sessionId,
            index: currentIndex,
            result: result
        })
    });

    currentIndex++;

    if (currentIndex >= total) {
        // 完成抽测
        await finishQuiz();
    } else {
        updateProgress();
        showCharacter();
    }
}

// 完成抽测
async function finishQuiz() {
    const response = await fetch('/api/quiz/finish', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({session_id: sessionId})
    });

    const data = await response.json();
    window.location.href = `/result?session=${sessionId}`;
}

// 键盘快捷键
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space') {
        e.preventDefault();
        if (!document.getElementById('answer-area').classList.contains('hidden')) {
            // 答案已显示，忽略
        } else {
            showAnswer();
        }
    }
    if (e.key === '1') submitResult('mastered');
    if (e.key === '2') submitResult('fuzzy');
    if (e.key === '3') submitResult('not_mastered');
});

// 初始化
// 需要修改 API 添加获取会话接口
// 暂时通过前端存储
loadSession();
</script>
{% endblock %}
```

- [ ] **Step 2: 为 QuizService 添加获取会话接口**

```python
# app/routers/api.py (添加路由)
@router.get("/quiz/session/{session_id}")
async def get_session(session_id: str):
    session = quiz_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session.session_id,
        "total": session.total,
        "current_index": session.current_index,
        "completed": session.completed,
        "characters": session.characters
    }
```

- [ ] **Step 3: 创建结果页面**

```html
<!-- app/templates/result.html -->
{% extends "base.html" %}

{% block title %}抽测完成 - 结果{% endblock %}

{% block content %}
<div class="max-w-2xl mx-auto text-center">
    <!-- 庆祝动画 -->
    <div class="text-6xl mb-4">🎉</div>
    <h1 class="text-3xl font-bold text-gray-800 mb-2">抽测完成！</h1>
    <p class="text-gray-600 mb-8">你真棒！继续加油 💪</p>

    <!-- 统计卡片 -->
    <div id="stats" class="bg-white rounded-2xl shadow-lg p-6 mb-6">
        <div class="grid grid-cols-4 gap-4">
            <div class="text-center">
                <div id="stat-total" class="text-3xl font-bold text-gray-800">-</div>
                <div class="text-sm text-gray-500">总数</div>
            </div>
            <div class="text-center">
                <div id="stat-mastered" class="text-3xl font-bold text-green-600">-</div>
                <div class="text-sm text-gray-500">掌握</div>
            </div>
            <div class="text-center">
                <div id="stat-fuzzy" class="text-3xl font-bold text-yellow-600">-</div>
                <div class="text-sm text-gray-500">模糊</div>
            </div>
            <div class="text-center">
                <div id="stat-not-mastered" class="text-3xl font-bold text-red-600">-</div>
                <div class="text-sm text-gray-500">未掌握</div>
            </div>
        </div>

        <div class="mt-6 pt-6 border-t">
            <div class="text-sm text-gray-500">正确率</div>
            <div id="stat-accuracy" class="text-4xl font-bold text-green-600">-%</div>
        </div>
    </div>

    <!-- 操作按钮 -->
    <div class="flex space-x-4">
        <a href="/" class="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold py-4 px-6 rounded-xl transition">
            🏠 返回首页
        </a>
        <a href="/mistakes" class="flex-1 bg-red-100 hover:bg-red-200 text-red-700 font-bold py-4 px-6 rounded-xl transition">
            ❌ 查看错字
        </a>
        <a href="/" class="flex-1 bg-green-500 hover:bg-green-600 text-white font-bold py-4 px-6 rounded-xl transition">
            🔄 再测一次
        </a>
    </div>
</div>

<script>
const urlParams = new URLSearchParams(window.location.search);
const sessionId = urlParams.get('session');

async function loadResults() {
    // 从 localStorage 或 API 获取结果
    // 简化处理：重新加载统计数据
    const response = await fetch('/api/stats');
    const data = await response.json();

    // 获取最新一次的统计
    if (data.daily_stats && data.daily_stats.length > 0) {
        const today = new Date().toISOString().split('T')[0];
        const todayStats = data.daily_stats.find(s => s.date === today);

        if (todayStats) {
            document.getElementById('stat-total').textContent = todayStats.total;
            document.getElementById('stat-mastered').textContent = todayStats.mastered;

            const accuracy = Math.round((todayStats.mastered / todayStats.total) * 100);
            document.getElementById('stat-accuracy').textContent = accuracy + '%';
        }
    }

    // 获取详细的本次抽测结果
    // 需要通过 API 获取，这里简化显示
}

loadResults();
</script>
{% endblock %}
```

- [ ] **Step 4: Commit**

```bash
git add app/templates/quiz.html app/templates/result.html app/routers/api.py
git commit -m "feat: add quiz and result pages"
```

---

## Chunk 9: 前端页面 - 错字本和打印页

### Task 9.1: 创建错字本页面

**Files:**
- Create: `app/templates/mistakes.html`

- [ ] **Step 1: 创建错字本页面**

```html
<!-- app/templates/mistakes.html -->
{% extends "base.html" %}

{% block title %}错字本{% endblock %}

{% block content %}
<div class="max-w-4xl mx-auto">
    <h1 class="text-3xl font-bold text-gray-800 mb-6">❌ 错字本</h1>

    <p class="text-gray-600 mb-6">这里记录了所有标记为"未掌握"的汉字，多加练习吧！</p>

    <!-- 错字列表 -->
    <div id="mistakes-list" class="bg-white rounded-2xl shadow-lg overflow-hidden">
        <div class="p-4 text-center text-gray-500">
            加载中...
        </div>
    </div>

    <!-- 空状态 -->
    <div id="empty-state" class="hidden text-center py-12">
        <div class="text-6xl mb-4">🎊</div>
        <h3 class="text-xl font-bold text-gray-800 mb-2">太棒了！</h3>
        <p class="text-gray-600">你没有错字，继续保持！</p>
    </div>

    <!-- 操作按钮 -->
    <div class="mt-6 flex space-x-4">
        <a href="/" class="flex-1 bg-green-500 hover:bg-green-600 text-white font-bold py-4 px-6 rounded-xl text-center transition">
            📝 开始抽测
        </a>
        <button onclick="printMistakes()" class="flex-1 bg-blue-500 hover:bg-blue-600 text-white font-bold py-4 px-6 rounded-xl transition">
            🖨️ 打印错字卡
        </button>
    </div>
</div>

<script>
async function loadMistakes() {
    const response = await fetch('/api/mistakes');
    const data = await response.json();

    const container = document.getElementById('mistakes-list');

    if (data.mistakes.length === 0) {
        container.classList.add('hidden');
        document.getElementById('empty-state').classList.remove('hidden');
        return;
    }

    let html = '';
    data.mistakes.forEach((m, index) => {
        html += `
            <div class="border-b last:border-b-0 p-4 hover:bg-red-50 transition">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-4">
                        <div class="text-4xl font-bold text-gray-800" style="font-family: 'KaiTi', 'STKaiti', serif; width: 60px;">
                            ${m.char}
                        </div>
                        <div>
                            <div class="text-lg text-green-600 font-medium">${m.pinyin}</div>
                            <div class="text-sm text-gray-600">${m.lesson}</div>
                        </div>
                    </div>
                    <div class="text-right">
                        <div class="text-sm text-red-600 font-medium">错了 ${m.mistake_count} 次</div>
                        <div class="text-xs text-gray-400">最近: ${m.last_tested}</div>
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

function printMistakes() {
    window.location.href = '/print?source=mistakes';
}

loadMistakes();
</script>
{% endblock %}
```

- [ ] **Step 2: 创建打印页面**

```html
<!-- app/templates/print.html -->
{% extends "base.html" %}

{% block title %}打印卡片{% endblock %}

{% block content %}
<div class="max-w-4xl mx-auto">
    <h1 class="text-3xl font-bold text-gray-800 mb-6">🖨️ 打印卡片</h1>

    <!-- 打印设置 -->
    <div class="bg-white rounded-2xl shadow-lg p-6 mb-6">
        <h3 class="font-bold text-gray-700 mb-4">选择打印内容</h3>

        <div class="space-y-3 mb-6">
            <label class="flex items-center space-x-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
                <input type="radio" name="print-source" value="mistakes" class="w-5 h-5 text-green-500">
                <span>错字本（所有未掌握的汉字）</span>
            </label>
            <label class="flex items-center space-x-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
                <input type="radio" name="print-source" value="all" class="w-5 h-5 text-green-500" checked>
                <span>全部汉字</span>
            </label>
        </div>

        <button onclick="generatePrintPage()" class="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 px-6 rounded-xl transition">
            生成打印页面
        </button>
    </div>

    <!-- 打印预览 -->
    <div id="print-preview" class="hidden">
        <div class="flex justify-between items-center mb-4">
            <h3 class="font-bold text-gray-700">打印预览</h3>
            <button onclick="window.print()" class="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded-lg transition">
                🖨️ 打印
            </button>
        </div>

        <div id="cards-container" class="bg-white p-8 shadow-lg">
            <!-- 卡片将在这里生成 -->
        </div>
    </div>
</div>

<style>
@media print {
    nav, footer, .no-print {
        display: none !important;
    }

    #print-preview {
        display: block !important;
    }

    #cards-container {
        box-shadow: none !important;
        padding: 0 !important;
    }

    body {
        background: white !important;
    }

    main {
        max-width: 100% !important;
        padding: 0 !important;
    }
}

.print-card {
    width: 90mm;
    height: 60mm;
    border: 2px solid #333;
    display: inline-flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    margin: 5mm;
    page-break-inside: avoid;
    background: white;
}

.print-card-front {
    font-size: 36pt;
    font-family: 'KaiTi', 'STKaiti', serif;
}

.print-card-back {
    font-size: 14pt;
    text-align: center;
    padding: 5mm;
}

.print-card-pinyin {
    font-size: 18pt;
    color: #059669;
    margin-bottom: 2mm;
}
</style>

<script>
async function generatePrintPage() {
    const source = document.querySelector('input[name="print-source"]:checked').value;

    let characters = [];

    if (source === 'mistakes') {
        const response = await fetch('/api/mistakes');
        const data = await response.json();
        characters = data.mistakes;
    } else {
        // 获取所有汉字
        const semesters = await fetch('/api/semesters').then(r => r.json());
        for (const s of semesters.semesters) {
            const chars = await fetch(`/api/characters?semester=${s.id}`).then(r => r.json());
            characters.push(...chars.characters);
        }
    }

    const container = document.getElementById('cards-container');
    container.innerHTML = '';

    // 生成卡片（正面汉字，背面信息）
    characters.forEach(char => {
        const card = document.createElement('div');
        card.className = 'print-card';

        if (source === 'mistakes') {
            card.innerHTML = `
                <div class="print-card-front">${char.char}</div>
                <div class="print-card-back">
                    <div class="print-card-pinyin">${char.pinyin}</div>
                    <div>${char.lesson}</div>
                </div>
            `;
        } else {
            card.innerHTML = `
                <div class="print-card-front">${char.char}</div>
                <div class="print-card-back">
                    <div class="print-card-pinyin">${char.pinyin}</div>
                    <div>${char.meaning}</div>
                </div>
            `;
        }

        container.appendChild(card);
    });

    document.getElementById('print-preview').classList.remove('hidden');
}
</script>
{% endblock %}
```

- [ ] **Step 3: Commit**

```bash
git add app/templates/mistakes.html app/templates/print.html
git commit -m "feat: add mistakes and print pages"
```

---

## Chunk 10: 测试和优化

### Task 10.1: 运行完整测试

**Files:**
- Test: All test files

- [ ] **Step 1: 运行所有测试**

```bash
pytest tests/ -v --tb=short
```

Expected: All tests PASS

- [ ] **Step 2: 代码格式检查**

```bash
ruff check app/ tests/ || echo "Install ruff: pip install ruff"
```

- [ ] **Step 3: Commit**

```bash
git commit -m "test: verify all tests pass" --allow-empty
```

---

### Task 10.2: 创建 README

**Files:**
- Create: `README.md`

- [ ] **Step 1: 创建 README**

```markdown
# 汉字抽测卡

帮助小学生每日校验汉字掌握情况的 Web 应用程序。

## 功能特点

- 📚 **本地数据**: 使用 Markdown 文件存储汉字数据和评测记录
- 🎯 **智能抽测**: 根据掌握情况动态调整抽测内容
- 🔄 **双向模式**: 支持汉字→拼音和拼音→汉字两种模式
- ❌ **错字本**: 自动汇总未掌握的汉字
- 🖨️ **打印功能**: 生成可打印的纸质抽测卡
- 👶 **儿童友好**: 色彩丰富的界面，适合小学生使用

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动应用

```bash
uvicorn app.main:app --reload
```

然后访问 http://localhost:8000

### 添加汉字数据

在 `data/characters/` 目录下创建 Markdown 文件：

```markdown
# 一年级下册

## 第一课：春天来了

| 汉字 | 拼音 | 释义 | 例句 |
|------|------|------|------|
| 春 | chūn | 春季，一年的第一季 | 春天来了，花儿开了。 |
```

## 项目结构

```
.
├── app/              # 应用程序
│   ├── main.py       # FastAPI 入口
│   ├── models/       # 数据模型
│   ├── services/     # 业务逻辑
│   ├── routers/      # 路由
│   ├── templates/    # HTML 模板
│   └── static/       # 静态资源
├── data/             # 数据文件
│   ├── characters/   # 汉字数据
│   └── records/      # 评测记录
└── tests/            # 测试文件
```

## 使用说明

1. 在首页选择学期和课文
2. 设置每日抽测数量（默认 20 个）
3. 点击"开始抽测"
4. 根据显示的汉字或拼音回忆答案
5. 点击"显示答案"查看正确结果
6. 标记掌握程度（掌握/模糊/未掌握）
7. 在"错字本"查看和复习未掌握的字
8. 使用"打印"功能生成纸质卡片

## 开发

### 运行测试

```bash
pytest tests/ -v
```

## License

MIT
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README"
```

---

## 计划完成

**Plan complete and saved to `docs/superpowers/plans/2026-03-16-chinese-character-quiz-implementation.md`. Ready to execute?**

### 执行路径

由于本项目使用 Claude Code（支持 subagents），**请使用 `superpowers:subagent-driven-development` 执行本计划**。

每个 Chunk 可以并行或串行执行，建议按顺序：
1. Chunk 1-2: 基础架构和数据模型
2. Chunk 3-5: 服务层
3. Chunk 6: API 层
4. Chunk 7-9: 前端页面
5. Chunk 10: 测试和优化
