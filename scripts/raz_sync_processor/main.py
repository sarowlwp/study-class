"""主处理器：协调各组件完成同步任务.

简化流程：
1. PDF -> pdf_text.json (每页文本)
2. MP3 -> word_timings.json (单词时间戳，无page信息)
3. LLM Mapper 生成 book.json
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

from .pdf_processor import PDFProcessor
from .audio_transcriber import AudioTranscriber
from .sync_generator import SyncGenerator
from .llm_mapper import LlmMapper
from .models import PageText, WordTiming
from .config import LOG_FORMAT, LOG_LEVEL, PDF_FILENAME, AUDIO_FILENAME, COVER_FILENAME, PDF_TEXT_JSON, WORD_TIMINGS_JSON

logger = logging.getLogger(__name__)


class RazSyncProcessor:
    """RAZ 同步处理器 - 简化版."""

    def __init__(
        self,
        model_size: str = "base",
        language: str = "en",
        device: str = "cpu"
    ):
        """初始化处理器."""
        self.model_size = model_size
        self.language = language
        self.device = device

        self.pdf_processor = PDFProcessor()
        self.audio_transcriber = AudioTranscriber(
            model_size=model_size,
            device=device
        )
        self.llm_mapper = LlmMapper()

    def process(
        self,
        input_dir: Path,
        output_dir: Optional[Path] = None,
        book_id: Optional[str] = None,
        title: Optional[str] = None,
        force: bool = False,
        only_llm: bool = False
    ) -> bool:
        """处理单本书.

        核心流程：
        1. 提取 PDF 文本 -> pdf_text.json
        2. 转录 MP3 -> word_timings.json (无 page 信息)
        3. LLM 匹配生成 book.json

        所有产物直接生成在 input_dir 中。
        """
        pdf_path = input_dir / PDF_FILENAME
        audio_path = self._find_audio_file(input_dir)

        # 所有产物直接生成在 input_dir
        work_dir = input_dir

        if not only_llm:
            if not pdf_path.exists():
                logger.error(f"PDF not found: {pdf_path}")
                return False

            if not audio_path:
                logger.error(f"Audio not found in: {input_dir}")
                return False
        else:
            # only_llm 模式：检查必要的 JSON 文件是否存在
            pdf_text_path = work_dir / PDF_TEXT_JSON
            word_timings_path = work_dir / WORD_TIMINGS_JSON
            if not pdf_text_path.exists():
                logger.error(f"pdf_text.json not found: {pdf_text_path}")
                return False
            if not word_timings_path.exists():
                logger.error(f"word_timings.json not found: {word_timings_path}")
                return False
            logger.info("Only LLM mode: skipping PDF and audio processing")

        # 检查是否已处理过
        book_json_path = work_dir / "book.json"
        if book_json_path.exists() and not force:
            logger.info(f"book.json exists, skipping: {work_dir}")
            return True

        if book_id is None:
            book_id = self._infer_book_id(input_dir)
        if title is None:
            title = self._infer_title(input_dir)
        level = input_dir.parent.name

        logger.info(f"Processing: {title} (ID: {book_id})")

        try:
            if only_llm:
                # 只运行 LLM 合并步骤
                pdf_text_path = work_dir / PDF_TEXT_JSON
                word_timings_path = work_dir / WORD_TIMINGS_JSON
                audio_filename = audio_path.name if audio_path else "audio.mp3"

                logger.info("Using LLM to map pages to audio timings...")
                book_json_path = self.llm_mapper.generate_book_json(
                    pdf_text_path=pdf_text_path,
                    word_timings_path=word_timings_path,
                    output_path=work_dir / "book.json",
                    book_id=book_id,
                    title=title,
                    level=level,
                    audio_filename=audio_filename
                )

                if not book_json_path:
                    logger.error("LLM mapping failed")
                    return False

                logger.info(f"Successfully processed: {title}")
                logger.info(f"Output: {work_dir}")
                return True

            # Step 1: 处理 PDF -> pdf_text.json
            logger.info("Step 1/3: Extracting PDF text...")

            # 检查是否已有 pdf_text.json，有则直接加载
            pdf_text_path = work_dir / PDF_TEXT_JSON
            if pdf_text_path.exists() and not force:
                logger.info(f"Loading existing pdf_text.json: {pdf_text_path}")
                import json
                with open(pdf_text_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    pages = [PageText(page_num=p["page"], text=p["text"]) for p in data["pages"]]
            else:
                # 否则处理 PDF
                pages = self._process_pdf(pdf_path)
                if not pages:
                    logger.error("PDF processing failed")
                    return False

            # Step 1.5: 提取封面图片 -> cover.jpg
            logger.info("Step 1.5: Extracting cover image...")
            cover_path = work_dir / COVER_FILENAME
            if not cover_path.exists() or force:
                self.pdf_processor.extract_cover_image(pdf_path, cover_path)
            else:
                logger.info(f"Cover exists, skipping: {cover_path}")

            # Step 2: 转录音频 -> word_timings.json (无 page 信息)
            logger.info("Step 2/3: Transcribing audio...")
            word_timings = self.audio_transcriber.transcribe(
                audio_path, language=self.language
            )
            if not word_timings:
                logger.error("Audio transcription failed")
                return False

            logger.info(f"Transcribed {len(word_timings)} words")

            # Step 3: 生成输出文件
            logger.info("Step 3/3: Generating output files...")
            generator = SyncGenerator(work_dir)

            # 3.1 生成 pdf_text.json（如果不存在）
            pdf_text_path = work_dir / PDF_TEXT_JSON
            if not pdf_text_path.exists() or force:
                pdf_text_path = generator.generate_pdf_text_json(
                    pages, book_id, title, level
                )

            # 3.2 生成 word_timings.json (无 page 信息)
            word_timings_path = generator.generate_word_timings_simple(
                word_timings
            )

            # 3.3 LLM 匹配生成 book.json
            logger.info("Using LLM to map pages to audio timings...")
            book_json_path = self.llm_mapper.generate_book_json(
                pdf_text_path=pdf_text_path,
                word_timings_path=word_timings_path,
                output_path=work_dir / "book.json",
                book_id=book_id,
                title=title,
                level=level,
                audio_filename=audio_path.name
            )

            if not book_json_path:
                logger.error("LLM mapping failed")
                return False

            logger.info(f"Successfully processed: {title}")
            logger.info(f"Output: {work_dir}")
            return True

        except Exception as e:
            logger.exception(f"Processing failed: {e}")
            return False

    def _process_pdf(self, pdf_path: Path) -> list:
        """处理 PDF，OCR 使用临时文件不保留."""
        import tempfile
        import os

        if self.pdf_processor.needs_ocr(pdf_path):
            logger.info("PDF needs OCR...")
            # 使用临时文件，处理完后自动删除
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                ocr_path = Path(tmp.name)
            try:
                if self.pdf_processor.add_ocr_layer(pdf_path, ocr_path):
                    return self.pdf_processor.extract_text_by_page(ocr_path)
            finally:
                # 清理临时 OCR 文件
                if ocr_path.exists():
                    os.unlink(ocr_path)
        return self.pdf_processor.extract_text_by_page(pdf_path)

    def _infer_book_id(self, input_dir: Path) -> str:
        """从目录路径推断书籍 ID."""
        level = input_dir.parent.name
        book_name = input_dir.name
        return f"{level}/{book_name}"

    def _infer_title(self, input_dir: Path) -> str:
        """从目录名推断书名."""
        name = input_dir.name
        return name.replace("-", " ").title()

    def _find_audio_file(self, input_dir: Path) -> Optional[Path]:
        """查找音频文件，支持常见命名."""
        audio_names = ["book.mp3", "audio.mp3", "audio.m4a", "audio.wav"]
        for name in audio_names:
            path = input_dir / name
            if path.exists():
                return path
        return None


def setup_logging():
    """配置日志."""
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def main():
    """CLI 入口."""
    setup_logging()

    parser = argparse.ArgumentParser(
        description="RAZ 音频-文本同步处理器 (简化版)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
简化流程:
  1. PDF -> pdf_text.json (每页文本)
  2. MP3 -> word_timings.json (单词时间戳)
  3. LLM -> book.json (页面与音频匹配)

所有产物直接生成在输入目录中。

示例:
  python -m scripts.raz_sync_processor -i data/raz/level-a/a-fish-sees
  python -m scripts.raz_sync_processor -i data/raz/level-a/a-fish-sees --model base --force
  python -m scripts.raz_sync_processor -i data/raz/level-a/a-fish-sees --only-llm
        """
    )

    parser.add_argument("--input", "-i", required=True, type=Path,
                        help="输入目录（需包含 book.pdf 和 audio.mp3，产物直接生成在此目录）")
    parser.add_argument("--output", "-o", type=Path,
                        help="输出目录（已废弃，产物直接生成在输入目录）")
    parser.add_argument("--model", "-m", default="base",
                        choices=["tiny", "base", "small", "medium", "large"],
                        help="Whisper 模型大小 (默认: base)")
    parser.add_argument("--lang", "-l", default="en", help="语言代码")
    parser.add_argument("--device", "-d", default="cpu", choices=["cpu", "cuda"],
                        help="计算设备")
    parser.add_argument("--book-id", help="书籍 ID")
    parser.add_argument("--title", help="书名")
    parser.add_argument("--force", "-f", action="store_true", help="强制重新处理")
    parser.add_argument("--only-llm", action="store_true",
                        help="仅运行 LLM 合并步骤（跳过 PDF 和音频处理，需要已存在的 pdf_text.json 和 word_timings.json）")

    args = parser.parse_args()

    processor = RazSyncProcessor(
        model_size=args.model,
        language=args.lang,
        device=args.device
    )

    success = processor.process(
        input_dir=args.input,
        output_dir=None,  # 产物直接生成在 input_dir
        book_id=args.book_id,
        title=args.title,
        force=args.force,
        only_llm=args.only_llm
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
