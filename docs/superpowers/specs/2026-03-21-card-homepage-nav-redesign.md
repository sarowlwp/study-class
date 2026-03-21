# 卡片主页 + 导航改造设计文档

**日期**: 2026-03-21
**范围**: `base.html`、`index.html`（重写）、新增 `hanzi.html`、`pages.py`、各功能模板（添加 page_title block）

---

## 背景

当前导航栏在 iPad 宽度下文字折行，且英语抽测入口未放入主导航。通过改造为卡片主页 + 简化顶栏，解决响应式问题并统一功能入口。

---

## 目标

1. `/` 改为纯卡片功能主页，所有功能入口在此一览
2. 新增 `/hanzi` 路由，承接原首页汉字抽测配置逻辑
3. 顶栏简化：左侧 Logo（点击回主页），右侧在功能页动态显示「← 返回主页 · 页面名」
4. 英语抽测加入主页卡片入口

---

## 设计

### 1. 新主页（`app/templates/index.html`，路由 `/`）

完全重写为卡片网格，不设 `page_title`（顶栏右侧不显示返回区）。

**卡片列表（顺序固定）：**

| 序号 | Emoji | 标题 | 说明 | 路由 |
|------|-------|------|------|------|
| 1 | 🎯 | 汉字抽测卡 | 按课文抽测生字 | `/hanzi` |
| 2 | ❌ | 错字本 | 复习没掌握的汉字 | `/mistakes` |
| 3 | 📄 | 字帖 | 生成描红字帖 | `/worksheet` |
| 4 | 📚 | 教材预览 | 查看电子版教材 | `/pdfs` |
| 5 | 📐 | 数学每日小测 | 生成可打印数学练习 | `/math-quiz` |
| 6 | 🔤 | 英语抽测 | 单词听写练习 | `/english` |

**布局：**
- Tailwind：`grid grid-cols-2 md:grid-cols-3 gap-4`
- 每张卡片：白底圆角卡片（`bg-white rounded-xl shadow p-6`），hover 加深阴影
- 卡片内部：大 emoji（`text-4xl`）+ 粗体标题 + 一行灰色说明文字
- 卡片整体为 `<a>` 标签，点击直接跳转

**页面结构：**
```
[标题：语文学习小工具 🎯]
[副标题：选择今天要练习的内容]
[卡片网格 2×3]
```

---

### 2. 顶栏改造（`app/templates/base.html`）

**删除**：所有 `<a>` 功能导航链接（汉字抽测卡、错字本、字帖、教材预览、数学每日小测）

**保留/新增**：
```html
<nav class="bg-white shadow-md">
  <div class="max-w-4xl mx-auto px-4 py-3">
    <div class="flex items-center justify-between">
      <!-- 左侧：Logo，始终显示，点击回主页 -->
      <a href="/" class="flex items-center space-x-2">
        <span class="text-2xl">📚</span>
        <span class="text-xl font-bold text-green-600">语文学习小工具</span>
      </a>
      <!-- 右侧：仅功能页显示，主页（page_title 为空）时隐藏 -->
      {% if page_title %}
      <div class="flex items-center space-x-2 text-sm text-gray-500">
        <a href="/" class="hover:text-green-600 transition">← 返回主页</a>
        <span>·</span>
        <span class="text-gray-700 font-medium">{{ page_title }}</span>
      </div>
      {% endif %}
    </div>
  </div>
</nav>
```

**`page_title` 传递机制**：
- `base.html` 定义 `{% block page_title %}{% endblock %}`，模板内容填充后通过 Jinja2 `set` 赋值给变量，或直接由后端路由传入 context
- **推荐方式**：后端路由在 `TemplateResponse` context 中传入 `page_title` 字符串；主页路由不传（默认 `None`/空）

---

### 3. 新汉字抽测页（`app/templates/hanzi.html`，路由 `/hanzi`）

将当前 `index.html` 的全部内容原样复制，不做任何逻辑改动。模板接收 `page_title="汉字抽测卡"`（由路由传入）。

---

### 4. 路由变更（`app/routers/pages.py`）

| 路由 | 变更 | context 新增 |
|------|------|-------------|
| `GET /` | 渲染新 `index.html`（卡片主页） | 无 `page_title` |
| `GET /hanzi`（新增） | 渲染 `hanzi.html` | `page_title="汉字抽测卡"` |
| `GET /mistakes` | 渲染 `mistakes.html` | `page_title="错字本"` |
| `GET /worksheet` | 渲染 `worksheet.html` | `page_title="字帖"` |
| `GET /pdfs` | 渲染 `pdfs.html` | `page_title="教材预览"` |
| `GET /math-quiz` | 渲染 `math_quiz.html` | `page_title="数学每日小测"` |
| `GET /quiz` | 渲染 `quiz.html` | `page_title="汉字抽测"` |
| `GET /result` | 渲染 `result.html` | `page_title="抽测结果"` |
| `GET /print` | 渲染 `print.html` | `page_title="打印卡片"` |

英语相关路由由 `app/routers/english.py` 管理，需同步添加 `page_title`（见下）。

---

### 5. 现有功能模板调整

以下模板**只需删除原有 Quick Links 区块**（如果有），无需其他逻辑改动：
- `index.html`（原首页）的 Quick Links 区块在新 `hanzi.html` 中也一并删除（功能入口已统一到主页）

以下模板**无需改动 HTML**（`page_title` 由路由注入，base.html 自动渲染）：
- `mistakes.html`、`worksheet.html`、`pdfs.html`、`math_quiz.html`、`quiz.html`、`result.html`、`print.html`

---

### 6. 英语路由（`app/routers/english.py`）

需添加 `page_title` 到以下路由的 context：
- `GET /english` → `page_title="英语抽测"`
- `GET /english/quiz` → `page_title="英语抽测"`（或「英语抽测 - 进行中」）
- `GET /english/result` → `page_title="英语抽测结果"`
- `GET /english/mistakes` → `page_title="英语错词本"`

---

## 约束

- 不改动任何后端 API、业务逻辑、数据层
- `hanzi.html` 内的 JS 逻辑（学期选择、课文选择、开始抽测）与现有 `index.html` 完全一致，不引入新行为
- 原首页中的 Quick Links 区块（指向 mistakes/print/pdfs/math-quiz/english 的卡片）在 `hanzi.html` 中删除，避免重复导航

---

## 文件变更清单

| 操作 | 文件 |
|------|------|
| 重写 | `app/templates/index.html` |
| 新建 | `app/templates/hanzi.html` |
| 修改 | `app/templates/base.html` |
| 修改 | `app/routers/pages.py` |
| 修改 | `app/routers/english.py` |
