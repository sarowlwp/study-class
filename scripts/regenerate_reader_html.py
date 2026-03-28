#!/usr/bin/env python3
"""重新生成所有 reader HTML（使用更新后的模板）."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.raz_sync_processor.sync_generator import SyncGenerator

LEVELS = ["level-a", "level-aa", "level-b"]
BASE_DIR = Path("data/raz")


def regenerate_html_for_dir(book_dir: Path) -> bool:
    """重新生成单个书籍的 HTML."""
    book_json = book_dir / "book.json"
    index_html = book_dir / "index.html"

    if not book_json.exists():
        return False

    try:
        # 删除旧的 HTML
        if index_html.exists():
            index_html.unlink()

        generator = SyncGenerator(book_dir)
        generator.generate_reader_html()
        print(f"  ✓ {book_dir.parent.name}/{book_dir.name}")
        return True
    except Exception as e:
        print(f"  ✗ {book_dir.name}: {e}")
        return False


def main():
    total = 0
    success = 0

    for level in LEVELS:
        level_dir = BASE_DIR / level
        if not level_dir.exists():
            continue

        print(f"\n=== {level} ===")
        for book_dir in sorted(level_dir.iterdir()):
            if book_dir.is_dir() and (book_dir / "book.json").exists():
                total += 1
                if regenerate_html_for_dir(book_dir):
                    success += 1

    print(f"\n总计: {total}, 成功: {success}")


if __name__ == "__main__":
    main()
