"""RAZ 音频-文本同步处理器.

将 RAZ 绘本的 PDF 和 MP3 自动对齐，生成带时间戳的配置文件。
"""

__version__ = "1.0.0"

from .audio_transcriber import AudioTranscriber

__all__ = [
    "AudioTranscriber",
]
