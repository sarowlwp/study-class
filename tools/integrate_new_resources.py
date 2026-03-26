#!/usr/bin/env python3
"""Scan and count new resources from extracted archives."""

import json
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict


def normalize_name(name: str) -> str:
    """Normalize name for matching."""
    name = re.sub(r"[\u200b-\u200f\ufeff]", "", name)
    name = re.sub(r"[-\s]*公众号[^.]*", "", name, flags=re.UNICODE)
    name = re.sub(r"[\u4e00-\u9fa5].*$", "", name)
    name = name.lower()
    name = re.sub(r"[^a-z0-9]", "", name)
    return name


def scan_new_resources(base_dir: Path) -> Dict[str, Dict[str, List[Path]]]:
    """Scan all PDF and MP3 files in new resource directories."""
    resources = defaultdict(lambda: {"pdf": [], "mp3": []})

    # Scan all PDF files
    for pdf_file in base_dir.rglob("*.pdf"):
        # Skip if in processed data directory
        if "data/raz" in str(pdf_file):
            continue
        level = extract_level_from_path(pdf_file)
        if level:
            resources[level]["pdf"].append(pdf_file)

    # Scan all MP3 files
    for mp3_file in base_dir.rglob("*.mp3"):
        if "data/raz" in str(mp3_file):
            continue
        level = extract_level_from_path(mp3_file)
        if level:
            resources[level]["mp3"].append(mp3_file)

    return dict(resources)


def extract_level_from_path(path: Path) -> str:
    """Extract level from file path."""
    path_str = str(path).lower()

    # Check parent directories for level indicator
    for part in path.parts:
        part_lower = part.lower()

        # Match patterns like "A级", "A-PDF", "A-MP3", "A[PDF][Mp3]"
        m = re.match(r'^([a-z]\d?)[\-_\[]', part_lower)
        if m:
            return m.group(1)

        # Match "aa", "z1", "z2" as standalone level dirs
        if part_lower in ['aa', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i',
                          'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's',
                          't', 'u', 'v', 'w', 'x', 'y', 'z', 'z1', 'z2']:
            return part_lower

    return None


def scan_existing_books(data_dir: Path) -> Dict[str, List[dict]]:
    """Scan existing books by level."""
    books = defaultdict(list)

    for book_json in data_dir.rglob("book.json"):
        try:
            with open(book_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            level = data.get("level", "").lower()
            if level:
                data["_json_path"] = str(book_json)
                data["_dir_path"] = str(book_json.parent)
                books[level].append(data)
        except Exception as e:
            print(f"Error reading {book_json}: {e}")

    return dict(books)


def match_resources_to_books(
    resources: Dict[str, Dict[str, List[Path]]],
    books: Dict[str, List[dict]]
) -> Tuple[int, int, int]:
    """Match new resources to existing books and identify gaps."""
    matched = 0
    missing_books = defaultdict(list)  # level -> [(title, pdf, mp3)]
    unmatched_resources = defaultdict(list)  # level -> [(type, path)]

    for level, files in resources.items():
        level_books = books.get(level, [])
        book_titles = {normalize_name(b.get("title", "")): b for b in level_books}

        # Match PDFs
        for pdf_path in files["pdf"]:
            pdf_name = pdf_path.stem
            normalized = normalize_name(pdf_name)

            # Check if matches existing book
            matched_book = None
            for book_norm, book in book_titles.items():
                if normalized in book_norm or book_norm in normalized:
                    matched_book = book
                    break

            if matched_book:
                matched += 1
            else:
                # Check if has matching MP3
                mp3_match = None
                for mp3_path in files["mp3"]:
                    mp3_name = mp3_path.stem
                    if normalize_name(mp3_name) == normalized:
                        mp3_match = mp3_path
                        break

                missing_books[level].append({
                    "title": pdf_name,
                    "pdf": pdf_path,
                    "mp3": mp3_match
                })

    return matched, missing_books, unmatched_resources


def copy_new_books(missing_books: Dict[str, List[dict]], data_dir: Path) -> int:
    """Copy new books to data directory and create book.json."""
    created = 0

    for level, books in missing_books.items():
        level_dir = data_dir / f"level-{level}"
        level_dir.mkdir(parents=True, exist_ok=True)

        for book_info in books:
            title = book_info["title"]
            pdf_path = book_info["pdf"]
            mp3_path = book_info.get("mp3")

            # Create book slug from title
            slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
            if not slug:
                slug = f"book-{created}"

            book_dir = level_dir / slug

            # Check if directory already exists
            if book_dir.exists():
                # Check if book.json exists
                if (book_dir / "book.json").exists():
                    continue

            book_dir.mkdir(parents=True, exist_ok=True)

            # Copy PDF
            dest_pdf = book_dir / "book.pdf"
            if not dest_pdf.exists():
                shutil.copy2(pdf_path, dest_pdf)

            # Copy MP3 if available
            audio_file = "audio.mp3"
            if mp3_path:
                dest_mp3 = book_dir / "audio.mp3"
                if not dest_mp3.exists():
                    shutil.copy2(mp3_path, dest_mp3)
            else:
                audio_file = None

            # Create book.json
            book_data = {
                "id": f"level-{level}/{slug}",
                "title": title,
                "level": level,
                "pdf": "book.pdf",
                "video": None,
                "audio": audio_file,
                "sentences": []
            }

            with open(book_dir / "book.json", "w", encoding="utf-8") as f:
                json.dump(book_data, f, indent=2, ensure_ascii=False)

            created += 1
            if created <= 10:
                print(f"Created: [{level.upper()}] {title}")

    return created


def main():
    base_dir = Path("/Users/sarowlwp/Document/go/study-class/raz-resourcer")
    data_dir = Path("/Users/sarowlwp/Document/go/study-class/data/raz")

    print("=" * 70)
    print("Scanning new resources...")
    print("=" * 70)

    resources = scan_new_resources(base_dir)

    print("\nNew resources by level:")
    print("-" * 70)
    total_pdf = 0
    total_mp3 = 0
    for level in sorted(resources.keys(), key=lambda x: (len(x), x)):
        pdf_count = len(resources[level]["pdf"])
        mp3_count = len(resources[level]["mp3"])
        total_pdf += pdf_count
        total_mp3 += mp3_count
        print(f"{level.upper():<5}: {pdf_count:>4} PDFs, {mp3_count:>4} MP3s")

    print("-" * 70)
    print(f"{'Total':<5}: {total_pdf:>4} PDFs, {total_mp3:>4} MP3s")

    print("\n" + "=" * 70)
    print("Scanning existing books...")
    print("=" * 70)

    books = scan_existing_books(data_dir)
    total_books = sum(len(b) for b in books.values())
    print(f"Existing books: {total_books}")

    print("\n" + "=" * 70)
    print("Matching resources to books...")
    print("=" * 70)

    matched, missing_books, _ = match_resources_to_books(resources, books)
    print(f"Matched to existing: {matched}")

    new_books_count = sum(len(b) for b in missing_books.values())
    print(f"Potential new books: {new_books_count}")

    if missing_books:
        print("\nNew books by level:")
        print("-" * 70)
        for level in sorted(missing_books.keys(), key=lambda x: (len(x), x)):
            count = len(missing_books[level])
            with_mp3 = sum(1 for b in missing_books[level] if b["mp3"])
            print(f"{level.upper():<5}: {count:>4} books ({with_mp3} with MP3)")

        print("\n" + "=" * 70)
        print("Creating new books...")
        print("=" * 70)

        created = copy_new_books(missing_books, data_dir)
        print(f"\nCreated {created} new books")


if __name__ == "__main__":
    main()
