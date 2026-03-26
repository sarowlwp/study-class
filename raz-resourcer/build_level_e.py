"""
Convert Level-E RAZ books from raz-resourcer to data/raz/level-e structure.

Source: 003.RAZ绘本JPG版+ 音频MP3/e/{Book Title}/
  - page-1.jpg           → cover (title audio)
  - page-2.jpg           → copyright page (skipped)
  - page-3.jpg ~ page-12.jpg → content pages (p3~p12 audio)
  - page-13.jpg          → back cover (skipped)
  - raz_*_title_text.mp3 → page01.mp3
  - raz_*_pN_text.mp3    → pageNN.mp3

Output: data/raz/level-e/{book-slug}/
  - page01.pdf ~ page11.pdf
  - page01.mp3 ~ page11.mp3
  - book.json
"""

import json
import os
import re
import shutil
from pathlib import Path

from PIL import Image

BASE_DIR = Path(__file__).parent.parent
SOURCE_DIR = Path(__file__).parent / "003.RAZ绘本JPG版+ 音频MP3" / "e"
OUTPUT_DIR = BASE_DIR / "data" / "raz" / "level-e"


def title_to_slug(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def jpg_to_pdf(jpg_path: Path, pdf_path: Path) -> None:
    img = Image.open(jpg_path).convert("RGB")
    img.save(pdf_path, "PDF", resolution=100.0)


def build_book(book_dir: Path) -> None:
    title = book_dir.name
    slug = title_to_slug(title)
    out_dir = OUTPUT_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    # Find title audio
    title_audios = list(book_dir.glob("*_title_text.mp3"))
    if not title_audios:
        print(f"  [WARN] No title audio in {title}, skipping")
        return
    title_audio = title_audios[0]

    # Find content page audios (p3~p12)
    content_audios: dict[int, Path] = {}
    for f in book_dir.glob("*_p*_text.mp3"):
        m = re.search(r"_p(\d+)_text\.mp3$", f.name)
        if m:
            content_audios[int(m.group(1))] = f

    # Build page list: page 1 = cover+title, page 2-11 = p3-p12
    # [(source_jpg, source_mp3), ...]
    pages_data: list[tuple[Path, Path]] = []

    cover_jpg = book_dir / "page-1.jpg"
    if not cover_jpg.exists():
        print(f"  [WARN] No cover page-1.jpg in {title}, skipping")
        return
    pages_data.append((cover_jpg, title_audio))

    for src_page_num in range(3, 13):  # 3..12
        jpg = book_dir / f"page-{src_page_num}.jpg"
        if not jpg.exists():
            print(f"  [WARN] Missing page-{src_page_num}.jpg in {title}")
            continue
        audio = content_audios.get(src_page_num)
        if audio is None:
            print(f"  [WARN] Missing p{src_page_num} audio in {title}")
            continue
        pages_data.append((jpg, audio))

    # Convert and copy files, build book.json pages
    book_pages = []
    for i, (jpg_path, mp3_path) in enumerate(pages_data, start=1):
        page_num = f"{i:02d}"
        pdf_name = f"page{page_num}.pdf"
        mp3_name = f"page{page_num}.mp3"

        jpg_to_pdf(jpg_path, out_dir / pdf_name)
        shutil.copy2(mp3_path, out_dir / mp3_name)

        book_pages.append({
            "page": i,
            "pdf": pdf_name,
            "audio": mp3_name,
            "sentences": [],
        })

    book_json = {
        "id": f"level-e/{slug}",
        "title": title,
        "level": "e",
        "video": None,
        "pages": book_pages,
    }

    with open(out_dir / "book.json", "w", encoding="utf-8") as f:
        json.dump(book_json, f, ensure_ascii=False, indent=2)

    print(f"  OK  {title} → level-e/{slug} ({len(book_pages)} pages)")


def main() -> None:
    book_dirs = sorted([d for d in SOURCE_DIR.iterdir() if d.is_dir()])
    print(f"Found {len(book_dirs)} books in level E\n")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for book_dir in book_dirs:
        build_book(book_dir)

    print(f"\nDone. Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
