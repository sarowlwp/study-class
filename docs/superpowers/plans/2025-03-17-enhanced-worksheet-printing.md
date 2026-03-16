# 增强错字打印功能实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建字帖打印页面，支持描红、笔顺、田字格/米字格，可自定义配置数据来源和显示选项

**Architecture:** 纯前端实现，使用 Hanzi Writer 库渲染笔顺动画，CSS Grid 布局网格，后端仅提供拼音 API

**Tech Stack:** FastAPI + Jinja2 + Vanilla JS + Hanzi Writer CDN + Tailwind CSS

---

## Chunk 1: 后端 API - 拼音获取端点

### Task 1: 添加 pypinyin 依赖

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: 添加依赖**

```
pypinyin==0.53.0
```

- [ ] **Step 2: 提交**

```bash
git add requirements.txt
git commit -m "chore: add pypinyin dependency"
```

### Task 2: 实现 /api/pinyin 端点

**Files:**
- Modify: `app/routers/api.py`

- [ ] **Step 1: 导入 pypinyin**

在文件顶部添加导入：

```python
from pypinyin import pinyin, Style
```

- [ ] **Step 2: 添加拼音 API 端点**

在 api.py 末尾添加：

```python
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

- [ ] **Step 3: 测试 API**

运行服务器：
```bash
uvicorn app.main:app --reload
```

测试 API：
```bash
curl "http://localhost:8000/api/pinyin?chars=你好世界"
```

Expected: `{"pinyin":{"你":"nǐ","好":"hǎo","世":"shì","界":"jiè"}}`

- [ ] **Step 4: 提交**

```bash
git add app/routers/api.py
git commit -m "feat(api): add /api/pinyin endpoint for custom character pinyin"
```

---

## Chunk 2: 前端页面 - HTML 模板

### Task 3: 创建 worksheet.html 模板

**Files:**
- Create: `app/templates/worksheet.html`

- [ ] **Step 1: 创建模板文件**

```html
{% extends "base.html" %}

{% block title %}字帖打印{% endblock %}

{% block extra_css %}
<style>
/* 配置面板样式 */
.config-panel {
  background: white;
  border-radius: 1rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  margin-bottom: 1.5rem;
}

.config-tabs {
  display: flex;
  border-bottom: 1px solid #e5e7eb;
}

.tab-btn {
  flex: 1;
  padding: 1rem;
  background: none;
  border: none;
  cursor: pointer;
  font-weight: 500;
  color: #6b7280;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: #374151;
  background: #f9fafb;
}

.tab-btn.active {
  color: #059669;
  border-bottom: 2px solid #059669;
}

.tab-content {
  padding: 1.5rem;
}

.tab-content.hidden {
  display: none;
}

/* 表单样式 */
.form-group {
  margin-bottom: 1rem;
}

.form-label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #374151;
}

.form-select,
.form-input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 1rem;
}

.form-select:focus,
.form-input:focus {
  outline: none;
  border-color: #059669;
  ring: 2px solid #d1fae5;
}

.radio-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.radio-label {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.radio-label:hover {
  background: #f9fafb;
}

.radio-label input[type="radio"] {
  margin-right: 0.5rem;
}

.radio-label input[type="radio"]:checked + span {
  color: #059669;
}

/* 字帖预览区域 */
#worksheet-preview {
  background: white;
  border-radius: 1rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
  min-height: 400px;
}

.worksheet-container {
  display: grid;
  gap: 10px;
  justify-content: center;
}

/* 汉字格子 */
.char-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}

.pinyin {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 4px;
  height: 20px;
}

.grid-box {
  aspect-ratio: 1;
  min-width: 60px;
  max-width: 120px;
  border: 2px solid #333;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 田字格 */
.grid-box.tian {
  background-image:
    linear-gradient(to right, #ddd 1px, transparent 1px),
    linear-gradient(to bottom, #ddd 1px, transparent 1px),
    linear-gradient(45deg, transparent 49.5%, #eee 49.5%, #eee 50.5%, transparent 50.5%),
    linear-gradient(-45deg, transparent 49.5%, #eee 49.5%, #eee 50.5%, transparent 50.5%);
  background-size: 100% 50%, 50% 100%, 100% 100%, 100% 100%;
  background-position: 0 50%, 50% 0, 0 0, 0 0;
  background-repeat: no-repeat;
}

/* 米字格 */
.grid-box.mi {
  background-image:
    linear-gradient(to right, #ddd 1px, transparent 1px),
    linear-gradient(to bottom, #ddd 1px, transparent 1px),
    linear-gradient(45deg, transparent 49%, #ccc 49%, #ccc 51%, transparent 51%),
    linear-gradient(-45deg, transparent 49%, #ccc 49%, #ccc 51%, transparent 51%);
  background-size: 100% 50%, 50% 100%, 100% 100%, 100% 100%;
  background-position: 0 50%, 50% 0, 0 0, 0 0;
  background-repeat: no-repeat;
}

/* 方格 */
.grid-box.square {
  /* 只有边框 */
}

/* 无格 */
.grid-box.none {
  border: none;
}

/* 描红字 */
.trace-char {
  font-family: 'KaiTi', 'STKaiti', 'BiauKai', '楷体', serif;
  color: #ccc;
  font-size: 48px;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
}

/* 笔顺容器 */
.stroke-container {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

/* 笔顺序号 */
.stroke-numbers {
  display: flex;
  gap: 2px;
  margin-top: 4px;
  font-size: 12px;
  color: #9ca3af;
}

/* 按钮 */
.btn {
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-primary {
  background: #059669;
  color: white;
}

.btn-primary:hover {
  background: #047857;
}

.btn-secondary {
  background: #3b82f6;
  color: white;
}

.btn-secondary:hover {
  background: #2563eb;
}

/* 错误提示 */
.error-message {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 0.75rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
}

/* 警告提示 */
.warning-message {
  background: #fffbeb;
  border: 1px solid #fcd34d;
  color: #d97706;
  padding: 0.75rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
}

/* 打印样式 */
@media print {
  @page {
    size: A4 landscape;
    margin: 10mm;
  }

  nav, footer, .config-panel, .no-print {
    display: none !important;
  }

  #worksheet-preview {
    box-shadow: none;
    padding: 0;
  }

  .worksheet-container {
    gap: 8mm;
  }

  .grid-box {
    width: 25mm;
    height: 25mm;
    min-width: auto;
    max-width: none;
  }

  .trace-char {
    opacity: 0.5 !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }

  .grid-box {
    border-color: #000 !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
}
</style>
{% endblock %}

{% block content %}
<div class="max-w-6xl mx-auto">
  <h1 class="text-3xl font-bold text-gray-800 mb-6">📄 字帖打印</h1>

  <!-- 错误/警告信息区域 -->
  <div id="message-area" class="hidden"></div>

  <!-- 配置面板 -->
  <div class="config-panel no-print">
    <div class="config-tabs">
      <button class="tab-btn active" data-tab="source">数据来源</button>
      <button class="tab-btn" data-tab="grid">网格设置</button>
      <button class="tab-btn" data-tab="content">内容选项</button>
      <button class="tab-btn" data-tab="print">预览/打印</button>
    </div>

    <!-- 数据来源 Tab -->
    <div class="tab-content" id="source-tab">
      <div class="radio-group">
        <label class="radio-label">
          <input type="radio" name="source" value="mistakes" checked>
          <span>❌ 错字本（所有未掌握的汉字）</span>
        </label>
        <label class="radio-label">
          <input type="radio" name="source" value="semester">
          <span>📚 指定学期</span>
          <select id="semester-select" class="form-select ml-4" style="width: auto;" disabled>
            <option value="">选择学期...</option>
          </select>
        </label>
        <label class="radio-label">
          <input type="radio" name="source" value="lessons">
          <span>📖 指定课文</span>
          <select id="lesson-select" class="form-select ml-4" style="width: auto;" disabled multiple>
            <option value="">先选择学期...</option>
          </select>
        </label>
        <label class="radio-label">
          <input type="radio" name="source" value="custom">
          <span>✏️ 自定义输入</span>
        </label>
        <div id="custom-input-container" class="hidden mt-2">
          <textarea id="custom-chars" class="form-input" rows="3" placeholder="输入要打印的汉字（1-100字）..."></textarea>
          <p class="text-sm text-gray-500 mt-1">已输入 <span id="char-count">0</span>/100 字</p>
        </div>
      </div>
    </div>

    <!-- 网格设置 Tab -->
    <div class="tab-content hidden" id="grid-tab">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="form-group">
          <label class="form-label">网格类型</label>
          <select id="grid-type" class="form-select">
            <option value="tian">田字格</option>
            <option value="mi">米字格</option>
            <option value="square">方格</option>
            <option value="none">无格</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">每行字数</label>
          <select id="cols" class="form-select">
            <option value="3">3字</option>
            <option value="4">4字</option>
            <option value="5" selected>5字</option>
            <option value="6">6字</option>
            <option value="7">7字</option>
            <option value="8">8字</option>
            <option value="9">9字</option>
            <option value="10">10字</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">描红深浅</label>
          <select id="trace-opacity" class="form-select">
            <option value="0.2">浅 (20%)</option>
            <option value="0.4" selected>中 (40%)</option>
            <option value="0.6">深 (60%)</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">字体</label>
          <select id="font" class="form-select">
            <option value="kaiti">楷体</option>
            <option value="songti">宋体</option>
            <option value="heiti">黑体</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 内容选项 Tab -->
    <div class="tab-content hidden" id="content-tab">
      <div class="space-y-4">
        <label class="flex items-center space-x-3">
          <input type="checkbox" id="show-pinyin" checked class="w-5 h-5 text-green-500">
          <span>显示拼音</span>
        </label>
        <label class="flex items-center space-x-3">
          <input type="checkbox" id="show-stroke" checked class="w-5 h-5 text-green-500">
          <span>显示笔顺</span>
        </label>
        <div class="form-group">
          <label class="form-label">笔顺显示方式</label>
          <select id="stroke-mode" class="form-select">
            <option value="animate">预览时动画</option>
            <option value="static">仅静态</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 预览/打印 Tab -->
    <div class="tab-content hidden" id="print-tab">
      <div class="text-center space-y-4">
        <p class="text-gray-600">点击"生成预览"查看字帖效果，确认无误后点击"打印"</p>
        <div class="flex justify-center space-x-4">
          <button id="preview-btn" class="btn btn-primary">👁️ 生成预览</button>
          <button id="print-btn" class="btn btn-secondary">🖨️ 打印</button>
        </div>
        <p class="text-sm text-gray-500">💡 建议使用 A4 纸，横向打印</p>
      </div>
    </div>
  </div>

  <!-- 预览区域 -->
  <div id="worksheet-preview" class="hidden">
    <div id="worksheet-container" class="worksheet-container"></div>
  </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/hanzi-writer@3.3/dist/hanzi-writer.min.js"></script>
<script src="/static/js/worksheet.js"></script>
{% endblock %}
```

- [ ] **Step 2: 提交**

```bash
git add app/templates/worksheet.html
git commit -m "feat(worksheet): add worksheet.html template with config panel and preview area"
```

### Task 4: 添加页面路由

**Files:**
- Modify: `app/routers/pages.py`

- [ ] **Step 1: 导入 Request（如未导入）**

检查 pages.py 是否已有 `from fastapi import Request`，如果没有则添加。

- [ ] **Step 2: 添加 worksheet 路由**

在文件末尾添加：

```python
@router.get("/worksheet")
async def worksheet_page(request: Request):
    return templates.TemplateResponse("worksheet.html", {"request": request})
```

- [ ] **Step 3: 测试路由**

运行服务器：
```bash
uvicorn app.main:app --reload
```

访问：http://localhost:8000/worksheet

Expected: 页面正常加载，显示配置面板

- [ ] **Step 4: 提交**

```bash
git add app/routers/pages.py
git commit -m "feat(pages): add /worksheet route for worksheet printing page"
```

---

## Chunk 3: 前端 JavaScript - 核心功能

### Task 5: 创建 worksheet.js

**Files:**
- Create: `app/static/js/worksheet.js`

- [ ] **Step 1: 创建基础模块结构**

```javascript
/**
 * 字帖打印功能模块
 */

// 配置状态
const WorksheetConfig = {
  source: 'mistakes',
  semester: null,
  lessons: [],
  customChars: '',
  gridType: 'tian',
  cols: 5,
  traceOpacity: 0.4,
  font: 'kaiti',
  showPinyin: true,
  showStroke: true,
  strokeMode: 'animate'
};

// Hanzi Writer 实例缓存
const writerInstances = [];

// 学期和课文数据缓存
let semestersData = [];
let lessonsData = [];

/**
 * 初始化页面
 */
function init() {
  bindTabEvents();
  bindSourceEvents();
  bindGridEvents();
  bindContentEvents();
  bindPrintEvents();
  loadSemesters();
  checkHanziWriter();
}

/**
 * 检查 Hanzi Writer 是否加载成功
 */
function checkHanziWriter() {
  if (typeof HanziWriter === 'undefined') {
    showWarning('笔顺动画库加载失败，将使用描红模式');
  }
}

/**
 * 绑定 Tab 切换事件
 */
function bindTabEvents() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tabId = btn.dataset.tab;
      switchTab(tabId);
    });
  });
}

/**
 * 切换 Tab
 */
function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabId);
  });
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.toggle('hidden', !content.id.startsWith(tabId));
  });
}

/**
 * 绑定数据来源事件
 */
function bindSourceEvents() {
  const sourceRadios = document.querySelectorAll('input[name="source"]');
  sourceRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
      WorksheetConfig.source = e.target.value;
      updateSourceUI();
    });
  });

  // 学期选择
  document.getElementById('semester-select')?.addEventListener('change', (e) => {
    WorksheetConfig.semester = e.target.value;
    if (WorksheetConfig.source === 'lessons') {
      loadLessons(WorksheetConfig.semester);
    }
  });

  // 课文选择
  document.getElementById('lesson-select')?.addEventListener('change', (e) => {
    WorksheetConfig.lessons = Array.from(e.target.selectedOptions).map(o => o.value);
  });

  // 自定义输入
  const customInput = document.getElementById('custom-chars');
  customInput?.addEventListener('input', (e) => {
    const chars = e.target.value;
    const validChars = chars.split('').filter(c => /[\u4e00-\u9fff]/.test(c));
    WorksheetConfig.customChars = validChars.join('');
    document.getElementById('char-count').textContent = validChars.length;

    if (validChars.length > 100) {
      showError('最多支持100个汉字');
    }
  });
}

/**
 * 更新数据来源 UI
 */
function updateSourceUI() {
  const semesterSelect = document.getElementById('semester-select');
  const lessonSelect = document.getElementById('lesson-select');
  const customContainer = document.getElementById('custom-input-container');

  semesterSelect.disabled = WorksheetConfig.source === 'mistakes' || WorksheetConfig.source === 'custom';
  lessonSelect.disabled = WorksheetConfig.source !== 'lessons';
  customContainer.classList.toggle('hidden', WorksheetConfig.source !== 'custom');
}

/**
 * 绑定网格设置事件
 */
function bindGridEvents() {
  document.getElementById('grid-type')?.addEventListener('change', (e) => {
    WorksheetConfig.gridType = e.target.value;
  });

  document.getElementById('cols')?.addEventListener('change', (e) => {
    WorksheetConfig.cols = parseInt(e.target.value);
  });

  document.getElementById('trace-opacity')?.addEventListener('change', (e) => {
    WorksheetConfig.traceOpacity = parseFloat(e.target.value);
  });

  document.getElementById('font')?.addEventListener('change', (e) => {
    WorksheetConfig.font = e.target.value;
  });
}

/**
 * 绑定内容选项事件
 */
function bindContentEvents() {
  document.getElementById('show-pinyin')?.addEventListener('change', (e) => {
    WorksheetConfig.showPinyin = e.target.checked;
  });

  document.getElementById('show-stroke')?.addEventListener('change', (e) => {
    WorksheetConfig.showStroke = e.target.checked;
  });

  document.getElementById('stroke-mode')?.addEventListener('change', (e) => {
    WorksheetConfig.strokeMode = e.target.value;
  });
}

/**
 * 绑定打印事件
 */
function bindPrintEvents() {
  document.getElementById('preview-btn')?.addEventListener('click', generatePreview);
  document.getElementById('print-btn')?.addEventListener('click', doPrint);
}

/**
 * 加载学期列表
 */
async function loadSemesters() {
  try {
    const response = await fetch('/api/semesters');
    if (!response.ok) throw new Error('加载学期失败');
    const data = await response.json();
    semestersData = data.semesters;

    const select = document.getElementById('semester-select');
    select.innerHTML = '<option value="">选择学期...</option>' +
      semestersData.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
  } catch (error) {
    showError('加载学期列表失败: ' + error.message);
  }
}

/**
 * 加载课文列表
 */
async function loadLessons(semester) {
  if (!semester) return;

  try {
    const response = await fetch(`/api/lessons?semester=${semester}`);
    if (!response.ok) throw new Error('加载课文失败');
    const data = await response.json();
    lessonsData = data.lessons;

    const select = document.getElementById('lesson-select');
    select.innerHTML = lessonsData.map(l =>
      `<option value="${l.id}">${l.name}</option>`
    ).join('');
  } catch (error) {
    showError('加载课文列表失败: ' + error.message);
  }
}

/**
 * 获取汉字数据
 */
async function fetchCharacters() {
  try {
    let url;
    switch(WorksheetConfig.source) {
      case 'mistakes':
        url = '/api/mistakes';
        break;
      case 'semester':
        if (!WorksheetConfig.semester) {
          throw new Error('请选择学期');
        }
        url = `/api/characters?semester=${WorksheetConfig.semester}`;
        break;
      case 'lessons':
        if (!WorksheetConfig.semester || WorksheetConfig.lessons.length === 0) {
          throw new Error('请选择学期和课文');
        }
        url = `/api/characters?semester=${WorksheetConfig.semester}&lessons=${WorksheetConfig.lessons.join(',')}`;
        break;
      case 'custom':
        return validateCustomChars(WorksheetConfig.customChars);
      default:
        throw new Error('未知的数据来源');
    }

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    const data = await response.json();

    if (!data.mistakes && !data.characters) {
      throw new Error('返回数据格式错误');
    }

    return data.mistakes || data.characters;
  } catch (error) {
    console.error('获取数据失败:', error);
    showError('获取汉字数据失败: ' + error.message);
    return [];
  }
}

/**
 * 验证自定义汉字
 */
function validateCustomChars(chars) {
  const validChars = chars.split('').filter(c => /[\u4e00-\u9fff]/.test(c));

  if (validChars.length === 0) {
    throw new Error('请输入有效的汉字');
  }
  if (validChars.length > 100) {
    throw new Error('最多支持100个汉字');
  }

  return validChars.map(char => ({ char, pinyin: '' }));
}

/**
 * 生成预览
 */
async function generatePreview() {
  try {
    hideMessage();
    const characters = await fetchCharacters();

    if (characters.length === 0) {
      showWarning('没有可打印的汉字');
      return;
    }

    renderWorksheet(characters);
    document.getElementById('worksheet-preview').classList.remove('hidden');
  } catch (error) {
    showError('生成预览失败: ' + error.message);
  }
}

/**
 * 渲染字帖
 */
function renderWorksheet(characters) {
  const container = document.getElementById('worksheet-container');
  container.innerHTML = '';

  // 清除旧的 Hanzi Writer 实例
  writerInstances.forEach(w => w.hideCharacter());
  writerInstances.length = 0;

  // 设置网格列数
  container.style.gridTemplateColumns = `repeat(${WorksheetConfig.cols}, minmax(60px, 120px))`;

  // 获取字体
  const fontFamily = getFontFamily(WorksheetConfig.font);

  characters.forEach((charData, index) => {
    const cell = createCharCell(charData, index, fontFamily);
    container.appendChild(cell);
  });
}

/**
 * 获取字体族
 */
function getFontFamily(font) {
  switch(font) {
    case 'songti': return "'SimSun', 'STSong', '宋体', serif";
    case 'heiti': return "'SimHei', 'STHeiti', '黑体', sans-serif";
    case 'kaiti':
    default: return "'KaiTi', 'STKaiti', 'BiauKai', '楷体', serif";
  }
}

/**
 * 创建单个汉字格子
 */
function createCharCell(charData, index, fontFamily) {
  const cell = document.createElement('div');
  cell.className = 'char-cell';

  // 拼音
  if (WorksheetConfig.showPinyin) {
    const pinyin = document.createElement('div');
    pinyin.className = 'pinyin';
    pinyin.textContent = charData.pinyin || '';
    cell.appendChild(pinyin);
  }

  // 网格盒子
  const gridBox = document.createElement('div');
  gridBox.className = `grid-box ${WorksheetConfig.gridType}`;
  gridBox.style.fontFamily = fontFamily;

  // 描红字（降级显示）
  const traceChar = document.createElement('span');
  traceChar.className = 'trace-char';
  traceChar.textContent = charData.char;
  traceChar.style.opacity = WorksheetConfig.traceOpacity;
  traceChar.style.fontFamily = fontFamily;
  gridBox.appendChild(traceChar);

  // Hanzi Writer 笔顺
  if (WorksheetConfig.showStroke && typeof HanziWriter !== 'undefined') {
    const strokeContainer = document.createElement('div');
    strokeContainer.className = 'stroke-container';
    gridBox.appendChild(strokeContainer);

    // 延迟初始化 Hanzi Writer
    setTimeout(() => {
      const writer = HanziWriter.create(strokeContainer, charData.char, {
        width: 60,
        height: 60,
        padding: 2,
        strokeAnimationSpeed: 1.5,
        delayBetweenStrokes: 300,
        strokeColor: '#333',
        showCharacter: false,
        showOutline: true,
        highlightOnComplete: true
      });

      writerInstances.push(writer);

      if (WorksheetConfig.strokeMode === 'animate') {
        writer.animateCharacter();
      } else {
        writer.showOutline();
      }
    }, index * 100);
  }

  cell.appendChild(gridBox);

  // 笔顺序号
  if (WorksheetConfig.showStroke) {
    const strokeNumbers = document.createElement('div');
    strokeNumbers.className = 'stroke-numbers';
    // 占位，实际笔画数需要 Hanzi Writer 加载后才能获取
    cell.appendChild(strokeNumbers);
  }

  return cell;
}

/**
 * 执行打印
 */
function doPrint() {
  // 确保预览已生成
  const container = document.getElementById('worksheet-container');
  if (container.children.length === 0) {
    showError('请先生成预览');
    return;
  }

  // 将 Hanzi Writer 切换到静态模式
  writerInstances.forEach(writer => {
    writer.showOutline();
  });

  // 延迟打印，确保渲染完成
  setTimeout(() => {
    window.print();
  }, 500);
}

/**
 * 显示错误信息
 */
function showError(message) {
  const area = document.getElementById('message-area');
  area.innerHTML = `<div class="error-message">${message}</div>`;
  area.classList.remove('hidden');
}

/**
 * 显示警告信息
 */
function showWarning(message) {
  const area = document.getElementById('message-area');
  area.innerHTML = `<div class="warning-message">${message}</div>`;
  area.classList.remove('hidden');
}

/**
 * 隐藏信息
 */
function hideMessage() {
  const area = document.getElementById('message-area');
  area.classList.add('hidden');
  area.innerHTML = '';
}

// 启动
document.addEventListener('DOMContentLoaded', init);
```

- [ ] **Step 2: 测试功能**

1. 刷新页面 http://localhost:8000/worksheet
2. 点击"数据来源" tab，选择"错字本"
3. 点击"预览/打印" tab，点击"生成预览"
4. Expected: 显示字帖预览（如果有错字数据）

- [ ] **Step 3: 提交**

```bash
git add app/static/js/worksheet.js
git commit -m "feat(worksheet): add worksheet.js with preview and print functionality"
```

---

## Chunk 4: 导航链接和测试

### Task 6: 更新导航栏

**Files:**
- Modify: `app/templates/base.html`

- [ ] **Step 1: 在导航栏添加字帖打印链接**

在 base.html 的导航栏中（nav 元素内），找到现有链接后添加：

```html
<a href="/worksheet" class="text-gray-600 hover:text-purple-600 px-3 py-2 rounded-lg hover:bg-purple-50 transition">📄 字帖</a>
```

- [ ] **Step 2: 提交**

```bash
git add app/templates/base.html
git commit -m "feat(nav): add worksheet link to navigation bar"
```

### Task 7: 修复拼音获取（自定义输入）

**Files:**
- Modify: `app/static/js/worksheet.js`

- [ ] **Step 1: 添加自定义输入拼音获取**

在 validateCustomChars 函数中，添加拼音 API 调用：

找到 `validateCustomChars` 函数，修改为：

```javascript
/**
 * 验证自定义汉字并获取拼音
 */
async function validateCustomChars(chars) {
  const validChars = chars.split('').filter(c => /[\u4e00-\u9fff]/.test(c));

  if (validChars.length === 0) {
    throw new Error('请输入有效的汉字');
  }
  if (validChars.length > 100) {
    throw new Error('最多支持100个汉字');
  }

  // 获取拼音
  try {
    const response = await fetch(`/api/pinyin?chars=${validChars.join('')}`);
    if (!response.ok) throw new Error('获取拼音失败');
    const data = await response.json();

    return validChars.map(char => ({
      char,
      pinyin: data.pinyin[char] || ''
    }));
  } catch (error) {
    // 如果拼音获取失败，返回无拼音的数据
    return validChars.map(char => ({ char, pinyin: '' }));
  }
}
```

- [ ] **Step 2: 更新 fetchCharacters 中的调用**

找到 `case 'custom':` 行，改为：

```javascript
case 'custom':
  return await validateCustomChars(WorksheetConfig.customChars);
```

- [ ] **Step 3: 提交**

```bash
git add app/static/js/worksheet.js
git commit -m "fix(worksheet): fetch pinyin for custom characters via API"
```

---

## Chunk 5: 测试验证

### Task 8: 功能测试

**Files:**
- 测试所有文件

- [ ] **Step 1: 启动服务器**

```bash
uvicorn app.main:app --reload
```

- [ ] **Step 2: 测试错字本数据**

1. 访问 http://localhost:8000/worksheet
2. 选择"错字本"
3. 点击"生成预览"
4. Expected: 显示错字本中的汉字（如果有数据）

- [ ] **Step 3: 测试自定义输入**

1. 选择"自定义输入"
2. 输入"你好世界"
3. 点击"生成预览"
4. Expected: 显示4个汉字，带有拼音

- [ ] **Step 4: 测试打印预览**

1. 点击"打印"按钮
2. 检查浏览器打印预览
3. Expected: 配置面板隐藏，只显示字帖

- [ ] **Step 5: 测试配置选项**

1. 测试不同网格类型（田字格/米字格/方格/无格）
2. 测试不同描红深浅
3. 测试显示/隐藏拼音和笔顺
4. 每步都点击"生成预览"验证效果

- [ ] **Step 6: 提交测试通过**

```bash
git log --oneline -5
```

Expected: 看到最近的 commits

---

## Chunk 6: 最终提交

### Task 9: 创建 Pull Request 或合并

- [ ] **Step 1: 最终检查**

```bash
git status
```

Expected: 干净的工作目录

- [ ] **Step 2: 推送到远程（如果需要）**

```bash
git push origin main
```

---

## 文件清单

### 新建文件
- `app/templates/worksheet.html` - 字帖打印页面模板
- `app/static/js/worksheet.js` - 字帖功能 JavaScript

### 修改文件
- `requirements.txt` - 添加 pypinyin 依赖
- `app/routers/api.py` - 添加 /api/pinyin 端点
- `app/routers/pages.py` - 添加 /worksheet 路由
- `app/templates/base.html` - 添加导航链接

---

## 注意事项

1. **Hanzi Writer CDN**: 如果 CDN 加载失败，会降级为描红字显示
2. **自定义输入拼音**: 需要后端 pypinyin 正常工作
3. **打印样式**: 使用 A4 横向布局测试
4. **兼容性**: 在 Chrome、Safari、Edge 中测试打印效果
