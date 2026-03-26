"""
解压 003.RAZ绘本JPG版+ 音频MP3/ 下所有压缩包，
并按 level-e 相同方式生成 data/raz/level-{x}/ 下的 book.json + PDF + MP3。

跳过 o.rar（结构不同，只有整本PDF，无分页音频）。
"""

import io
import json
import os
import re
import shutil
import zipfile
from pathlib import Path

import rarfile
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
ARCHIVE_DIR = Path(__file__).resolve().parent / "003.RAZ绘本JPG版+ 音频MP3"
OUTPUT_BASE = BASE_DIR / "data" / "raz"

SKIP_LEVELS = {"o"}  # 结构不同，跳过


def title_to_slug(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def jpg_bytes_to_pdf(jpg_bytes: bytes, pdf_path: Path) -> bool:
    """返回 True 表示成功，False 表示图片损坏。"""
    try:
        img = Image.open(io.BytesIO(jpg_bytes)).convert("RGB")
        img.save(pdf_path, "PDF", resolution=100.0)
        return True
    except (OSError, Exception):
        return False


def open_archive(archive_path: Path):
    """返回 (opener, is_rar)"""
    if archive_path.suffix == ".rar":
        return rarfile.RarFile(archive_path), True
    return zipfile.ZipFile(archive_path), False


def list_books(arc, level: str) -> dict[str, dict[str, bytes]]:
    """
    返回 {book_title: {filename: bytes}} 字典。
    处理 k.rar 的双层嵌套 (k/k/Book/file) 和普通单层 (level/Book/file)。
    """
    books: dict[str, dict[str, bytes]] = {}

    for member in arc.namelist():
        # 去掉目录条目
        if member.endswith("/") or member.endswith("\\"):
            continue

        parts = [p for p in member.replace("\\", "/").split("/") if p]

        # 找到书名所在层级：跳过与 level 同名的前缀目录
        # 结构可能是 level/Book/file 或 level/level/Book/file
        idx = 0
        while idx < len(parts) - 1 and parts[idx].lower() == level.lower():
            idx += 1

        if len(parts) - idx < 2:
            continue  # 文件直接在顶层，跳过

        book_name = parts[idx]
        filename = parts[-1]
        books.setdefault(book_name, {})[filename] = None  # 先记录结构

    # 第二遍读取内容
    books_with_data: dict[str, dict[str, bytes]] = {}
    for member in arc.namelist():
        if member.endswith("/") or member.endswith("\\"):
            continue
        parts = [p for p in member.replace("\\", "/").split("/") if p]
        idx = 0
        while idx < len(parts) - 1 and parts[idx].lower() == level.lower():
            idx += 1
        if len(parts) - idx < 2:
            continue
        book_name = parts[idx]
        filename = parts[-1]
        if book_name not in books:
            continue
        try:
            data = arc.read(member)
        except Exception:
            data = b""
        books_with_data.setdefault(book_name, {})[filename] = data

    return books_with_data


def process_book(
    book_title: str,
    files: dict[str, bytes],
    level: str,
) -> int:
    """处理单本书，返回生成的页数（0 表示跳过）。"""
    slug = title_to_slug(book_title)
    out_dir = OUTPUT_BASE / f"level-{level}" / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    # 查找 title 音频
    title_audio_name = next(
        (fn for fn in files if re.search(r"_title_text\.mp3$", fn)), None
    )

    # 查找内容页音频: {page_num: filename}
    content_audios: dict[int, str] = {}
    for fn in files:
        m = re.search(r"_p(\d+)_text\.mp3$", fn)
        if m:
            content_audios[int(m.group(1))] = fn

    if not title_audio_name and not content_audios:
        print(f"    [跳过] {book_title}：找不到任何音频文件")
        shutil.rmtree(out_dir)
        return 0

    # 组装页面列表：(jpg_filename, mp3_filename)
    pages_data: list[tuple[str, str]] = []

    # 标题页
    if title_audio_name and "page-1.jpg" in files:
        pages_data.append(("page-1.jpg", title_audio_name))

    # 内容页：按页码排序，只包含有对应 JPG 的页
    for page_num in sorted(content_audios.keys()):
        jpg_fn = f"page-{page_num}.jpg"
        if jpg_fn in files:
            pages_data.append((jpg_fn, content_audios[page_num]))

    if not pages_data:
        print(f"    [跳过] {book_title}：没有可用页面")
        shutil.rmtree(out_dir)
        return 0

    # 生成文件
    book_pages = []
    for i, (jpg_fn, mp3_fn) in enumerate(pages_data, start=1):
        page_num_str = f"{i:02d}"
        pdf_name = f"page{page_num_str}.pdf"
        mp3_name = f"page{page_num_str}.mp3"

        if not jpg_bytes_to_pdf(files[jpg_fn], out_dir / pdf_name):
            print(f"    [警告] 图片损坏，跳过 {jpg_fn} in {book_title}")
            continue
        (out_dir / mp3_name).write_bytes(files[mp3_fn])

        book_pages.append({
            "page": i,
            "pdf": pdf_name,
            "audio": mp3_name,
            "sentences": [],
        })

    book_json = {
        "id": f"level-{level}/{slug}",
        "title": book_title,
        "level": level,
        "video": None,
        "pages": book_pages,
    }
    with open(out_dir / "book.json", "w", encoding="utf-8") as f:
        json.dump(book_json, f, ensure_ascii=False, indent=2)

    return len(book_pages)


def process_archive(archive_path: Path) -> None:
    # 推断 level（取文件名去掉扩展名）
    level = archive_path.stem.lower()
    if level in SKIP_LEVELS:
        print(f"[跳过] {archive_path.name}（结构不兼容）")
        return

    # 如果已输出目录存在，跳过
    if (OUTPUT_BASE / f"level-{level}").exists():
        print(f"[跳过] level-{level} 已处理完成")
        return

    print(f"\n===== 处理 level-{level} ({archive_path.name}) =====")

    arc, _ = open_archive(archive_path)
    with arc:
        books = list_books(arc, level)

    print(f"  发现 {len(books)} 本书")
    ok = 0
    for title, files in sorted(books.items()):
        n = process_book(title, files, level)
        if n > 0:
            print(f"  OK  {title} → level-{level}/{title_to_slug(title)} ({n}页)")
            ok += 1

    print(f"  完成：{ok}/{len(books)} 本书")


def main() -> None:
    archives = sorted(
        [f for f in ARCHIVE_DIR.iterdir() if f.suffix in (".zip", ".rar")]
    )
    print(f"共发现 {len(archives)} 个压缩包\n")

    for archive in archives:
        process_archive(archive)

    print("\n全部完成。")


if __name__ == "__main__":
    main()
