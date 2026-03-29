# RAZ 音频-文本同步处理器设计文档

**日期**: 2026-03-27
**作者**: Claude Code
**状态**: 待实现

---

## 1. 项目概述

### 1.1 目标

实现一个纯开源、本地运行的脚本模块，将 RAZ 英文绘本的 PDF 和 MP3 进行自动对齐，生成带时间戳的 JSON 配置，支持翻页自动播放音频和逐词高亮。

### 1.2 核心流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  RAZ PDF    │────▶│  OCRmyPDF   │────▶│  每页文本   │────▶│             │
│  (扫描版)   │     │  +文字层    │     │  提取       │     │   页面-时间  │
└─────────────┘     └─────────────┘     └─────────────┘     │   映射算法   │
                                                             │   (LCS对齐)  │
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     │              │
│  RAZ MP3    │────▶│  WhisperX   │────▶│  词级时间戳  │────▶│              │
│  (整书音频) │     │  转录       │     │  (0.01s)    │     │              │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                                                    │
                                                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          输出文件 (synced/)                              │
│  ├── book.json          # 页面级时间戳 + 文本                            │
│  ├── book.pdf           # 原始PDF (软链接)                               │
│  ├── book.mp3           # 原始音频 (软链接)                              │
│  ├── word_timings.json  # 逐词时间戳 (支持高亮)                          │
│  └── index.html         # 独立阅读器 (双击打开)                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.3 技术栈

| 组件 | 工具 | 用途 |
|------|------|------|
| PDF OCR | OCRmyPDF + Tesseract | 为扫描版PDF添加隐藏文字层 |
| PDF文本提取 | PyMuPDF (fitz) | 提取每页文本内容 |
| 音频转录 | faster-whisper | 生成词级时间戳 |
| 文本对齐 | difflib.SequenceMatcher | 页面与转录文本对齐 |
| 阅读器 | PDF.js + HTML5 Audio API | 翻页同步 + 逐词高亮 |

---

## 2. 数据格式

### 2.1 book.json

```json
{
  "id": "level-a/all-kinds-of-faces",
  "title": "All Kinds Of Faces",
  "level": "a",
  "pdf": "book.pdf",
  "audio": "book.mp3",
  "page_count": 10,
  "pages": [
    {
      "page": 1,
      "start_time": 0.0,
      "end_time": 3.74,
      "text": "All kinds of faces written by Annette Carruthers."
    },
    {
      "page": 2,
      "start_time": 4.22,
      "end_time": 5.66,
      "text": "This face is happy."
    }
  ]
}
```

### 2.2 word_timings.json

```json
{
  "version": "1.0",
  "total_words": 85,
  "timings": [
    {
      "word": "All",
      "start": 0.12,
      "end": 0.35,
      "page": 1,
      "char_start": 0,
      "char_end": 3
    },
    {
      "word": "kinds",
      "start": 0.38,
      "end": 0.62,
      "page": 1,
      "char_start": 4,
      "char_end": 9
    }
  ]
}
```

---

## 3. 模块设计

### 3.1 模块结构

```
scripts/raz_sync_processor/
├── __init__.py
├── __main__.py              # 入口脚本
├── config.py                # 配置常量
├── pdf_processor.py         # PDF OCR + 文本提取
├── audio_transcriber.py     # faster-whisper 转录
├── text_aligner.py          # 页面-时间对齐算法
├── json_generator.py        # 输出 JSON 生成
└── reader_template.py       # index.html 模板
```

### 3.2 核心类

#### PDFProcessor

```python
class PDFProcessor:
    """处理PDF文件：OCR + 文本提取"""

    def __init__(self, tesseract_cmd: str = "tesseract"):
        self.tesseract_cmd = tesseract_cmd

    def add_ocr_layer(self, input_path: Path, output_path: Path) -> bool:
        """使用OCRmyPDF为PDF添加隐藏文字层"""
        pass

    def extract_text_by_page(self, pdf_path: Path) -> List[PageText]:
        """提取每页文本，返回 [(page_num, text), ...]"""
        pass
```

#### AudioTranscriber

```python
class AudioTranscriber:
    """音频转录：使用 faster-whisper 生成词级时间戳"""

    def __init__(self, model_size: str = "base", device: str = "cpu"):
        self.model_size = model_size
        self.device = device

    def transcribe(self, audio_path: Path) -> List[WordTiming]:
        """
        转录音频，返回词级时间戳

        Returns:
            List[WordTiming]: [(word, start, end), ...]
        """
        pass
```

#### TextAligner

```python
class TextAligner:
    """文本对齐：将页面文本与转录文本对齐，计算时间映射"""

    def align(
        self,
        pages: List[PageText],
        word_timings: List[WordTiming]
    ) -> List[PageTiming]:
        """
        使用序列对齐算法计算每页的起止时间

        Algorithm:
            1. 将所有页面文本拼接成完整文本
            2. 将 word_timings 拼接成转录文本
            3. 使用 LCS/编辑距离找到最佳对齐
            4. 根据对齐结果计算每页的时间范围
        """
        pass
```

### 3.3 入口脚本

```python
# scripts/raz_sync_processor/__main__.py

def main():
    parser = argparse.ArgumentParser(description="RAZ 音频-文本同步处理器")
    parser.add_argument("--input", "-i", required=True, help="输入目录 (含 book.pdf, book.mp3)")
    parser.add_argument("--output", "-o", required=True, help="输出目录")
    parser.add_argument("--model", "-m", default="base", choices=["tiny", "base", "small"])
    parser.add_argument("--lang", "-l", default="en", help="语言代码")
    parser.add_argument("--force", "-f", action="store_true", help="强制重新处理")
    args = parser.parse_args()

    processor = RazSyncProcessor(
        model_size=args.model,
        language=args.lang
    )
    processor.process(
        input_dir=Path(args.input),
        output_dir=Path(args.output),
        force=args.force
    )

if __name__ == "__main__":
    main()
```

---

## 4. 对齐算法详解

### 4.1 问题定义

**输入**:
- `pages`: [(1, "All kinds of faces..."), (2, "This face is happy..."), ...]
- `words`: [("All", 0.12, 0.35), ("kinds", 0.38, 0.62), ...]

**输出**:
- 每页的起止时间: [(1, 0.0, 3.74), (2, 4.22, 5.66), ...]

### 4.2 算法步骤

```python
def align_pages(pages: List[PageText], words: List[WordTiming]) -> List[PageTiming]:
    # Step 1: 标准化文本（小写、去标点）
    page_texts = [normalize(p.text) for p in pages]
    full_page_text = " ".join(page_texts)

    word_texts = [normalize(w.word) for w in words]
    full_word_text = " ".join(word_texts)

    # Step 2: 序列对齐
    matcher = SequenceMatcher(None, full_page_text, full_word_text)

    # Step 3: 建立字符级映射
    char_mapping = build_char_mapping(matcher.get_matching_blocks())

    # Step 4: 计算每页时间
    page_timings = []
    char_pos = 0
    for i, (page_num, text) in enumerate(pages):
        start_char = char_pos
        end_char = char_pos + len(normalize(text))

        # 找到对应的时间戳
        start_time = words[char_to_word_index(char_mapping, start_char)].start
        end_time = words[char_to_word_index(char_mapping, end_char)].end

        page_timings.append(PageTiming(page_num, start_time, end_time))
        char_pos = end_char + 1  # +1 for space

    return page_timings
```

---

## 5. 阅读器设计

### 5.1 功能

1. **PDF 展示**: 使用 PDF.js，支持单页/双页模式
2. **音频控制**: 播放/暂停，进度条，音量控制
3. **翻页同步**: 翻页时音频自动跳到对应时间
4. **逐词高亮**: 根据播放时间高亮当前单词
5. **键盘快捷键**: 空格播放/暂停，方向键翻页

### 5.2 核心代码

```javascript
// 初始化
const pdfDoc = await pdfjsLib.getDocument('book.pdf').promise;
const audio = new Audio('book.mp3');
const bookData = await fetch('book.json').then(r => r.json());
const wordTimings = await fetch('word_timings.json').then(r => r.json());

let currentPage = 1;

// 翻页
function goToPage(pageNum) {
    currentPage = pageNum;
    renderPage(pageNum);

    // 同步音频
    const page = bookData.pages.find(p => p.page === pageNum);
    if (page) {
        audio.currentTime = page.start_time;
        audio.play();
    }
}

// 逐词高亮
audio.addEventListener('timeupdate', () => {
    const currentTime = audio.currentTime;
    const currentWord = wordTimings.timings.find(
        w => w.start <= currentTime && w.end >= currentTime
    );

    if (currentWord && currentWord.page !== currentPage) {
        goToPage(currentWord.page);
    }

    highlightWord(currentWord);
});
```

---

## 6. 使用方式

### 6.1 安装依赖

```bash
# 安装 Python 依赖
pip install ocrmypdf pymupdf faster-whisper

# 安装 Tesseract OCR (macOS)
brew install tesseract

# 安装 Tesseract OCR (Ubuntu)
sudo apt-get install tesseract-ocr
```

### 6.2 运行处理脚本

```bash
# 处理单本书
python -m scripts.raz_sync_processor \
    --input data/raz/level-a/all-kinds-of-faces \
    --output data/raz/level-a/all-kinds-of-faces-synced \
    --model base

# 输出
# ✅ 已生成: data/raz/level-a/all-kinds-of-faces-synced/index.html
# 双击打开即可阅读
```

### 6.3 输出目录结构

```
data/raz/level-a/all-kinds-of-faces-synced/
├── book.json              # 页面时间戳配置
├── book.pdf -> ../all-kinds-of-faces/book.pdf    # 软链接
├── book.mp3 -> ../all-kinds-of-faces/book.mp3    # 软链接
├── word_timings.json      # 逐词时间戳
└── index.html             # 独立阅读器
```

---

## 7. 错误处理

| 场景 | 处理策略 |
|------|----------|
| OCR 识别率低 | 输出警告，人工检查 |
| 对齐失败 | 使用启发式方法（按句子数均分） |
| 音频与文本长度不匹配 | 记录差异，标记为"需审核" |
| 依赖缺失 | 清晰的错误提示 + 安装指引 |

---

## 8. 扩展性

### 8.1 未来扩展

1. **批量处理**: 支持处理整个 level 的所有书籍
2. **Web UI**: 可视化处理进度和结果预览
3. **人工校对**: 提供对齐结果编辑界面
4. **多语言**: 支持其他语言绘本
5. **导出格式**: 支持 EPUB、有声书格式

### 8.2 兼容性

- 生成的 `index.html` 是纯静态文件，可脱离原系统运行
- `book.json` 格式版本化，便于后续升级

---

## 9. 任务清单

- [ ] 实现 PDFProcessor（OCR + 文本提取）
- [ ] 实现 AudioTranscriber（faster-whisper 封装）
- [ ] 实现 TextAligner（LCS 对齐算法）
- [ ] 实现 JSONGenerator（输出文件生成）
- [ ] 实现 index.html 阅读器模板
- [ ] 编写入口脚本和 CLI
- [ ] 添加错误处理和日志
- [ ] 编写使用文档
- [ ] 测试 all-kinds-of-faces 样本
