# LLM Mapper 模块文档

## 用途

`LlmMapper` 使用 Claude LLM 将 RAZ 绘本的 PDF 页面与音频时间戳进行智能匹配，生成 `book.json` 配置文件。

**为什么用 LLM？**
- 传统 LCS 文本对齐在儿童绘本上效果不佳（图片多、文字少、格式不固定）
- LLM 可以理解上下文，处理封面、版权页等特殊页面
- 能处理音频与 PDF 文本不完全一致的情况

## 核心流程

```
pdf_text.json + word_timings.json ──► LLM 分析 ──► book.json
```

## 输入文件格式

### pdf_text.json
```json
{
  "id": "level-a/athletes",
  "title": "Athletes",
  "level": "a",
  "source": "pdf_extraction",
  "page_count": 12,
  "pages": [
    {"page": 1, "text": "Athletes\nWritten by Russ Buoyak"},
    {"page": 2, "text": "Some athletes run."},
    ...
  ]
}
```

### word_timings.json
```json
{
  "version": "1.0",
  "total_words": 69,
  "timings": [
    {"word": "athletes", "start": 0.0, "end": 1.18},
    {"word": "written", "start": 1.62, "end": 2.32},
    ...
  ]
}
```

## 输出文件格式

### book.json
```json
{
  "id": "level-a/athletes",
  "title": "Athletes",
  "level": "a",
  "pdf": "book.pdf",
  "audio": "audio.mp3",
  "sentences": [
    {
      "start": null,
      "end": null,
      "text": null,
      "page": 1
    },
    {
      "start": 0.0,
      "end": 10.5,
      "text": "athletes written by russ buoyak focus question what do athletes do",
      "page": 2
    },
    ...
  ]
}
```

**关键字段说明：**
- `sentences` 数组：每个元素对应一页
- `start/end`: 音频时间（秒），无音频的页面为 `null`
- `text`: MP3 转录的文字（小写），不是 PDF 原文
- `page`: 页码（从1开始）

## 代码接口

```python
from scripts.raz_sync_processor.llm_mapper import LlmMapper

mapper = LlmMapper(model="claude-sonnet-4-6")

result = mapper.generate_book_json(
    pdf_text_path=Path("output/pdf_text.json"),
    word_timings_path=Path("output/word_timings.json"),
    output_path=Path("output/book.json"),
    book_id="level-a/athletes",
    title="Athletes",
    level="a",
    audio_filename="audio.mp3"
)
# 成功返回 output_path，失败返回 None
```

## Prompt 设计要点

系统通过以下策略引导 LLM 正确匹配：

1. **角色设定**: "专业的教育资源音频同步分析助手"
2. **输入说明**: 明确告知两个文件的来源和格式
3. **任务规则**:
   - 封面/版权页通常无音频 → `start: null, end: null`
   - 内容页文本应与音频单词对应
   - 内容是 RAZ 绘本，匹配时考虑完整性
4. **输出约束**: 强制要求纯 JSON，无其他说明

## 错误处理

- `ANTHROPIC_API_KEY` 未设置 → 初始化时 warning，调用时失败
- LLM 返回非 JSON → 尝试从代码块提取，失败返回 None
- 网络/API 错误 → 捕获异常，返回 None

## 与其他模块的关系

```
PDFProcessor ──► pdf_text.json ──┐
                                ├──► LlmMapper ──► book.json
AudioTranscriber ──► word_timings.json ──┘
```

## 修改注意事项

1. **模型选择**: 默认 `claude-sonnet-4-6`，可更换为其他 Claude 模型
2. **max_tokens**: 默认 4000，处理长绘本可能需要增加
3. **Prompt 调整**: 修改 `_build_prompt()` 可改变匹配行为
4. **后处理**: 目前仅对 `level-` 前缀做简单修复，可扩展更多字段校验
