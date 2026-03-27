# RAZ 音频-文本同步处理器

将 RAZ 英文绘本的 PDF 和 MP3 自动对齐，生成带时间戳的配置文件和独立阅读器。

## 功能特性

- **PDF OCR**: 使用 OCRmyPDF 为扫描版 PDF 添加隐藏文字层
- **音频转录**: 使用 faster-whisper 生成词级时间戳（精度 0.01s）
- **文本对齐**: 使用 LCS 序列对齐算法自动匹配页面与时间戳
- **独立阅读器**: 生成可双击打开的 HTML 阅读器，支持翻页同步和逐词高亮

## 安装依赖

```bash
# Python 依赖
pip install ocrmypdf pymupdf faster-whisper

# Tesseract OCR (macOS)
brew install tesseract

# Tesseract OCR (Ubuntu)
sudo apt-get install tesseract-ocr
```

## 使用方法

### 处理单本书

```bash
python -m scripts.raz_sync_processor \
    --input data/raz/level-a/all-kinds-of-faces \
    --output data/raz/level-a/all-kinds-of-faces-synced \
    --model base
```

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-i, --input` | 输入目录（需含 book.pdf, book.mp3） | 必填 |
| `-o, --output` | 输出目录 | 必填 |
| `-m, --model` | Whisper 模型 (tiny/base/small/medium/large) | base |
| `-l, --lang` | 语言代码 | en |
| `-d, --device` | 计算设备 (cpu/cuda) | cpu |
| `--book-id` | 书籍 ID | 自动推断 |
| `--title` | 书名 | 自动推断 |
| `-f, --force` | 强制重新处理 | False |

### 使用示例

```bash
# 使用 tiny 模型（更快，精度稍低）
python -m scripts.raz_sync_processor -i input/ -o output/ --model tiny

# 强制重新处理
python -m scripts.raz_sync_processor -i input/ -o output/ --force

# 指定书名
python -m scripts.raz_sync_processor -i input/ -o output/ --title "My Book"
```

## 输出文件

```
output/
├── book.json          # 页面时间戳配置
├── book.pdf           # 原始 PDF（软链接）
├── book.mp3           # 原始音频（软链接）
├── word_timings.json  # 逐词时间戳
└── index.html         # 独立阅读器
```

### book.json 格式

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
    }
  ]
}
```

## 阅读器使用

双击 `index.html` 即可在浏览器中打开阅读器：

- **翻页**: 点击"上一页"/"下一页"按钮或使用方向键
- **音频同步**: 翻页时自动跳到对应时间
- **逐词高亮**: 播放时自动高亮当前朗读的单词

## 测试

```bash
# 运行所有测试
python -m pytest tests/test_raz_sync_processor/ -v

# 运行特定测试
python -m pytest tests/test_raz_sync_processor/test_text_aligner.py -v
```

## 架构说明

```
┌─────────────────────────────────────────────────────────────┐
│                    RazSyncProcessor                         │
├─────────────────────────────────────────────────────────────┤
│  PDFProcessor        │  OCR + 每页文本提取                   │
│  AudioTranscriber    │  faster-whisper → 词级时间戳          │
│  TextAligner         │  LCS 对齐 → 页面时间范围              │
│  SyncGenerator       │  JSON + HTML 生成                     │
└─────────────────────────────────────────────────────────────┘
```

## 许可证

MIT
