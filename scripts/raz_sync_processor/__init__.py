"""RAZ 音频-文本同步处理器.

将 RAZ 绘本的 PDF 和 MP3 自动对齐，生成带时间戳的配置文件。
"""

__version__ = "1.0.0"

from .pdf_processor import PDFProcessor
from .audio_transcriber import AudioTranscriber
from .llm_mapper import LlmMapper
from .sync_generator import SyncGenerator
from .main import RazSyncProcessor, main

__all__ = [
    "PDFProcessor",
    "AudioTranscriber",
    "LlmMapper",
    "SyncGenerator",
    "RazSyncProcessor",
    "main",
]
