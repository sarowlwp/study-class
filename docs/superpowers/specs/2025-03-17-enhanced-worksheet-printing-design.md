# 增强错字打印功能设计文档

## 概述

增强现有错字打印功能，支持生成描红字帖、笔顺分解、田字格/米字格等多种格式，可自定义配置打印选项。

## 目标

- 支持描红字帖打印（浅灰色汉字供描摹）
- 支持笔顺分解显示（使用 Hanzi Writer 库）
- 支持田字格、米字格、方格、无格四种网格类型
- 支持多种数据来源（错字本、指定课文、指定学期、自定义输入）
- 提供丰富的自定义配置选项

## 技术方案

采用**纯前端方案**：HTML + CSS + Hanzi Writer JavaScript 库

### 选型理由

1. 符合项目现有轻量级 Web 应用架构
2. 实现简单，无需后端改动
3. 实时预览效果
4. Hanzi Writer 动画效果优秀
5. 部署维护成本低

## 页面架构

```
┌─────────────────────────────────────────────────────────────┐
│                     字帖打印页面 (/worksheet)                │
│  ┌──────────────┬─────────────────────────────────────────┐ │
│  │              │                                         │ │
│  │   配置面板    │            字帖预览区域                  │ │
│  │  (左侧边栏)   │         [田字格 + 描红字 + 拼音]          │ │
│  │              │                                         │ │
│  │  📚 数据来源  │                                         │ │
│  │  ▦ 网格设置   │                                         │ │
│  │  📝 字配置   │                                         │ │
│  │  ✨ 内容选项  │                                         │ │
│  │              │                                         │ │
│  │  [生成预览]  │                                         │ │
│  │  [打印字帖]  │                                         │ │
│  │              │                                         │ │
│  └──────────────┴─────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**注**：实际实现为侧边栏布局，非 Tab 切换方式。

## 配置面板详细设计

### 1. 数据来源 Tab

| 选项 | 说明 |
|------|------|
| 错字本 | 获取所有标记为"未掌握"的汉字（调用 /api/mistakes） |
| 指定学期 | 下拉选择学期，打印该学期全部汉字 |
| 指定课文 | 选择学期后，显示课文列表，可选择多课 |
| 自定义输入 | 文本框手动输入任意汉字（支持 1-100 字）。超出限制时提示"最多支持100个汉字"，推荐单次打印 50 字以内以获得最佳效果 |

### 2. 网格设置 Tab

| 配置项 | 选项 | 默认值 |
|--------|------|--------|
| 网格类型 | 田字格 / 米字格 / 方格 / 无格 | 田字格 |
| 每行字数 | 3-10 | 5 |
| 每页行数 | 3-12 | 6 |
| 描红深浅 | 浅(20%) / 中(40%) / 深(60%) | 中 |
| 字体 | 楷体 / 宋体 / 黑体 | 楷体 |

**字体加载策略：**
- 使用系统字体栈，确保无需下载字体文件即可显示
- 字体栈配置：
  - 楷体: `'KaiTi', 'STKaiti', 'BiauKai', '楷体', serif`
  - 宋体: `'SimSun', 'STSong', '宋体', serif`
  - 黑体: `'SimHei', 'STHeiti', '黑体', sans-serif`
- 打印时使用 `!important` 确保字体嵌入：`-webkit-print-color-adjust: exact`

### 3. 内容选项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| 显示拼音 | 在每个汉字上方显示拼音 | 开启 |
| 布局模式 | 横向排列 / 每行一字 | 横向排列 |
| 打印方向 | 横版 / 竖版 | 横版 |

### 4. 操作按钮

- **生成预览** 按钮：根据配置渲染字帖
- **打印字帖** 按钮：调用 window.print()
- 打印提示：建议使用 A4 纸，横向打印

**注**：配置修改后自动触发生成预览（带防抖），无需手动点击"生成预览"。

## 字帖样式设计

### 田字格 CSS 实现（响应式）

使用 CSS Grid 和百分比实现响应式布局，根据每行字数动态计算格子大小：

```css
.worksheet-container {
  display: grid;
  grid-template-columns: repeat(var(--cols, 5), 1fr);
  gap: 10px;
  max-width: 100%;
  padding: 20px;
}

.tian-zi-ge {
  /* 响应式正方形，保持宽高比 */
  aspect-ratio: 1;
  min-width: 60px;
  max-width: 120px;
  border: 2px solid #333;
  position: relative;
  background-image:
    /* 横中线 */
    linear-gradient(to right, #ddd 1px, transparent 1px),
    /* 竖中线 */
    linear-gradient(to bottom, #ddd 1px, transparent 1px),
    /* 对角线1 */
    linear-gradient(45deg, transparent 49.5%, #eee 49.5%, #eee 50.5%, transparent 50.5%),
    /* 对角线2 */
    linear-gradient(-45deg, transparent 49.5%, #eee 49.5%, #eee 50.5%, transparent 50.5%);
  background-size: 100% 50%, 50% 100%, 100% 100%, 100% 100%;
  background-position: 0 50%, 50% 0, 0 0, 0 0;
  background-repeat: no-repeat;
}

/* 打印时固定大小 */
@media print {
  .tian-zi-ge {
    width: 25mm;
    height: 25mm;
  }
}
```

### 米字格 CSS 实现

```css
.mi-zi-ge {
  /* 与田字格类似，但对角线更明显 */
  background-image:
    linear-gradient(to right, #ddd 1px, transparent 1px),
    linear-gradient(to bottom, #ddd 1px, transparent 1px),
    linear-gradient(45deg, transparent 49%, #ccc 49%, #ccc 51%, transparent 51%),
    linear-gradient(-45deg, transparent 49%, #ccc 49%, #ccc 51%, transparent 51%);
}
```

### 描红字样式

```css
.trace-char {
  font-family: 'KaiTi', 'STKaiti', 'BiauKai', '楷体', serif;
  color: #ccc;
  opacity: 0.4; /* 根据深浅配置调整: 0.2 / 0.4 / 0.6 */
  font-size: var(--char-size, 48px); /* 使用 CSS 变量，默认 48px，范围 24-72px */
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
```

**注**：字体大小可通过滑块调整（24px - 72px，步进 4px），使用 CSS 变量 `--char-size` 实现预览和打印样式同步。

## 描红字渲染

使用纯 CSS 和字体渲染描红字，无需外部库：

```javascript
function createTraceChar(character, config) {
  const traceChar = document.createElement('span');
  traceChar.className = `trace-char ${config.opacityClass}`;
  traceChar.textContent = character;
  return traceChar;
}
```

**第一字红色示例**：每行第一个格子显示红色示例字（`.trace-char.example`），帮助学习者对照书写。
  // 降级显示灰色汉字
  renderFallbackChar(container, character, config.traceOpacity);
  showWarning('笔顺动画加载失败，已使用描红模式');
}
```

## 错误处理

### 数据获取错误

```javascript
async function fetchCharacters(source) {
  try {
    let url;
    switch(source.type) {
      case 'mistakes':
        url = '/api/mistakes';
        break;
      case 'semester':
        url = `/api/characters?semester=${source.semester}`;
        break;
      case 'lessons':
        url = `/api/characters?semester=${source.semester}&lessons=${source.lessons.join(',')}`;
        break;
      case 'custom':
        // 自定义输入不需要 API 调用
        return validateCustomChars(source.chars);
    }

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    const data = await response.json();

    // 数据校验
    if (!data.mistakes && !data.characters) {
      throw new Error('返回数据格式错误');
    }

    return data.mistakes || data.characters;
  } catch (error) {
    console.error('获取数据失败:', error);
    showError(`获取汉字数据失败: ${error.message}`);
    return [];
  }
}

function validateCustomChars(chars) {
  // 过滤非汉字字符
  const validChars = chars.split('').filter(c => /[\u4e00-\u9fff]/.test(c));
  if (validChars.length === 0) {
    throw new Error('请输入有效的汉字');
  }
  if (validChars.length > 100) {
    throw new Error('最多支持100个汉字');
  }
  return validChars.map(char => ({ char, pinyin: '' }));
}
```

### 渲染错误

```javascript
function renderWorksheet() {
  try {
    // ... 渲染逻辑
  } catch (error) {
    console.error('渲染失败:', error);
    showError('字帖生成失败，请刷新页面重试');
    // 清理部分渲染的内容
    document.getElementById('worksheet-preview').innerHTML = '';
  }
}
```

## 数据流设计

```
┌────────────────────────────────────────────────────────────┐
│ 1. 用户选择数据来源                                          │
│    - 错字本: GET /api/mistakes                              │
│    - 学期: GET /api/semesters → GET /api/characters         │
│    - 课文: GET /api/lessons → GET /api/characters           │
│    - 自定义: 直接读取输入                                    │
└────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────┐
│ 2. 用户配置选项                                             │
│    - 收集网格类型、行列数、描红深浅、内容显示等配置            │
└────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────┐
│ 3. 生成预览                                                 │
│    - 创建网格容器                                            │
│    - 为每个汉字创建格子元素                                   │
│    - 渲染拼音（可选）                                        │
│    - 初始化 Hanzi Writer（动画模式）                         │
│    - 渲染笔顺序号（可选）                                     │
└────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────┐
│ 4. 打印输出                                                 │
│    - 切换 Hanzi Writer 为静态模式                            │
│    - 调用 window.print()                                    │
│    - @media print 控制打印样式                               │
└────────────────────────────────────────────────────────────┘
```

## API 复用清单

| API 端点 | 用途 | 是否需修改 | 响应数据说明 |
|----------|------|-----------|-------------|
| GET /api/mistakes | 获取错字本数据 | 否 | 返回 `{mistakes: [{char, pinyin, lesson, mistake_count, last_tested}]}`，注意不包含 semester |
| GET /api/semesters | 获取学期列表 | 否 | 返回 `{semesters: [{id, name, file, total_chars}]}` |
| GET /api/lessons?semester=x | 获取课文列表 | 否 | 返回 `{semester, lessons: [{id, name, char_count, mastered_count}]}` |
| GET /api/characters?semester=x&lessons=y | 获取汉字详情 | 否 | 返回 `{characters: [{char, pinyin, meaning, example, lesson, semester}]}` |

### 自定义输入的拼音处理

对于"自定义输入"数据来源，使用前端缓存机制获取拼音：

```javascript
// 前端缓存已加载字符的拼音
const pinyinCache = new Map();

// 从已加载的字符数据中查找拼音
function getPinyinFromCache(char) {
    return pinyinCache.get(char) || '';
}
```

**说明**：实际实现中，自定义输入的字符会通过 `/api/characters` 接口查询拼音（利用现有字符数据），不在后端单独实现 `/api/pinyin` 端点。

## 打印样式设计

### 页面布局与分页

```css
@page {
  /* A4 横向打印 */
  size: A4 landscape;
  margin: 10mm;
}

@media print {
  /* 隐藏非打印元素 */
  nav, footer, .config-panel, .no-print {
    display: none !important;
  }

  /* 调整预览区域 */
  #worksheet-preview {
    display: block !important;
    width: 100% !important;
    padding: 5mm !important;
    margin: 0 !important;
  }

  /* 固定网格大小以适应纸张 */
  .worksheet-container {
    display: grid;
    gap: 8mm;
    max-width: 277mm; /* A4 横向宽度减去边距 */
  }

  .tian-zi-ge, .mi-zi-ge {
    width: 25mm;
    height: 25mm;
    border: 0.5mm solid #333;
  }

  /* 确保每行在一页内，不跨页断开 */
  .worksheet-row {
    page-break-inside: avoid;
    page-break-after: auto;
    display: flex;
    justify-content: flex-start;
    gap: 8mm;
    margin-bottom: 8mm;
  }

  /* 强制分页：当需要新页时 */
  .page-break {
    page-break-before: always;
  }

  /* 描红字在打印时加深 */
  .trace-char {
    opacity: 0.5 !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }

  /* 网格线 */
  .tian-zi-ge, .mi-zi-ge {
    border-color: #000 !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
}
```

## 页面结构 (HTML)

```html
{% extends "base.html" %}

{% block content %}
<div class="worksheet-page">
  <!-- 配置面板 -->
  <div class="config-panel no-print">
    <div class="tabs">
      <button class="tab-btn active" data-tab="source">数据来源</button>
      <button class="tab-btn" data-tab="grid">网格设置</button>
      <button class="tab-btn" data-tab="content">内容选项</button>
      <button class="tab-btn" data-tab="print">预览/打印</button>
    </div>

    <!-- Tab 内容 -->
    <div class="tab-content" id="source-tab">...</div>
    <div class="tab-content hidden" id="grid-tab">...</div>
    <div class="tab-content hidden" id="content-tab">...</div>
    <div class="tab-content hidden" id="print-tab">...</div>
  </div>

  <!-- 预览区域 -->
  <div id="worksheet-preview">
    <div class="worksheet-container">
      <!-- 动态生成的字帖格子 -->
    </div>
  </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/hanzi-writer@3.3/dist/hanzi-writer.min.js"></script>
<script src="/static/js/worksheet.js"></script>
{% endblock %}
```

## JavaScript 模块设计

### worksheet.js 主要函数

```javascript
// 配置管理
const WorksheetConfig = {
  source: 'mistakes', // mistakes | semester | lessons | custom
  semester: null,
  lessons: [],
  customChars: '',
  gridType: 'tian', // tian | mi | square | none
  cols: 5,
  rows: 6,
  traceOpacity: 0.4, // 0.2 | 0.4 | 0.6
  font: 'kaiti', // kaiti | songti | heiti
  showPinyin: true,
  showStroke: true,
  strokeMode: 'animate' // animate | static
};

// 数据获取
async function fetchCharacters() { ... }

// 渲染字帖
function renderWorksheet() { ... }

// 创建单个汉字格子
function createCharCell(character, index) { ... }

// 打印控制
function prepareForPrint() { ... }
function doPrint() { ... }

// 事件绑定
document.addEventListener('DOMContentLoaded', init);
```

## 路由设计

### 页面路由

在 `app/routers/pages.py` 中添加：

```python
@router.get("/worksheet")
async def worksheet_page(request: Request):
    return templates.TemplateResponse("worksheet.html", {"request": request})
```

### API 路由（拼音获取）

在 `app/routers/api.py` 中添加：

```python
from pypinyin import pinyin, Style

@router.get("/pinyin")
async def get_pinyin(chars: str):
    """获取汉字的拼音（用于自定义输入）"""
    result = {}
    for char in chars:
        if '\u4e00' <= char <= '\u9fff':
            py = pinyin(char, style=Style.TONE)
            result[char] = py[0][0] if py else ""
    return {"pinyin": result}
```

## 兼容性考虑

1. **Hanzi Writer CDN 加载失败**：显示降级方案（仅显示汉字轮廓）
2. **浏览器打印支持**：测试 Chrome、Safari、Edge 打印效果
3. **字体回退**：楷体 → STKaiti → KaiTi → serif
4. **移动端**：配置面板支持横向滚动，预览区可缩放

## 性能优化

1. **懒加载笔顺**：只渲染可视区域的 Hanzi Writer 实例
2. **防抖处理**：配置更改时延迟 300ms 再重新渲染
3. **缓存数据**：获取的汉字数据缓存，避免重复请求

## 测试要点

### 功能测试
1. **数据来源测试**
   - 错字本：验证只显示 `ResultType.NOT_MASTERED` 的汉字
   - 学期/课文：验证数据正确加载，可多选课文
   - 自定义：验证汉字过滤（只保留汉字字符），验证 100 字限制

2. **网格类型测试**
   - 田字格：横竖中线 + 对角线正确显示
   - 米字格：对角线更明显
   - 方格：只有边框，无内部线条
   - 无格：无边框，只有描红字

3. **配置测试**
   - 描红深浅：20% / 40% / 60% 三种透明度
   - 每行字数 3-10：格子大小自适应
   - 拼音显示：位置正确，多音字处理
   - 笔顺显示：序号正确，动画正常播放

4. **打印测试**
   - Chrome/Safari/Edge 打印预览正常
   - A4 横向布局正确
   - 分页合理（每行不跨页）
   - 颜色在黑白打印模式下可见

### 兼容性测试
- Windows: Chrome, Edge
- macOS: Chrome, Safari
- iOS Safari (基本浏览)
- 安卓 Chrome (基本浏览)

### 错误处理测试
- 网络断开时的 API 错误提示
- CDN 加载失败时的降级显示
- 空数据提示（错字本为空时）
- 非法输入处理（非汉字字符）

### 性能测试
- 50 个汉字渲染时间 < 3 秒
- 100 个汉字渲染时间 < 5 秒
- 内存占用稳定，无内存泄漏

## 后续扩展可能

1. 支持导出 PDF（使用 jsPDF 或 html2pdf.js）
2. 保存常用配置模板
3. 支持笔顺书写练习（在格子里手写）
4. 支持自定义格子大小

## 参考资源

- [Hanzi Writer 文档](https://hanziwriter.org/docs.html)
- [田字格/米字格绘制参考](https://miaozitie.80wdb.com/)
- [CSS @media print](https://developer.mozilla.org/en-US/docs/Web/CSS/@media)
