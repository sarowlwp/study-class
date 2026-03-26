#!/usr/bin/env python3
"""Analyze unmatched books to find why they didn't match."""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set


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


def scan_videos(video_base: Path) -> Set[str]:
    """Scan all video names."""
    video_names = set()

    for level_dir in video_base.iterdir():
        if not level_dir.is_dir():
            continue

        level_match = re.match(r"^([a-z]+)级", level_dir.name, re.IGNORECASE)
        if not level_match:
            continue

        for video_file in level_dir.glob("*.mp4"):
            video_name = extract_video_name(video_file.name)
            if video_name:
                video_names.add(normalize_name(video_name))

    return video_names


def analyze_unmatched(data_dir: Path, video_names: Set[str]) -> Dict[str, List[str]]:
    """Analyze books that don't match any video."""
    unmatched_by_level = {}

    for book_json in data_dir.rglob("book.json"):
        try:
            with open(book_json, "r", encoding="utf-8") as f:
                data = json.load(f)

            if data.get("video") is None:
                title = data.get("title", "")
                level = data.get("level", "").lower()
                normalized = normalize_name(title)

                if normalized not in video_names:
                    if level not in unmatched_by_level:
                        unmatched_by_level[level] = []
                    unmatched_by_level[level].append({
                        "title": title,
                        "normalized": normalized
                    })
        except Exception as e:
            pass

    return unmatched_by_level


def main():
    data_dir = Path("/Users/sarowlwp/Document/go/study-class/data/raz")
    video_base = Path("/Users/sarowlwp/Document/go/study-class/raz-resourcer/RAZ视频")

    print("Scanning video names...")
    video_names = scan_videos(video_base)
    print(f"Found {len(video_names)} unique video names\n")

    print("Analyzing unmatched books...")
    unmatched = analyze_unmatched(data_dir, video_names)

    total_unmatched = sum(len(books) for books in unmatched.values())
    print(f"\nTotal unmatched: {total_unmatched}\n")

    # Show samples by level
    for level in sorted(unmatched.keys()):
        books = unmatched[level]
        print(f"\nLevel {level.upper()}: {len(books)} unmatched")
        for book in books[:5]:  # Show first 5
            print(f"  - {book['title']}")
            print(f"    (normalized: {book['normalized']})")


if __name__ == "__main__":
    main()
