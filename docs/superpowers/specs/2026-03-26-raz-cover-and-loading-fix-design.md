# RAZ 封面缩略图与练习页面加载修复设计文档

**日期**: 2026-03-26
**作者**: Claude Code
**状态**: 已评审通过

---

## 1. 背景与目标

### 1.1 背景
- 当前 RAZ 书库页面书籍卡片仅显示 📚 emoji，未使用已存在的封面资源
- 练习页面从 `config.current_session` 恢复断点时可能因数据问题导致页面空白

### 1.2 目标
1. 在书库列表中展示每本书的封面缩略图
2. 修复练习页面点击学习后内容空白的问题

---

## 2. 需求分析

### 2.1 封面缩略图
- 每本书的 `book.json` 已包含 `cover` 字段（如 `"cover": "cover.jpg"`）
- 封面文件与书籍其他资源在同一目录下
- 需要处理封面图片缺失或加载失败的情况

### 2.2 练习页面空白问题
- 问题：用户点击"学习"后，新页面整体无内容
- 可能原因：
  - `BOOK_DATA.pages` 为空数组
  - session 恢复的索引越界
  - 页面初始化逻辑未考虑边界情况

---

## 3. 设计方案

### 3.1 封面缩略图

**选择方案**: B（顶部图片 + 底部文字）

**设计理由**:
- 图片清晰展示，用户可直观识别书籍
- 文字在图片下方，不受封面色彩影响
- 实现简单，易于维护

**卡片布局**:
```
+------------------+
|                  |
|   封面图片        |  <-- aspect-ratio: 3/4
|   (object-cover) |
|                  |
+------------------+
| 书名（两行截断）   |
+------------------+
```

**错误处理**: 封面加载失败时显示默认占位图

### 3.2 练习页面加载修复

**选择方案**: A（加强初始化检查）

**设计理由**:
- 在客户端进行数据校验，无需服务端改动
- 可立即向用户展示友好错误提示
- 修复 session 恢复逻辑的边界问题

**检查点**:
1. 校验 `BOOK_DATA.pages` 是否存在且非空
2. 恢复 session 时检查 page 是否存在
3. 确保 `sentence_index` 在有效范围内
4. 最终索引边界检查（防止越界）

---

## 4. 实现细节

### 4.1 数据模型修改

**`app/models/raz.py`**:
```python
@dataclass
class RazBook:
    id: str           # 格式: level-{x}/{dir_name}，如 "level-a/a-fish-sees"
    title: str
    level: str
    pages: List[RazPage]
    video: Optional[str] = None
    cover: Optional[str] = None  # 新增: 仅允许安全文件名

    @property
    def directory_name(self) -> str:
        """返回书籍目录名，用于构建资源路径。"""
        return self.id.split("/")[-1] if "/" in self.id else self.id

    def validate_cover(self) -> bool:
        """校验 cover 字段是否为安全的文件名。"""
        if not self.cover:
            return True
        import re
        return bool(re.match(r'^[a-zA-Z0-9_\-\.]+\.(jpg|jpeg|png|gif|webp)$', self.cover))
```

**说明**:
- `id` 格式为 `level-{x}/{dir_name}`，如 `level-a/a-fish-sees`
- `cover` 字段仅允许安全文件名（字母、数字、下划线、连字符、点），防止路径遍历
- 图片扩展名白名单：jpg, jpeg, png, gif, webp

### 4.2 服务层修改

**`app/services/raz_service.py`**:
- `_load_book()` 方法读取 JSON 中的 `cover` 字段

### 4.3 路由层修改

**`app/routers/raz.py`**:
- `raz_index()` 路由确保 `book.cover` 传递到模板
- `api_get_books()` API 可选返回 cover 字段

### 4.4 前端模板修改

**`app/templates/raz/index.html`**:
```html
<div class="aspect-[3/4] w-full overflow-hidden rounded-t-lg bg-gray-100">
  <img src="/raz/media/{{ book.level }}/{{ book.directory_name }}/{{ book.cover }}"
       alt="{{ book.title }}"
       class="h-full w-full object-cover"
       onerror="this.src='/static/images/default-cover.png'">
</div>
<div class="p-3">
  <p class="text-center font-semibold text-gray-700 text-sm line-clamp-2">
    {{ book.title }}
  </p>
</div>
```

**安全说明**:
- 使用 `book.directory_name` 属性获取目录名，避免在模板中处理字符串分割
- Jinja2 默认自动转义 HTML 特殊字符，`{{ book.title }}` 会自动转义 `<`, `>`, `"` 等字符，防止 XSS
- `cover` 字段已在服务端校验，仅允许安全的文件名

**`app/templates/raz/practice.html`**:
```javascript
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
  document.getElementById('btn-record').disabled = true;
  document.getElementById('btn-play').disabled = true;
}
```

### 4.5 默认封面占位图

创建 `app/static/images/default-cover.png` 或 SVG 作为封面加载失败的 fallback。

---

## 5. 边界情况处理

| 场景 | 处理方式 |
|------|----------|
| 封面字段缺失 (`null`/`undefined`) | 使用默认占位图 |
| 封面字段为空字符串 | 使用默认占位图 |
| 封面文件名包含非法字符 | 服务端校验失败，使用默认占位图 |
| 封面文件不存在 | `onerror` 显示默认图 |
| 书籍 pages 为空数组 | 显示错误提示，禁用录音按钮 |
| 当前 page.sentences 为空数组 | 显示错误提示，禁用录音按钮 |
| session page 不存在 | 重置到第一页 |
| session sentence_index 越界 | 限制在有效范围内 |
| session 恢复后 page.sentences 为空 | 显示错误提示

---

## 6. 测试计划

### 6.1 封面缩略图
- [ ] 有封面的书籍正确显示封面
- [ ] 无封面字段的书籍显示默认图
- [ ] 封面字段为空字符串时显示默认图
- [ ] 封面包含非法字符时被拒绝，显示默认图
- [ ] 封面加载失败时显示默认图
- [ ] 长书名正确截断（最多两行）
- [ ] 书名包含 HTML 特殊字符（如 `<`, `>`, `"`）时正确转义显示

### 6.2 练习页面
- [ ] 正常书籍加载正确
- [ ] pages 为空的书籍显示错误提示
- [ ] 当前 page.sentences 为空的页面显示错误提示
- [ ] 从 session 恢复断点正确
- [ ] session page 不存在时重置到第一页
- [ ] session sentence_index 越界时限制在有效范围
- [ ] 验证 XSS 防护（书名包含特殊字符）

---

## 7. 非功能性需求

- **性能**: 封面图片使用浏览器缓存，不增加额外请求
- **兼容性**: 保持现有 API 响应结构，仅新增可选字段
- **可访问性**: 图片添加 `alt` 属性

---

## 8. 后续优化（可选）

- 懒加载封面图片优化首屏性能
- 服务端预生成封面缩略图（小尺寸）
- 统计封面缺失的书籍列表
