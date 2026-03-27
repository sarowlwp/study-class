"""配置常量."""

import logging

# 日志配置
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.INFO

# 默认模型配置
DEFAULT_WHISPER_MODEL = "base"
DEFAULT_LANGUAGE = "en"

# 文件路径
PDF_FILENAME = "book.pdf"
AUDIO_FILENAME = "book.mp3"
OUTPUT_JSON = "book.json"
WORD_TIMINGS_JSON = "word_timings.json"
READER_HTML = "index.html"

# OCR 配置
OCR_LANGUAGE = "eng"
OCR_DPI = 300

# 对齐算法阈值
MIN_ALIGNMENT_RATIO = 0.8  # 最小对齐比例
