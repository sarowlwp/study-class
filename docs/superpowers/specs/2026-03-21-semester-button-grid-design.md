# 学期选择 Button Grid 改造设计文档

**日期**: 2026-03-21
**范围**: `app/templates/index.html`（仅前端，无后端改动）

---

## 背景

汉字评测卡首页（`/`）的学期选择目前使用 `<select>` 下拉框，用户体验偏弱。改为平铺 button 网格，点击即选，视觉更直观。

---

## 目标

将 `<select id="semester">` 替换为 6×2 的 button 网格，保持原有的联动逻辑（选中学期后自动加载课文列表）。

---

## 设计

### 布局

```
[一上] [二上] [三上] [四上] [五上] [六上]
[一下] [二下] [三下] [四下] [五下] [六下]
```

- Tailwind 类：`grid grid-cols-6 gap-2`
- 上册（autumn）填第一行，下册（spring）填第二行
- 按钮文字用简称：将学期 name（如"一年级上册"）截取为"一上"/"一下"

### 按钮状态

| 状态 | 样式 |
|------|------|
| 默认 | 白底、灰边框（`border border-gray-300`）、灰字 |
| 选中 | 绿色背景（`bg-green-500 text-white border-green-500`） |
| hover | 浅绿背景（`hover:bg-green-50`） |

### HTML 变化

**删除**：
```html
<select id="semester" class="...">
  <option value="">请选择...</option>
</select>
```

**替换为**：
```html
<div id="semester-grid" class="grid grid-cols-6 gap-2">
  <!-- 由 JS 动态生成 -->
</div>
```

### JS 变化

**`loadSemesters()`**：

原来向 `<select>` 追加 `<option>`，改为：
1. 将 semesters 按 id 排序（autumn 在前，spring 在后）
2. 生成 12 个 `<button>`，每个带 `data-id` 属性
3. 每个按钮 click 事件：清除其他按钮选中态 → 标记自身选中 → 调用 `loadLessons(semesterId)`

**`startQuiz()`**：

原来读 `document.getElementById('semester').value`，改为读：
```js
document.querySelector('#semester-grid button.selected')?.dataset.id
```

**`updateStartButton()`**：保持不变（仍检查课文 checkbox 是否选中）。

---

## 约束

- 不改动后端 API
- 不改动其他模板或样式文件
- 保持 Tailwind CSS 风格与现有页面一致
