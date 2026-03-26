#!/usr/bin/env python3
"""
为新增的书籍生成 sentences 数据。
使用 faster-whisper 转录音频，生成标准格式的 sentences。

用法:
  python3 transcribe_new_books.py              # 处理所有新增书
  python3 transcribe_new_books.py --level b    # 只处理指定级别
  python3 transcribe_new_books.py --dry-run    # 仅预览
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# 检查 faster_whisper 是否可用
try:
    from faster_whisper import WhisperModel
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False
    print("警告: faster_whisper 未安装，将只生成空结构")
    print("安装: pip install faster-whisper")

RAZ_DIR = Path("/Users/sarowlwp/Document/go/study-class/data/raz")
MODEL_SIZE = "base"


def load_model() -> "WhisperModel":
    """加载 Whisper 模型。"""
    print(f"加载 Whisper 模型: {MODEL_SIZE} ...")
    return WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")


def transcribe_audio(model: "WhisperModel", audio_path: Path) -> List[Dict[str, Any]]:
    """
    转录音频，返回带时间戳的句子列表。

    返回格式:
    [
        {"start": 0.0, "end": 3.12, "text": "...", "confidence": 0.95},
        ...
    ]
    """
    sentences = []

    try:
        segments, info = model.transcribe(
            str(audio_path),
            language="en",
            beam_size=5,
            vad_filter=True,
        )

        for seg in segments:
            sentences.append({
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": seg.text.strip(),
                "confidence": round(seg.avg_logprob, 3) if hasattr(seg, 'avg_logprob') else 0.9,
            })

    except Exception as e:
        print(f"    [警告] 转录失败: {e}")

    return sentences


def is_old_book(book_dir: Path) -> bool:
    """
    检查是否是旧书（已有完整 sentences 数据）。

    判断标准:
    - book.json 存在且包含带 start/end 的 sentences
    """
    book_json = book_dir / "book.json"
    if not book_json.exists():
        return False

    try:
        with open(book_json, encoding="utf-8") as f:
            book = json.load(f)

        sentences = book.get("sentences", [])
        if not sentences:
            return False

        # 检查是否有 start/end 字段（旧书有完整数据）
        for sent in sentences:
            if "start" in sent and "end" in sent:
                return True

        return False

    except Exception:
        return False


def process_book(model: "WhisperModel", book_dir: Path, dry_run: bool = False) -> bool:
    """
    处理单本书，生成 sentences 数据。

    返回是否已处理。
    """
    book_json_path = book_dir / "book.json"
    if not book_json_path.exists():
        return False

    # 跳过旧书
    if is_old_book(book_dir):
        return False

    with open(book_json_path, encoding="utf-8") as f:
        book = json.load(f)

    # 检查是否有音频
    audio_file = book.get("audio")
    if not audio_file:
        print(f"  [跳过] {book_dir.name} - 无音频")
        return False

    audio_path = book_dir / audio_file
    if not audio_path.exists():
        print(f"  [跳过] {book_dir.name} - 音频文件不存在: {audio_file}")
        return False

    # 转录音频
    if dry_run:
        print(f"  [预览] {book['title']} - 将转录 {audio_path.name}")
        return True

    print(f"  转录: {book['title']}")
    sentences_data = transcribe_audio(model, audio_path)

    if not sentences_data:
        print(f"    [警告] 无转录结果")
        return False

    # 构建标准格式的 sentences
    sentences = []
    for i, sent in enumerate(sentences_data):
        sentences.append({
            "start": sent["start"],
            "end": sent["end"],
            "text": sent["text"],
            "page": 1,  # 默认第一页，或根据时间推断
            "confidence": sent.get("confidence", 0.9),
        })

    # 更新 book.json
    book["sentences"] = sentences

    with open(book_json_path, "w", encoding="utf-8") as f:
        json.dump(book, f, ensure_ascii=False, indent=2)

    print(f"    完成: {len(sentences)} 句")
    return True


def process_level(model: "WhisperModel", level_dir: Path, dry_run: bool = False) -> Tuple[int, int, int]:
    """
    处理单个级别。

    返回: (已处理, 跳过旧书, 错误)
    """
    book_dirs = sorted([d for d in level_dir.iterdir() if d.is_dir()])

    processed = 0
    skipped_old = 0
    errors = 0

    for book_dir in book_dirs:
        if is_old_book(book_dir):
            skipped_old += 1
            continue

        try:
            if process_book(model, book_dir, dry_run):
                processed += 1
        except Exception as e:
            print(f"  [错误] {book_dir.name}: {e}")
            errors += 1

    return processed, skipped_old, errors


def main():
    parser = argparse.ArgumentParser(description="为新增书籍生成 sentences 数据")
    parser.add_argument("--level", metavar="LEVEL", help="只处理指定级别（如 b/c/d）")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不实际处理")
    args = parser.parse_args()

    # 加载模型
    model = None
    if not args.dry_run and HAS_WHISPER:
        model = load_model()

    if args.level:
        # 处理指定级别
        level_dir = RAZ_DIR / f"level-{args.level}"
        if not level_dir.exists():
            print(f"错误: 找不到级别目录 {level_dir}")
            sys.exit(1)

        print(f"\n=== 处理 level-{args.level} ===")
        processed, skipped, errors = process_level(model, level_dir, args.dry_run)
        print(f"\n结果: 已处理 {processed}, 跳过旧书 {skipped}, 错误 {errors}")

    else:
        # 处理所有级别
        level_dirs = sorted([d for d in RAZ_DIR.iterdir() if d.is_dir()])

        total_processed = 0
        total_skipped = 0
        total_errors = 0

        for level_dir in level_dirs:
            level = level_dir.name.replace("level-", "")
            book_count = len([d for d in level_dir.iterdir() if d.is_dir()])

            print(f"\n[{level.upper()}] {book_count} 本书")
            processed, skipped, errors = process_level(model, level_dir, args.dry_run)

            total_processed += processed
            total_skipped += skipped
            total_errors += errors

            if processed > 0 or errors > 0:
                print(f"  → 已处理 {processed}, 跳过旧书 {skipped}, 错误 {errors}")

        print(f"\n{'='*60}")
        print(f"总计: 已处理 {total_processed}, 跳过旧书 {total_skipped}, 错误 {total_errors}")


if __name__ == "__main__":
    main()
