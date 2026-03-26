#!/usr/bin/env python3
"""并行转录脚本 - 加速版本"""

import json
import os
import sys
import multiprocessing as mp
from pathlib import Path
from typing import List, Dict, Any

# 必须设置这个环境变量
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from faster_whisper import WhisperModel

RAZ_DIR = Path("/Users/sarowlwp/Document/go/study-class/data/raz")
MODEL_SIZE = "base"
NUM_WORKERS = 4  # 并行工作进程数


def load_model():
    """加载模型"""
    return WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")


def transcribe_one(args):
    """转录单本书（用于多进程）"""
    book_dir_path, level = args
    book_dir = Path(book_dir_path)
    book_json = book_dir / "book.json"

    if not book_json.exists():
        return (book_dir.name, 0, "no_json")

    try:
        with open(book_json, encoding="utf-8") as f:
            book = json.load(f)

        # 检查是否已有 sentences
        if book.get("sentences") and len(book["sentences"]) > 0:
            if isinstance(book["sentences"][0], dict) and "start" in book["sentences"][0]:
                return (book_dir.name, 0, "already_done")

        audio_file = book.get("audio")
        if not audio_file:
            return (book_dir.name, 0, "no_audio")

        audio_path = book_dir / audio_file
        if not audio_path.exists():
            return (book_dir.name, 0, "audio_missing")

        # 每个进程加载自己的模型实例
        model = load_model()

        segments, info = model.transcribe(
            str(audio_path),
            language="en",
            beam_size=1,  # 加速：使用贪婪解码
            best_of=1,
            vad_filter=False,  # 加速：禁用 VAD
            condition_on_previous_text=False,  # 加速
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

    # 获取需要处理的书籍
    books_to_process = []
    for book_dir in sorted(level_dir.iterdir()):
        if not book_dir.is_dir():
            continue
        book_json = book_dir / "book.json"
        if not book_json.exists():
            continue

        # 检查是否需要处理
        try:
            with open(book_json, encoding="utf-8") as f:
                book = json.load(f)

            # 跳过已有完整 sentences 的
            sentences = book.get("sentences", [])
            if sentences and isinstance(sentences[0], dict) and "start" in sentences[0]:
                continue

            # 跳过无音频的
            if not book.get("audio"):
                continue

            books_to_process.append((str(book_dir), level))
        except:
            pass

    total = len(books_to_process)
    print(f"Level {level.upper()}: 共 {total} 本需要转录")
    print(f"使用 {NUM_WORKERS} 个并行进程\n")

    if total == 0:
        print("没有需要处理的书籍")
        return

    # 并行处理
    with mp.Pool(NUM_WORKERS) as pool:
        results = []
        for result in pool.imap_unordered(transcribe_one, books_to_process):
            name, count, status = result
            results.append(result)

            if status == "success":
                print(f"✓ {name}: {count} 句")
            elif status == "already_done":
                print(f"○ {name}: 已存在")
            elif status.startswith("error"):
                print(f"✗ {name}: {status}")
            else:
                print(f"- {name}: {status}")

    # 统计
    success = sum(1 for _, _, s in results if s == "success")
    print(f"\n完成: {success}/{total}")


if __name__ == "__main__":
    main()
