#!/usr/bin/env python3
"""Global video matching across all levels - find misplaced videos."""

import json
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def clean_title(title: str) -> str:
    """Clean title by removing Chinese advertisement suffixes and zero-width chars."""
    title = re.sub(r"[\u200b-\u200f\ufeff]", "", title)
    title = re.sub(r"[-\s]*公众号[^.]*", "", title, flags=re.UNICODE)
    title = re.sub(r"[\u4e00-\u9fa5].*$", "", title)
    return title.strip()


def normalize_name(name: str) -> str:
    """Normalize name for matching."""
    name = clean_title(name)
    name = name.lower()
    name = re.sub(r"[^a-z0-9\s]", "", name)
    name = name.replace(" ", "")
    return name.strip()


def normalize_without_numbers(name: str) -> str:
    """Normalize name and remove leading numbers."""
    name = normalize_name(name)
    name = re.sub(r"^\d+", "", name)
    return name.strip()


def extract_video_name(filename: str) -> Optional[str]:
    """Extract book name from video filename."""
    filename = re.sub(r"[\u200b-\u200f\ufeff]", "", filename)
    filename = re.sub(r"[-\s]*公众号[^.]*", "", filename, flags=re.UNICODE)
    filename = re.sub(r"[\u4e00-\u9fa5]", "", filename)
    filename = filename.strip()

    match = re.match(r"^[a-z]+-\d+(.+)\.mp4$", filename, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    match = re.match(r"^Reading AZ Level [A-Z]+\s*\.?\s*(.+)\.mp4$", filename, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return None


def scan_videos(video_base: Path) -> Dict[str, List[Tuple[str, Path, str]]]:
    """Scan all video files and index by normalized name."""
    videos = {}

    if not video_base.exists():
        print(f"Video base directory not found: {video_base}")
        return videos

    for level_dir in video_base.iterdir():
        if not level_dir.is_dir():
            continue

        level_match = re.match(r"^([a-z]+\d*)级", level_dir.name, re.IGNORECASE)
        if not level_match:
            continue

        level = level_match.group(1).lower()

        for video_file in level_dir.glob("*.mp4"):
            video_name = extract_video_name(video_file.name)
            if video_name:
                # Index by multiple variations
                for key_func in [normalize_name, normalize_without_numbers]:
                    key = key_func(video_name)
                    if key not in videos:
                        videos[key] = []
                    videos[key].append((level, video_file, video_name))

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


def find_global_match(book_title: str, book_level: str, videos: Dict[str, List[Tuple[str, Path, str]]]) -> Optional[Tuple[Path, str, str]]:
    """Find matching video globally across all levels."""
    # Try exact normalized match
    normalized_title = normalize_name(book_title)
    normalized_no_nums = normalize_without_numbers(book_title)

    for key in [normalized_title, normalized_no_nums]:
        if key in videos:
            matches = videos[key]
            # First try same level
            for level, path, orig in matches:
                if level.lower().replace("z1", "z").replace("z2", "z") == book_level.lower():
                    return (path, orig, level)
            # If no same level, return first (with different level)
            return (matches[0][1], matches[0][2], matches[0][0])

    return None


def match_and_fix_videos(
    books: List[Tuple[Path, dict]],
    videos: Dict[str, List[Tuple[str, Path, str]]],
    dry_run: bool = True
) -> Tuple[int, int, int]:
    """Match books with videos globally and fix them."""
    matched_same_level = 0
    matched_cross_level = 0
    fixed = 0

    for book_json, book_data in books:
        book_title = book_data.get("title", "")
        book_level = book_data.get("level", "").lower()
        book_dir = book_json.parent

        match = find_global_match(book_title, book_level, videos)

        if match:
            video_path, video_name, video_level = match
            is_same_level = video_level.lower().replace("z1", "z").replace("z2", "z") == book_level.lower()

            if is_same_level:
                matched_same_level += 1
                level_indicator = f"[{book_level.upper()}]"
            else:
                matched_cross_level += 1
                level_indicator = f"[{book_level.upper()} <- {video_level.upper()}]"

            print(f"✓ Match: {level_indicator} {book_title}")
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

    return matched_same_level, matched_cross_level, fixed


def main():
    data_dir = Path("/Users/sarowlwp/Document/go/study-class/data/raz")
    video_base = Path("/Users/sarowlwp/Document/go/study-class/raz-resourcer/RAZ视频")

    print("=" * 70)
    print("Global Video Matching (Cross-Level)")
    print("=" * 70)
    print()

    print("Scanning video files...")
    videos = scan_videos(video_base)
    print(f"Found {len(videos)} unique video name keys")
    print()

    print("Scanning books without video...")
    books = scan_books(data_dir)
    print(f"Found {len(books)} books without video")
    print()

    print("=" * 70)
    print("Matching (dry run)...")
    print("=" * 70)
    same_level, cross_level, _ = match_and_fix_videos(books, videos, dry_run=True)
    print(f"\nMatched same level: {same_level}")
    print(f"Matched cross level: {cross_level}")
    print(f"Total matched: {same_level + cross_level}\n")

    if same_level + cross_level > 0:
        print("=" * 70)
        print("Applying fixes...")
        print("=" * 70)
        _, _, fixed = match_and_fix_videos(books, videos, dry_run=False)
        print(f"\nFixed: {fixed} books")


if __name__ == "__main__":
    main()
