#!/usr/bin/env python3
"""Fix missing videos by matching book.json with video files."""

import json
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def clean_title(title: str) -> str:
    """Clean title by removing Chinese advertisement suffixes and zero-width chars."""
    # Remove zero-width characters
    title = re.sub(r"[\u200b-\u200f\ufeff]", "", title)
    # Remove Chinese suffixes like "-公众号-Lily的育儿百宝箱(...)"
    title = re.sub(r"[-\s]*公众号.*$", "", title, flags=re.UNICODE)
    # Remove standalone Chinese characters at the end
    title = re.sub(r"[\u4e00-\u9fa5].*$", "", title)
    return title.strip()


def normalize_name(name: str) -> str:
    """Normalize name for matching."""
    # First clean the name
    name = clean_title(name)
    # Convert to lowercase
    name = name.lower()
    # Remove non-alphanumeric characters except spaces
    name = re.sub(r"[^a-z0-9\s]", "", name)
    # Remove all spaces for loose matching
    name = name.replace(" ", "")
    return name.strip()


def extract_video_name(filename: str) -> Optional[str]:
    """Extract book name from video filename.

    Supports formats:
    - 'AA-01Farm Animals.mp4' -> 'Farm Animals'
    - 'H-01 A Desert Counting Book-公众号....mp4' -> 'A Desert Counting Book'
    - 'Reading AZ Level I. A Broken Leg for Bonk.mp4' -> 'A Broken Leg for Bonk'
    """
    # Remove zero-width characters
    filename = re.sub(r"[\u200b-\u200f\ufeff]", "", filename)
    # First, clean up Chinese ads from filename (but stop before .mp4)
    filename = re.sub(r"[-\s]*公众号[^.]*", "", filename, flags=re.UNICODE)
    # Remove standalone Chinese characters
    filename = re.sub(r"[\u4e00-\u9fa5]", "", filename)
    filename = filename.strip()

    # Pattern 1: {level}-{number}{name}.mp4 (AA-G级别)
    match = re.match(r"^[a-z]+-\d+(.+)\.mp4$", filename, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Pattern 2: 'Reading AZ Level X {name}.mp4' (H-Z级别) - note: no dot after level
    match = re.match(r"^Reading AZ Level [A-Z]+\s*\.?\s*(.+)\.mp4$", filename, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return None


def scan_videos(video_base: Path) -> Dict[str, List[Tuple[str, Path]]]:
    """Scan all video files and index by normalized name."""
    videos = {}  # normalized_name -> [(level, path)]

    if not video_base.exists():
        print(f"Video base directory not found: {video_base}")
        return videos

    for level_dir in video_base.iterdir():
        if not level_dir.is_dir():
            continue

        # Extract level from directory name
        # Patterns: "AA级视频", "H级-视频", "Level I", "Level K(1)"
        level = None
        dir_name = level_dir.name

        # Pattern 1: Chinese format like "AA级视频", "H级-视频"
        level_match = re.match(r"^([a-z]+)级", dir_name, re.IGNORECASE)
        if level_match:
            level = level_match.group(1).lower()
        else:
            # Pattern 2: English format like "Level I", "Level K(1)"
            level_match = re.match(r"^Level\s+([a-z]+\d?)", dir_name, re.IGNORECASE)
            if level_match:
                level = level_match.group(1).lower()

        if not level:
            continue

        for video_file in level_dir.glob("*.mp4"):
            video_name = extract_video_name(video_file.name)
            if video_name:
                normalized = normalize_name(video_name)
                if normalized not in videos:
                    videos[normalized] = []
                videos[normalized].append((level, video_file))

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


def match_and_fix_videos(
    books: List[Tuple[Path, dict]],
    videos: Dict[str, List[Tuple[str, Path]]],
    dry_run: bool = True
) -> Tuple[int, int]:
    """Match books with videos and fix them."""
    matched = 0
    fixed = 0

    for book_json, book_data in books:
        book_title = book_data.get("title", "")
        book_level = book_data.get("level", "").lower()
        book_dir = book_json.parent

        # Normalize book title for matching
        normalized_title = normalize_name(book_title)

        # Try exact match
        video_matches = videos.get(normalized_title, [])

        # Filter by level if possible
        level_match = None
        for level, path in video_matches:
            if level.lower() == book_level:
                level_match = path
                break

        # If no level match, use first available
        if not level_match and video_matches:
            level_match = video_matches[0][1]

        if level_match:
            matched += 1
            print(f"✓ Match: [{book_level.upper()}] {book_title}")
            print(f"  Book: {book_dir}")
            print(f"  Video: {level_match}")

            if not dry_run:
                try:
                    # Copy video
                    dest = book_dir / "video.mp4"
                    shutil.copy2(level_match, dest)
                    print(f"  Copied: {dest}")

                    # Update book.json
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
    print("Scanning video files...")
    print("=" * 60)
    videos = scan_videos(video_base)
    print(f"Found {len(videos)} unique video names\n")

    print("=" * 60)
    print("Scanning books without video...")
    print("=" * 60)
    books = scan_books(data_dir)
    print(f"Found {len(books)} books without video\n")

    print("=" * 60)
    print("Matching (dry run)...")
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
