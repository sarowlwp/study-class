#!/usr/bin/env python3
"""Fix videos using pattern-based name corrections."""

import json
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def clean_title(title: str) -> str:
    """Clean title by removing Chinese advertisement suffixes."""
    title = re.sub(r"[-\s]*公众号.*$", "", title, flags=re.UNICODE)
    title = re.sub(r"[\u4e00-\u9fa5].*$", "", title)
    return title.strip()


def normalize_name(name: str) -> str:
    """Normalize name for matching."""
    name = clean_title(name)
    name = name.lower()
    name = re.sub(r"[^a-z0-9\s]", "", name)
    name = name.replace(" ", "")
    return name.strip()


def extract_video_name(filename: str) -> Optional[str]:
    """Extract book name from video filename."""
    filename = re.sub(r"[-\s]*公众号.*$", "", filename, flags=re.UNICODE)
    filename = re.sub(r"[\u4e00-\u9fa5].*$", "", filename)
    filename = filename.strip()

    match = re.match(r"^[a-z]+-\d+(.+)\.mp4$", filename, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    match = re.match(r"^Reading AZ Level [A-Z]+\.\s*(.+)\.mp4$", filename, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return None


def generate_name_variations(name: str) -> List[str]:
    """Generate possible variations of a book name."""
    variations = [name]
    clean = clean_title(name)

    # Pattern 1: CamelCase to words (Pipthe -> Pip the)
    # Add spaces before capital letters
    spaced = re.sub(r'([a-z])([A-Z])', r'\1 \2', clean)
    if spaced != clean:
        variations.append(spaced)

    # Pattern 2: Remove leading numbers (25 George -> George)
    no_numbers = re.sub(r'^\d+\s*', '', clean)
    if no_numbers != clean:
        variations.append(no_numbers)

    # Pattern 3: Handle common word separators
    for sep in ['', ' ', '-']:
        variations.append(clean.replace(' ', sep))

    return list(set(variations))


def scan_videos(video_base: Path) -> Dict[str, List[Tuple[str, Path, str]]]:
    """Scan all video files and index by multiple normalized forms."""
    videos = {}  # normalized_name -> [(level, path, original_name)]

    for level_dir in video_base.iterdir():
        if not level_dir.is_dir():
            continue

        level_match = re.match(r"^([a-z]+)级", level_dir.name, re.IGNORECASE)
        if not level_match:
            continue

        level = level_match.group(1).lower()

        for video_file in level_dir.glob("*.mp4"):
            video_name = extract_video_name(video_file.name)
            if video_name:
                # Index by multiple variations
                variations = generate_name_variations(video_name)
                for var in variations:
                    normalized = normalize_name(var)
                    if normalized not in videos:
                        videos[normalized] = []
                    videos[normalized].append((level, video_file, video_name))

    return videos


def scan_books(data_dir: Path) -> List[Tuple[Path, dict]]:
    """Scan all books without video."""
    books = []

    for book_json in data_dir.rglob("book.json"):
        try:
            with open(book_json, "r", encoding="utf-8") as f:
                data = json.load(f)

            if data.get("video") is None:
                books.append((book_json, data))
        except Exception as e:
            print(f"Error reading {book_json}: {e}")

    return books


def find_match(book_title: str, book_level: str, videos: Dict[str, List[Tuple[str, Path, str]]]) -> Optional[Tuple[Path, str]]:
    """Find matching video using multiple name variations."""
    variations = generate_name_variations(book_title)

    for var in variations:
        normalized = normalize_name(var)
        if normalized in videos:
            matches = videos[normalized]
            # Prefer same level
            for level, path, orig in matches:
                if level.lower() == book_level.lower():
                    return (path, orig)
            # Otherwise return first
            return (matches[0][1], matches[0][2])

    return None


def match_and_fix_videos(
    books: List[Tuple[Path, dict]],
    videos: Dict[str, List[Tuple[str, Path, str]]],
    dry_run: bool = True
) -> Tuple[int, int]:
    """Match books with videos and fix them."""
    matched = 0
    fixed = 0

    for book_json, book_data in books:
        book_title = book_data.get("title", "")
        book_level = book_data.get("level", "").lower()
        book_dir = book_json.parent

        match = find_match(book_title, book_level, videos)

        if match:
            video_path, video_name = match
            matched += 1
            print(f"✓ Match: [{book_level.upper()}] {book_title}")
            print(f"  Video name: {video_name}")
            print(f"  Book: {book_dir}")
            print(f"  Video: {video_path}")

            if not dry_run:
                try:
                    dest = book_dir / "video.mp4"
                    shutil.copy2(video_path, dest)
                    print(f"  Copied: {dest}")

                    book_data["video"] = "video.mp4"
                    with open(book_json, "w", encoding="utf-8") as f:
                        json.dump(book_data, f, indent=2, ensure_ascii=False)
                    print(f"  Updated: {book_json}")
                    fixed += 1
                except Exception as e:
                    print(f"  ERROR: {e}")
            print()

    return matched, fixed


def main():
    data_dir = Path("/Users/sarowlwp/Document/go/study-class/data/raz")
    video_base = Path("/Users/sarowlwp/Document/go/study-class/raz-resourcer/RAZ视频")

    print("=" * 60)
    print("Scanning video files with variations...")
    print("=" * 60)
    videos = scan_videos(video_base)
    print(f"Found {len(videos)} unique video name keys\n")

    print("=" * 60)
    print("Scanning books without video...")
    print("=" * 60)
    books = scan_books(data_dir)
    print(f"Found {len(books)} books without video\n")

    print("=" * 60)
    print("Matching with pattern variations...")
    print("=" * 60)
    matched, _ = match_and_fix_videos(books, videos, dry_run=True)
    print(f"\nMatched: {matched} books\n")

    if matched > 0:
        print("\n" + "=" * 60)
        print("Applying fixes...")
        print("=" * 60)
        _, fixed = match_and_fix_videos(books, videos, dry_run=False)
        print(f"\nFixed: {fixed} books")


if __name__ == "__main__":
    main()
