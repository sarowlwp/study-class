# 正确率超过 80% 才显示夸赞 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将夸赞逻辑从测试中途（逐题）移至结果页，仅在最终正确率 > 80% 时触发一次。

**Architecture:** 从 `quiz.html` 删除 praise 相关代码，迁移至 `result.html` 的 `loadResults()` 函数中，在 todayStats 存在且 accuracy > 80 时触发。无后端变更。

**Tech Stack:** Jinja2 HTML 模板、原生 JavaScript、Tailwind CSS

---

### Task 1: 删除 quiz.html 中的 praise 逻辑

**Files:**
- Modify: `app/templates/quiz.html:6-15`（删除 praise toast HTML）
- Modify: `app/templates/quiz.html:54-81`（删除 JS 变量和函数）
- Modify: `app/templates/quiz.html:158-160`（删除 submitResult 中的调用）

- [ ] **Step 1: 删除 praise toast HTML**

找到并删除 `quiz.html` 中第 6-15 行的整个 `#praise-toast` div：

```html
<!-- 删除这段 -->
<div id="praise-toast"
     class="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
            flex flex-col items-center pointer-events-none z-50"
     style="opacity: 0; transition: opacity 0.5s; margin-top: -100px;">
    <img src="{{ url_for('static', path='images/yoshi.png') }}"
         class="w-52 h-52 object-contain mb-2"
         alt="耀西"
         onerror="this.style.display='none'">
    <div id="praise-text" class="text-7xl font-bold text-green-500 drop-shadow-lg"></div>
</div>
```

- [ ] **Step 2: 删除 praise JS 代码**

找到并删除 `quiz.html` 中以下变量和函数：

```js
// 删除这些
const PRAISE_TEXTS = ['太棒了', '真不错', '很赞'];
let _praiseTimer = null;

function praise() { ... }        // 整个函数
function showPraiseToast(text) { ... }  // 整个函数
```

- [ ] **Step 3: 删除 submitResult 中的 praise 调用**

将 `submitResult` 函数中的以下代码删除：

```js
// 删除这段（约第 158-160 行）
if (result === 'mastered') {
    praise();
}
```

删除后 `submitResult` 开头应直接是 `await fetch(...)`.

- [ ] **Step 4: 验证 quiz.html 中无 praise 残留**

在文件中搜索确认以下关键词均不存在：
- `praise`
- `PRAISE_TEXTS`
- `praiseTimer`
- `praise-toast`

- [ ] **Step 5: 提交**

```bash
git add app/templates/quiz.html
git commit -m "feat(quiz): 移除测试中途的逐题夸赞逻辑"
```

---

### Task 2: 在 result.html 添加 praise 逻辑（正确率 > 80% 才触发）

**Files:**
- Modify: `app/templates/result.html`（新增 toast HTML + JS + 条件调用）

- [ ] **Step 1: 在 result.html 添加 praise toast HTML**

在 `{% block content %}` 开头（`<div class="max-w-2xl mx-auto text-center">` 之前）插入：

```html
<div id="praise-toast"
     class="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
            flex flex-col items-center pointer-events-none z-50"
     style="opacity: 0; transition: opacity 0.5s; margin-top: -100px;">
    <img src="{{ url_for('static', path='images/yoshi.png') }}"
         class="w-52 h-52 object-contain mb-2"
         alt="耀西"
         onerror="this.style.display='none'">
    <div id="praise-text" class="text-7xl font-bold text-green-500 drop-shadow-lg"></div>
</div>
```

- [ ] **Step 2: 在 result.html 的 `<script>` 顶部添加 praise JS**

在 `<script>` 标签内（`const urlParams` 之前）添加：

```js
const PRAISE_TEXTS = ['太棒了', '真不错', '很赞'];
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

- [ ] **Step 3: 在 loadResults() 中添加正确率判断**

找到 `loadResults()` 内已有的 accuracy 计算行（约第 67 行）：

```js
const accuracy = Math.round((todayStats.mastered / todayStats.total) * 100);
document.getElementById('stat-accuracy').textContent = accuracy + '%';
```

在这两行**之后**（仍在 `if (todayStats)` 块内）添加：

```js
if (accuracy > 80) {
    praise();
}
```

- [ ] **Step 4: 手动验证**

启动开发服务器：
```bash
uvicorn app.main:app --reload
```

测试场景：
1. 完成一次测验，全部答"掌握"（正确率 100%）→ 结果页应显示夸赞 toast + 语音
2. 完成一次测验，全部答"不会"（正确率 0%）→ 结果页应无夸赞
3. 测验中点"掌握"→ 测验中途不应出现 toast

- [ ] **Step 5: 提交**

```bash
git add app/templates/result.html
git commit -m "feat(result): 正确率超过 80% 时在结果页显示夸赞"
```
