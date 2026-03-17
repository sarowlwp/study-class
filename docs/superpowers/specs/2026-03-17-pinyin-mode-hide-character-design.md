# 拼音模式隐藏目标汉字设计文档

## 问题描述

在拼音模式下（pinyin_to_char），界面会显示：
- 拼音（如：chūn）
- 释义（如：春天）
- 例句（如：春天来了，花儿开了。）

释义和例句中包含了目标汉字（"春"），这会提前暴露答案，影响测验效果。

## 解决方案

### 1. 隐藏规则

- **方式**：将目标汉字替换为双下划线 `__`
- **位置**：前端处理（quiz.html）
- **范围**：释义（meaning）和例句（example）
- **触发条件**：仅在 `pinyin_to_char` 模式下执行

### 2. 实现细节

**字符替换函数：**
```javascript
function hideTargetChar(text, targetChar) {
    if (!text || !targetChar) return text;
    const regex = new RegExp(targetChar, 'g');
    return text.replace(regex, '__');
}
```

**应用位置：**
- 文件：`app/templates/quiz.html`
- 函数：`showCharacter()` 中的 `else` 分支（pinyin_to_char 模式）
- 替换字段：`char.meaning` 和 `char.example`

### 3. 示例效果

| 字段 | 原始内容 | 处理后 |
|------|---------|--------|
| 拼音 | chūn | chūn |
| 释义 | 春天 | __天 |
| 例句 | 春天来了，花儿开了。 | __天来了，花儿开了。 |

### 4. 边界情况处理

- **多音字**：不影响，按单个字符匹配替换
- **重复出现**：全部替换（如"春春"→"____"）
- **空值处理**：函数内做空值检查，避免报错
- **标点符号**：不影响替换逻辑

## 验收标准

- [ ] 拼音模式下释义中的目标汉字被替换为 `__`
- [ ] 拼音模式下例句中的目标汉字被替换为 `__`
- [ ] 看字选拼音模式（char_to_pinyin）不受影响
- [ ] 多字重复出现时全部替换
- [ ] 显示答案后显示完整原文（无替换）

## 任务清单

- [ ] 添加 `hideTargetChar()` 函数
- [ ] 修改 `showCharacter()` 函数应用隐藏逻辑
- [ ] 本地测试验证
