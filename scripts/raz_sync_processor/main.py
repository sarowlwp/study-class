"""主处理器：协调各组件完成同步任务."""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

from .pdf_processor import PDFProcessor
from .audio_transcriber import AudioTranscriber
from .text_aligner import TextAligner
from .sync_generator import SyncGenerator
from .models import PageText, WordTiming, PageTiming, WordTimingWithLocation
from .config import LOG_FORMAT, LOG_LEVEL, PDF_FILENAME, AUDIO_FILENAME

logger = logging.getLogger(__name__)


class RazSyncProcessor:
    """RAZ 同步处理器主类."""

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
        self.text_aligner = TextAligner()

    def process(
        self,
        input_dir: Path,
        output_dir: Path,
        book_id: Optional[str] = None,
        title: Optional[str] = None,
        force: bool = False
    ) -> bool:
        """处理单本书."""
        pdf_path = input_dir / PDF_FILENAME
        audio_path = input_dir / AUDIO_FILENAME

        if not pdf_path.exists():
            logger.error(f"PDF not found: {pdf_path}")
            return False

        if not audio_path.exists():
            logger.error(f"Audio not found: {audio_path}")
            return False

        if output_dir.exists() and not force:
            logger.info(f"Output exists, skipping: {output_dir}")
            return True

        output_dir.mkdir(parents=True, exist_ok=True)

        if book_id is None:
            book_id = self._infer_book_id(input_dir)
        if title is None:
            title = self._infer_title(input_dir)
        level = input_dir.parent.name

        logger.info(f"Processing: {title} (ID: {book_id})")

        try:
            # Step 1: 处理 PDF
            logger.info("Step 1/4: Processing PDF...")
            pages = self._process_pdf(pdf_path)
            if not pages:
                logger.error("PDF processing failed")
                return False

            # Step 2: 转录音频
            logger.info("Step 2/4: Transcribing audio...")
            word_timings = self._transcribe_audio(audio_path)
            if not word_timings:
                logger.error("Audio transcription failed")
                return False

            # Step 3: 对齐文本
            logger.info("Step 3/4: Aligning text...")
            page_timings = self.text_aligner.align(pages, word_timings)
            if not page_timings:
                logger.error("Text alignment failed")
                return False

            # Step 4: 生成输出
            logger.info("Step 4/4: Generating output...")
            generator = SyncGenerator(output_dir)
            generator.create_symlinks(input_dir)
            generator.generate_book_json(book_id, title, level, page_timings)

            word_timings_with_loc = self._add_word_locations(
                word_timings, page_timings
            )
            generator.generate_word_timings(word_timings_with_loc)
            generator.generate_reader_html()

            logger.info(f"Successfully processed: {title}")
            return True

        except Exception as e:
            logger.exception(f"Processing failed: {e}")
            return False

    def _process_pdf(self, pdf_path: Path) -> list:
        """处理 PDF."""
        if self.pdf_processor.needs_ocr(pdf_path):
            logger.info("PDF needs OCR...")
            ocr_path = pdf_path.parent / "book_ocr.pdf"
            if self.pdf_processor.add_ocr_layer(pdf_path, ocr_path):
                return self.pdf_processor.extract_text_by_page(ocr_path)
        return self.pdf_processor.extract_text_by_page(pdf_path)

    def _transcribe_audio(self, audio_path: Path) -> list:
        """转录音频."""
        return self.audio_transcriber.transcribe(
            audio_path,
            language=self.language
        )

    def _add_word_locations(
        self,
        word_timings: list,
        page_timings: list
    ) -> list:
        """为单词添加页面和字符位置信息."""
        result = []
        char_offset = 0
        current_page_idx = 0

        for word in word_timings:
            while (current_page_idx < len(page_timings) - 1 and
                   word.start > page_timings[current_page_idx].end_time):
                char_offset += len(page_timings[current_page_idx].text) + 1
                current_page_idx += 1

            page = page_timings[current_page_idx]
            word_len = len(word.word)

            result.append(WordTimingWithLocation(
                word=word.word,
                start=word.start,
                end=word.end,
                page=page.page_num,
                char_start=char_offset,
                char_end=char_offset + word_len
            ))

            char_offset += word_len + 1

        return result

    def _infer_book_id(self, input_dir: Path) -> str:
        """从目录路径推断书籍 ID."""
        level = input_dir.parent.name
        book_name = input_dir.name
        return f"{level}/{book_name}"

    def _infer_title(self, input_dir: Path) -> str:
        """从目录名推断书名."""
        name = input_dir.name
        return name.replace("-", " ").title()


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
        description="RAZ 音频-文本同步处理器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m scripts.raz_sync_processor -i input/ -o output/
  python -m scripts.raz_sync_processor -i input/ -o output/ --model tiny --force
        """
    )

    parser.add_argument("--input", "-i", required=True, type=Path,
                        help="输入目录（需包含 book.pdf 和 book.mp3）")
    parser.add_argument("--output", "-o", required=True, type=Path,
                        help="输出目录")
    parser.add_argument("--model", "-m", default="base",
                        choices=["tiny", "base", "small", "medium", "large"],
                        help="Whisper 模型大小 (默认: base)")
    parser.add_argument("--lang", "-l", default="en", help="语言代码")
    parser.add_argument("--device", "-d", default="cpu", choices=["cpu", "cuda"],
                        help="计算设备")
    parser.add_argument("--book-id", help="书籍 ID")
    parser.add_argument("--title", help="书名")
    parser.add_argument("--force", "-f", action="store_true", help="强制重新处理")

    args = parser.parse_args()

    processor = RazSyncProcessor(
        model_size=args.model,
        language=args.lang,
        device=args.device
    )

    success = processor.process(
        input_dir=args.input,
        output_dir=args.output,
        book_id=args.book_id,
        title=args.title,
        force=args.force
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
