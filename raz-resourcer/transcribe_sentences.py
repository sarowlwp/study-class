"""
用 faster-whisper 转录 data/raz/ 下所有书的 MP3 音频，
将结果写入每本书的 book.json sentences 字段。

跳过已有 sentences 内容的页面。

用法:
  python3.11 transcribe_sentences.py              # 处理全部级别
  python3.11 transcribe_sentences.py --level e    # 只处理指定级别
  KMP_DUPLICATE_LIB_OK=TRUE python3.11 transcribe_sentences.py
"""

import argparse
import json
import re
import sys
from pathlib import Path

from faster_whisper import WhisperModel

RAZ_DIR = Path(__file__).resolve().parent.parent / "data" / "raz"
MODEL_SIZE = "base"


def load_model() -> WhisperModel:
    print(f"加载 Whisper 模型: {MODEL_SIZE} ...")
    return WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")


def transcribe_audio(model: WhisperModel, audio_path: Path) -> str:
    try:
        segments, _ = model.transcribe(
            str(audio_path),
            language="en",
            beam_size=5,
            vad_filter=True,
        )
        return " ".join(seg.text.strip() for seg in segments).strip()
    except Exception as e:
        print(f"    [警告] 转录失败 {audio_path.name}: {e}")
        return ""


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def process_book(model: WhisperModel, book_dir: Path) -> bool:
    book_json_path = book_dir / "book.json"
    if not book_json_path.exists():
        return False

    with open(book_json_path, encoding="utf-8") as f:
        book = json.load(f)

    # 跳过已全部填充 sentences 的书
    if all(page.get("sentences") for page in book.get("pages", [])):
        return False

    changed = False
    for page in book["pages"]:
        # 已有 sentences 则跳过
        if page.get("sentences"):
            continue

        audio_path = book_dir / page["audio"]
        if not audio_path.exists():
            print(f"    [警告] 找不到音频: {audio_path.name}")
            continue

        text = transcribe_audio(model, audio_path)
        sentences = split_sentences(text)
        page["sentences"] = sentences
        changed = True

    if changed:
        with open(book_json_path, "w", encoding="utf-8") as f:
            json.dump(book, f, ensure_ascii=False, indent=2)

    return changed


def process_level(model: WhisperModel, level_dir: Path) -> tuple[int, int]:
    book_dirs = sorted([d for d in level_dir.iterdir() if d.is_dir()])
    done = skip = 0
    for book_dir in book_dirs:
        updated = process_book(model, book_dir)
        if updated:
            done += 1
            print(f"    OK  {book_dir.name}")
        else:
            skip += 1
    return done, skip


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", metavar="LEVEL", help="只处理指定级别（如 d/e/g）")
    args = parser.parse_args()

    model = load_model()

    if args.level:
        level_dir = RAZ_DIR / f"level-{args.level}"
        if not level_dir.exists():
            print(f"找不到: {level_dir}")
            sys.exit(1)
        print(f"\n=== 处理 level-{args.level} ===")
        done, skip = process_level(model, level_dir)
        print(f"完成 {done} 本，跳过 {skip} 本（已有数据）。")
    else:
        level_dirs = sorted([d for d in RAZ_DIR.iterdir() if d.is_dir()])
        total_done = total_skip = 0
        for level_dir in level_dirs:
            level = level_dir.name
            book_dirs = [d for d in level_dir.iterdir() if d.is_dir()]
            print(f"\n[{level}] {len(book_dirs)} 本书")
            done, skip = process_level(model, level_dir)
            total_done += done
            total_skip += skip
            print(f"  → 完成 {done}，跳过 {skip}")

        print(f"\n全部完成：共更新 {total_done} 本书，跳过 {total_skip} 本。")


if __name__ == "__main__":
    main()
