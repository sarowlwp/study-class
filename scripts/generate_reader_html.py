#!/usr/bin/env python3
"""为已处理的 RAZ 目录生成 reader HTML."""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.raz_sync_processor.sync_generator import SyncGenerator

LEVELS = ["level-a", "level-aa", "level-b"]
BASE_DIR = Path("data/raz")


def generate_reader_html_for_dir(book_dir: Path) -> bool:
    """为单个书籍目录生成 reader HTML."""
    book_json = book_dir / "book.json"
    index_html = book_dir / "index.html"

    if not book_json.exists():
        return False

    if index_html.exists():
        print(f"  跳过 {book_dir.name} (已存在)")
        return True

    try:
        generator = SyncGenerator(book_dir)
        generator.generate_reader_html()
        print(f"  ✓ {book_dir.name}")
        return True
    except Exception as e:
        print(f"  ✗ {book_dir.name}: {e}")
        return False


def main():
    """批量生成 reader HTML."""
    total = 0
    success = 0

    for level in LEVELS:
        level_dir = BASE_DIR / level
        if not level_dir.exists():
            continue

        print(f"\n=== {level} ===")
        for book_dir in level_dir.iterdir():
            if book_dir.is_dir() and (book_dir / "book.json").exists():
                total += 1
                if generate_reader_html_for_dir(book_dir):
                    success += 1

    print(f"\n总计: {total}, 成功: {success}")


if __name__ == "__main__":
    main()
