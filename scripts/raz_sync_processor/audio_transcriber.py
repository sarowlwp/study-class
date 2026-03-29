"""音频转录器：使用 faster-whisper 生成词级时间戳."""

import logging
from pathlib import Path
from typing import List

from .config import DEFAULT_WHISPER_MODEL

logger = logging.getLogger(__name__)


class AudioTranscriber:
    """使用 faster-whisper 转录音频."""

    def __init__(
        self,
        model_size: str = DEFAULT_WHISPER_MODEL,
        device: str = "cpu",
        compute_type: str = "int8"
    ):
        """初始化转录器."""
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        # 不在 __init__ 中导入 faster-whisper，避免包初始化时加载

    def transcribe(
        self,
        audio_path: Path,
        language: str = "en",
        beam_size: int = 5
    ) -> List:  # 返回 List，不指定类型，避免导入 WordTiming
        """转录音频，生成词级时间戳.

        Returns:
            List: 每个单词包含 word, start, end 三个字段
            注意：faster-whisper 不提供 page 信息，page 需要通过对齐算法推断
        """
        logger.info(f"Transcribing audio: {audio_path}")
        logger.info(f"Loading Whisper model: {self.model_size}")

        try:
            # 仅在需要时导入 faster-whisper，避免与包初始化冲突
            from faster_whisper import WhisperModel
            from .models import WordTiming

            model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
            segments, info = model.transcribe(
                str(audio_path),
                language=language,
                beam_size=beam_size,
                word_timestamps=True,
                condition_on_previous_text=False,
            )

            logger.info(f"Detected language: {info.language}")

            word_timings = []
            for segment in segments:
                if segment.words:
                    for word_info in segment.words:
                        word = self._normalize_word(word_info.word)
                        if word:
                            timing = WordTiming(
                                word=word,
                                start=round(word_info.start, 3),
                                end=round(word_info.end, 3)
                            )
                            word_timings.append(timing)

            logger.info(f"Transcribed {len(word_timings)} words")
            return word_timings

        except Exception as e:
            logger.error(f"❌ Audio transcription failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def _normalize_word(self, word: str) -> str:
        """标准化单词."""
        word = word.strip().lower()
        word = word.strip('.,!?;:()[]{}')
        return word
