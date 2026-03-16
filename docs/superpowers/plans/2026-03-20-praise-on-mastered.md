# 汉字抽测「掌握」夸奖反馈 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在汉字抽测页面点击「掌握」时，播放随机中文夸奖语音，并弹出耀西图片 + 夸奖文字，1.5 秒后淡出。

**Architecture:** 纯前端修改，所有代码在 `app/templates/quiz.html` 单文件内完成。使用浏览器原生 Web Speech API 合成语音，使用内联 style 控制 toast 动画（避免 Tailwind JIT 动态类名问题）。

**Tech Stack:** Jinja2 模板、Tailwind CSS（CDN）、原生 JavaScript、Web Speech API

---

## 文件变更清单

| 操作 | 文件 |
|------|------|
| 修改 | `app/templates/quiz.html` |
| 新增目录 | `app/static/images/`（放置用户提供的 `yoshi.png`） |

---

### Task 1: 创建图片目录并放置耀西图片

**Files:**
- Create dir: `app/static/images/`

- [ ] **Step 1: 创建 images 目录**

```bash
mkdir -p app/static/images
```

- [ ] **Step 2: 放置耀西图片**

将耀西图片文件命名为 `yoshi.png` 并复制到 `app/static/images/yoshi.png`。

> 如暂时没有图片，可跳过此步骤——toast 会通过 `onerror` 自动隐藏图片，文字仍正常显示。

- [ ] **Step 3: 确认文件存在**

```bash
ls app/static/images/yoshi.png
```

Expected: 文件路径输出，无报错

- [ ] **Step 4: Commit**

```bash
git add app/static/images/yoshi.png
git commit -m "chore(assets): add yoshi image for praise feedback"
```

> 若暂时没有图片，跳过此 task，后续补充即可。

---

### Task 2: 添加 Toast HTML 结构

**Files:**
- Modify: `app/templates/quiz.html`（在 `{% block content %}` 内顶部，`<div class="max-w-2xl mx-auto">` 之前插入）

- [ ] **Step 1: 在 quiz.html 的 `{% block content %}` 开头插入 toast HTML**

在以下位置（`quiz.html` 第 5-6 行之间）：
```html
{% block content %}
<div class="max-w-2xl mx-auto">
```

插入后变为：
```html
{% block content %}
<div id="praise-toast"
     class="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
            flex flex-col items-center pointer-events-none z-50"
     style="opacity: 0; transition: opacity 0.5s;">
    <img src="{{ url_for('static', path='images/yoshi.png') }}"
         class="w-32 h-32 object-contain mb-2"
         alt="耀西"
         onerror="this.style.display='none'">
    <div id="praise-text" class="text-5xl font-bold text-green-500 drop-shadow-lg"></div>
</div>
<div class="max-w-2xl mx-auto">
```

**关键点：**
- `style="opacity: 0; transition: opacity 0.5s;"` 必须用内联 style，不能用 Tailwind 类
- `url_for('static', path='images/yoshi.png')` 使用 Jinja2 helper，不能硬编码路径
- `onerror="this.style.display='none'"` 图片缺失时自动隐藏

- [ ] **Step 2: 启动服务验证页面不报错**

```bash
# 服务已在运行，访问任意 quiz 页面确认不报 500 错误
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/
```

Expected: `200`

- [ ] **Step 3: Commit**

```bash
git add app/templates/quiz.html
git commit -m "feat(quiz): add praise toast HTML structure"
```

---

### Task 3: 添加 JS 夸奖函数

**Files:**
- Modify: `app/templates/quiz.html`（在现有 `<script>` 块内，`const sessionId` 之前插入）

- [ ] **Step 1: 在 `<script>` 块顶部，`const sessionId = '{{ session_id }}';` 这行之前插入以下代码**

```js
const PRAISE_TEXTS = [
    '你太棒了', '真厉害', '太厉害了', '非常棒', '写得很好', '完全正确'
];
let _praiseTimer = null;

function praise() {
    const text = PRAISE_TEXTS[Math.floor(Math.random() * PRAISE_TEXTS.length)];

    if ('speechSynthesis' in window) {
        speechSynthesis.cancel();
        const utter = new SpeechSynthesisUtterance(text);
        utter.lang = 'zh-CN';
        utter.rate = 0.9;
        utter.onerror = () => {};
        speechSynthesis.speak(utter);
    }

    showPraiseToast(text);
}

function showPraiseToast(text) {
    clearTimeout(_praiseTimer);
    const toast = document.getElementById('praise-toast');
    const textEl = document.getElementById('praise-text');
    textEl.textContent = text + '！';
    toast.style.opacity = '1';
    _praiseTimer = setTimeout(() => {
        toast.style.opacity = '0';
    }, 1500);
}

```

**关键点：**
- 所有代码必须在现有 `<script>` 块内部，不能新建 `<script>` 标签
- `_praiseTimer` 用 `let`，`PRAISE_TEXTS` 用 `const`
- `utter.onerror = () => {}` 静默处理语音错误，避免控制台报错

- [ ] **Step 2: Commit**

```bash
git add app/templates/quiz.html
git commit -m "feat(quiz): add praise speech and toast functions"
```

---

### Task 4: 在 submitResult 中触发夸奖

**Files:**
- Modify: `app/templates/quiz.html`（修改现有 `submitResult` 函数）

- [ ] **Step 1: 找到 submitResult 函数（约第 118 行），在函数开头添加触发逻辑**

原代码：
```js
async function submitResult(result) {
    await fetch('/api/quiz/submit', {
```

修改后：
```js
async function submitResult(result) {
    if (result === 'mastered') {
        praise();
    }
    await fetch('/api/quiz/submit', {
```

- [ ] **Step 2: Commit**

```bash
git add app/templates/quiz.html
git commit -m "feat(quiz): trigger praise on mastered result"
```

---

### Task 5: 手动验证

- [ ] **Step 1: 打开浏览器访问抽测页面**

确保服务在运行（`uvicorn app.main:app --reload`），访问首页选择一组汉字开始抽测。

- [ ] **Step 2: 验证「掌握」触发夸奖**

点击「掌握」按钮，确认：
- [ ] 屏幕居中弹出耀西图片 + 夸奖文字（如「你太棒了！」）
- [ ] 文字为绿色大字
- [ ] 1.5 秒后淡出
- [ ] 听到中文语音朗读夸奖语句

- [ ] **Step 3: 验证「模糊」和「不会」不触发**

点击「模糊」或「不会」，确认无 toast 弹出、无语音播放。

- [ ] **Step 4: 验证键盘快捷键**

现有代码（`quiz.html` 键盘事件处理器）已包含：`if (e.key === '1') submitResult('mastered');`，无需修改。

显示答案后按键盘 `1`，确认触发夸奖效果（与点击「掌握」相同）。

- [ ] **Step 5: 验证连续快速点击**

快速连续点击「掌握」多次，确认：
- [ ] Toast 不会出现多个堆叠
- [ ] 定时器正确重置，最后一次点击后 1.5 秒淡出
- [ ] 语音不会排队堆积（每次取消前一次）
