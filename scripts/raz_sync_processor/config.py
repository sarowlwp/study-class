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
WORD_TIMINGS_JSON = "word_timings.json"
READER_HTML = "index.html"
PDF_TEXT_JSON = "pdf_text.json"

# OCR 配置
OCR_LANGUAGE = "eng"
OCR_DPI = 300
