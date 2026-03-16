# 顶部导航菜单优化 - 实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 优化站点顶部导航菜单，包括更名、调整导航项顺序、增大点击区域

**Architecture:** 纯前端模板修改，仅涉及 Jinja2 模板文件的 HTML 结构调整，使用 Tailwind CSS 类控制样式

**Tech Stack:** Jinja2, Tailwind CSS

---

## Chunk 1: 修改 base.html 导航和站点标题

**Files:**
- Modify: `app/templates/base.html`

### Task 1.1: 更新站点标题（Logo 文字）

- [ ] **Step 1: 修改站点标题**

  File: `app/templates/base.html`, Line 18

  ```html
  <!-- Before -->
  <span class="text-xl font-bold text-green-600">汉字抽测卡</span>

  <!-- After -->
  <span class="text-xl font-bold text-green-600">语文学习小工具</span>
  ```

- [ ] **Step 2: 更新页面默认标题**

  File: `app/templates/base.html`, Line 6

  ```html
  <!-- Before -->
  <title>{% block title %}汉字抽测卡{% endblock %}</title>

  <!-- After -->
  <title>{% block title %}语文学习小工具{% endblock %}</title>
  ```

- [ ] **Step 3: Commit**

  ```bash
  git add app/templates/base.html
  git commit -m "feat(nav): update site title to 语文学习小工具"
  ```

### Task 1.2: 重构导航菜单

- [ ] **Step 1: 替换导航项（首页 → 🎯 汉字抽测卡）**

  File: `app/templates/base.html`, Line 21

  ```html
  <!-- Before -->
  <a href="/" class="text-gray-600 hover:text-green-600 px-3 py-2 rounded-lg hover:bg-green-50 transition">首页</a>

  <!-- After -->
  <a href="/" class="text-gray-600 hover:text-green-600 px-4 py-2.5 rounded-lg hover:bg-green-50 transition">🎯 汉字抽测卡</a>
  ```

- [ ] **Step 2: 更新错字本导航项（增加 emoji）**

  File: `app/templates/base.html`, Line 22

  ```html
  <!-- Before -->
  <a href="/mistakes" class="text-gray-600 hover:text-red-600 px-3 py-2 rounded-lg hover:bg-red-50 transition">错字本</a>

  <!-- After -->
  <a href="/mistakes" class="text-gray-600 hover:text-red-600 px-4 py-2.5 rounded-lg hover:bg-red-50 transition">❌ 错字本</a>
  ```

- [ ] **Step 3: 移除打印导航项并前移字帖**

  File: `app/templates/base.html`, Lines 23-24

  ```html
  <!-- Before -->
  <a href="/print" class="text-gray-600 hover:text-blue-600 px-3 py-2 rounded-lg hover:bg-blue-50 transition">打印</a>
  <a href="/worksheet" class="text-gray-600 hover:text-purple-600 px-3 py-2 rounded-lg hover:bg-purple-50 transition">📄 字帖</a>

  <!-- After -->
  <a href="/worksheet" class="text-gray-600 hover:text-purple-600 px-4 py-2.5 rounded-lg hover:bg-purple-50 transition">📄 字帖</a>
  ```

- [ ] **Step 4: 新增教材预览导航项**

  File: `app/templates/base.html`, After line with 字帖

  ```html
  <!-- After 字帖链接，添加 -->
  <a href="/pdfs" class="text-gray-600 hover:text-orange-600 px-4 py-2.5 rounded-lg hover:bg-orange-50 transition">📚 教材预览</a>
  ```

- [ ] **Step 5: Commit**

  ```bash
  git add app/templates/base.html
  git commit -m "feat(nav): reorganize navigation menu with larger click areas"
  ```

### Task 1.3: 更新 Footer

- [ ] **Step 1: 修改 Footer 站点名称**

  File: `app/templates/base.html`, Line 37

  ```html
  <!-- Before -->
  <p>汉字抽测卡 - 每日进步一点点 🌱</p>

  <!-- After -->
  <p>语文学习小工具 - 每日进步一点点 🌱</p>
  ```

- [ ] **Step 2: Commit**

  ```bash
  git add app/templates/base.html
  git commit -m "feat(nav): update footer site name"
  ```

---

## Chunk 2: 修改 index.html 首页大标题

**Files:**
- Modify: `app/templates/index.html`

### Task 2.1: 更新首页大标题

- [ ] **Step 1: 修改首页欢迎标题**

  File: `app/templates/index.html`, Line 5

  ```html
  <!-- Before -->
  <h1 class="text-4xl font-bold text-gray-800 mb-2">欢迎来到汉字抽测卡! 🎯</h1>

  <!-- After -->
  <h1 class="text-4xl font-bold text-gray-800 mb-2">欢迎来到语文学习小工具! 🎯</h1>
  ```

- [ ] **Step 2: Commit**

  ```bash
  git add app/templates/index.html
  git commit -m "feat(home): update welcome title to match new site name"
  ```

---

## Chunk 3: 验证测试

### Task 3.1: 手动验证

- [ ] **Step 1: 启动开发服务器**

  ```bash
  uvicorn app.main:app --reload --port 8000
  ```

- [ ] **Step 2: 验证导航菜单**

  Open: http://localhost:8000

  Checklist:
  - [ ] 左上角显示 "📚 语文学习小工具"
  - [ ] 导航项顺序：🎯 汉字抽测卡、❌ 错字本、📄 字帖、📚 教材预览
  - [ ] 导航项可点击区域比之前更大
  - [ ] 点击每个导航项都能正确跳转

- [ ] **Step 3: 验证 Footer**

  Checklist:
  - [ ] 页面底部显示 "语文学习小工具 - 每日进步一点点 🌱"

- [ ] **Step 4: 验证首页大标题**

  Checklist:
  - [ ] 首页大标题显示 "欢迎来到语文学习小工具! 🎯"

- [ ] **Step 5: 验证打印功能保留**

  Open: http://localhost:8000/print

  Checklist:
  - [ ] 打印页面仍可正常访问
  - [ ] 打印功能正常工作

- [ ] **Step 6: 验证其他页面导航一致性**

  Check pages:
  - http://localhost:8000/mistakes
  - http://localhost:8000/worksheet
  - http://localhost:8000/pdfs

  Checklist:
  - [ ] 所有页面显示一致的导航菜单

- [ ] **Step 7: Commit verification results**

  ```bash
  git log --oneline -5
  ```

  Expected output should show 4 commits:
  - feat(home): update welcome title...
  - feat(nav): update footer site name
  - feat(nav): reorganize navigation menu...
  - feat(nav): update site title to 语文学习小工具

---

## Summary of Changes

| File | Changes |
|------|---------|
| `app/templates/base.html` | 站点标题、导航菜单（4项）、Footer |
| `app/templates/index.html` | 首页大标题 |

**Total modified files:** 2
**Total commits:** 4
