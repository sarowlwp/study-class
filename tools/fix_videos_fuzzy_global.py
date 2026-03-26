#!/usr/bin/env python3
"""Fuzzy global video matching using substring and word-level matching."""

import json
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher


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


def get_words(name: str) -> set:
    """Extract significant words from name (longer than 3 chars)."""
    name = clean_title(name).lower()
    words = re.findall(r'[a-z]{4,}', name)
    return set(words)


def similarity(a: str, b: str) -> float:
    """Calculate similarity between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


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


def scan_videos(video_base: Path) -> List[Tuple[str, Path, str, set]]:
    """Scan all video files and return list of (normalized, path, original, words)."""
    videos = []

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
                normalized = normalize_name(video_name)
                words = get_words(video_name)
                videos.append((normalized, video_file, video_name, words, level))

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


def find_fuzzy_match(book_title: str, book_level: str, videos: List[Tuple[str, Path, str, set, str]]) -> Optional[Tuple[Path, str, str, float]]:
    """Find matching video using fuzzy matching strategies."""
    normalized_title = normalize_name(book_title)
    book_words = get_words(book_title)

    best_match = None
    best_score = 0.0

    for norm_video, path, orig, words, level in videos:
        score = 0.0

        # Strategy 1: Exact normalized match
        if norm_video == normalized_title:
            score = 1.0
        # Strategy 2: Substring match (book name is part of video name or vice versa)
        elif normalized_title in norm_video or norm_video in normalized_title:
            min_len = min(len(normalized_title), len(norm_video))
            max_len = max(len(normalized_title), len(norm_video))
            score = 0.8 * (min_len / max_len)
        # Strategy 3: Word overlap
        elif book_words and words:
            common = book_words & words
            if common:
                score = 0.6 * (len(common) / max(len(book_words), len(words)))
        # Strategy 4: Similarity ratio for similar lengths
        elif abs(len(norm_video) - len(normalized_title)) < 10:
            sim = similarity(normalized_title, norm_video)
            if sim > 0.7:
                score = sim * 0.5

        # Boost score if levels match
        level_match = level.lower().replace("z1", "z").replace("z2", "z") == book_level.lower()
        if level_match:
            score += 0.15

        if score > best_score and score >= 0.65:
            best_score = score
            best_match = (path, orig, level, score)

    return best_match


def match_and_fix_videos(
    books: List[Tuple[Path, dict]],
    videos: List[Tuple[str, Path, str, set, str]],
    dry_run: bool = True
) -> Tuple[int, int, int]:
    """Match books with videos and fix them."""
    matched_same_level = 0
    matched_cross_level = 0
    fixed = 0

    for book_json, book_data in books:
        book_title = book_data.get("title", "")
        book_level = book_data.get("level", "").lower()
        book_dir = book_json.parent

        match = find_fuzzy_match(book_title, book_level, videos)

        if match:
            video_path, video_name, video_level, score = match
            is_same_level = video_level.lower().replace("z1", "z").replace("z2", "z") == book_level.lower()

            if is_same_level:
                matched_same_level += 1
                level_indicator = f"[{book_level.upper()}]"
            else:
                matched_cross_level += 1
                level_indicator = f"[{book_level.upper()} <- {video_level.upper()}]"

            print(f"✓ Match ({score:.2f}): {level_indicator} {book_title}")
            print(f"  Video: {video_name}")
            print(f"  Book: {book_dir.name}")

            if not dry_run:
                try:
                    dest = book_dir / "video.mp4"
                    shutil.copy2(video_path, dest)
                    print(f"  -> Copied to: {dest}")

                    book_data["video"] = "video.mp4"
                    with open(book_json, "w", encoding="utf-8") as f:
                        json.dump(book_data, f, indent=2, ensure_ascii=False)
                    fixed += 1
                except Exception as e:
                    print(f"  ERROR: {e}")
            print()

    return matched_same_level, matched_cross_level, fixed


def main():
    data_dir = Path("/Users/sarowlwp/Document/go/study-class/data/raz")
    video_base = Path("/Users/sarowlwp/Document/go/study-class/raz-resourcer/RAZ视频")

    print("=" * 70)
    print("Fuzzy Global Video Matching")
    print("=" * 70)
    print()

    print("Scanning video files...")
    videos = scan_videos(video_base)
    print(f"Found {len(videos)} videos")
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
    else:
        print("\nNo matches found.")


if __name__ == "__main__":
    main()
