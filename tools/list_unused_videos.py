#!/usr/bin/env python3
"""List all video files that are not matched to any book."""

import json
import re
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
    name = re.sub(r"^\d+\s*", "", name)
    name = re.sub(r"[^a-z0-9]", "", name)
    return name


def normalize_keep_numbers(name: str) -> str:
    """Normalize but keep numbers."""
    name = clean_title(name)
    name = name.lower()
    name = re.sub(r"[^a-z0-9]", "", name)
    return name


def extract_video_info(filename: str):
    """Extract level and name from video filename."""
    orig_filename = filename
    filename = re.sub(r"[\u200b-\u200f\ufeff]", "", filename)
    filename = re.sub(r"[-\s]*公众号[^.]*", "", filename, flags=re.UNICODE)
    filename = re.sub(r"[\u4e00-\u9fa5]", "", filename)
    filename = filename.strip()

    match = re.match(r"^([a-z]+)-\d+(.+)\.mp4$", filename, re.IGNORECASE)
    if match:
        level = match.group(1).lower()
        name = match.group(2).strip()
        return level, name, orig_filename

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

        dir_level = level_match.group(1).lower()

        for video_file in level_dir.glob("*.mp4"):
            level, name, orig = extract_video_info(video_file.name)
            if level and name:
                all_videos.append({
                    'level': level,
                    'name': name,
                    'normalized': normalize_keep_numbers(name),
                    'normalized_no_num': normalize(name),
                    'filepath': str(video_file),
                    'filename': orig,
                    'dir_level': dir_level
                })

    print(f"共找到 {len(all_videos)} 个视频文件\n")

    print("=" * 100)
    print("扫描所有书籍...")
    print("=" * 100)

    # Scan all books with video
    books_with_video = []
    books_without_video = []

    for book_json in data_dir.rglob("book.json"):
        try:
            with open(book_json, "r", encoding="utf-8") as f:
                data = json.load(f)

            title = data.get("title", "")
            level = data.get("level", "").lower()
            video = data.get("video")

            book_info = {
                'level': level,
                'title': title,
                'normalized': normalize_keep_numbers(title),
                'normalized_no_num': normalize(title),
                'dirpath': str(book_json.parent),
                'dirname': book_json.parent.name
            }

            if video:
                books_with_video.append(book_info)
            else:
                books_without_video.append(book_info)

        except Exception as e:
            print(f"Error reading {book_json}: {e}")

    print(f"有视频的书籍: {len(books_with_video)}")
    print(f"无视频的书籍: {len(books_without_video)}\n")

    # Create book lookup by normalized names
    book_norms = set()
    book_norms_no_num = set()
    for book in books_with_video + books_without_video:
        book_norms.add((book['level'], book['normalized']))
        book_norms_no_num.add((book['level'], book['normalized_no_num']))

    # Find unmatched videos
    print("=" * 100)
    print("分析未匹配视频...")
    print("=" * 100)

    matched_videos = []
    unmatched_videos = []

    for video in all_videos:
        v_level_clean = video['level'].replace('z1', 'z').replace('z2', 'z')

        # Check if there's a book with same normalized name and level
        matched = False
        for b_level, b_norm in book_norms:
            if b_level == v_level_clean and b_norm == video['normalized']:
                matched = True
                break

        if not matched:
            # Try without numbers
            for b_level, b_norm in book_norms_no_num:
                if b_level == v_level_clean and b_norm == video['normalized_no_num']:
                    matched = True
                    break

        if matched:
            matched_videos.append(video)
        else:
            unmatched_videos.append(video)

    print(f"已匹配视频: {len(matched_videos)}")
    print(f"未匹配视频: {len(unmatched_videos)}\n")

    # Group unmatched videos by level
    unmatched_by_level = defaultdict(list)
    for video in unmatched_videos:
        unmatched_by_level[video['level']].append(video)

    # Print unmatched videos
    print("=" * 100)
    print(f"未匹配视频列表 (共 {len(unmatched_videos)} 个)")
    print("=" * 100)

    for level in sorted(unmatched_by_level.keys(), key=lambda x: (len(x), x)):
        videos = unmatched_by_level[level]
        print(f"\n【{level.upper()} 级】({len(videos)} 个):")
        print("-" * 80)
        for video in videos:
            print(f"  - {video['filename']}")
            print(f"    书名提取: {video['name']}")

    # Summary
    print("\n" + "=" * 100)
    print("汇总")
    print("=" * 100)
    print(f"视频文件总数: {len(all_videos)}")
    print(f"已匹配: {len(matched_videos)}")
    print(f"未匹配: {len(unmatched_videos)}")

    # Cross-level potential matches
    print("\n" + "=" * 100)
    print("跨级别潜在匹配 (视频存在但可能在其他级别)")
    print("=" * 100)

    # Find videos that could match books in other levels
    potential_cross = []
    for video in unmatched_videos:
        v_norm = video['normalized_no_num']
        v_level = video['level'].replace('z1', 'z').replace('z2', 'z')

        for book in books_without_video:
            if book['normalized_no_num'] == v_norm:
                if book['level'] != v_level:
                    potential_cross.append((video, book))

    if potential_cross:
        print(f"\n找到 {len(potential_cross)} 个跨级别潜在匹配:\n")
        for video, book in potential_cross[:20]:
            print(f"视频: [{video['level'].upper()}] {video['name']}")
            print(f"书籍: [{book['level'].upper()}] {book['title']}")
            print()
    else:
        print("\n没有发现跨级别匹配")


if __name__ == "__main__":
    main()
