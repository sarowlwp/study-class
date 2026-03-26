#!/usr/bin/env python3
"""Match missing audio files from remaining resources."""

import json
import re
import shutil
from pathlib import Path
from collections import defaultdict
from difflib import SequenceMatcher


def normalize(name: str) -> str:
    """Normalize name for matching."""
    name = re.sub(r"[\u200b-\u200f\ufeff]", "", name)
    name = re.sub(r"[-\s]*公众号[^.]*", "", name, flags=re.UNICODE)
    name = re.sub(r"[\u4e00-\u9fa5].*$", "", name)
    name = name.lower()
    name = re.sub(r"[^a-z0-9]", "", name)
    return name


def similarity(a: str, b: str) -> float:
    """Calculate similarity between two strings."""
    return SequenceMatcher(None, a, b).ratio()


def scan_audio_by_level(base_dir: Path) -> dict:
    """Scan all remaining MP3 files organized by level."""
    audio_by_level = defaultdict(list)

    # Map directory patterns to levels
    level_patterns = {
        'aa': ['aa', 'AA'],
        'a': ['a', 'A'],
        'b': ['b', 'B'],
        'c': ['c', 'C'],
        'd': ['d', 'D'],
        'e': ['e', 'E'],
        'f': ['f', 'F'],
        'g': ['g', 'G'],
        'h': ['h', 'H'],
        'i': ['i', 'I'],
        'j': ['j', 'J'],
        'k': ['k', 'K'],
        'l': ['l', 'L'],
        'm': ['m', 'M'],
        'n': ['n', 'N'],
        'o': ['o', 'O'],
        'p': ['p', 'P'],
        'q': ['q', 'Q'],
        'r': ['r', 'R'],
        's': ['s', 'S'],
        't': ['t', 'T'],
        'u': ['u', 'U'],
        'v': ['v', 'V'],
        'w': ['w', 'W'],
        'x': ['x', 'X'],
        'y': ['y', 'Y'],
        'z': ['z', 'Z'],
        'z1': ['z1', 'Z1'],
        'z2': ['z2', 'Z2'],
    }

    # Scan all MP3 files
    for mp3_file in base_dir.rglob("*.mp3"):
        if "data/raz" in str(mp3_file):
            continue

        # Determine level from path
        path_str = str(mp3_file).lower()
        level = None

        # Check for level in path
        for lvl, patterns in level_patterns.items():
            for pattern in patterns:
                # Match patterns like "B-MP3", "B级音频", "B/B", etc.
                if f"/{pattern}/" in path_str or f"/{pattern}-" in path_str:
                    level = lvl
                    break
            if level:
                break

        if level:
            normalized = normalize(mp3_file.stem)
            audio_by_level[level].append({
                'path': mp3_file,
                'name': mp3_file.stem,
                'normalized': normalized
            })

    return audio_by_level


def find_books_without_audio(data_dir: Path) -> list:
    """Find all books without audio."""
    books = []

    for book_json in data_dir.rglob("book.json"):
        try:
            with open(book_json, "r", encoding="utf-8") as f:
                data = json.load(f)

            level = data.get("level", "").lower()
            title = data.get("title", "")
            book_dir = book_json.parent

            # Check if audio file actually exists
            audio = data.get("audio")
            has_audio = False
            if audio:
                audio_path = book_dir / audio
                has_audio = audio_path.exists()

            if not has_audio:
                books.append({
                    'level': level,
                    'title': title,
                    'normalized': normalize(title),
                    'dir': book_dir,
                    'json': book_json,
                    'data': data
                })
        except Exception as e:
            pass

    return books


def find_best_match(book: dict, audio_files: list) -> tuple:
    """Find best matching audio file."""
    book_norm = book['normalized']
    book_title = book['title'].lower()

    best_match = None
    best_score = 0

    for audio in audio_files:
        audio_norm = audio['normalized']
        audio_name = audio['name'].lower()

        # Exact normalized match
        if audio_norm == book_norm:
            return (audio, 1.0)

        # Check if book title is contained in audio name or vice versa
        if book_norm in audio_norm or audio_norm in book_norm:
            score = similarity(book_norm, audio_norm)
            if score > best_score:
                best_score = score
                best_match = audio

        # Check similarity
        score = similarity(book_norm, audio_norm)
        if score > best_score:
            best_score = score
            best_match = audio

    return (best_match, best_score)


def match_and_copy_audio(audio_by_level: dict, books: list, dry_run: bool = True) -> int:
    """Match audio files to books and copy them."""
    matched = 0
    unmatched = []

    for book in books:
        level = book['level']

        if level not in audio_by_level:
            unmatched.append(book)
            continue

        best_audio, score = find_best_match(book, audio_by_level[level])

        if best_audio and score >= 0.8:
            if dry_run:
                print(f"[DRY RUN] [{level.upper()}] {book['title']}")
                print(f"  -> Match: {best_audio['name']} (score: {score:.2f})")
            else:
                try:
                    dest = book['dir'] / "audio.mp3"
                    shutil.copy2(best_audio['path'], dest)

                    book['data']['audio'] = "audio.mp3"
                    with open(book['json'], "w", encoding="utf-8") as f:
                        json.dump(book['data'], f, indent=2, ensure_ascii=False)

                    print(f"✓ Fixed: [{level.upper()}] {book['title']} <- {best_audio['name']}")
                    matched += 1
                except Exception as e:
                    print(f"  ERROR: {e}")
                    unmatched.append(book)
        else:
            unmatched.append(book)

    return matched, unmatched


def main():
    base_dir = Path("/Users/sarowlwp/Document/go/study-class/raz-resourcer")
    data_dir = Path("/Users/sarowlwp/Document/go/study-class/data/raz")

    print("=" * 70)
    print("Scanning remaining audio files...")
    print("=" * 70)

    audio_by_level = scan_audio_by_level(base_dir)
    total_audio = sum(len(v) for v in audio_by_level.values())
    print(f"Found {total_audio} remaining audio files")

    for level in sorted(audio_by_level.keys(), key=lambda x: (len(x), x)):
        print(f"  {level.upper()}: {len(audio_by_level[level])} files")

    print("\n" + "=" * 70)
    print("Finding books without audio...")
    print("=" * 70)

    books = find_books_without_audio(data_dir)
    print(f"Found {len(books)} books without audio")

    # Group by level
    by_level = defaultdict(list)
    for book in books:
        by_level[book['level']].append(book)

    print("\nMissing audio by level:")
    for level in sorted(by_level.keys(), key=lambda x: (len(x), x)):
        print(f"  {level.upper()}: {len(by_level[level])} books")

    # Dry run
    print("\n" + "=" * 70)
    print("Dry run - potential matches (score >= 0.8):")
    print("=" * 70)

    potential = 0
    for book in books:
        level = book['level']
        if level in audio_by_level:
            best_audio, score = find_best_match(book, audio_by_level[level])
            if best_audio and score >= 0.8:
                potential += 1
                if potential <= 15:
                    print(f"\n[{level.upper()}] {book['title']}")
                    print(f"  normalized: {book['normalized']}")
                    print(f"  -> {best_audio['name']}")
                    print(f"  -> normalized: {best_audio['normalized']}")
                    print(f"  score: {score:.2f}")

    print(f"\nTotal potential matches: {potential}/{len(books)}")

    # Apply fixes
    print("\n" + "=" * 70)
    print("Applying fixes...")
    print("=" * 70)

    matched, unmatched = match_and_copy_audio(audio_by_level, books, dry_run=False)
    print(f"\nFixed {matched} books")

    if unmatched:
        print(f"\nStill missing audio ({len(unmatched)} books):")
        for book in unmatched:
            print(f"  [{book['level'].upper()}] {book['title']}")


if __name__ == "__main__":
    main()
