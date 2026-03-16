"""
PDF 课本资源初始化工具

将统编版语文课本 PDF 转换为 characters 目录下的 markdown 资源文件。
使用 mapull/chinese-dictionary 开源字典数据填充释义。

用法:
    python -m app.scripts.pdf_to_characters --pdf data/pdfs/grade2-spring.pdf --grade 2 --semester spring --fill-meaning
"""

import os
import re
import json
import argparse
import asyncio
import aiohttp
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

# 可选依赖
try:
    from PyPDF2 import PdfReader
except ImportError:
    raise ImportError("请先安装 PyPDF2: pip install PyPDF2")

try:
    from pypinyin import pinyin, Style
    PYPINYIN_AVAILABLE = True
except ImportError:
    PYPINYIN_AVAILABLE = False

from app.config import CHARACTERS_DIR, DATA_DIR


@dataclass
class Character:
    """汉字数据模型"""
    char: str
    pinyin: str
    meaning: str = ""
    example: str = ""


@dataclass
class Lesson:
    """课文/单元数据模型"""
    name: str
    characters: List[Character]


class ChineseDictionaryService:
    """
    汉语字典服务 - 使用 mapull/chinese-dictionary 数据
    项目地址: https://github.com/mapull/chinese-dictionary/
    """

    DICT_FILE = DATA_DIR / "dict" / "char_common_detail.json"

    def __init__(self):
        self._dict_data: Dict[str, Dict] = {}
        self._load_dictionary()

    def _load_dictionary(self):
        """加载字典数据"""
        if not self.DICT_FILE.exists():
            raise FileNotFoundError(
                f"字典文件不存在: {self.DICT_FILE}\n"
                "请先下载字典数据:\n"
                "curl -L -o data/dict/char_common_detail.json "
                "https://raw.githubusercontent.com/mapull/chinese-dictionary/master/character/common/char_common_detail.json"
            )

        # 文件格式: 多个独立的 JSON 对象 {}{}...{}
        with open(self.DICT_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析每个 JSON 对象
        depth = 0
        start = 0
        count = 0

        for i, char in enumerate(content):
            if char == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(content[start:i+1])
                        if 'char' in obj:
                            self._dict_data[obj['char']] = obj
                            count += 1
                    except json.JSONDecodeError:
                        pass

        print(f"  已加载字典: {count} 个汉字")

    def lookup(self, char: str) -> Dict[str, str]:
        """
        查询汉字的释义和例句

        Returns:
            {"meaning": "释义", "example": "例句"}
        """
        if char not in self._dict_data:
            return {"meaning": "常用汉字", "example": ""}

        data = self._dict_data[char]

        # 提取释义
        meaning_parts = []
        example = ""

        if 'pronunciations' in data and data['pronunciations']:
            pron = data['pronunciations'][0]  # 使用第一个读音

            if 'explanations' in pron and pron['explanations']:
                for exp in pron['explanations'][:2]:  # 取前2条解释
                    if 'content' in exp:
                        content = exp['content']
                        # 清理括号内的详细内容，保留简洁释义
                        content = re.sub(r'[（(].*?[）)]', '', content)
                        content = content.strip()
                        if content and content not in ['。', '；']:
                            meaning_parts.append(content)

                    # 提取例句
                    if not example and 'detail' in exp and exp['detail']:
                        for detail in exp['detail'][:1]:
                            if 'text' in detail:
                                example = detail['text']
                                break

                    # 从 words 中提取例句
                    if not example and 'words' in exp and exp['words']:
                        for word in exp['words'][:1]:
                            if 'text' in word:
                                example = word['text']
                                break

        meaning = '；'.join(meaning_parts) if meaning_parts else "常用汉字"

        # 截断过长的释义
        if len(meaning) > 40:
            meaning = meaning[:37] + "..."

        return {"meaning": meaning, "example": example}

    def batch_lookup(self, characters: List[str]) -> Dict[str, Dict[str, str]]:
        """批量查询多个汉字"""
        results = {}
        total = len(characters)
        filled = 0

        for i, char in enumerate(characters):
            result = self.lookup(char)
            results[char] = result
            if result["meaning"] and result["meaning"] != "常用汉字":
                filled += 1

            if (i + 1) % 50 == 0 or (i + 1) == total:
                print(f"    进度: {i+1}/{total} ({(i+1)*100//total}%)  已填充: {filled}")

        print(f"  查询完成: {filled}/{total} 个汉字有详细释义")
        return results


class PdfToCharacterConverter:
    """PDF 转汉字资源转换器"""

    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        self.reader = PdfReader(str(pdf_path))
        self.total_pages = len(self.reader.pages)

    def extract_text(self, start_page: int = 0, end_page: Optional[int] = None) -> str:
        """提取指定范围的页面文本"""
        if end_page is None:
            end_page = self.total_pages

        text_parts = []
        for i in range(start_page, min(end_page, self.total_pages)):
            page = self.reader.pages[i]
            page_text = page.extract_text()
            if page_text:
                text_parts.append(f"=== Page {i + 1} ===\n{page_text}")

        return "\n\n".join(text_parts)

    def extract_lesson_titles(self) -> Dict[str, str]:
        """从PDF目录页提取课文标题映射 {课文编号: 标题}"""
        titles = {}

        # 目录在第4-5页（索引3-4），提取目录内容
        for page_idx in range(min(6, self.total_pages)):
            page = self.reader.pages[page_idx]
            text = page.extract_text() or ""

            # 检查是否是目录页
            if "目录" not in text[:100] and page_idx > 0:
                continue

            lines = text.split('\n')
            current_type = "课文"  # 默认类型
            pending_num = None  # 暂存的数字

            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue

                # 检测类型切换（包括类型+数字在同一行的情况）
                # 如 "识字\t1\t 神州谣" 或 "课文\t8\t"
                if line.startswith('识字') or line.startswith('课文'):
                    current_type = '识字' if line.startswith('识字') else '课文'
                    # 检查是否包含数字和标题
                    match = re.match(r'^(识字|课文)\s*(\d+)\s+(.+)', line)
                    if match:
                        num = match.group(2)
                        title = match.group(3).strip()
                        # 清理标题
                        title = re.sub(r'\s+', '', title)
                        title = title.strip('◎')
                        # 如果标题包含点线页码，去掉页码部分
                        title = re.sub(r'[\.\s]+\d+$', '', title)
                        if len(title) >= 2:
                            lesson_key = f"{current_type} {num}"
                            titles[lesson_key] = title
                    continue

                # 模式1: 数字 + 标题 + 点线 + 页码（单行完整格式）
                # 如 "\t5\t 雷锋叔叔，你在哪里 \t.....16"
                match = re.match(r'^[\s◎]*(\d+)\s+(.+?)[\.\s]+\d+$', line)
                if match:
                    num = match.group(1)
                    title = match.group(2).strip()
                    # 清理标题中的多余空格和特殊字符
                    title = re.sub(r'\s+', '', title)
                    title = title.strip('◎')
                    if len(title) >= 2:
                        lesson_key = f"{current_type} {num}"
                        titles[lesson_key] = title
                    pending_num = None
                    continue

                # 模式2: 这一行只有数字，标题在下一行
                match = re.match(r'^[\s◎]*(\d+)$', line)
                if match:
                    num_str = match.group(1)
                    # 检查是否是两位数被分割的情况（如课文24变成"2"和"4"）
                    # 如果当前是单个数字，但前一行的最后一个字符也是数字，则可能是分割
                    if len(num_str) == 1 and i > 0:
                        prev_line = lines[i - 1].strip()
                        # 如果前一行也是单个数字，组合它们
                        if re.match(r'^\d+$', prev_line) and len(prev_line) == 1:
                            num_str = prev_line + num_str
                    pending_num = num_str
                    # 立即查看下一行获取标题
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        # 下一行应该是标题 + 页码
                        title_match = re.match(r'^(.+?)[\.\s]+\d+$', next_line)
                        if title_match:
                            title = title_match.group(1).strip()
                            title = re.sub(r'\s+', '', title)
                            # 过滤掉以数字开头的标题（可能是24的"4"开头的行）
                            if len(title) >= 2 and not title.startswith('◎') and not re.match(r'^\d', title):
                                lesson_key = f"{current_type} {num_str}"
                                titles[lesson_key] = title
                            pending_num = None
                    continue

                # 模式3: 可能是带◎的口语交际等，跳过
                if line.startswith('◎') or '口语交际' in line or '语文园地' in line:
                    continue

        return titles

    def find_character_tables(self) -> List[Tuple[int, int]]:
        """查找生字表所在的页面范围"""
        check_pages = min(30, self.total_pages)
        start_check = self.total_pages - check_pages

        table_ranges = []
        in_table = False
        table_start = 0

        for i in range(start_check, self.total_pages):
            page = self.reader.pages[i]
            text = page.extract_text() or ""

            if re.search(r'(识字表|写字表|词语表|生字表)', text):
                if not in_table:
                    in_table = True
                    table_start = i
            elif in_table and not text.strip():
                continue

        if in_table:
            table_ranges.append((table_start, self.total_pages))

        return table_ranges

    def parse_character_table(self, text: str, titles: Dict[str, str] = None) -> List[Lesson]:
        """解析生字表文本，提取课文和生字信息"""
        lessons = []
        text = self._clean_text(text)
        titles = titles or {}

        lines = text.split('\n')
        current_lesson: Optional[Lesson] = None
        current_type = "课文"  # 默认类型
        pending_num = None  # 暂存数字，处理 "1 0" 这样的情况

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # 检测类型标记
            if line == "课文":
                current_type = "课文"
                continue
            if line == "识字":
                current_type = "识字"
                continue

            # 匹配数字开头，如 "1 诗童趁..." 或 "1 0 周围..."
            # 处理两位数被分开的情况
            match = re.match(r'^(\d+)\s+(.*)$', line)
            if match:
                num_part = match.group(1)
                content = match.group(2)

                # 检查是否是两位数被分割（如 "1 0" 表示 10）
                if pending_num is not None and num_part in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                    # 组合成两位数
                    lesson_num = pending_num + num_part
                    pending_num = None
                else:
                    # 保存当前数字，可能是两位数的第一位
                    pending_num = num_part
                    # 如果下一行不是单个数字，则使用当前数字
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        next_match = re.match(r'^(\d+)\s+(.*)$', next_line)
                        if next_match and next_match.group(1) in ['0', '1', '2', '3', '4', '5']:
                            # 可能是两位数，等待下一行
                            continue
                    lesson_num = pending_num
                    pending_num = None

                # 构建 lesson_key
                lesson_key = f"{current_type} {lesson_num}"

                # 保存上一课
                if current_lesson and current_lesson.characters:
                    lessons.append(current_lesson)

                # 使用提取的标题或默认标题
                lesson_name = titles.get(lesson_key, f"{current_type} {lesson_num}")

                current_lesson = Lesson(name=lesson_name, characters=[])
                chars = self._parse_chars_from_text(content)
                if current_lesson:
                    current_lesson.characters.extend(chars)
                continue

            # 如果当前有课程，继续添加生字
            elif current_lesson and line:
                chars = self._parse_chars_from_text(line)
                current_lesson.characters.extend(chars)

        if current_lesson and current_lesson.characters:
            lessons.append(current_lesson)

        return lessons

    def _clean_text(self, text: str) -> str:
        """清理 PDF 提取的文本"""
        text = re.sub(r'~\S+', '', text)
        text = re.sub(r'\(\s*\d+\s*\)', '', text)
        text = re.sub(r'\n+', '\n', text)
        return text.strip()

    def _extract_lesson_name(self, text: str) -> Optional[str]:
        """从文本中提取课文名称"""
        return None

    def _parse_chars_from_text(self, text: str) -> List[Character]:
        """从文本中解析汉字和拼音"""
        characters = []
        pattern = r'([\u4e00-\u9fa5])([a-zA-Züāáǎàōóǒòēéěèīíǐìūúǔùǖǘǚǜ]+)'

        for match in re.finditer(pattern, text):
            char = match.group(1)
            pinyin = self._normalize_pinyin(match.group(2))

            if '\u4e00' <= char <= '\u9fff':
                characters.append(Character(
                    char=char,
                    pinyin=pinyin,
                    meaning="",
                    example=""
                ))

        return characters

    def _normalize_pinyin(self, pinyin: str) -> str:
        """规范化拼音（简单处理）"""
        if not pinyin:
            return pinyin

        direct_map = {
            'U': 'ī', 'T': 'ō', 'A': 'ā', 'N': 'n', 'G': 'g',
            'P': 'ú', 'W': 'á', 'Q': 'ā',
            'L': 'ǐ', 'O': 'ǎo', 'E': 'ě',
            'K': 'ì',
        }

        result = []
        i = 0
        n = len(pinyin)

        while i < n:
            char = pinyin[i]

            if char in direct_map:
                if char == 'L' and result and result[-1] == 'i':
                    result[-1] = 'ǐ'
                else:
                    result.append(direct_map[char])
                i += 1
            elif char.isupper():
                result.append(char.lower())
                i += 1
            else:
                result.append(char)
                i += 1

        return ''.join(result)

    def generate_markdown(
        self,
        grade: int,
        semester: str,
        title: Optional[str] = None,
        use_pypinyin: bool = True,
        fill_meaning: bool = False
    ) -> str:
        """生成 markdown 格式的资源文件"""
        # 先提取课文标题
        print("正在提取课文标题...")
        lesson_titles = self.extract_lesson_titles()
        print(f"  找到 {len(lesson_titles)} 个课文标题")

        table_ranges = self.find_character_tables()

        if not table_ranges:
            text = self.extract_text()
            lessons = self.parse_character_table(text, lesson_titles)
        else:
            all_lessons = []
            for start, end in table_ranges:
                text = self.extract_text(start, end)
                lessons = self.parse_character_table(text, lesson_titles)
                all_lessons.extend(lessons)
            lessons = all_lessons

        # 如果需要填充释义，使用字典服务
        char_dict_data: Dict[str, Dict[str, str]] = {}
        if fill_meaning:
            all_chars = [c.char for lesson in lessons for c in lesson.characters]
            unique_chars = list(dict.fromkeys(all_chars))  # 去重但保持顺序
            print(f"正在查询 {len(unique_chars)} 个汉字的释义...")

            dict_service = ChineseDictionaryService()
            char_dict_data = dict_service.batch_lookup(unique_chars)

            # 确保 100% 有释义
            for char in unique_chars:
                if not char_dict_data[char].get("meaning"):
                    char_dict_data[char] = {"meaning": "常用汉字", "example": ""}

        if title is None:
            semester_name = "上册" if semester == "autumn" else "下册"
            title = f"{self._number_to_chinese(grade)}年级{semester_name}"

        lines = [f"# {title}", ""]

        for lesson in lessons:
            lines.append(f"## {lesson.name}")
            lines.append("")
            lines.append("| 汉字 | 拼音 | 释义 | 例句 |")
            lines.append("|------|------|------|------|")

            for char in lesson.characters:
                if use_pypinyin and PYPINYIN_AVAILABLE:
                    pinyin_result = pinyin(char.char, style=Style.TONE)
                    char_pinyin = pinyin_result[0][0] if pinyin_result else char.pinyin
                else:
                    char_pinyin = char.pinyin

                if fill_meaning and char.char in char_dict_data:
                    meaning = char_dict_data[char.char].get("meaning") or "常用汉字"
                    example = char_dict_data[char.char].get("example") or ""
                else:
                    meaning = char.meaning or "待补充"
                    example = char.example or ""

                lines.append(f"| {char.char} | {char_pinyin} | {meaning} | {example} |")

            lines.append("")

        return '\n'.join(lines)

    def _number_to_chinese(self, num: int) -> str:
        """数字转中文"""
        chinese_nums = ['零', '一', '二', '三', '四', '五', '六']
        return chinese_nums[num] if 0 <= num <= 6 else str(num)

    def save_markdown(
        self,
        grade: int,
        semester: str,
        title: Optional[str] = None,
        output_dir: Optional[Path] = None,
        fill_meaning: bool = False
    ) -> Path:
        """保存 markdown 文件"""
        if output_dir is None:
            output_dir = CHARACTERS_DIR

        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"grade{grade}-{semester}.md"
        output_path = output_dir / filename

        markdown = self.generate_markdown(
            grade, semester, title,
            fill_meaning=fill_meaning
        )
        output_path.write_text(markdown, encoding='utf-8')

        return output_path


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="将 PDF 课本转换为 characters 资源文件"
    )
    parser.add_argument(
        "--pdf", "-p",
        required=True,
        help="PDF 文件路径"
    )
    parser.add_argument(
        "--grade", "-g",
        type=int,
        required=True,
        choices=range(1, 7),
        help="年级 (1-6)"
    )
    parser.add_argument(
        "--semester", "-s",
        required=True,
        choices=["spring", "autumn"],
        help="学期 (spring=下册, autumn=上册)"
    )
    parser.add_argument(
        "--title", "-t",
        help="自定义标题（可选）"
    )
    parser.add_argument(
        "--output", "-o",
        help="输出目录（默认 data/characters）"
    )
    parser.add_argument(
        "--fill-meaning", "-m",
        action="store_true",
        help="自动填充释义和例句（使用 chinese-dictionary 字典数据）"
    )

    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"错误: PDF 文件不存在: {pdf_path}")
        return 1

    output_dir = Path(args.output) if args.output else None

    converter = PdfToCharacterConverter(pdf_path)

    if args.fill_meaning:
        print("正在使用 chinese-dictionary 字典数据填充释义...")

    output_path = converter.save_markdown(
        grade=args.grade,
        semester=args.semester,
        title=args.title,
        output_dir=output_dir,
        fill_meaning=args.fill_meaning
    )

    print(f"✓ 资源文件已生成: {output_path}")

    # 显示统计信息
    lessons = converter.parse_character_table(
        converter.extract_text(
            converter.find_character_tables()[0][0] if converter.find_character_tables() else 0
        )
    )
    total_chars = sum(len(l.characters) for l in lessons)
    print(f"✓ 共 {len(lessons)} 个单元/课文，{total_chars} 个生字")

    return 0


if __name__ == "__main__":
    exit(main())
