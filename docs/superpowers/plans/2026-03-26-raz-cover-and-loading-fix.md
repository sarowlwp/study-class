# RAZ 封面缩略图与练习页面加载修复实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 RAZ 书库列表添加封面缩略图显示，并修复练习页面点击学习后内容空白的问题

**Architecture:**
- 后端：扩展 `RazBook` 模型添加 `cover` 字段和 `directory_name` 属性，服务层读取封面并校验安全性
- 前端：书库卡片使用封面图片+书名的布局；练习页面增强初始化检查处理边界情况

**Tech Stack:** Python (FastAPI), Jinja2, TailwindCSS, JavaScript

---

## 文件结构

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/models/raz.py` | 修改 | 添加 `cover` 字段、`directory_name` 属性、封面校验方法 |
| `app/services/raz_service.py` | 修改 | `_load_book()` 读取 cover 字段 |
| `app/routers/raz.py` | 修改 | `api_get_books()` 返回 cover 字段 |
| `app/templates/raz/index.html` | 修改 | 书籍卡片显示封面图片 |
| `app/templates/raz/practice.html` | 修改 | 增强 init() 函数的错误处理 |
| `app/static/images/default-cover.png` | 创建 | 封面加载失败时的默认占位图 |
| `tests/test_raz_models.py` | 创建 | 测试 RazBook 的 cover 校验和 directory_name |
| `tests/test_raz_service.py` | 修改 | 添加封面相关测试 |

---

## Task 1: 扩展 RazBook 数据模型

**Files:**
- Modify: `app/models/raz.py:14-21`
- Test: `tests/test_raz_models.py` (创建)

- [ ] **Step 1: 编写测试 - 验证 RazBook 新功能**

```python
# tests/test_raz_models.py
import pytest
from app.models.raz import RazBook, RazPage


class TestRazBook:
    def test_directory_name_with_slash(self):
        """测试 id 包含斜杠时正确提取目录名"""
        book = RazBook(
            id="level-a/a-fish-sees",
            title="A Fish Sees",
            level="a",
            pages=[],
            cover="cover.jpg"
        )
        assert book.directory_name == "a-fish-sees"

    def test_directory_name_without_slash(self):
        """测试 id 不包含斜杠时返回原值"""
        book = RazBook(
            id="a-fish-sees",
            title="A Fish Sees",
            level="a",
            pages=[],
            cover="cover.jpg"
        )
        assert book.directory_name == "a-fish-sees"

    def test_validate_cover_valid(self):
        """测试有效的 cover 文件名通过校验"""
        book = RazBook(
            id="level-a/test",
            title="Test",
            level="a",
            pages=[],
            cover="cover.jpg"
        )
        assert book.validate_cover() is True

    def test_validate_cover_none(self):
        """测试 cover 为 None 时通过校验"""
        book = RazBook(
            id="level-a/test",
            title="Test",
            level="a",
            pages=[],
            cover=None
        )
        assert book.validate_cover() is True

    def test_validate_cover_invalid_path_traversal(self):
        """测试路径遍历字符被识别为无效"""
        book = RazBook(
            id="level-a/test",
            title="Test",
            level="a",
            pages=[],
            cover="../../../etc/passwd"
        )
        assert book.validate_cover() is False

    def test_validate_cover_invalid_extension(self):
        """测试不允许的扩展名被识别为无效"""
        book = RazBook(
            id="level-a/test",
            title="Test",
            level="a",
            pages=[],
            cover="cover.exe"
        )
        assert book.validate_cover() is False
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_raz_models.py -v
```

Expected: FAIL (attribute not found)

- [ ] **Step 3: 实现 RazBook 新功能**

```python
# app/models/raz.py - 完整文件内容
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
            r'^[a-zA-Z0-9_\-\.]+\.(jpg|jpeg|png|gif|webp)$',
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
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_raz_models.py -v
```

Expected: PASS (6 tests)

- [ ] **Step 5: 提交**

```bash
git add tests/test_raz_models.py app/models/raz.py
git commit -m "feat(raz): add cover field and validation to RazBook model

- Add cover field to RazBook dataclass
- Add directory_name property for resource path building
- Add validate_cover() method with security checks
- Add comprehensive unit tests"
```

---

## Task 2: 修改 RazService 读取 cover 字段

**Files:**
- Modify: `app/services/raz_service.py:37-60`
- Test: `tests/test_raz_service.py` (修改)

- [ ] **Step 1: 编写测试 - 验证服务层读取 cover**

```python
# 添加到 tests/test_raz_service.py

def test_load_book_with_cover(tmp_path):
    """测试 _load_book 正确读取 cover 字段"""
    from app.services.raz_service import RazService
    from app.models.raz import RazBook

    # 创建临时书籍目录结构
    book_dir = tmp_path / "level-a" / "test-book"
    book_dir.mkdir(parents=True)

    book_json = book_dir / "book.json"
    book_json.write_text(json.dumps({
        "id": "level-a/test-book",
        "title": "Test Book",
        "level": "a",
        "cover": "cover.jpg",
        "pages": [
            {"page": 1, "pdf": "page1.pdf", "audio": "page1.mp3", "sentences": ["Hello"]}
        ]
    }), encoding="utf-8")

    service = RazService(tmp_path, tmp_path / "records", tmp_path / "config.json")
    book = service._load_book(book_dir)

    assert book is not None
    assert book.cover == "cover.jpg"
    assert book.validate_cover() is True


def test_load_book_without_cover(tmp_path):
    """测试 _load_book 处理无 cover 字段的情况"""
    from app.services.raz_service import RazService

    book_dir = tmp_path / "level-a" / "test-book"
    book_dir.mkdir(parents=True)

    book_json = book_dir / "book.json"
    book_json.write_text(json.dumps({
        "id": "level-a/test-book",
        "title": "Test Book",
        "level": "a",
        "pages": []
    }), encoding="utf-8")

    service = RazService(tmp_path, tmp_path / "records", tmp_path / "config.json")
    book = service._load_book(book_dir)

    assert book is not None
    assert book.cover is None
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_raz_service.py::test_load_book_with_cover -v
```

Expected: FAIL (cover attribute not found or wrong value)

- [ ] **Step 3: 修改 _load_book 方法**

```python
# app/services/raz_service.py - 修改 _load_book 方法 (第37-60行)

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

        # 读取 cover 字段，如果校验失败则设为 None
        cover = data.get("cover")
        book = RazBook(
            id=data["id"],
            title=data["title"],
            level=data["level"],
            pages=pages,
            video=data.get("video"),
            cover=cover,
        )
        # 如果 cover 不合法，重置为 None
        if not book.validate_cover():
            book.cover = None
        return book
    except Exception:
        return None
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_raz_service.py::test_load_book_with_cover tests/test_raz_service.py::test_load_book_without_cover -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add tests/test_raz_service.py app/services/raz_service.py
git commit -m "feat(raz): load cover field in RazService with validation

- _load_book() now reads and validates cover field from book.json
- Invalid cover filenames are reset to None for security
- Add tests for loading books with and without cover"
```

---

## Task 3: 修改 API 返回 cover 字段

**Files:**
- Modify: `app/routers/raz.py:96-101`

- [ ] **Step 1: 修改 api_get_books 端点**

```python
# app/routers/raz.py - 修改第96-101行的 api_get_books 函数

@router.get("/api/raz/books")
async def api_get_books(level: Optional[str] = None):
    config = raz_service.get_config()
    target_level = level or config.current_level
    books = raz_service.get_books(target_level)
    return [{
        "id": b.id,
        "title": b.title,
        "level": b.level,
        "page_count": len(b.pages),
        "cover": b.cover,  # 新增
    } for b in books]
```

- [ ] **Step 2: 手动测试 API**

```bash
# 启动服务器后测试
curl -s http://localhost:8000/api/raz/books?level=a | python -m json.tool | head -20
```

Expected: 返回的书籍对象包含 cover 字段

- [ ] **Step 3: 提交**

```bash
git add app/routers/raz.py
git commit -m "feat(raz): include cover field in /api/raz/books API response"
```

---

## Task 4: 创建默认封面占位图

**Files:**
- Create: `app/static/images/default-cover.png`

- [ ] **Step 1: 创建 SVG 格式的默认封面**

```bash
# 创建 SVG 文件 (体积小，可缩放)
cat > app/static/images/default-cover.svg << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" width="300" height="400" viewBox="0 0 300 400">
  <rect width="300" height="400" fill="#f3f4f6"/>
  <rect x="20" y="20" width="260" height="360" fill="#e5e7eb" stroke="#d1d5db" stroke-width="2"/>
  <text x="150" y="180" font-family="Arial, sans-serif" font-size="48" fill="#9ca3af" text-anchor="middle">📚</text>
  <text x="150" y="240" font-family="Arial, sans-serif" font-size="16" fill="#6b7280" text-anchor="middle">No Cover</text>
</svg>
EOF
```

- [ ] **Step 2: 验证文件创建成功**

```bash
ls -la app/static/images/default-cover.svg
file app/static/images/default-cover.svg
```

Expected: 文件存在，类型为 SVG

- [ ] **Step 3: 提交**

```bash
git add app/static/images/default-cover.svg
git commit -m "feat(raz): add default cover placeholder SVG"
```

---

## Task 5: 修改书库列表模板显示封面

**Files:**
- Modify: `app/templates/raz/index.html:38-46`

- [ ] **Step 1: 修改书籍卡片模板**

```html
<!-- app/templates/raz/index.html - 替换第38-46行的书籍卡片 -->
{% if books %}
<div class="grid grid-cols-2 md:grid-cols-3 gap-4" id="book-list">
  {% for book in books %}
  <a href="/raz/book/{{ book.level }}/{{ book.directory_name }}"
     class="block bg-white rounded-xl shadow hover:shadow-md transition overflow-hidden border border-gray-100">
    <!-- 封面图片 -->
    <div class="aspect-[3/4] w-full overflow-hidden bg-gray-100">
      {% if book.cover %}
      <img src="/raz/media/{{ book.level }}/{{ book.directory_name }}/{{ book.cover }}"
           alt="{{ book.title }}"
           class="h-full w-full object-cover"
           onerror="this.src='/static/images/default-cover.svg'">
      {% else %}
      <img src="/static/images/default-cover.svg"
           alt="{{ book.title }}"
           class="h-full w-full object-cover">
      {% endif %}
    </div>
    <!-- 书名 -->
    <div class="p-3">
      <p class="text-center font-semibold text-gray-700 text-sm line-clamp-2">{{ book.title }}</p>
      <p class="text-center text-xs text-gray-400 mt-1">{{ book.pages | length }} 页</p>
    </div>
  </a>
  {% endfor %}
</div>
{% else %}
```

- [ ] **Step 2: 手动测试页面**

```bash
# 启动服务器
uvicorn app.main:app --reload

# 访问 http://localhost:8000/raz 查看效果
```

Expected:
- 有封面的书籍显示封面图片
- 无封面的书籍显示默认占位图
- 图片加载失败时显示默认占位图

- [ ] **Step 3: 提交**

```bash
git add app/templates/raz/index.html
git commit -m "feat(raz): display book cover thumbnails in library list

- Show cover image at top of book card with 3:4 aspect ratio
- Use default-cover.svg for missing or failed covers
- Display page count below title"
```

---

## Task 6: 修复练习页面初始化

**Files:**
- Modify: `app/templates/raz/practice.html:80-91`

- [ ] **Step 1: 替换 init() 函数**

```javascript
// app/templates/raz/practice.html - 替换第80-91行的 init 函数

// ── 初始化 ───────────────────────────────────────────────────────────────────
function init() {
  // 1. 数据校验：检查 pages 是否存在且非空
  if (!BOOK_DATA.pages || BOOK_DATA.pages.length === 0) {
    showError('本书暂无练习内容，请返回书库选择其他书籍。');
    return;
  }

  // 2. 恢复 session（带边界检查）
  const session = {{ (config.current_session or {})|tojson }};
  if (session.book_id === BOOK_DATA.id) {
    const pageIdx = BOOK_DATA.pages.findIndex(p => p.page === session.page);
    // 检查 pageIdx 是否在有效范围内
    if (pageIdx >= 0 && pageIdx < BOOK_DATA.pages.length) {
      const page = BOOK_DATA.pages[pageIdx];
      // 检查 sentences 是否存在且非空
      if (page.sentences && page.sentences.length > 0) {
        currentPageIdx = pageIdx;
        currentSentIdx = Math.min(
          Math.max(0, session.sentence_index || 0),
          page.sentences.length - 1
        );
      }
    }
  }

  // 3. 最终索引边界检查（防止越界）
  currentPageIdx = Math.max(0, Math.min(currentPageIdx, BOOK_DATA.pages.length - 1));

  // 4. 确保当前页有 sentences
  const currentPage = BOOK_DATA.pages[currentPageIdx];
  if (!currentPage.sentences || currentPage.sentences.length === 0) {
    showError('当前页面无练习内容，请返回书库选择其他书籍。');
    return;
  }

  renderCurrent();
}

function showError(msg) {
  document.getElementById('current-sentence').textContent = '⚠️ ' + msg;
  document.getElementById('current-sentence').className = 'text-xl font-semibold text-red-600 leading-relaxed';
  document.getElementById('btn-record').disabled = true;
  document.getElementById('btn-play').disabled = true;
  document.getElementById('page-pdf').style.display = 'none';
}
```

- [ ] **Step 2: 手动测试练习页面**

```bash
# 访问正常书籍的练习页面
open http://localhost:8000/raz/practice/a/a-fish-sees

# 测试页面应该正常加载
```

Expected:
- 正常书籍正确加载
- pages 为空的书籍显示错误提示
- session 恢复异常时重置到第一页

- [ ] **Step 3: 提交**

```bash
git add app/templates/raz/practice.html
git commit -m "fix(raz): strengthen practice page initialization with error handling

- Add validation for BOOK_DATA.pages existence and non-empty
- Add boundary checks when restoring from session
- Add final validation for current page sentences
- Add showError() function for user-friendly error messages
- Fix blank page issue caused by invalid session data"
```

---

## Task 7: 修复模板中的书籍链接

**Files:**
- Modify: `app/templates/raz/index.html:40`

- [ ] **Step 1: 检查并修复书籍链接**

当前模板中已经有 `book.directory_name`，但需要确认 `app/routers/raz.py` 中 `raz_book` 路由的 URL 模式是否匹配。

```python
# 检查 app/routers/raz.py 第42-52行
@router.get("/raz/book/{level}/{book_dir}")
async def raz_book(request: Request, level: str, book_dir: str):
    book_id = f"level-{level}/{book_dir}"
    ...
```

链接格式 `/raz/book/{{ book.level }}/{{ book.directory_name }}` 是正确的。

- [ ] **Step 2: 确认无需修改并标记完成**

```bash
# 点击书籍卡片测试链接是否正常跳转
echo "手动测试：点击书库中的书籍卡片，应正确跳转到书籍详情页"
```

- [ ] **Step 3: 如果发现问题则提交修复**

```bash
# 只有发现问题时才执行此提交
git add app/templates/raz/index.html
git commit -m "fix(raz): correct book detail page links using directory_name"
```

---

## 集成测试

- [ ] **Step 1: 运行全部测试**

```bash
pytest tests/test_raz_models.py tests/test_raz_service.py -v
```

Expected: All tests pass

- [ ] **Step 2: 手动端到端测试**

```bash
# 1. 启动服务器
uvicorn app.main:app --reload

# 2. 访问书库页面
echo "访问 http://localhost:8000/raz"
echo "验证：有封面的书显示封面图片，无封面的显示默认图"

# 3. 点击进入练习页面
echo "点击一本书进入练习页面"
echo "验证：页面正常加载，显示 PDF 和句子"

# 4. 测试练习功能
echo "点击'开始录音'测试录音功能"
echo "点击'听示范'测试音频播放"
```

- [ ] **Step 3: 最终提交**

```bash
git log --oneline -10
git status
```

确认所有修改已提交，无未提交的变更。

---

## 附录：边界情况验证清单

| 场景 | 验证方法 |
|------|----------|
| 封面字段缺失 | 找一本 book.json 无 cover 字段的书 |
| 封面字段为空字符串 | 修改 book.json 测试 |
| 封面文件不存在 | 修改 cover 为不存在的文件名 |
| 书籍 pages 为空 | 修改 book.json 测试 |
| session page 不存在 | 手动修改 raz-config.json 测试 |
| session sentence_index 越界 | 手动修改 raz-config.json 测试 |
| 书名含特殊字符 | 修改 book.json title 测试 XSS 防护 |

---

## 回滚计划

如果出现问题需要回滚：

```bash
# 查看提交历史
git log --oneline

# 回滚到实现前的状态（假设当前在 main 分支）
git reset --hard <commit-before-changes>

# 或者撤销特定提交
git revert <commit-hash>
```
