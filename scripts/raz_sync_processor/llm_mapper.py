"""LLM 映射器：使用 LLM 分析 PDF 文本和音频时间戳，生成页面音频映射."""

import json
import logging
import os
from pathlib import Path
from typing import Optional

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

logger = logging.getLogger(__name__)


class LlmMapper:
    """使用 LLM 分析并生成 book.json."""

    def __init__(self, model: str = "claude-sonnet-4-6"):
        """初始化 LLM 映射器."""
        self.model = model
        self._client = None

        if Anthropic is None:
            raise ImportError("anthropic is required. Install: pip install anthropic")

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set, LLM mapping will fail")

    @property
    def client(self) -> Anthropic:
        """懒加载 Anthropic 客户端."""
        if self._client is None:
            self._client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        return self._client

    def generate_book_json(
        self,
        pdf_text_path: Path,
        word_timings_path: Path,
        output_path: Path,
        book_id: str,
        title: str,
        level: str,
        audio_filename: str = "audio.mp3"
    ) -> Optional[Path]:
        """使用 LLM 分析并生成 book.json.

        Args:
            pdf_text_path: pdf_text.json 路径
            word_timings_path: word_timings.json 路径
            output_path: 输出 book.json 路径
            book_id: 书籍 ID
            title: 书名
            level: 级别
            audio_filename: 音频文件名

        Returns:
            成功返回输出路径，失败返回 None
        """
        try:
            # 加载输入文件
            with open(pdf_text_path, "r", encoding="utf-8") as f:
                pdf_data = json.load(f)

            with open(word_timings_path, "r", encoding="utf-8") as f:
                timings_data = json.load(f)

            # 构建 prompt
            prompt = self._build_prompt(pdf_data, timings_data, book_id, title, level, audio_filename)

            # 调用 LLM
            logger.info("Calling LLM to analyze page-audio mapping...")
            result = self._call_llm(prompt)

            if result is None:
                logger.error("LLM analysis failed")
                return None

            # 修复 level 字段
            if result.get("level", "").startswith("level-"):
                result["level"] = result["level"].replace("level-", "")

            # 保存结果
            output_path.write_text(
                json.dumps(result, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            logger.info(f"Generated: {output_path}")

            return output_path

        except Exception as e:
            logger.exception(f"Failed to generate book.json: {e}")
            return None

    def _build_prompt(
        self,
        pdf_data: dict,
        timings_data: dict,
        book_id: str,
        title: str,
        level: str,
        audio_filename: str
    ) -> str:
        """构建给 LLM 的 prompt."""
        return f""""你是一个专业的RAZ leveled reader 教育资源音频同步分析助手，特别擅长精准、零幻觉的文本-音频对齐工作。

请严格分析以下两个文件的内容，为 PDF 的每一页确定对应的音频播放时间范围。

## 文件 1: pdf_text.json - PDF 页面文本
```json
{json.dumps(pdf_data, ensure_ascii=False, indent=2)}
```

## 文件 2: word_timings.json - 单词级时间戳
```json
{json.dumps(timings_data, ensure_ascii=False, indent=2)}
```

## 核心任务原则（必须 100% 严格遵守，禁止任何幻觉）

###顺序连续匹配（防幻觉核心）：
音频是线性播放的，必须按 PDF 页面顺序（1→2→3…）依次匹配。
使用贪婪顺序连续匹配：从 word_timings 开头开始，依次为当前页面找到最长的连续单词序列（n-gram 优先，长度至少覆盖页面主要内容）。
禁止跳页、倒序、重复分配或凭空猜测。匹配完成后，下一个页面的搜索起点必须从上一个匹配的最后一个单词之后开始。
允许轻微 ASR 转录差异（单复数、冠词、省略、简单重复），但词序和整体语义必须高度一致。若无法找到合理连续匹配，该页 start/end 设为 null。

###文本处理规则：
将 PDF 文本和 word_timings 中的所有 word 全部转为小写，并移除标点（.,!?;:"'等）用于匹配对比。
输出 text 字段必须是 word_timings 中对应连续单词的精确拼接（' '.join(words)），绝不能复制、改写或使用 PDF 原文。
构建完整音频转录文本（所有 word 按顺序 join），作为全局参考。

###时间范围精确截断规则（重点提升播放自然性）：
对于匹配到的单词序列 [i..j]：
start = max(0.0, timings[i]['start'] - 0.22)   # 固定前置缓冲，绝不在单词中间截断
end   = timings[j]['end'] + 0.28               # 固定后置缓冲

###必须优先在自然截断点切割：
优先选择句子结束处（. ! ? 之后）或相邻单词间隙 ≥ 0.6 秒的自然停顿处。
若当前匹配结束位置不是理想停顿，可微调 end 到最近的自然停顿，但调整幅度不超过 0.4 秒。
允许相邻页面间最多 0.12 秒的重叠（overlap），但必须保证 page n 的 end ≤ page n+1 的 start + 0.12。
所有时间必须直接来源于 word_timings 中的 start/end 值，禁止任何推测、补齐或编造时间。

###特殊页面处理：
封面、版权页、标题页、目录页等前置/后置页面：若无明显连续匹配或音频极短（少于 3 个单词），一律 start: null, end: null, text: ''。
正文页面必须有明确连续匹配，否则也设为 null（绝不强制分配不匹配的音频）。

###完整性与验证：
最终 sentences 数组长度必须精确等于 PDF 总页数。
所有页面时间线必须整体连续且非重叠过大（总时长应接近音频总时长）。
若出现匹配失败的页面，在 JSON 中直接使用 null，不添加任何额外说明。

## 输出要求

请返回一个 JSON 对象，格式如下：
{{
  "id": "{book_id}",
  "title": "{title}",
  "level": "{level}",
  "pdf": "book.pdf",
  "cover": "cover.jpg",
  "audio": "{audio_filename}",
  "page_count": <PDF总页数>,
  "sentences": [
    {{
      "start": 0.0,
      "end": <结束时间>,
      "text": "页面主要文本（使用 MP3 转录的小写文字）",
      "page": 1
    }},
    ...
  ]
}}

要求：
- 必须包含字段：id, title, level, pdf, audio, page_count, sentences
- page_count 是整数，表示 PDF 的总页数
- sentences 数组每个元素包含：start, end, text, page
- start 和 end 必须是数字（秒），表示该页面对应的音频时间范围
- 没有音频的页面（如版权页）设置 start: null, end: null
- text 字段必须使用 MP3 转录的小写文字，不是 PDF 原文
- 返回纯 JSON，不要有其他说明文字"""

    def _call_llm(self, prompt: str) -> Optional[dict]:
        """调用 LLM 分析并返回结果."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # 提取 JSON 内容
            content = response.content[0].text

            # 尝试从代码块中提取 JSON
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()

            # 尝试解析 JSON
            try:
                result = json.loads(json_str)
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse failed: {e}. Trying to fix...")

                # 尝试修复常见问题
                fixed_str = self._fix_json(json_str)
                if fixed_str:
                    try:
                        result = json.loads(fixed_str)
                        logger.info("Successfully fixed JSON!")
                        return result
                    except:
                        pass

                logger.error(f"Failed to parse JSON. Content snippet: {json_str[:200]}")
                return None

        except Exception as e:
            logger.exception(f"LLM call failed: {e}")
            return None

    def _fix_json(self, json_str: str) -> Optional[str]:
        """尝试修复 JSON 格式问题."""
        import re

        # 尝试找到第一个 { 和最后一个 }
        start_idx = json_str.find("{")
        end_idx = json_str.rfind("}")

        if start_idx == -1 or end_idx == -1:
            return None

        # 提取 JSON 部分
        json_str = json_str[start_idx:end_idx + 1]

        # 尝试修复常见问题
        # 1. 修复 trailing commas
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)

        # 2. 修复单引号
        json_str = json_str.replace("'", '"')

        # 3. 修复未闭合的字符串
        # 这个比较复杂，先不做

        return json_str
