"""Audio transcription using faster-whisper with sentence-level timestamps."""

from pathlib import Path
from typing import Iterator, List, Optional

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

from .models import Sentence


class WhisperTranscriber:
    """Transcribe audio files using faster-whisper."""

    def __init__(
        self,
        model_size: str = "small",
        device: str = "cpu",
        compute_type: str = "int8",
    ):
        if WhisperModel is None:
            raise ImportError(
                "faster-whisper is not installed. "
                "Install it with: pip install faster-whisper"
            )
        self.model = WhisperModel(
            model_size, device=device, compute_type=compute_type
        )

    def transcribe(
        self,
        audio_path: Path,
        language: str = "en",
        confidence_threshold: float = 0.8,
    ) -> List[Sentence]:
        """
        Transcribe audio file to sentences with timestamps.

        Args:
            audio_path: Path to audio file
            language: Language code (default "en")
            confidence_threshold: Minimum confidence for sentences

        Returns:
            List of Sentence objects with timing info
        """
        segments, info = self.model.transcribe(
            str(audio_path),
            language=language,
            word_timestamps=True,
            vad_filter=True,
        )

        sentences = []
        current_words = []
        current_start = None
        current_confidences = []

        for segment in segments:
            words = segment.words or []

            for word in words:
                if current_start is None:
                    current_start = word.start

                current_words.append(word.word)
                current_confidences.append(word.probability)

                # Check for sentence end
                text = "".join(current_words).strip()
                if text and text[-1] in ".!?":
                    end_time = word.end
                    avg_confidence = sum(current_confidences) / len(
                        current_confidences
                    )

                    sentences.append(
                        Sentence(
                            start=current_start,
                            end=end_time,
                            text=text,
                            page=1,  # Will be updated by page mapper later
                            confidence=round(avg_confidence, 3),
                        )
                    )

                    # Reset for next sentence
                    current_words = []
                    current_start = None
                    current_confidences = []

        # Handle any remaining words as final sentence
        if current_words:
            text = "".join(current_words).strip()
            if text:
                avg_confidence = sum(current_confidences) / len(current_confidences)
                sentences.append(
                    Sentence(
                        start=current_start or 0,
                        end=words[-1].end if words else current_start or 0,
                        text=text,
                        page=1,
                        confidence=round(avg_confidence, 3),
                    )
                )

        return sentences

    def transcribe_with_progress(
        self,
        audio_path: Path,
        progress_callback=None,
    ) -> List[Sentence]:
        """Transcribe with optional progress callback."""
        return self.transcribe(audio_path)
