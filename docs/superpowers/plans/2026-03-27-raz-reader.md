# RAZ Reader 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现基于 pdf.js 的 RAZ 阅读器，支持 TTS 朗读、录音评测、滑动翻页

**Architecture:**
- 后端 FastAPI 提供书籍数据 API（复用现有 raz 模块）
- 前端使用 pdf.js 渲染 PDF，Web Speech API 朗读，WebRTC 录音
- 界面基于已确认的 demo 设计（可拖拽工具栏、滑动翻页）

**Tech Stack:** FastAPI, Python 3.10+, pdf.js, Web Speech API, WebRTC

---

## 文件结构

### 新增文件
- `app/templates/raz/reader.html` - 阅读器页面模板
- `app/static/js/raz-reader.js` - 阅读器前端逻辑

### 修改文件
- `app/routers/raz.py` - 添加阅读器路由和 API
- `app/services/raz_service.py` - 支持新的 book.json 格式
- `app/models/raz.py` - 添加 RazSentence 数据类

---

## Task 1: 更新数据模型

**Files:**
- Modify: `app/models/raz.py`

**步骤:**

- [ ] **Step 1: 添加 RazSentence 数据类**

```python
@dataclass
class RazSentence:
    start: float      # 秒
    end: float        # 秒
    text: str
    page: int
    confidence: Optional[float] = None
```

- [ ] **Step 2: 更新 RazBook 支持 sentences**

```python
@dataclass
class RazBook:
    id: str
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
```

- [ ] **Step 3: 提交**

```bash
git add app/models/raz.py
git commit -m "feat(raz): add RazSentence model and update RazBook"
```

---

## Task 2: 更新服务层

**Files:**
- Modify: `app/services/raz_service.py`

**步骤:**

- [ ] **Step 1: 更新 _load_book 支持新格式**

```python
def _load_book(self, book_dir: Path) -> Optional[RazBook]:
    json_file = book_dir / "book.json"
    if not json_file.exists():
        return None

    data = json.loads(json_file.read_text(encoding="utf-8"))

    # 解析 sentences
    sentences = []
    for s in data.get("sentences", []):
        sentences.append(RazSentence(
            start=s["start"],
            end=s["end"],
            text=s["text"],
            page=s["page"],
            confidence=s.get("confidence"),
        ))

    # 计算总页数
    total_pages = max((s.page for s in sentences), default=1)

    return RazBook(
        id=data["id"],
        title=data["title"],
        level=data["level"],
        pdf=data.get("pdf"),
        audio=data.get("audio"),
        video=data.get("video"),
        cover=data.get("cover"),
        total_pages=total_pages,
        sentences=sentences,
    )
```

- [ ] **Step 2: 提交**

```bash
git add app/services/raz_service.py
git commit -m "feat(raz): support new book.json format with sentences"
```

---

## Task 3: 添加阅读器路由和 API

**Files:**
- Modify: `app/routers/raz.py`

**步骤:**

- [ ] **Step 1: 添加阅读器页面路由**

```python
@router.get("/raz/reader/{level}/{book_dir}")
async def raz_reader(request: Request, level: str, book_dir: str):
    book_id = f"level-{level}/{book_dir}"
    book = raz_service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    return templates.TemplateResponse("raz/reader.html", {
        "request": request,
        "page_title": book.title,
        "book": book,
    })
```

- [ ] **Step 2: 添加书籍数据 API**

```python
@router.get("/api/raz/book/{level}/{book_dir}")
async def api_get_book_detail(level: str, book_dir: str):
    book_id = f"level-{level}/{book_dir}"
    book = raz_service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    return {
        "id": book.id,
        "title": book.title,
        "level": book.level,
        "pdf": f"/raz/media/{book.level}/{book_dir}/{book.pdf}" if book.pdf else None,
        "audio": f"/raz/media/{book.level}/{book_dir}/{book.audio}" if book.audio else None,
        "total_pages": book.total_pages,
        "sentences": [
            {"start": s.start, "end": s.end, "text": s.text, "page": s.page}
            for s in book.sentences
        ],
    }
```

- [ ] **Step 3: 提交**

```bash
git add app/routers/raz.py
git commit -m "feat(raz): add reader route and book detail API"
```

---

## Task 4: 创建阅读器页面模板

**Files:**
- Create: `app/templates/raz/reader.html`

**步骤:**

- [ ] **Step 1: 创建模板文件**

基于 demo-final.html 创建 Jinja2 模板，替换硬编码数据为模板变量。

- [ ] **Step 2: 提交**

```bash
git add app/templates/raz/reader.html
git commit -m "feat(raz): add reader template"
```

---

## Task 5: 创建前端 JS

**Files:**
- Create: `app/static/js/raz-reader.js`

**步骤:**

- [ ] **Step 1: 创建 JS 文件**

提取 demo-final.html 中的 JavaScript 逻辑到独立文件。

- [ ] **Step 2: 提交**

```bash
git add app/static/js/raz-reader.js
git commit -m "feat(raz): add reader frontend JavaScript"
```

---

## Task 6: 添加 pdf.js 库

**Files:**
- Create: `app/static/lib/pdf.min.js`
- Create: `app/static/lib/pdf.worker.min.js`

**步骤:**

- [ ] **Step 1: 下载 pdf.js**

从 CDN 下载并保存到 static/lib/ 目录。

- [ ] **Step 2: 提交**

```bash
git add app/static/lib/pdf*.js
git commit -m "chore: add pdf.js library"
```

---

## Task 7: 测试验证

**步骤:**

- [ ] **Step 1: 运行测试**

```bash
pytest tests/test_raz_service.py -v
pytest tests/test_api.py -v
```

- [ ] **Step 2: 手动测试**

1. 访问 `/raz/reader/a/a-fish-sees`
2. 验证 PDF 渲染
3. 验证音频播放
4. 验证录音评测
5. 验证滑动翻页

- [ ] **Step 3: 提交**

```bash
git commit -m "test(raz): verify reader implementation"
```

---

## 执行方式

**Plan complete! Two execution options:**

**1. Subagent-Driven (recommended)** - Dispatch a fresh subagent per task, review between tasks

**2. Inline Execution** - Execute tasks in this session with checkpoints

Which approach would you prefer?
