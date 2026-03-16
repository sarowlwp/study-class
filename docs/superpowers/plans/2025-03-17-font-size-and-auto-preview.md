# 字帖字体大小调整与自动预览实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现字帖字体大小调整功能（24px-72px滑块）和所有配置项修改后自动触发生成预览。

**Architecture:** 使用 CSS 变量 `--char-size` 实现字体大小的动态调整，通过 JavaScript 在配置变更时更新 CSS 变量并触发预览渲染。使用防抖函数控制触发频率。

**Tech Stack:** Vanilla JavaScript, CSS Custom Properties, LocalStorage

---

## 文件结构

| 文件 | 用途 |
|------|------|
| `app/templates/worksheet.html` | HTML 模板，添加字体大小控件和 CSS 变量支持 |
| `app/static/js/worksheet.js` | JavaScript，实现自动触发逻辑和事件绑定 |

---

## Task 1: 添加 CSS 变量支持

**Files:**
- Modify: `app/templates/worksheet.html:253-258` (worksheet-container 样式)
- Modify: `app/templates/worksheet.html:370-380` (trace-char 样式)
- Modify: `app/templates/worksheet.html:542-580` (打印样式)

- [ ] **Step 1: 修改预览样式中的 worksheet-container 添加 CSS 变量**

```css
.worksheet-container {
    display: grid;
    grid-template-columns: repeat(var(--cols, 5), 1fr);
    gap: 10px;
    max-width: 100%;
    --char-size: 48px;  /* 添加字体大小 CSS 变量，默认 48px */
}
```

- [ ] **Step 2: 修改 trace-char 使用 CSS 变量**

```css
.trace-char {
    font-family: "KaiTi", "STKaiti", "BiauKai", "楷体", serif;
    color: #ccc;
    opacity: 0.4;
    font-size: var(--char-size);  /* 使用 CSS 变量代替固定 48px */
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    pointer-events: none;
}
```

- [ ] **Step 3: 修改打印样式支持 CSS 变量**

在 `@media print` 区块中找到 `.worksheet-container` 和 `.trace-char`，更新为：

```css
/* Worksheet container */
.worksheet-container {
    display: grid;
    grid-template-columns: repeat(var(--cols, 5), 1fr);
    gap: 10px;
    width: 100%;
    max-width: 100%;
    --char-size: 48px;  /* 打印时也使用 CSS 变量 */
}

/* Trace character */
.trace-char {
    font-family: "KaiTi", "STKaiti", "BiauKai", "楷体", serif;
    color: #ccc;
    opacity: 0.4;
    font-size: var(--char-size);  /* 使用 CSS 变量 */
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    pointer-events: none;
}
```

- [ ] **Step 4: 提交**

```bash
git add app/templates/worksheet.html
git commit -m "feat(worksheet): add CSS variable support for char-size"
```

---

## Task 2: 添加字体大小 UI 控件

**Files:**
- Modify: `app/templates/worksheet.html:1057-1059`（描红深浅后添加字体大小控件）

- [ ] **Step 1: 在网格设置区域添加字体大小滑块**

在"描红深浅"配置后添加：

```html
<div class="form-group">
    <label for="char-size-input">字体大小 <span class="text-gray-400 text-xs">（描红字）</span></label>
    <div class="range-container">
        <input type="range" id="char-size-input" class="range-input" min="24" max="72" step="4" value="48">
        <span class="range-value" id="char-size-value">48px</span>
    </div>
</div>
```

- [ ] **Step 2: 提交**

```bash
git add app/templates/worksheet.html
git commit -m "feat(worksheet): add char-size slider UI control"
```

---

## Task 3: 在 JavaScript 中添加字体大小状态和自动触发逻辑

**Files:**
- Modify: `app/static/js/worksheet.js:75-91`（state 对象）
- Modify: `app/static/js/worksheet.js:1086-1100`（getCurrentConfig 函数）
- Modify: `app/static/js/worksheet.js:990-1050`（applySavedConfig 函数）
- Modify: `app/static/js/worksheet.js:60-70`（cacheElements 中添加 charSizeInput 和 charSizeValue）
- Modify: `app/static/js/worksheet.js:292-329`（bindGridEvents 函数）

- [ ] **Step 1: 在 state 对象中添加 charSize**

```javascript
const state = {
    source: savedConfig?.source || "mistakes",
    gridType: savedConfig?.gridType || "tian",
    font: savedConfig?.font || "kaiti",
    cols: savedConfig?.cols || 5,
    traceOpacity: savedConfig?.traceOpacity || 0.4,
    charSize: savedConfig?.charSize || 48,  // 添加字体大小状态
    showPinyin: savedConfig?.showPinyin !== undefined ? savedConfig.showPinyin : true,
    layoutMode: savedConfig?.layoutMode || "horizontal",
    printOrientation: savedConfig?.printOrientation || "landscape",
    exampleCount: savedConfig?.exampleCount || 1,
    traceCount: savedConfig?.traceCount || 5,
    selectedSemester: savedConfig?.selectedSemester || "",
    selectedLessons: savedConfig?.selectedLessons || [],
    customChars: "",
    characters: [],
    isLoading: false
};
```

- [ ] **Step 2: 在 getCurrentConfig 中添加 charSize**

```javascript
function getCurrentConfig() {
    return {
        source: state.source,
        gridType: state.gridType,
        font: state.font,
        cols: state.cols,
        traceOpacity: state.traceOpacity,
        charSize: state.charSize,  // 添加
        showPinyin: state.showPinyin,
        layoutMode: state.layoutMode,
        printOrientation: state.printOrientation,
        exampleCount: state.exampleCount,
        traceCount: state.traceCount,
        selectedSemester: state.selectedSemester,
        selectedLessons: state.selectedLessons
    };
}
```

- [ ] **Step 3: 在 cacheElements 中添加字体大小元素缓存**

在函数中添加：

```javascript
charSizeInput: document.getElementById("char-size-input"),
charSizeValue: document.getElementById("char-size-value"),
```

- [ ] **Step 4: 在 bindGridEvents 中添加字体大小事件绑定**

```javascript
// Char size
if (elements.charSizeInput) {
    elements.charSizeInput.addEventListener("input", debounce((e) => {
        state.charSize = parseInt(e.target.value, 10);
        if (elements.charSizeValue) {
            elements.charSizeValue.textContent = state.charSize + "px";
        }
        saveConfig(getCurrentConfig());
        updateCharSize();  // 更新 CSS 变量
        generatePreview(); // 自动触发预览
    }, 200));
}
```

- [ ] **Step 5: 添加 updateCharSize 函数**

在 bindGridEvents 函数后添加：

```javascript
function updateCharSize() {
    if (elements.worksheetContainer) {
        elements.worksheetContainer.style.setProperty("--char-size", state.charSize + "px");
    }
}
```

- [ ] **Step 6: 在 applySavedConfig 中添加字体大小恢复**

在 applySavedConfig 函数末尾添加：

```javascript
// Apply char size
if (elements.charSizeInput) {
    elements.charSizeInput.value = state.charSize;
    elements.charSizeValue.textContent = state.charSize + "px";
}
updateCharSize();  // 设置 CSS 变量
```

- [ ] **Step 7: 提交**

```bash
git add app/static/js/worksheet.js
git commit -m "feat(worksheet): add char-size state management and auto-trigger"
```

---

## Task 4: 为所有配置项添加自动触发预览

**Files:**
- Modify: `app/static/js/worksheet.js:221-267`（bindSourceEvents）
- Modify: `app/static/js/worksheet.js:292-329`（bindGridEvents）
- Modify: `app/static/js/worksheet.js:335-386`（bindContentEvents）

- [ ] **Step 1: 修改 bindSourceEvents 添加自动触发**

在 source 切换时添加：

```javascript
// Source radio buttons
elements.sourceInputs.forEach(input => {
    input.addEventListener("change", () => {
        state.source = input.value;
        saveConfig(getCurrentConfig());
        updateSourceOptions();

        if (state.source === "semester") {
            loadSemesters(elements.semesterSelect).then(() => {
                generatePreview();  // 数据加载后触发预览
            });
        } else if (state.source === "lessons") {
            loadSemesters(elements.lessonsSemesterSelect).then(() => {
                generatePreview();  // 数据加载后触发预览
            });
        } else {
            generatePreview();  // 其他来源立即触发
        }
    });
});
```

- [ ] **Step 2: 修改 semester select 事件添加自动触发**

```javascript
elements.semesterSelect?.addEventListener("change", (e) => {
    state.selectedSemester = e.target.value;
    saveConfig(getCurrentConfig());
    generatePreview();  // 添加自动触发
});
```

- [ ] **Step 3: 修改 lessons semester select 事件**

```javascript
elements.lessonsSemesterSelect?.addEventListener("change", (e) => {
    state.selectedSemester = e.target.value;
    saveConfig(getCurrentConfig());
    if (state.selectedSemester) {
        loadLessons(state.selectedSemester).then(() => {
            generatePreview();  // 课程加载后触发
        });
    } else {
        elements.lessonsGrid.innerHTML = '<p class="text-gray-500 text-sm col-span-full">请先选择学期</p>';
        state.selectedLessons = [];
        saveConfig(getCurrentConfig());
        generatePreview();  // 清空时触发
    }
});
```

- [ ] **Step 4: 修改 custom chars 事件添加自动触发**

```javascript
elements.customChars?.addEventListener("input", debounce((e) => {
    const chars = e.target.value;
    const validChars = chars.replace(/[^\u4e00-\u9fff]/g, "");
    state.customChars = validChars.slice(0, 100);
    elements.charCount.textContent = state.customChars.length;

    if (validChars.length > 100) {
        showWarning("最多支持100个汉字，已自动截断");
    }
    generatePreview();  // 添加自动触发
}, 500));  // 增加延迟到 500ms
```

- [ ] **Step 5: 修改 bindGridEvents 中的 grid-type 事件**

```javascript
elements.gridTypeInputs.forEach(input => {
    input.addEventListener("change", () => {
        if (input.checked) {
            state.gridType = input.value;
            saveConfig(getCurrentConfig());
            generatePreview();  // 添加自动触发
        }
    });
});
```

- [ ] **Step 6: 修改 font 事件**

```javascript
elements.fontInputs.forEach(input => {
    input.addEventListener("change", () => {
        if (input.checked) {
            state.font = input.value;
            saveConfig(getCurrentConfig());
            generatePreview();  // 添加自动触发
        }
    });
});
```

- [ ] **Step 7: 修改 cols 事件**

```javascript
elements.colsInput?.addEventListener("input", debounce((e) => {
    state.cols = parseInt(e.target.value, 10);
    elements.colsValue.textContent = state.cols;
    saveConfig(getCurrentConfig());
    generatePreview();  // 添加自动触发
}, 200));
```

- [ ] **Step 8: 修改 trace-opacity 事件**

```javascript
elements.traceOpacityInputs.forEach(input => {
    input.addEventListener("change", () => {
        if (input.checked) {
            state.traceOpacity = parseFloat(input.value);
            saveConfig(getCurrentConfig());
            generatePreview();  // 添加自动触发
        }
    });
});
```

- [ ] **Step 9: 修改 bindContentEvents 中的 show-pinyin 事件**

```javascript
elements.showPinyin?.addEventListener("change", (e) => {
    state.showPinyin = e.target.checked;
    saveConfig(getCurrentConfig());
    generatePreview();  // 添加自动触发
});
```

- [ ] **Step 10: 修改 layout-mode 事件**

```javascript
elements.layoutModeInputs?.forEach(input => {
    input.addEventListener("change", () => {
        if (input.checked) {
            state.layoutMode = input.value;
            if (state.layoutMode === "vertical") {
                state.cols = 1;
                if (elements.colsInput) elements.colsInput.value = 1;
                if (elements.colsValue) elements.colsValue.textContent = 1;
            }
            saveConfig(getCurrentConfig());
            generatePreview();  // 添加自动触发
        }
    });
});
```

- [ ] **Step 11: 修改 print-orientation 事件**

```javascript
elements.printOrientationInputs?.forEach(input => {
    input.addEventListener("change", () => {
        if (input.checked) {
            state.printOrientation = input.value;
            updatePrintOrientation();
            saveConfig(getCurrentConfig());
            generatePreview();  // 添加自动触发
        }
    });
});
```

- [ ] **Step 12: 修改 example-count 事件**

```javascript
elements.exampleCountInput?.addEventListener("input", debounce((e) => {
    state.exampleCount = parseInt(e.target.value, 10);
    if (elements.exampleCountValue) {
        elements.exampleCountValue.textContent = state.exampleCount;
    }
    saveConfig(getCurrentConfig());
    generatePreview();  // 添加自动触发
}, 200));
```

- [ ] **Step 13: 修改 trace-count 事件**

```javascript
elements.traceCountInput?.addEventListener("input", debounce((e) => {
    state.traceCount = parseInt(e.target.value, 10);
    if (elements.traceCountValue) {
        elements.traceCountValue.textContent = state.traceCount;
    }
    saveConfig(getCurrentConfig());
    generatePreview();  // 添加自动触发
}, 200));
```

- [ ] **Step 14: 提交**

```bash
git add app/static/js/worksheet.js
git commit -m "feat(worksheet): auto-trigger preview on all config changes"
```

---

## Task 5: 添加课程选择自动触发和首次加载自动预览

**Files:**
- Modify: `app/static/js/worksheet.js`（loadLessons 函数中的 checkbox 事件）
- Modify: `app/static/js/worksheet.js:1103-1145`（init 函数末尾）

- [ ] **Step 1: 在 loadLessons 函数中的 checkbox 事件添加自动触发**

找到 loadLessons 函数，在 checkbox change 事件中添加：

```javascript
checkbox.addEventListener("change", () => {
    if (checkbox.checked) {
        state.selectedLessons.push(lesson.id);
    } else {
        state.selectedLessons = state.selectedLessons.filter(id => id !== lesson.id);
    }
    saveConfig(getCurrentConfig());
    generatePreview();  // 添加自动触发
});
```

- [ ] **Step 2: 在 init 函数末尾添加首次加载自动预览**

在 init 函数末尾添加：

```javascript
// Auto-generate preview on first load
if (state.source === "mistakes") {
    // 错字本直接生成预览
    generatePreview();
} else if (state.source === "custom" && state.customChars) {
    // 自定义输入且有内容时生成预览
    generatePreview();
} else if (state.source === "semester" && state.selectedSemester) {
    // 学期已选择时，等待学期加载完成后生成
    // （已在 loadSemesters 的 then 中处理）
} else if (state.source === "lessons" && state.selectedSemester && state.selectedLessons.length > 0) {
    // 课程已选择时，等待课程加载完成后生成
    // （已在 loadLessons 的 then 中处理）
}
```

- [ ] **Step 3: 提交**

```bash
git add app/static/js/worksheet.js
git commit -m "feat(worksheet): auto-trigger for lesson selection and initial load"
```

---

## Task 6: 测试验证

**Files:**
- Test: `app/templates/worksheet.html`
- Test: `app/static/js/worksheet.js`

- [ ] **Step 1: 验证 CSS 变量生效**

1. 打开字帖页面
2. 检查 `.worksheet-container` 是否有 `--char-size: 48px` 样式
3. 检查 `.trace-char` 是否使用 `var(--char-size)`

- [ ] **Step 2: 验证字体大小控件**

1. 拖动字体大小滑块
2. 观察描红字大小是否实时变化
3. 观察值显示是否为 "48px" 格式
4. 刷新页面，检查是否恢复上次设置的值

- [ ] **Step 3: 验证自动触发**

1. 修改任意配置项（网格类型、字体、每行方格数等）
2. 观察是否自动更新预览
3. Range 滑块是否 200ms 后触发
4. 文本输入是否 500ms 后触发
5. Radio/Checkbox 是否立即触发

- [ ] **Step 4: 验证打印一致性**

1. 调整字体大小
2. 点击打印
3. 检查打印预览中的字体大小是否与预览一致

- [ ] **Step 5: 提交最终版本**

```bash
git add -A
git commit -m "feat(worksheet): complete font size adjustment and auto preview"
```

---

## 验收标准

- [ ] 字体大小滑块显示在网格设置区域，范围 24-72px，步进 4px
- [ ] 拖动滑块时描红字大小实时变化，值显示为 "48px" 格式
- [ ] 字体大小持久化到 localStorage，刷新后恢复
- [ ] 打印时字体大小与预览一致
- [ ] 修改任意配置项后自动触发生成预览
- [ ] Range 滑块有 200ms 防抖，Textarea 有 500ms 防抖
- [ ] Radio/Checkbox/Select 立即触发
- [ ] "生成预览"按钮点击立即刷新
- [ ] 首次进入页面自动生成默认预览
