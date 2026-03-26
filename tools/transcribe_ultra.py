#!/usr/bin/env python3
"""超并行转录脚本 - 8进程"""

import json
import os
import sys
import multiprocessing as mp
from pathlib import Path
from typing import List, Dict, Any

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from faster_whisper import WhisperModel

RAZ_DIR = Path("/Users/sarowlwp/Document/go/study-class/data/raz")
MODEL_SIZE = "base"
NUM_WORKERS = 8  # 使用全部 8 核


def load_model():
    return WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")


def transcribe_one(args):
    book_dir_path, level = args
    book_dir = Path(book_dir_path)
    book_json = book_dir / "book.json"

    if not book_json.exists():
        return (book_dir.name, 0, "no_json")

    try:
        with open(book_json, encoding="utf-8") as f:
            book = json.load(f)

        if book.get("sentences") and len(book["sentences"]) > 0:
            if isinstance(book["sentences"][0], dict) and "start" in book["sentences"][0]:
                return (book_dir.name, 0, "already_done")

        audio_file = book.get("audio")
        if not audio_file:
            return (book_dir.name, 0, "no_audio")

        audio_path = book_dir / audio_file
        if not audio_path.exists():
            return (book_dir.name, 0, "audio_missing")

        model = load_model()

        segments, info = model.transcribe(
            str(audio_path),
            language="en",
            beam_size=1,
            best_of=1,
            vad_filter=False,
            condition_on_previous_text=False,
        )

        sentences = []
        for seg in segments:
            sentences.append({
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": seg.text.strip(),
                "page": 1,
                "confidence": round(seg.avg_logprob, 3) if hasattr(seg, 'avg_logprob') else 0.9,
            })

        if sentences:
            book["sentences"] = sentences
            with open(book_json, "w", encoding="utf-8") as f:
                json.dump(book, f, ensure_ascii=False, indent=2)
            return (book_dir.name, len(sentences), "success")
        else:
            return (book_dir.name, 0, "empty")

    except Exception as e:
        return (book_dir.name, 0, f"error: {e}")


def main():
    level = sys.argv[1] if len(sys.argv) > 1 else "x"
    level_dir = RAZ_DIR / f"level-{level}"

    if not level_dir.exists():
        print(f"错误: 找不到 {level_dir}")
        sys.exit(1)

    books_to_process = []
    for book_dir in sorted(level_dir.iterdir()):
        if not book_dir.is_dir():
            continue
        book_json = book_dir / "book.json"
        if not book_json.exists():
            continue

        try:
            with open(book_json, encoding="utf-8") as f:
                book = json.load(f)

            sentences = book.get("sentences", [])
            if sentences and isinstance(sentences[0], dict) and "start" in sentences[0]:
                continue

            if not book.get("audio"):
                continue

            books_to_process.append((str(book_dir), level))
        except:
            pass

    total = len(books_to_process)
    print(f"Level {level.upper()}: 共 {total} 本需要转录")
    print(f"使用 {NUM_WORKERS} 个并行进程（全核加速）\n")

    if total == 0:
        print("没有需要处理的书籍")
        return

    completed = 0
    with mp.Pool(NUM_WORKERS) as pool:
        for result in pool.imap_unordered(transcribe_one, books_to_process):
            name, count, status = result
            completed += 1

            if status == "success":
                print(f"[{completed}/{total}] ✓ {name}: {count} 句")
            elif status == "already_done":
                print(f"[{completed}/{total}] ○ {name}: 已存在")
            elif status.startswith("error"):
                print(f"[{completed}/{total}] ✗ {name}: {status}")
            else:
                print(f"[{completed}/{total}] - {name}: {status}")

    print(f"\n全部完成!")


if __name__ == "__main__":
    main()
