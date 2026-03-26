#!/usr/bin/env python3
"""为书籍生成封面图 - 从 PDF 第一页提取"""

import json
import os
import sys
import multiprocessing as mp
from pathlib import Path
from typing import Tuple

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

try:
    import fitz  # PyMuPDF
    HAS_PDF = True
except ImportError:
    HAS_PDF = False
    print("[警告] PyMuPDF 未安装，请先: pip install pymupdf")

RAZ_DIR = Path("/Users/sarowlwp/Document/go/study-class/data/raz")
COVER_QUALITY = 2  # 图片质量，1-100，越小文件越小
COVER_DPI = 150
NUM_WORKERS = 6


def extract_cover_from_pdf(args) -> Tuple[str, str, int]:
    """从 PDF 提取封面"""
    book_dir_path, level = args
    book_dir = Path(book_dir_path)
    book_json = book_dir / "book.json"

    if not book_json.exists() or not HAS_PDF:
        return (book_dir.name, "no_json", 0)

    try:
        with open(book_json, encoding="utf-8") as f:
            book = json.load(f)

        # 检查是否已有 cover 字段
        if book.get("cover"):
            return (book_dir.name, "already_has_cover", 0)

        pdf_file = book.get("pdf")
        if not pdf_file:
            return (book_dir.name, "no_pdf", 0)

        pdf_path = book_dir / pdf_file
        if not pdf_path.exists():
            return (book_dir.name, "pdf_missing", 0)

        cover_path = book_dir / "cover.jpg"

        # 使用 PyMuPDF 提取第一页
        doc = fitz.open(str(pdf_path))
        if len(doc) == 0:
            doc.close()
            return (book_dir.name, "empty_pdf", 0)

        page = doc[0]

        # 渲染页面为图片
        mat = fitz.Matrix(COVER_DPI/72, COVER_DPI/72)  # 缩放矩阵
        pix = page.get_pixmap(matrix=mat)

        # 保存为 JPEG
        pix.save(str(cover_path))
        doc.close()

        # 更新 book.json
        book["cover"] = "cover.jpg"
        with open(book_json, "w", encoding="utf-8") as f:
            json.dump(book, f, ensure_ascii=False, indent=2)

        file_size = cover_path.stat().st_size // 1024  # KB
        return (book_dir.name, "success", file_size)

    except Exception as e:
        return (book_dir.name, f"error: {e}", 0)


def main():
    # 收集所有需要处理的书籍
    books_to_process = []

    for level_dir in sorted(RAZ_DIR.iterdir()):
        if not level_dir.is_dir() or not level_dir.name.startswith("level-"):
            continue

        level = level_dir.name.replace("level-", "")

        for book_dir in level_dir.iterdir():
            if not book_dir.is_dir():
                continue

            book_json = book_dir / "book.json"
            if not book_json.exists():
                continue

            try:
                with open(book_json, encoding="utf-8") as f:
                    book = json.load(f)

                # 跳过已有 cover 的
                if book.get("cover"):
                    continue

                # 跳过无 PDF 的
                if not book.get("pdf"):
                    continue

                books_to_process.append((str(book_dir), level))
            except:
                pass

    total = len(books_to_process)
    print(f"共 {total} 本书需要生成封面")
    print(f"使用 {NUM_WORKERS} 个并行进程\n")

    if total == 0:
        print("没有需要处理的书籍")
        return

    if not HAS_PDF:
        print("错误: PyMuPDF 未安装")
        print("安装: pip install pymupdf")
        return

    completed = 0
    success_count = 0

    with mp.Pool(NUM_WORKERS) as pool:
        for result in pool.imap_unordered(extract_cover_from_pdf, books_to_process):
            name, status, size = result
            completed += 1

            if status == "success":
                success_count += 1
                print(f"[{completed}/{total}] ✓ {name}: {size}KB")
            elif status == "already_has_cover":
                print(f"[{completed}/{total}] ○ {name}: 已有封面")
            elif status.startswith("error"):
                print(f"[{completed}/{total}] ✗ {name}: {status}")
            else:
                print(f"[{completed}/{total}] - {name}: {status}")

    print(f"\n完成: {success_count}/{total}")


if __name__ == "__main__":
    main()
