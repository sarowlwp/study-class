# 字帖字体大小调整与自动预览设计文档

**日期**: 2025-03-17
**功能**: 字帖支持调整字体大小 + 配置修改自动触发生成预览

---

## 1. 功能概述

### 1.1 字体大小调整
- 用户可通过滑块调整田字格内描红字的大小
- 范围：24px - 72px，步进 4px
- 默认值：48px
- 使用 CSS 变量实现，预览和打印样式同步

### 1.2 自动预览
- 所有配置项修改后自动触发生成预览
- 根据控件类型应用不同的防抖延迟
- 保留"生成预览"按钮作为手动刷新选项
- 首次进入页面自动加载默认配置生成预览

---

## 2. 技术方案

### 2.1 字体大小实现（CSS 变量方案）

**CSS 层**
```css
/* 预览样式 */
.worksheet-container {
    --char-size: 48px;  /* 默认 48px */
}

.trace-char {
    font-size: var(--char-size);
}

/* 打印样式 - 继承相同的变量 */
@media print {
    .worksheet-container {
        --char-size: 48px;
    }
    .trace-char {
        font-size: var(--char-size);
    }
}
```

**JavaScript 更新**
```javascript
function updateCharSize(size) {
    container.style.setProperty('--char-size', `${size}px`);
    localStorage.setItem('worksheetCharSize', size);
}
```

### 2.2 自动预览机制

**触发范围（全部配置项）**

| 配置区域 | 具体配置项 |
|---------|-----------|
| 数据来源 | source radio、semester select、lessons checkboxes、custom textarea |
| 网格设置 | grid-type radio、font radio、cols-input range、trace-opacity radio、char-size range |
| 字配置 | example-count range、trace-count range |
| 内容选项 | show-pinyin checkbox、layout-mode radio、print-orientation radio |

**防抖策略**

| 控件类型 | 延迟 | 说明 |
|---------|------|------|
| Range 滑块 | 200ms | 拖动过程中延迟，停止后触发 |
| Textarea 输入 | 500ms | 等用户输入完成 |
| Radio/Checkbox/Select | 0ms | 立即触发 |

**首次加载**
- 页面加载后自动使用默认配置生成预览
- 默认配置：错字本数据、田字格、楷体、5格/行、48px字体

---

## 3. UI 设计

### 3.1 字体大小控件
- 位置：网格设置区域（"描红深浅"下方）
- 控件类型：range 滑块
- 范围：24 - 72
- 步进：4
- 显示格式："48px"

### 3.2 "生成预览"按钮
- 保留按钮，作为手动刷新选项
- 点击时立即触发预览生成（无视防抖）

---

## 4. 持久化

### 4.1 LocalStorage Keys
- `worksheetCharSize`: 字体大小（默认 48）
- 复用现有配置保存机制（如已存在）

### 4.2 配置恢复
- 页面加载时从 localStorage 读取所有配置
- 应用到 UI 控件
- 设置 CSS 变量
- 自动生成预览

---

## 5. 文件变更

### 5.1 修改文件
- `app/templates/worksheet.html`: 添加字体大小控件、CSS 变量支持
- `app/static/js/worksheet.js`: 实现自动触发逻辑、防抖、事件绑定

---

## 6. 验收标准

- [ ] 字体大小滑块显示在网格设置区域
- [ ] 拖动滑块时描红字大小实时变化
- [ ] 字体大小值持久化到 localStorage
- [ ] 刷新页面后恢复上次设置的字体大小
- [ ] 打印时字体大小与预览一致
- [ ] 修改任意配置项后自动触发生成预览
- [ ] Range 滑块有 200ms 防抖，Textarea 有 500ms 防抖
- [ ] Radio/Checkbox/Select 立即触发
- [ ] "生成预览"按钮点击立即刷新
- [ ] 首次进入页面自动生成默认预览
