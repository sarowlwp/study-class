#!/usr/bin/env python3
"""Comprehensive matching check between books and videos."""

import json
import re
from pathlib import Path
from collections import defaultdict
from difflib import SequenceMatcher


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


def normalize_keep_numbers(name: str) -> str:
    """Normalize but keep numbers."""
    name = clean_title(name)
    name = name.lower()
    name = re.sub(r"[^a-z0-9]", "", name)
    return name


def similarity(a: str, b: str) -> float:
    """Calculate similarity between two strings."""
    return SequenceMatcher(None, a, b).ratio()


def extract_video_name(filename: str):
    """Extract book name and level from video filename."""
    orig_filename = filename
    # Remove zero-width characters
    filename = re.sub(r"[\u200b-\u200f\ufeff]", "", filename)
    # Remove Chinese ads
    filename = re.sub(r"[-\s]*公众号[^.]*", "", filename, flags=re.UNICODE)
    # Remove Chinese characters
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

    # Scan all videos
    print("=" * 100)
    print("扫描所有视频文件...")
    print("=" * 100)

    videos = []  # (level, name, normalized, normalized_no_num, filepath)
    for level_dir in video_base.iterdir():
        if not level_dir.is_dir():
            continue

        for video_file in level_dir.glob("*.mp4"):
            level, name, orig = extract_video_name(video_file.name)
            if level and name:
                videos.append({
                    'level': level,
                    'name': name,
                    'normalized': normalize_keep_numbers(name),
                    'normalized_no_num': normalize(name),
                    'filepath': str(video_file),
                    'filename': orig
                })

    print(f"共找到 {len(videos)} 个视频文件\n")

    # Scan all books without video
    print("=" * 100)
    print("扫描所有没有视频的书籍...")
    print("=" * 100)

    books = []  # (level, title, normalized, normalized_no_num, dirpath)
    for book_json in data_dir.rglob("book.json"):
        try:
            with open(book_json, "r", encoding="utf-8") as f:
                data = json.load(f)

            if data.get("video") is None:
                title = data.get("title", "")
                level = data.get("level", "").lower()
                books.append({
                    'level': level,
                    'title': title,
                    'normalized': normalize_keep_numbers(title),
                    'normalized_no_num': normalize(title),
                    'dirpath': str(book_json.parent),
                    'dirname': book_json.parent.name
                })
        except Exception as e:
            print(f"Error reading {book_json}: {e}")

    print(f"共找到 {len(books)} 本没有视频的书籍\n")

    # Create video lookup
    video_by_norm = defaultdict(list)
    video_by_norm_no_num = defaultdict(list)
    for v in videos:
        video_by_norm[v['normalized']].append(v)
        video_by_norm_no_num[v['normalized_no_num']].append(v)

    # Matching analysis
    print("=" * 100)
    print("详细匹配分析")
    print("=" * 100)

    exact_matches = []
    number_prefix_matches = []
    similar_matches = []
    no_match = []

    for book in books:
        b_level = book['level']
        b_title = book['title']
        b_norm = book['normalized']
        b_norm_no_num = book['normalized_no_num']

        # Check 1: Exact normalized match (same level)
        matched = False
        if b_norm in video_by_norm:
            for v in video_by_norm[b_norm]:
                v_level_clean = v['level'].replace('z1', 'z').replace('z2', 'z')
                if v_level_clean == b_level:
                    exact_matches.append((book, v))
                    matched = True
                    break

        if matched:
            continue

        # Check 2: Number prefix match (book has number, video doesn't)
        if b_norm_no_num in video_by_norm_no_num and b_norm_no_num != b_norm:
            for v in video_by_norm_no_num[b_norm_no_num]:
                v_level_clean = v['level'].replace('z1', 'z').replace('z2', 'z')
                if v_level_clean == b_level:
                    number_prefix_matches.append((book, v))
                    matched = True
                    break

        if matched:
            continue

        # Check 3: Similarity match (> 0.8)
        best_sim = 0
        best_video = None
        for v in videos:
            sim = similarity(b_norm_no_num, v['normalized_no_num'])
            if sim > best_sim:
                best_sim = sim
                best_video = v

        if best_sim > 0.8:
            similar_matches.append((book, best_video, best_sim))
            continue

        # No match
        no_match.append(book)

    # Print results
    print(f"\n【1】完全匹配 (Exact): {len(exact_matches)} 本")
    print("-" * 100)
    for book, video in exact_matches[:5]:
        print(f"[{book['level'].upper()}] {book['title']}")
        print(f"  -> 视频: [{video['level'].upper()}] {video['name']}")
    if len(exact_matches) > 5:
        print(f"  ... 还有 {len(exact_matches) - 5} 个")

    print(f"\n【2】数字前缀匹配 (Number prefix): {len(number_prefix_matches)} 本")
    print("-" * 100)
    for book, video in number_prefix_matches[:10]:
        print(f"[{book['level'].upper()}] {book['title']}")
        print(f"  -> 视频: [{video['level'].upper()}] {video['name']}")
    if len(number_prefix_matches) > 10:
        print(f"  ... 还有 {len(number_prefix_matches) - 10} 个")

    print(f"\n【3】相似匹配 (Similarity > 0.8): {len(similar_matches)} 本")
    print("-" * 100)
    for book, video, sim in sorted(similar_matches, key=lambda x: -x[2])[:10]:
        print(f"[{book['level'].upper()}] {book['title']}")
        print(f"  -> 视频: [{video['level'].upper()}] {video['name']} (相似度: {sim:.2f})")
    if len(similar_matches) > 10:
        print(f"  ... 还有 {len(similar_matches) - 10} 个")

    print(f"\n【4】无匹配 (No match): {len(no_match)} 本")
    print("-" * 100)

    # Group by level
    no_match_by_level = defaultdict(list)
    for book in no_match:
        no_match_by_level[book['level']].append(book)

    for level in sorted(no_match_by_level.keys(), key=lambda x: (len(x), x)):
        books_in_level = no_match_by_level[level]
        print(f"\n{level.upper()} 级 ({len(books_in_level)} 本):")
        for book in books_in_level:
            print(f"  - {book['title']}")
            print(f"    (normalized: {book['normalized_no_num']})")

    # Summary
    print("\n" + "=" * 100)
    print("汇总")
    print("=" * 100)
    print(f"视频文件总数: {len(videos)}")
    print(f"无视频书籍总数: {len(books)}")
    print(f"  - 完全匹配: {len(exact_matches)}")
    print(f"  - 数字前缀匹配: {len(number_prefix_matches)}")
    print(f"  - 相似匹配: {len(similar_matches)}")
    print(f"  - 无匹配: {len(no_match)}")


if __name__ == "__main__":
    main()
