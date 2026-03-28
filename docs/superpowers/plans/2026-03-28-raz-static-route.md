# RAZ 静态资源路由改造实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 RAZ 静态资源路由从 `/raz/media/{level}/...` 统一改为 `/raz/level-{level}/...`

**Architecture:** 修改 FastAPI 路由定义和模板中的 URL 生成逻辑，保持文件系统路径不变

**Tech Stack:** FastAPI, Jinja2, Python 3.10+

**相关设计文档:** `docs/superpowers/specs/2026-03-28-raz-static-route-design.md`

---

## 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/routers/raz.py` | 修改 | 更新路由路径和 API 返回的 URL |
| `app/templates/raz/reader.html` | 修改 | 更新 PDF/音频 URL 生成 |
| `app/templates/raz/practice.html` | 检查/修改 | 检查是否有硬编码 `/raz/media/` 路径 |
| `app/templates/raz/book.html` | 检查/修改 | 检查是否有硬编码 `/raz/media/` 路径 |
| `app/templates/raz/index.html` | 检查/修改 | 检查是否有硬编码 `/raz/media/` 路径 |

---

## Task 1: 更新后端路由路径

**Files:**
- Modify: `app/routers/raz.py:273`

- [ ] **Step 1: 修改路由定义**

将 `@router.get("/raz/media/{level}/{book_dir}/{filename}")` 改为 `@router.get("/raz/level-{level}/{book_dir}/{filename}")`：

```python
@router.get("/raz/level-{level}/{book_dir}/{filename}")
async def raz_media(level: str, book_dir: str, filename: str):
    """安全地提供书库媒体文件。路径参数严格校验，防止路径穿越。"""
    if not all(_SAFE_PATH_PATTERN.match(p) for p in [level, book_dir, filename]):
        raise HTTPException(status_code=400, detail="Invalid path")

    file_path = RAZ_DIR / f"level-{level}" / book_dir / filename
    try:
        file_path.resolve().relative_to(RAZ_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)
```

- [ ] **Step 2: 验证路由已修改**

运行: `grep -n "raz/level-" app/routers/raz.py`

Expected: 显示修改后的路由定义

- [ ] **Step 3: Commit**

```bash
git add app/routers/raz.py
git commit -m "refactor(raz): 更新静态资源路由为 /raz/level-{level}/"
```

---

## Task 2: 更新 API 返回的 URL 格式

**Files:**
- Modify: `app/routers/raz.py:170-171`

- [ ] **Step 1: 修改 API 返回的 pdf 和 audio URL**

找到 `/api/raz/book-detail/{level}/{book_dir}` 端点，修改返回的 URL：

```python
@router.get("/api/raz/book-detail/{level}/{book_dir}")
async def api_get_book_detail(level: str, book_dir: str):
    """获取书籍详情（含时间轴，供阅读器使用）"""
    book_id = f"level-{level}/{book_dir}"
    book = raz_service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    return {
        "id": book.id,
        "title": book.title,
        "level": book.level,
        "pdf": f"/raz/{book.level}/{book_dir}/{book.pdf}" if book.pdf else None,
        "audio": f"/raz/{book.level}/{book_dir}/{book.audio}" if book.audio else None,
        "total_pages": book.total_pages,
        "sentences": [
            {"start": s.start, "end": s.end, "text": s.text, "page": s.page}
            for s in book.sentences
        ],
    }
```

- [ ] **Step 2: 验证修改**

运行: `grep -A2 '"pdf":' app/routers/raz.py`

Expected: 显示新的 URL 格式 `/raz/{book.level}/...`

- [ ] **Step 3: Commit**

```bash
git add app/routers/raz.py
git commit -m "refactor(raz): 更新 API 返回的静态资源 URL 格式"
```

---

## Task 3: 更新 reader.html 模板

**Files:**
- Modify: `app/templates/raz/reader.html:432-433`

- [ ] **Step 1: 修改 bookData 的 URL 生成**

将：
```javascript
pdf: buildResourceUrl("/raz/media/{{ book.level }}/{{ book_dir }}/{{ book.pdf or 'book.pdf' }}"),
audio: {% if book.audio %}buildResourceUrl("/raz/media/{{ book.level }}/{{ book_dir }}/{{ book.audio }}"){% else %}null{% endif %},
```

改为：
```javascript
pdf: buildResourceUrl("/raz/{{ book.level }}/{{ book_dir }}/{{ book.pdf or 'book.pdf' }}"),
audio: {% if book.audio %}buildResourceUrl("/raz/{{ book.level }}/{{ book_dir }}/{{ book.audio }}"){% else %}null{% endif %},
```

- [ ] **Step 2: 验证修改**

运行: `grep -n "buildResourceUrl" app/templates/raz/reader.html`

Expected: 显示新的 URL 路径 `/raz/{{ book.level }}/...`

- [ ] **Step 3: Commit**

```bash
git add app/templates/raz/reader.html
git commit -m "refactor(raz): 更新 reader.html 静态资源 URL"
```

---

## Task 4: 检查并更新其他模板

**Files:**
- Read/Modify: `app/templates/raz/practice.html`
- Read/Modify: `app/templates/raz/book.html`
- Read/Modify: `app/templates/raz/index.html`

- [ ] **Step 1: 检查 practice.html 中的 URL**

运行: `grep -n "/raz/media/" app/templates/raz/practice.html || echo "未找到旧路径"`

如有匹配，将 `/raz/media/` 改为 `/raz/level-` 格式。

- [ ] **Step 2: 检查 book.html 中的 URL**

运行: `grep -n "/raz/media/" app/templates/raz/book.html || echo "未找到旧路径"`

如有匹配，进行相同替换。

- [ ] **Step 3: 检查 index.html 中的 URL**

运行: `grep -n "/raz/media/" app/templates/raz/index.html || echo "未找到旧路径"`

如有匹配，进行相同替换。

- [ ] **Step 4: Commit（如有修改）**

```bash
git add -A
git commit -m "refactor(raz): 更新其他模板中的静态资源 URL"
```

---

## Task 5: 启动服务并测试

**Files:**
- N/A (验证步骤)

- [ ] **Step 1: 启动开发服务器**

```bash
uvicorn app.main:app --reload --port 8000
```

- [ ] **Step 2: 测试新路由**

在浏览器中访问（使用实际存在的书籍）:
- `http://localhost:8000/raz/level-a/mybook/book.pdf`
- 应能正常返回 PDF 文件

- [ ] **Step 3: 测试 API**

```bash
curl http://localhost:8000/api/raz/book-detail/a/mybook
```

Expected: 返回的 `pdf` 和 `audio` 字段使用新路径格式 `/raz/level-a/...`

- [ ] **Step 4: 测试 reader 页面**

在浏览器中打开 reader 页面，验证 PDF 和音频能正常加载。

---

## Task 6: 验证旧路由已失效（可选）

- [ ] **Step 1: 确认旧路由返回 404**

```bash
curl -I http://localhost:8000/raz/media/a/mybook/book.pdf
```

Expected: HTTP 404 Not Found

---

## Spec Coverage Check

| 设计文档要求 | 对应任务 |
|-------------|---------|
| 后端路由改为 `/raz/level-{level}/...` | Task 1 |
| API 返回新格式 URL | Task 2 |
| reader.html 更新 | Task 3 |
| 其他模板检查 | Task 4 |
| 本地测试 | Task 5 |

## Placeholder Scan

- 无 TBD/TODO
- 所有代码步骤包含完整代码
- 所有命令包含预期输出
- 文件路径精确
