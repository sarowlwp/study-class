# RAZ 资源适配新格式设计文档

**日期**: 2026-03-23
**状态**: 待评审

---

## 1. 背景与目标

### 1.1 现状

现有 RAZ 系统使用按页组织的资源格式：

```
data/raz/level-w/vikings/
├── page01.pdf
├── page01.mp3
├── page02.pdf
├── page02.mp3
└── book.json  # 每页独立条目
```

**问题**：
- 每页独立的 PDF 和音频导致加载碎片化
- 没有视频支持
- 缺少句子级别的时间戳信息

### 1.2 新资源结构

新获取的资源采用整本组织方式：

```
raz-resourcer/
├── RAZ AA级-Z音频/
│   └── E级音频/
│       └── 01 arctic animals.mp3      # 整本音频
├── RAZ-pdf点读版/
│   └── E.PDF/                          # 目录，内含每本书独立PDF
│       ├── Arctic Animals.pdf
│       └── All About Orcas.pdf
└── RAZ视频/
    └── E级视频/
        └── E-01Arctic Animals.mp4      # 配套视频
```

### 1.3 目标

构建自动化工具链，将新资源转换为新的 `book.json` 格式，支持：
- 整本 PDF 而非分页
- 整本音频 + 句子级别时间戳
- 配套视频支持

---

## 2. 新 book.json 格式

### 2.1 Schema

```json
{
  "id": "level-e/arctic-animals",
  "title": "Arctic Animals",
  "level": "e",
  "pdf": "book.pdf",
  "video": "video.mp4",
  "audio": "audio.mp3",
  "sentences": [
    {
      "start": 0.5,
      "end": 3.2,
      "text": "Arctic Animals.",
      "page": 1
    }
  ]
}
```

### 2.2 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | 是 | 格式：`level-{字母}/{书名kebab-case}` |
| `title` | string | 是 | 书籍标题（首字母大写） |
| `level` | string | 是 | 阅读级别：aa, a-z, z1, z2 |
| `pdf` | string | 是 | PDF 文件名（每本书独立PDF） |
| `video` | string \| null | 是 | 视频文件名，无则为 `null`（字段必须存在） |
| `audio` | string | 是 | 整本音频文件名 |
| `sentences` | array | 是 | 句子数组，含时间戳、文本和页码 |

### 2.3 sentences 结构

| 字段 | 类型 | 说明 |
|------|------|------|
| `start` | float | 句子开始时间（秒） |
| `end` | float | 句子结束时间（秒） |
| `text` | string | 句子文本内容 |
| `page` | int | 该句子所在的 PDF 页码（相对于 pdf_start_page） |
| `confidence` | float | Whisper 置信度（0-1），用于质量评估 |

---

## 3. 系统架构

### 3.1 组件图

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAZ Resource Adapter                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Scanner    │───▶│   Matcher    │───▶│ Transcriber  │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌──────────────────────────────────────────────────────┐      │
│  │                Book Generator                         │      │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │      │
│  │  │ Name Norm  │─▶│ Whisper ASR│─▶│ JSON Writer│     │      │
│  │  └────────────┘  └────────────┘  └────────────┘     │      │
│  └──────────────────────────────────────────────────────┘      │
│                            │                                    │
│                            ▼                                    │
│  ┌──────────────────────────────────────────────────────┐      │
│  │              Output: data/raz/level-*/                │      │
│  │  ├─ book.json                                        │      │
│  │  ├─ book.pdf  (复制/重命名)                          │      │
│  │  ├─ audio.mp3 (复制/重命名)                          │      │
│  │  └─ video.mp4 (复制/重命名，如存在)                   │      │
│  └──────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 组件职责

| 组件 | 文件 | 职责 |
|------|------|------|
| Scanner | `scanner.py` | 扫描 `raz-resourcer/` 三个目录，收集资源列表 |
| Matcher | `matcher.py` | 基于标准化书名匹配音频、PDF、视频 |
| Transcriber | `transcriber.py` | 使用 faster-whisper 转录音频 |
| Book Generator | `generator.py` | 组装数据，生成 book.json 并复制资源 |
| CLI | `cli.py` | 命令行接口 |

---

## 4. 核心算法

### 4.1 书名标准化

将不同来源的文件名统一为可匹配的键：

```python
def normalize_name(name: str) -> str:
    """
    输入: "01 arctic animals.mp3"
          "E-01Arctic Animals.mp4"
          "04places plants and animals live.mp3"

    处理步骤:
    1. 移除序号前缀: "01 " → ""
    2. 移除非字母数字: "-" → ""
    3. 统一小写: "Arctic" → "arctic"
    4. 压缩空格

    输出: "arcticanimals"
          "arcticanimals"
          "placesplantsandanimalslive"
    """
```

### 4.2 资源匹配流程

```
音频文件: "01 arctic animals.mp3" ──┐
                                     ├─▶ 标准化 ──▶ "arcticanimals" ──▶ 匹配成功
视频文件: "E-01Arctic Animals.mp4" ──┤              (作为书籍 ID)
                                     │
PDF 文件: "Arctic Animals.pdf" ───────┘
```

匹配成功后，根据标准化键创建输出目录结构：
- 书名: "Arctic Animals" → ID: "arctic-animals"
- 输出目录: `data/raz/level-e/arctic-animals/`

### 4.3 转录与句子切分

使用 `faster-whisper` 的 word-level 时间戳：

```python
from faster_whisper import WhisperModel

model = WhisperModel("small", device="cpu", compute_type="int8")
segments, _ = model.transcribe(
    "audio.mp3",
    language="en",
    word_timestamps=True,
    vad_filter=True
)

# 合并 words 为 sentences
sentences = merge_words_to_sentences(segments)
```

**合并策略**：
- 以句号、问号、感叹号作为句子边界
- 累积同一句话的 words，计算 start/end 时间
- 过滤空白和过短片段（< 0.3s）

---

## 5. 目录与文件结构

### 5.1 工具目录

```
tools/
├── raz_adapter/
│   ├── __init__.py
│   ├── scanner.py       # 资源扫描
│   ├── matcher.py       # 书名匹配
│   ├── normalizer.py    # 名称标准化
│   ├── transcriber.py   # 音频转录
│   ├── generator.py     # book.json 生成
│   └── cli.py           # 命令行入口
├── requirements.txt     # faster-whisper 等依赖
└── README.md
```

### 5.2 输出目录

```
data/raz/level-e/arctic-animals/
├── book.json       # 新生成的配置文件
├── book.pdf        # 从 E.PDF/Arctic Animals.pdf 复制并重命名
├── audio.mp3       # 从 E级音频/01 arctic animals.mp3 复制并重命名
└── video.mp4       # 从 E级视频/E-01Arctic Animals.mp4 复制（如存在）
```

---

## 6. 命令行接口

### 6.1 处理单本书

```bash
python -m tools.raz_adapter \
  --audio "raz-resourcer/RAZ AA级-Z音频/E级音频/01 arctic animals.mp3" \
  --pdf "raz-resourcer/RAZ-pdf点读版/E.PDF" \
  --video "raz-resourcer/RAZ视频/E级视频/E-01Arctic Animals.mp4" \
  --output "data/raz/level-e/arctic-animals"
```

### 6.2 处理整个级别

```bash
python -m tools.raz_adapter \
  --level e \
  --resourcer-dir "raz-resourcer" \
  --output-dir "data/raz"
```

处理流程：
1. 扫描 `raz-resourcer/RAZ-pdf点读版/E.PDF/` 获取所有PDF文件
2. 扫描 `raz-resourcer/RAZ AA级-Z音频/E级音频/` 获取所有音频文件
3. 扫描 `raz-resourcer/RAZ视频/E级视频/` 获取所有视频文件
4. 根据标准化书名匹配三者
5. 为每本匹配成功的书生成输出目录和 book.json

### 6.3 常用选项

| 选项 | 说明 |
|------|------|
| `--model {tiny,base,small,medium,large}` | Whisper 模型大小 |
| `--device {cpu,cuda}` | 推理设备 |
| `--workers N` | 并行工作数（CPU 模式下多进程，GPU 建议为 1） |
| `--on-duplicate {skip,replace,newest,first}` | 遇到重复书名时的处理策略 |
| `--dry-run` | 预览处理，不实际生成文件 |
| `--force` | 覆盖已存在的 book.json |
| `--backup` | 覆盖前创建 .bak 备份文件 |
| `--confidence-threshold` | 置信度阈值，低于此值的句子标记为待审查（默认 0.8） |

---

## 7. 依赖与安装

### 7.1 Python 依赖

```txt
# requirements.txt
faster-whisper>=0.10.0
pydantic>=2.0.0
click>=8.0.0
tqdm>=4.65.0
```

### 7.2 系统依赖

- Python 3.10+
- ffmpeg（音频解码）
- 可选：CUDA（GPU 加速）

### 7.3 模型文件

首次运行自动下载到 `~/.cache/whisper/`：
- `small` 模型：约 466MB，推荐平衡
- `base` 模型：约 148MB，快速测试
- `medium` 模型：约 1.5GB，更高精度

---

## 8. 性能预估

### 8.1 转录速度

在 M1 Mac（8GB）：

| 模型 | 速度比 | 单本书（5分钟音频） |
|------|--------|---------------------|
| tiny | ~32x | ~10 秒 |
| base | ~16x | ~20 秒 |
| small | ~6x | ~50 秒 |
| medium | ~2x | ~2.5 分钟 |

### 8.2 批量处理估算

- E 级约 93 本书
- 使用 small 模型：约 1.3 小时
- 使用 base 模型：约 30 分钟

### 8.3 并发模型

**CPU 模式**:
- 使用多进程（`multiprocessing`）并行处理多本书
- 每本书顺序执行：转录 → 切分 → 生成
- 推荐 `workers = CPU 核心数`

**GPU 模式**:
- faster-whisper 支持 batch 推理，但单进程已能饱和 GPU
- 推荐 `workers = 1`，通过内部 batch 提升吞吐量
- 显存不足时自动回退到 CPU 或减小 batch size

---

## 9. 错误处理

### 9.1 可恢复错误

| 场景 | 处理方式 |
|------|----------|
| 某本书转录失败 | 记录错误，继续处理其他书 |
| 缺少视频 | 设置 `video: null`，继续处理 |
| 书名匹配失败 | 输出警告，跳过该书 |
| 缺少PDF | 报错并跳过该书 |
| 重复书名（多版本） | 根据 `--on-duplicate` 策略处理 |
| 低置信度转录 | 标记句子 `confidence`，生成警告 |

### 9.2 日志输出

```
[2026-03-23 10:30:15] INFO: 开始处理级别 E (93 本书)
[2026-03-23 10:30:16] INFO: [1/93] arctic-animals - 转录中...
[2026-03-23 10:31:05] INFO: [1/93] arctic-animals - 完成 (32 句子)
[2026-03-23 10:31:06] WARNING: [2/93] all-about-orcas - 未找到视频
[2026-03-23 10:31:06] INFO: [2/93] all-about-orcas - 完成
...
[2026-03-23 11:45:30] INFO: 完成 93/93，失败 0，警告 12
```

---

## 10. 测试策略

### 10.1 单元测试

| 测试模块 | 测试用例 |
|---------|---------|
| `test_normalizer.py` | 书名标准化：序号、空格、大小写、特殊字符 |
| `test_matcher.py` | 音频-视频匹配、重复检测、大小写不敏感 |
| `test_transcriber.py` | 句子切分边界、时间戳累积、置信度计算 |

### 10.2 集成测试

```bash
# 单本书完整流程测试
python -m tools.raz_adapter \
  --audio "test/fixtures/sample.mp3" \
  --pdf "test/fixtures/sample.pdf" \
  --output "test/output/single" \
  --model tiny

# 验证输出
pytest tests/integration/test_generator.py
```

### 10.3 测试数据

`tests/fixtures/` 包含：
- `sample.mp3`: 30 秒测试音频（公开领域）
- `sample.pdf`: 3 页测试 PDF
- `expected.json`: 预期输出

---

## 11. 后续工作

### 11.1 前端适配

新格式需要前端支持：
1. 整本 PDF 渲染（而非单页）
2. 音频播放进度与句子高亮同步
3. 视频播放器集成

### 11.2 迁移策略

1. **格式检测**: 前端通过检查 `book.json` 中的字段判断格式：
   - 旧格式：包含 `pages` 数组
   - 新格式：包含 `sentences` 数组

2. **兼容性处理**: 前端同时支持两种格式：
   ```typescript
   function isNewFormat(book: Book): book is NewBook {
     return 'sentences' in book && Array.isArray(book.sentences);
   }
   ```

3. **PDF 处理差异**:
   - 旧格式：按页加载 `page{N}.pdf`
   - 新格式：加载整本 `book.pdf`

4. **存量数据**: 旧书保持现有格式，新处理的书使用新格式

5. **风险评估**: 现有硬编码路径检查：
   - `data/raz/{level}/{book}/page*.pdf` → 需适配
   - `data/raz/{level}/{book}/page*.mp3` → 需适配
   - `book.json` 解析 → 通过格式检测兼容

---

## 12. 附录

### 12.1 书名匹配示例

| 音频文件名 | 视频文件名 | 标准化键 |
|-----------|-----------|---------|
| `01 arctic animals.mp3` | `E-01Arctic Animals.mp4` | `arcticanimals` |
| `02 all about orcas.mp3` | `E-02All About Orcas.mp4` | `allaboutorcas` |
| `04places plants and animals live.mp3` | - | `placesplantsandanimalslive` |

### 12.2 级别映射

| 资源目录名 | 级别代码 |
|-----------|---------|
| `AA级音频` | `aa` |
| `A级音频` | `a` |
| `E级音频` | `e` |
| `Z级` | `z` |
| `Z①级` | `z1` |
| `Z②级` | `z2` |

**注意**: 级别代码 `z1`, `z2` 用于区分 Z 级的两个细分级别。

---

## 13. 审批记录

| 版本 | 日期 | 审批人 | 状态 |
|------|------|--------|------|
| 1.0 | 2026-03-23 | - | 待评审 |
