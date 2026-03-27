"""PDF 处理器：OCR + 文本提取."""

import re
import logging
from pathlib import Path
from typing import List, Optional

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

from .models import PageText
from .config import OCR_DPI

logger = logging.getLogger(__name__)


class PDFProcessor:
    """处理 PDF 文件：提取每页文本."""

    def __init__(self, dpi: int = OCR_DPI):
        """初始化处理器.

        Args:
            dpi: PDF 渲染分辨率
        """
        self.dpi = dpi

    def _check_fitz(self):
        """检查 fitz 是否可用."""
        if fitz is None:
            raise ImportError("PyMuPDF (fitz) is required. Install: pip install pymupdf")

    def extract_text_by_page(self, pdf_path: Path) -> List[PageText]:
        """提取每页文本."""
        logger.info(f"Extracting text from {pdf_path}")
        pages = []
        doc = fitz.open(pdf_path)

        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text().strip()
                pages.append(PageText(page_num=page_num + 1, text=text))
        finally:
            doc.close()

        logger.info(f"Extracted {len(pages)} pages")
        return pages

    def needs_ocr(self, pdf_path: Path, sample_pages: int = 2) -> bool:
        """检查 PDF 是否需要 OCR."""
        doc = fitz.open(pdf_path)
        try:
            for i in range(min(sample_pages, len(doc))):
                text = doc[i].get_text().strip()
                if len(text) > 10:
                    return False
            return True
        finally:
            doc.close()

    def add_ocr_layer(
        self,
        input_path: Path,
        output_path: Path,
        language: str = "eng"
    ) -> bool:
        """使用 OCRmyPDF 为 PDF 添加隐藏文字层."""
        try:
            import ocrmypdf
        except ImportError:
            logger.error("ocrmypdf not installed")
            return False

        try:
            ocrmypdf.ocr(
                input_path,
                output_path,
                language=language,
                deskew=True,
                optimize=1,
                progress_bar=False,
            )
            return True
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return False

    def _normalize_text(self, text: str) -> str:
        """标准化文本用于对齐."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
