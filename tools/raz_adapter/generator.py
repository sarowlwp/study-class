"""Book generator for creating book.json and copying assets."""

import json
import shutil
from pathlib import Path
from typing import List, Optional

from .models import Book, Sentence
from .matcher import MatchedBook
from .transcriber import WhisperTranscriber


class BookGenerator:
    """Generate book.json and copy assets for matched books."""

    def __init__(
        self,
        output_dir: Path,
        transcriber: Optional[WhisperTranscriber] = None,
        confidence_threshold: float = 0.8
    ):
        self.output_dir = Path(output_dir)
        self.transcriber = transcriber
        self.confidence_threshold = confidence_threshold

    def generate(
        self,
        matched_book: MatchedBook,
        skip_existing: bool = False
    ) -> Optional[Path]:
        """
        Generate book.json and copy assets for a matched book.

        Args:
            matched_book: The matched book with PDF, audio, video paths
            skip_existing: If True, skip if book.json already exists

        Returns:
            Path to output directory if successful, None otherwise
        """
        output_path = self._get_output_path(matched_book)

        if skip_existing and (output_path / "book.json").exists():
            return None

        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)

        # Copy assets
        self._copy_assets(matched_book, output_path)

        # Transcribe audio to get sentences
        sentences = []
        if self.transcriber and matched_book.audio:
            try:
                sentences = self.transcriber.transcribe(
                    matched_book.audio,
                    confidence_threshold=self.confidence_threshold
                )
            except Exception as e:
                print(f"Warning: Transcription failed for {matched_book.title}: {e}")

        # Create book.json
        book = Book(
            id=f"level-{matched_book.level}/{matched_book.book_id}",
            title=matched_book.title,
            level=matched_book.level,
            pdf="book.pdf",
            video="video.mp4" if matched_book.video else None,
            audio="audio.mp3",
            sentences=sentences
        )

        book.save(output_path / "book.json")
        return output_path

    def _get_output_path(self, matched_book: MatchedBook) -> Path:
        """Get output path for a book."""
        return self.output_dir / f"level-{matched_book.level}" / matched_book.book_id

    def _copy_assets(self, matched_book: MatchedBook, output_path: Path) -> None:
        """Copy PDF, audio, and video to output directory."""
        if matched_book.pdf:
            shutil.copy2(matched_book.pdf, output_path / "book.pdf")

        if matched_book.audio:
            shutil.copy2(matched_book.audio, output_path / "audio.mp3")

        if matched_book.video:
            shutil.copy2(matched_book.video, output_path / "video.mp4")

    def generate_all(
        self,
        matched_books: List[MatchedBook],
        skip_existing: bool = False
    ) -> List[Path]:
        """
        Generate books for all matched books.

        Returns:
            List of output paths for successfully generated books
        """
        generated = []
        for book in matched_books:
            result = self.generate(book, skip_existing=skip_existing)
            if result:
                generated.append(result)
        return generated
