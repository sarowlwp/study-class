#!/usr/bin/env python3
"""
整理新增书籍的 book.json 格式，确保字段规范。
不处理已有完整 sentences 的旧书。

用法:
  python3 format_new_books.py              # 处理所有新增书
  python3 format_new_books.py --level b    # 只处理指定级别
  python3 format_new_books.py --dry-run    # 仅预览
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, List

RAZ_DIR = Path("/Users/sarowlwp/Document/go/study-class/data/raz")


def normalize_slug(title: str) -> str:
    """将标题转换为 slug 格式。"""
    slug = re.sub(r"[^a-zA-Z0-9\s]", "", title)
    slug = re.sub(r"\s+", "-", slug.strip())
    return slug.lower()


def is_old_book(book_data: Dict[str, Any]) -> bool:
    """
    检查是否是旧书（已有完整 sentences 数据）。

    判断标准:
    - sentences 数组非空且包含 start/end 字段
    """
    sentences = book_data.get("sentences", [])
    if not sentences:
        return False

    # 检查是否有 start/end 字段（旧书有完整数据）
    for sent in sentences:
        if isinstance(sent, dict) and "start" in sent and "end" in sent:
            return True

    return False


def format_book_json(book_dir: Path, dry_run: bool = False) -> bool:
    """
    整理单本书的 book.json 格式。

    标准格式:
    {
      "id": "level-a/book-slug",
      "title": "Book Title",
      "level": "a",
      "pdf": "book.pdf",
      "video": null or "video.mp4",
      "audio": null or "audio.mp3",
      "sentences": [...]
    }

    返回是否已修改。
    """
    book_json_path = book_dir / "book.json"
    if not book_json_path.exists():
        return False

    try:
        with open(book_json_path, "r", encoding="utf-8") as f:
            book = json.load(f)
    except Exception as e:
        print(f"  [错误] 读取失败 {book_dir.name}: {e}")
        return False

    # 跳过旧书（已有完整 sentences）
    if is_old_book(book):
        return False

    # 提取/修正字段
    level = book.get("level", "").lower()
    title = book.get("title", "").strip()

    if not level or not title:
        print(f"  [跳过] {book_dir.name} - 缺少 level 或 title")
        return False

    # 构建标准格式
    formatted: Dict[str, Any] = {
        "id": f"level-{level}/{book_dir.name}",
        "title": title,
        "level": level,
        "pdf": "book.pdf",
        "video": book.get("video"),  # 保持原有值
        "audio": book.get("audio"),  # 保持原有值
        "sentences": [],  # 新书保持空数组，等待转录
    }

    # 检查资源文件是否存在
    if (book_dir / "book.pdf").exists():
        formatted["pdf"] = "book.pdf"
    else:
        formatted["pdf"] = None

    if (book_dir / "video.mp4").exists():
        formatted["video"] = "video.mp4"
    else:
        formatted["video"] = None

    if (book_dir / "audio.mp3").exists():
        formatted["audio"] = "audio.mp3"
    else:
        formatted["audio"] = None

    # 检查是否需要修改
    if formatted == book:
        return False

    if dry_run:
        print(f"  [预览] {title}")
        print(f"    PDF: {formatted['pdf'] is not None}")
        print(f"    Audio: {formatted['audio'] is not None}")
        print(f"    Video: {formatted['video'] is not None}")
        return True

    # 写入文件
    try:
        with open(book_json_path, "w", encoding="utf-8") as f:
            json.dump(formatted, f, ensure_ascii=False, indent=2)
        print(f"  ✓ {title}")
        return True
    except Exception as e:
        print(f"  [错误] 写入失败 {book_dir.name}: {e}")
        return False


def process_level(level_dir: Path, dry_run: bool = False) -> tuple:
    """处理单个级别。"""
    book_dirs = sorted([d for d in level_dir.iterdir() if d.is_dir()])

    modified = 0
    skipped_old = 0
    unchanged = 0

    for book_dir in book_dirs:
        book_json = book_dir / "book.json"
        if not book_json.exists():
            continue

        # 检查是否是旧书
        try:
            with open(book_json, "r", encoding="utf-8") as f:
                book = json.load(f)
            if is_old_book(book):
                skipped_old += 1
                continue
        except Exception:
            pass

        # 处理新书
        if format_book_json(book_dir, dry_run):
            modified += 1
        else:
            unchanged += 1

    return modified, skipped_old, unchanged


def main():
    parser = argparse.ArgumentParser(description="整理新增书籍的 book.json 格式")
    parser.add_argument("--level", metavar="LEVEL", help="只处理指定级别（如 b/c/d）")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不实际修改")
    args = parser.parse_args()

    if args.level:
        # 处理指定级别
        level_dir = RAZ_DIR / f"level-{args.level}"
        if not level_dir.exists():
            print(f"错误: 找不到级别目录 {level_dir}")
            sys.exit(1)

        print(f"\n=== 处理 level-{args.level} ===")
        modified, skipped_old, unchanged = process_level(level_dir, args.dry_run)
        print(f"\n结果: 已修改 {modified}, 跳过旧书 {skipped_old}, 无需修改 {unchanged}")

    else:
        # 处理所有级别
        level_dirs = sorted([d for d in RAZ_DIR.iterdir() if d.is_dir()])

        total_modified = 0
        total_skipped = 0
        total_unchanged = 0

        for level_dir in level_dirs:
            level = level_dir.name.replace("level-", "")
            book_count = len([d for d in level_dir.iterdir() if d.is_dir()])

            modified, skipped_old, unchanged = process_level(level_dir, args.dry_run)

            if modified > 0:
                print(f"[{level.upper()}] {book_count} 本书 → 已修改 {modified}, 跳过旧书 {skipped_old}")

            total_modified += modified
            total_skipped += skipped_old
            total_unchanged += unchanged

        print(f"\n{'='*60}")
        print(f"总计: 已修改 {total_modified}, 跳过旧书 {total_skipped}, 无需修改 {total_unchanged}")

        if args.dry_run:
            print("\n这是预览模式，实际未修改文件。")
            print("去掉 --dry-run 参数执行实际修改。")


if __name__ == "__main__":
    main()
