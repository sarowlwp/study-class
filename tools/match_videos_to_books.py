#!/usr/bin/env python3
"""Match videos to books by extracting titles and comparing normalized forms."""

import json
import re
import shutil
from pathlib import Path
from collections import defaultdict


def clean_title(title: str) -> str:
    """Clean title by removing Chinese advertisement suffixes and zero-width chars."""
    title = re.sub(r"[\u200b-\u200f\ufeff]", "", title)
    title = re.sub(r"[-\s]*公众号[^.]*", "", title, flags=re.UNICODE)
    title = re.sub(r"[\u4e00-\u9fa5].*$", "", title)
    return title.strip()


def normalize(name: str) -> str:
    """Normalize name for matching."""
    name = clean_title(name)
    name = name.lower()
    name = re.sub(r"^\d+\s*", "", name)  # Remove leading numbers
    name = re.sub(r"[^a-z0-9]", "", name)
    return name


def extract_video_info(filename: str):
    """Extract level and name from video filename."""
    orig_filename = filename
    filename = re.sub(r"[\u200b-\u200f\ufeff]", "", filename)
    filename = re.sub(r"[-\s]*公众号[^.]*", "", filename, flags=re.UNICODE)
    filename = re.sub(r"[\u4e00-\u9fa5]", "", filename)
    filename = filename.strip()

    # Pattern 1: {level}-{number}{name}.mp4 (AA-G级别)
    match = re.match(r"^([a-z]+)-\d+(.+)\.mp4$", filename, re.IGNORECASE)
    if match:
        level = match.group(1).lower()
        name = match.group(2).strip()
        return level, name, orig_filename

    # Pattern 2: 'Reading AZ Level X {name}.mp4' (H-Z级别)
    match = re.match(r"^Reading AZ Level ([A-Z]+\d*)\.?\s*(.+)\.mp4$", filename, re.IGNORECASE)
    if match:
        level = match.group(1).lower()
        name = match.group(2).strip()
        return level, name, orig_filename

    return None, None, orig_filename


def main():
    data_dir = Path("/Users/sarowlwp/Document/go/study-class/data/raz")
    video_base = Path("/Users/sarowlwp/Document/go/study-class/raz-resourcer/RAZ视频")

    print("=" * 100)
    print("扫描所有视频文件...")
    print("=" * 100)

    # Scan all videos
    all_videos = []
    for level_dir in video_base.iterdir():
        if not level_dir.is_dir():
            continue

        level_match = re.match(r"^([a-z]+\d*)级", level_dir.name, re.IGNORECASE)
        if not level_match:
            continue

        for video_file in level_dir.glob("*.mp4"):
            level, name, orig = extract_video_info(video_file.name)
            if level and name:
                all_videos.append({
                    'level': level,
                    'name': name,
                    'normalized': normalize(name),
                    'filepath': str(video_file),
                    'filename': orig
                })

    print(f"共找到 {len(all_videos)} 个视频文件\n")

    print("=" * 100)
    print("扫描所有书籍 (无视频)...")
    print("=" * 100)

    # Scan all books without video
    books_without_video = []
    for book_json in data_dir.rglob("book.json"):
        try:
            with open(book_json, "r", encoding="utf-8") as f:
                data = json.load(f)

            if data.get("video") is None:
                title = data.get("title", "")
                level = data.get("level", "").lower()
                books_without_video.append({
                    'level': level,
                    'title': title,
                    'normalized': normalize(title),
                    'dirpath': str(book_json.parent),
                    'jsonpath': str(book_json)
                })
        except Exception as e:
            print(f"Error reading {book_json}: {e}")

    print(f"共找到 {len(books_without_video)} 本没有视频的书籍\n")

    # Create book lookup by (level, normalized)
    book_lookup = {}
    for book in books_without_video:
        key = (book['level'], book['normalized'])
        if key not in book_lookup:
            book_lookup[key] = []
        book_lookup[key].append(book)

    # Match videos to books
    print("=" * 100)
    print("匹配视频到书籍...")
    print("=" * 100)

    matched = []
    unmatched_videos = []

    for video in all_videos:
        v_level = video['level'].replace('z1', 'z').replace('z2', 'z')
        v_norm = video['normalized']

        key = (v_level, v_norm)
        if key in book_lookup and book_lookup[key]:
            book = book_lookup[key].pop(0)  # Use first match
            matched.append((video, book))
        else:
            unmatched_videos.append(video)

    print(f"\n匹配成功: {len(matched)} 对")
    print(f"未匹配视频: {len(unmatched_videos)}\n")

    # Show matched samples
    if matched:
        print("=" * 100)
        print("匹配成功的示例 (前20个):")
        print("=" * 100)
        for video, book in matched[:20]:
            print(f"\n视频: [{video['level'].upper()}] {video['filename']}")
            print(f"  提取书名: {video['name']}")
            print(f"书籍: [{book['level'].upper()}] {book['title']}")
            print(f"  目录: {book['dirpath']}")

    # Show unmatched videos
    if unmatched_videos:
        print("\n" + "=" * 100)
        print(f"未匹配视频 (共 {len(unmatched_videos)} 个)")
        print("=" * 100)

        # Group by level
        unmatched_by_level = defaultdict(list)
        for video in unmatched_videos:
            unmatched_by_level[video['level']].append(video)

        for level in sorted(unmatched_by_level.keys(), key=lambda x: (len(x), x)):
            videos = unmatched_by_level[level]
            print(f"\n【{level.upper()} 级】({len(videos)} 个):")
            for video in videos[:5]:  # Show first 5
                print(f"  - {video['filename']}")
                print(f"    提取: {video['name']} (normalized: {video['normalized']})")
            if len(videos) > 5:
                print(f"    ... 还有 {len(videos) - 5} 个")

    # Apply fixes
    if matched:
        print("\n" + "=" * 100)
        print("应用修复...")
        print("=" * 100)

        fixed = 0
        for video, book in matched:
            try:
                dest = Path(book['dirpath']) / "video.mp4"
                shutil.copy2(video['filepath'], dest)

                # Update book.json
                with open(book['jsonpath'], "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["video"] = "video.mp4"
                with open(book['jsonpath'], "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                fixed += 1
                if fixed <= 10:
                    print(f"✓ [{book['level'].upper()}] {book['title']}")
            except Exception as e:
                print(f"  ERROR: {e}")

        print(f"\n已修复: {fixed} 本书")


if __name__ == "__main__":
    main()
