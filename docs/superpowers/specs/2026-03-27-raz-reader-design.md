# RAZ Reader 阅读器设计文档

**日期**: 2026-03-27
**状态**: 待实现

---

## 1. 功能概述

为 RAZ 英语学习系统新增基于 pdf.js 的阅读器模块，提供流畅的 PDF 阅读体验，支持整书音频同步和单句发音评测。

**核心功能**:
- pdf.js 渲染 PDF 页面（单页显示，无缩放/搜索）
- 整书音频播放，按页自动分段
- 单句语音评测，实时打分反馈
- iPad 优化的大按钮交互
- 翻页时音频自动暂停

---

## 2. 数据结构

### 2.1 书库目录结构

```
data/raz/
  level-c/
    birthday-party/
      book.json       # 书籍元数据
      book.pdf        # 整本书 PDF
      audio.mp3       # 整本书音频
      video.mp4       # 整本书视频（可选）
      cover.jpg       # 封面图
```

### 2.2 book.json 格式

```json
{
  "id": "level-c/birthday-party",
  "title": "Birthday Party",
  "level": "c",
  "pdf": "book.pdf",
  "audio": "audio.mp3",
  "video": "video.mp4",
  "cover": "cover.jpg",
  "sentences": [
    {
      "start": 7.04,
      "end": 7.9,
      "text": "We go shopping.",
      "page": 1,
      "confidence": 0.968
    },
    {
      "start": 8.66,
      "end": 10.6,
      "text": "It is birthday party time.",
      "page": 1,
      "confidence": 0.985
    }
  ]
}
```

**字段说明**:
- `id`: 全局唯一标识，格式 `level-{x}/{dir_name}`
- `sentences`: 句子数组，每个句子包含时间戳、文本、页码
- `start`, `end`: 音频时间戳（秒）
- `page`: 句子所属页码（从1开始）
- `confidence`: ASR 置信度（可选）

---

## 3. 页面架构

### 3.1 路由设计

| 路由 | 说明 |
|------|------|
| `GET /raz` | 书库首页（现有） |
| `GET /raz/reader/{level}/{book_dir}` | **新增**: 阅读器页面 |
| `GET /api/raz/book/{level}/{book_dir}` | 书籍数据 API（扩展） |
| `POST /api/raz/assess` | 录音评测（现有） |

### 3.2 阅读器界面布局

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   [← 返回书库]         Birthday Party                   │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│              ┌─────────────────────┐                   │
│              │                     │                   │
│              │   PDF 页面显示       │                   │
│              │   (pdf.js canvas)   │                   │
│              │                     │                   │
│              └─────────────────────┘                   │
│                                                         │
│        [◀ 上一页]      3 / 10      [下一页 ▶]           │
│                                                         │
├─────────────────────────────────────────────────────────┤
│   🔊  [▶ 播放整页]  ━━━━━━━●━━━━━━━  [⏸ 暂停]           │
├─────────────────────────────────────────────────────────┤
│  📖 当前页面句子：                                       │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  "We go shopping."                      [🎤]    │   │
│  │                                    85分 ⭐      │   │
│  ├─────────────────────────────────────────────────┤   │
│  │  "It is birthday party time."           [🎤]    │   │
│  │                                  点击录音        │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 3.3 录音中状态

```
┌─────────────────────────────────────────────────────────┐
│  "We go shopping."                                      │
│                                                         │
│        [ 🔴 录音中... 点击结束 ]                          │
│                                                         │
│           ⏱ 00:03                                       │
└─────────────────────────────────────────────────────────┘
```

---

## 4. 交互逻辑

### 4.1 页面加载流程

1. 服务端渲染 `reader.html`，注入书籍元数据
2. pdf.js 加载 `book.pdf`，渲染第1页到 canvas
3. 初始化音频对象，加载 `audio.mp3`
4. 根据当前页码过滤显示句子列表

### 4.2 音频播放逻辑

```javascript
// 播放当前页音频
function playCurrentPage() {
  const currentPage = 3; // 当前页码

  // 从 sentences 中提取当前页的时间范围
  const pageSentences = sentences.filter(s => s.page === currentPage);
  if (pageSentences.length === 0) return;

  const startTime = pageSentences[0].start;
  const endTime = pageSentences[pageSentences.length - 1].end;

  audio.currentTime = startTime;

  // 监听时间更新，到页尾自动暂停
  audio.ontimeupdate = () => {
    if (audio.currentTime >= endTime) {
      audio.pause();
    }
  };

  audio.play();
}
```

### 4.3 翻页逻辑

```javascript
function goToPage(pageNum) {
  // 1. 停止音频
  audio.pause();
  audio.ontimeupdate = null;

  // 2. 渲染新页面
  renderPdfPage(pageNum);

  // 3. 更新句子列表
  updateSentenceList(pageNum);

  // 4. 重置评测状态
  resetAssessmentState();
}
```

### 4.4 单句评测流程

1. 点击句子右侧 🎤 按钮
2. 按钮变为 "🔴 录音中... 点击结束"
3. 使用 WebRTC `MediaRecorder` 采集音频
4. 点击结束 → POST 到 `/api/raz/assess`
5. 显示评分结果（分数 + 星级反馈）
6. 按钮恢复为 🎤，记录评测结果

---

## 5. 后端架构

### 5.1 新增/修改文件

```
app/
  routers/
    raz.py                  # 添加 GET /raz/reader/{level}/{book_dir}
  services/
    raz_service.py          # _load_book() 支持新 book.json 格式
  templates/
    raz/
      reader.html           # 阅读器页面（iPad 优化）
      index.html            # 书库页（添加阅读器入口）
  static/
    js/
      raz-reader.js         # 阅读器核心逻辑
    lib/
      pdf.min.js            # pdf.js 库
      pdf.worker.min.js     # pdf.js worker
```

### 5.2 API 响应格式

**GET /api/raz/book/{level}/{book_dir}**

```json
{
  "id": "level-c/birthday-party",
  "title": "Birthday Party",
  "level": "c",
  "pdf": "/raz/media/c/birthday-party/book.pdf",
  "audio": "/raz/media/c/birthday-party/audio.mp3",
  "video": "/raz/media/c/birthday-party/video.mp4",
  "cover": "/raz/media/c/birthday-party/cover.jpg",
  "total_pages": 10,
  "sentences": [
    {
      "start": 7.04,
      "end": 7.9,
      "text": "We go shopping.",
      "page": 1,
      "confidence": 0.968
    }
  ]
}
```

### 5.3 服务端数据转换

```python
def _load_book(self, book_dir: Path) -> Optional[RazBook]:
    json_file = book_dir / "book.json"
    if not json_file.exists():
        return None

    data = json.loads(json_file.read_text(encoding="utf-8"))

    # 计算总页数（从 sentences 中提取最大 page）
    sentences = data.get("sentences", [])
    total_pages = max((s["page"] for s in sentences), default=1)

    return RazBook(
        id=data["id"],
        title=data["title"],
        level=data["level"],
        pdf=data.get("pdf"),
        audio=data.get("audio"),
        video=data.get("video"),
        cover=data.get("cover"),
        total_pages=total_pages,
        sentences=sentences,
    )
```

---

## 6. 前端实现

### 6.1 pdf.js 渲染

```javascript
async function renderPage(pageNum) {
  const pdf = await pdfjsLib.getDocument(pdfUrl).promise;
  const page = await pdf.getPage(pageNum);

  // 固定缩放，适配容器宽度
  const containerWidth = document.getElementById('pdf-container').clientWidth;
  const viewport = page.getViewport({ scale: 1 });
  const scale = containerWidth / viewport.width;
  const scaledViewport = page.getViewport({ scale });

  const canvas = document.getElementById('pdf-canvas');
  const context = canvas.getContext('2d');
  canvas.height = scaledViewport.height;
  canvas.width = scaledViewport.width;

  await page.render({
    canvasContext: context,
    viewport: scaledViewport
  }).promise;
}
```

### 6.2 句子列表渲染

```javascript
function renderSentences(pageNum) {
  const pageSentences = bookData.sentences.filter(s => s.page === pageNum);
  const container = document.getElementById('sentence-list');

  container.innerHTML = pageSentences.map((s, idx) => `
    <div class="sentence-item" data-idx="${idx}">
      <span class="text">"${s.text}"</span>
      <button class="record-btn" data-idx="${idx}">🎤</button>
      <div class="score hidden"></div>
    </div>
  `).join('');
}
```

### 6.3 录音与评测

```javascript
async function toggleRecord(sentenceIdx) {
  if (isRecording) {
    stopRecordAndSubmit(sentenceIdx);
  } else {
    await startRecord(sentenceIdx);
  }
}

async function startRecord(sentenceIdx) {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  audioChunks = [];

  mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
  mediaRecorder.start();
  isRecording = true;

  updateRecordButton(sentenceIdx, 'recording');
}

async function stopRecordAndSubmit(sentenceIdx) {
  mediaRecorder.stop();
  mediaRecorder.stream.getTracks().forEach(t => t.stop());
  isRecording = false;

  const blob = new Blob(audioChunks, { type: 'audio/webm' });
  const sentence = getSentenceByIdx(sentenceIdx);

  const formData = new FormData();
  formData.append('audio', blob);
  formData.append('text', sentence.text);
  // ... 其他字段

  const res = await fetch('/api/raz/assess', { method: 'POST', body: formData });
  const result = await res.json();

  showScore(sentenceIdx, result.score, result.feedback);
}
```

---

## 7. iPad 优化设计

### 7.1 尺寸规范

| 元素 | 尺寸 |
|------|------|
| 按钮最小尺寸 | 60 x 60 px |
| 按钮字体 | 18 px |
| 句子文本 | 22 px |
| 页码显示 | 20 px |
| 元素间距 | 20 px |
| 触摸目标间隙 | 10 px |

### 7.2 交互优化

- **点击式录音**：点击开始 → 点击结束（避免长按误触）
- **视觉反馈**：按钮点击有颜色变化（active 状态）
- **大翻页按钮**：左右箭头按钮尺寸加大，方便儿童操作
- **禁止双击缩放**：`touch-action: manipulation`

### 7.3 CSS 示例

```css
/* iPad 优化样式 */
.reader-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.nav-btn {
  min-width: 80px;
  min-height: 60px;
  font-size: 18px;
  padding: 15px 25px;
  border-radius: 12px;
  touch-action: manipulation;
}

.record-btn {
  width: 60px;
  height: 60px;
  font-size: 24px;
  border-radius: 50%;
  background: #f0f0f0;
  border: 2px solid #ddd;
}

.record-btn.recording {
  background: #ff4444;
  color: white;
  animation: pulse 1s infinite;
}

.sentence-text {
  font-size: 22px;
  line-height: 1.6;
}
```

---

## 8. 错误处理

| 场景 | 处理方式 |
|------|----------|
| PDF 加载失败 | 显示 "无法加载书籍，请刷新重试" |
| 音频文件不存在 | 隐藏音频控制条，仅显示 PDF |
| 无 sentences 数据 | 隐藏句子评测区域 |
| 麦克风权限被拒 | 提示"请在设置中开启麦克风权限" |
| 录音过短 | 提示"录音太短，请重新录制" |
| 评测 API 失败 | 提示"评分失败，可重试或跳过" |
| 翻页到边界 | 禁用对应方向翻页按钮 |

---

## 9. 兼容性考虑

### 9.1 向后兼容

新旧 `book.json` 格式并存：
- 新格式（有 `sentences` 数组）→ 使用阅读器
- 旧格式（有 `pages` 数组）→ 跳转到现有 `practice.html`

### 9.2 降级策略

```python
@router.get("/raz/book/{level}/{book_dir}")
async def raz_book(request: Request, level: str, book_dir: str):
    book = raz_service.get_book(f"level-{level}/{book_dir}")

    # 判断是否支持阅读器
    if book.sentences and book.pdf:
        # 新格式，使用阅读器
        return templates.TemplateResponse("raz/reader.html", {...})
    elif book.pages:
        # 旧格式，使用现有练习页
        return RedirectResponse(url=f"/raz/practice/{level}/{book_dir}")
```

---

## 10. 实现优先级

1. **P0**: pdf.js 渲染 + 翻页控制
2. **P0**: 整书音频播放 + 页级暂停
3. **P1**: 单句评测集成
4. **P1**: iPad 优化样式
5. **P2**: 返回书库入口改造
6. **P2**: 降级兼容处理

---

## 附录: 数据模型更新

```python
# app/models/raz.py

@dataclass
class RazSentence:
    start: float      # 秒
    end: float        # 秒
    text: str
    page: int
    confidence: Optional[float] = None


@dataclass
class RazBook:
    id: str
    title: str
    level: str
    pdf: Optional[str] = None
    audio: Optional[str] = None
    video: Optional[str] = None
    cover: Optional[str] = None
    total_pages: int = 0
    sentences: List[RazSentence] = field(default_factory=list)
    # 旧格式兼容
    pages: List[RazPage] = field(default_factory=list)
```
