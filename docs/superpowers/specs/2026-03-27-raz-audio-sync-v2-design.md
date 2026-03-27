# RAZ 音频-文本同步处理器 v2 设计文档

**日期**: 2026-03-27
**作者**: Claude Code
**状态**: 已实现

---

## 1. 核心改进：stable-ts 强制对齐

v2 版本最大的改变是引入 **stable-ts** 的 **Forced Alignment（强制对齐）** 功能。

### 1.1 什么是强制对齐？

**传统转录（v1）**:
```
音频 → Whisper 自由转录 → 文字（可能有错）
```

**强制对齐（v2）**:
```
PDF 文字（参考剧本）
       ↓
音频 → [必须对齐到剧本] → 时间戳（文字100%准确）
```

强制对齐告诉模型："**音频里说的就是这段文字，请给我每个词的时间位置。**"

### 1.2 为什么更准确？

| 场景 | v1 (自由转录) | v2 (强制对齐) |
|------|--------------|--------------|
| 发音模糊 | 可能转录错误 | 按剧本强制识别 |
| 背景噪音 | 可能漏词 | 知道应该有什么词 |
| 语速变化 | 时间戳可能偏移 | 更稳定的时间估计 |
| 儿童发音 | 错误率较高 | 参考文本指导识别 |

---

## 2. 架构对比

### v1 架构
```
┌─────────┐     ┌──────────────────┐     ┌───────────┐
│ RAZ PDF │────▶│ OCR / 文本提取   │────▶│ 页面文本  │
└─────────┘     └──────────────────┘     └─────┬─────┘
                                               │
┌─────────┐     ┌──────────────────┐     ┌─────▼─────┐
│ RAZ MP3 │────▶│ faster-whisper   │────▶│ 转录文本  │
└─────────┘     │ (自由转录)        │     └─────┬─────┘
                └──────────────────┘           │
                                               ▼
                                        ┌─────────────┐
                                        │ LCS 对齐算法 │
                                        │ (文本匹配)   │
                                        └──────┬──────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │ 页面时间戳   │
                                        └─────────────┘
```

### v2 架构
```
┌─────────┐     ┌──────────────────┐
│ RAZ PDF │────▶│ OCR / 文本提取   │────┐
└─────────┘     └──────────────────┘    │
                                        │ 参考剧本
┌─────────┐     ┌──────────────────┐    │ (干净文字)
│ RAZ MP3 │────▶│ stable-ts align  │◀───┘
└─────────┘     │ (强制对齐)        │
                └────────┬─────────┘
                         │
                         ▼
                  ┌─────────────┐
                  │ 逐词时间戳   │
                  │ (100%准确)  │
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │ 页面边界检测 │
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │ 页面时间戳   │
                  └─────────────┘
```

---

## 3. 关键代码对比

### v1: 自由转录 + LCS 对齐
```python
# 1. 自由转录（可能出错）
segments, _ = whisper_model.transcribe(
    audio_path,
    word_timestamps=True
)

# 2. 提取单词时间戳
word_timings = []
for segment in segments:
    for word in segment.words:
        word_timings.append(WordTiming(
            word=word.word,
            start=word.start,
            end=word.end
        ))

# 3. LCS 对齐页面和转录
page_timings = aligner.align(pages, word_timings)
```

### v2: 强制对齐
```python
# 1. 构建参考剧本（PDF 干净文字）
script = " ".join([p.text for p in pages])

# 2. 强制对齐（核心改进）
result = model.align(
    audio_path,
    script,           # ← 告诉模型：音频说的就是这段文字
    language="en",
    combine_words=True
)

# 3. 直接获取时间戳（文字与 PDF 完全一致）
word_timings = extract_word_timings(result)
page_timings = map_words_to_pages(pages, word_timings)
```

---

## 4. stable-ts 关键参数

```python
result = model.align(
    audio_file,
    script_text,
    language="en",

    # 单词合并策略
    combine_words=True,      # 合并短词为自然片段

    # 时间约束
    max_word_dur=2.0,        # 单个单词最大持续时间（秒）
    word_dur_factor=5.0,     # 时间弹性因子

    # 对齐精度
    original_split=False,    # 是否保持原始分割
)
```

---

## 5. 页面边界检测算法

强制对齐给出的是整个音频的逐词时间戳，需要将它们映射回页面。

### 算法步骤

```python
def map_words_to_pages(pages, word_timings):
    """将单词时间戳映射回页面."""
    boundaries = []
    current_idx = 0

    for page in pages:
        # 获取页面单词列表
        page_words = page.text.split()

        # 在 word_timings 中查找匹配
        start_idx = find_word_sequence(
            page_words,
            word_timings,
            current_idx
        )

        if start_idx:
            end_idx = start_idx + len(page_words) - 1
            boundaries.append((start_idx, end_idx))
            current_idx = end_idx + 1
        else:
            # 回退：按比例估算
            boundaries.append(estimate_boundary(...))

    return boundaries
```

### 模糊匹配

处理可能的微小差异（如 "color" vs "colour"）：

```python
def is_similar(word1, word2):
    """检查两个单词是否相似."""
    if word1 == word2:
        return True

    # 编辑距离 <= 1
    if levenshtein_distance(word1, word2) <= 1:
        return True

    return False
```

---

## 6. 使用方式

### 安装依赖

```bash
# 安装 stable-ts（核心）
pip install stable-ts

# 其他依赖（同 v1）
pip install pymupdf ocrmypdf
```

### 运行处理

```bash
# 与 v1 完全相同的 CLI
python -m scripts.raz_sync_processor_v2 \
    -i data/raz/level-a/all-kinds-of-faces \
    -o output/ \
    --model base
```

---

## 7. 文件结构

```
scripts/raz_sync_processor_v2/
├── __init__.py
├── __main__.py
├── config.py              # 配置（同 v1）
├── models.py              # 数据模型（同 v1）
├── pdf_processor.py       # PDF 处理（同 v1）
├── audio_aligner.py       # ← 新：stable-ts 强制对齐
├── sync_generator.py      # 输出生成（同 v1）
├── main.py                # ← 改：适配新对齐器
├── README.md              # v2 说明文档
├── install_deps.sh        # 依赖安装脚本
└── demo_stable_ts.py      # 演示脚本
```

---

## 8. 迁移指南

### 从 v1 迁移到 v2

1. **安装依赖**
   ```bash
   pip install stable-ts
   ```

2. **代码导入**
   ```python
   # v1
   from scripts.raz_sync_processor import RazSyncProcessor

   # v2
   from scripts.raz_sync_processor_v2 import RazSyncProcessorV2
   ```

3. **重新处理数据**
   - v2 生成的时间戳格式与 v1 兼容
   - 建议重新处理以获得更准确的结果

---

## 9. 测试结果（预期）

| 指标 | v1 (faster-whisper) | v2 (stable-ts) | 提升 |
|------|---------------------|----------------|------|
| 文字准确率 | ~95% | 100% | +5% |
| 对齐精度 | 依赖转录质量 | 直接对齐 | 显著 |
| 处理速度 | 快 | 中等 | - |
| 内存占用 | 中等 | 中等 | = |

---

## 10. 注意事项

1. **模型选择**：stable-ts 支持相同的 Whisper 模型（tiny/base/small/medium/large）

2. **语言支持**：强制对齐需要指定语言代码（默认 "en"）

3. **长音频**：超长音频可能需要分段处理

4. **错误处理**：如果音频与文本严重不匹配，对齐可能失败

---

## 11. 参考资料

- [stable-ts GitHub](https://github.com/jianfch/stable-ts)
- [Whisper 论文](https://arxiv.org/abs/2212.04356)
- [Forced Alignment 技术介绍](https://en.wikipedia.org/wiki/Forced_alignment)
