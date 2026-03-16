# 汉字抽测「掌握」夸奖反馈功能设计

**日期**: 2026-03-20
**状态**: 已批准
**范围**: `app/templates/quiz.html` 单文件修改

---

## 功能概述

在汉字抽测卡页面，当用户点击「掌握」按钮时，同时触发：
1. **语音播放**：随机从夸奖词库中选一句，通过浏览器 Web Speech API 朗读
2. **视觉弹出**：耀西图片 + 夸奖文字居中弹出，1.5 秒后淡出

---

## 触发条件

- 仅在点击「**掌握**」时触发（`submitResult('mastered')`）
- 键盘快捷键 `1` 通过 `submitResult('mastered')` 统一入口触发，无需额外修改
  - 当前键盘事件代码：`if (e.key === '1') submitResult('mastered');` ✓
- 点击「模糊」和「不会」不触发任何夸奖反馈

---

## 页面导航行为说明

`submitResult` 有两种路径：

1. **非最后一题**：`currentIndex++` → `showCharacter()`，DOM 原地更新，toast 元素持续存在，动画可正常完成
2. **最后一题**：调用 `finishQuiz()` → `window.location.href` 跳转，页面卸载，toast 动画中断

**结论**：非最后一题时 toast 正常工作；最后一题的 toast 可能因页面跳转而中断，此为可接受行为，无需处理。

---

## 实现细节

### 变量与函数声明位置

所有新增变量（`PRAISE_TEXTS`、`_praiseTimer`）和函数（`praise()`、`showPraiseToast()`）
**必须声明在 `quiz.html` 现有的 `<script>` 块内部**，不能放到全局作用域或额外的 `<script>` 标签中。

### 夸奖词库

```js
const PRAISE_TEXTS = [
    '你太棒了', '真厉害', '太厉害了', '非常棒', '写得很好', '完全正确'
];
```

每次从数组中随机取一条，使用 `Math.random()` 选取。

### 语音合成

使用浏览器原生 `Web Speech API`，无需后端支持，无需音频文件。

**要求**：
- 调用前检测 API 可用性，不支持时静默跳过（toast 仍正常显示）
- 调用前执行 `speechSynthesis.cancel()` 防止连续触发时语音队列堆积
- 设置 `utter.onerror = () => {}` 静默处理 `language-unavailable` 等错误事件，避免控制台报错
- 若 `zh-CN` 不可用（部分 iOS、Android、Linux 无中文 TTS），不尝试回退其他语音，直接静默放弃

```js
function praise() {
    const text = PRAISE_TEXTS[Math.floor(Math.random() * PRAISE_TEXTS.length)];

    if ('speechSynthesis' in window) {
        speechSynthesis.cancel();
        const utter = new SpeechSynthesisUtterance(text);
        utter.lang = 'zh-CN';
        utter.rate = 0.9;
        utter.onerror = () => {};  // 静默处理 language-unavailable 等错误
        speechSynthesis.speak(utter);
    }

    showPraiseToast(text);
}
```

### 视觉弹出 Toast

**HTML**（插入到 `quiz.html` 的 `{% block content %}` 内顶部，主卡片 div 之前）：

```html
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
```

> **重要**：
> - 使用 Jinja2 的 `url_for('static', path='images/yoshi.png')` 而非硬编码路径，确保与 `main.py` 中 `StaticFiles` 挂载点保持一致
> - opacity 通过内联 `style` 控制，**严禁**将其改为 Tailwind 类（`opacity-0`/`opacity-100`），Tailwind JIT 模式不会生成动态添加的类名

**JS**：

```js
let _praiseTimer = null;

function showPraiseToast(text) {
    clearTimeout(_praiseTimer);
    const toast = document.getElementById('praise-toast');
    const textEl = document.getElementById('praise-text');
    textEl.textContent = text + '！';
    toast.style.opacity = '1';  // 显式重置，处理连续点击时的中途状态
    _praiseTimer = setTimeout(() => {
        toast.style.opacity = '0';
    }, 1500);
}
```

### 触发入口修改

在 `submitResult` 函数开头，当 `result === 'mastered'` 时调用 `praise()`：

```js
async function submitResult(result) {
    if (result === 'mastered') {
        praise();
    }
    // ... 原有提交逻辑不变
}
```

---

## 资源依赖

| 资源 | 路径 | 来源 | 缺失处理 |
|------|------|------|---------|
| 耀西图片 | `app/static/images/yoshi.png` | 用户提供 | `onerror` 自动隐藏，不影响文字显示 |
| Web Speech API | 浏览器内置 | 无需安装 | 不可用时静默跳过语音，toast 正常显示 |

> **注意**：需在 `app/static/images/` 目录下放置 `yoshi.png` 图片文件（由用户提供）。如未放置，toast 仍可正常显示夸奖文字。

---

## 边界情况处理

| 场景 | 处理方式 |
|------|---------|
| 连续快速点击「掌握」 | `clearTimeout` 重置定时器；`opacity` 显式置 1；`speechSynthesis.cancel()` 取消前次语音 |
| 浏览器不支持 Web Speech API | 静默跳过语音，toast 正常显示 |
| `zh-CN` 语音不可用（iOS/Android/Linux）| `utter.onerror = () => {}` 静默处理，不回退其他语音 |
| `yoshi.png` 图片缺失 | `onerror` 隐藏图片，文字正常显示 |
| 最后一题点掌握后页面跳转 | toast 动画中断，可接受行为，无需处理 |

---

## 影响范围

- 仅修改 `app/templates/quiz.html`
- 不影响后端逻辑、API、其他页面
- 键盘快捷键 `1`（对应掌握）通过统一入口 `submitResult` 触发，自动生效

---

## 不在范围内

- 英语抽测页面不包含此功能（可后续扩展）
- 不添加「模糊」或「不会」的反馈音效
- 不提供后台管理夸奖词的能力
