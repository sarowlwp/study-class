"""PDF 处理器：OCR + 文本提取."""

import os
import re
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import easyocr
except ImportError:
    easyocr = None

try:
    import numpy as np
except ImportError:
    np = None

from PIL import Image

from .models import PageText
from .config import OCR_DPI, COVER_DPI, COVER_TARGET_SIZE_KB, COVER_MAX_DIMENSION

logger = logging.getLogger(__name__)


class PDFProcessor:
    """处理 PDF 文件：提取每页文本."""

    def __init__(self, dpi: int = OCR_DPI, lang: str = "en"):
        """初始化处理器.

        Args:
            dpi: PDF 渲染分辨率
            lang: OCR 语言 (默认: en)
        """
        self.dpi = dpi
        self.lang = lang
        self._reader: Optional[easyocr.Reader] = None

    def _get_reader(self) -> "easyocr.Reader":
        """获取或初始化 EasyOCR 引擎."""
        if self._reader is None:
            if easyocr is None:
                raise ImportError(
                    "EasyOCR is required. Install: pip install easyocr"
                )
            logger.info("Initializing EasyOCR...")
            self._reader = easyocr.Reader(
                [self.lang],
                gpu=False,
                verbose=False,
                model_storage_directory=str(Path.home() / ".EasyOCR" / "model")
            )
        return self._reader

    def _check_fitz(self):
        """检查 fitz 是否可用."""
        if fitz is None:
            raise ImportError("PyMuPDF (fitz) is required. Install: pip install pymupdf")

    def extract_text_by_page(self, pdf_path: Path) -> List[PageText]:
        """提取每页文本（自动使用 OCR 如果需要）."""
        logger.info(f"Extracting text from {pdf_path}")

        # 首先尝试直接提取文本
        pages = self._extract_raw_text(pdf_path)

        # 检查是否需要 OCR
        if self._needs_ocr_from_pages(pages):
            logger.info("PDF needs OCR, using EasyOCR...")
            pages = self._extract_with_easyocr(pdf_path)

        return pages

    def _extract_raw_text(self, pdf_path: Path) -> List[PageText]:
        """直接提取 PDF 文本（不 OCR）."""
        pages = []
        doc = fitz.open(pdf_path)
        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text().strip()
                pages.append(PageText(page_num=page_num + 1, text=text))
        finally:
            doc.close()
        return pages

    def _needs_ocr_from_pages(self, pages: List[PageText], sample_pages: int = 2) -> bool:
        """检查页面是否需要 OCR."""
        for i in range(min(sample_pages, len(pages))):
            if len(pages[i].text) > 10:
                return False
        return True

    def _extract_with_easyocr(self, pdf_path: Path) -> List[PageText]:
        """使用 EasyOCR 提取 PDF 每页文本.

        Args:
            pdf_path: PDF 文件路径

        Returns:
            每页的 PageText 列表
        """
        pages: List[PageText] = []
        doc = fitz.open(pdf_path)
        reader = self._get_reader()

        try:
            for page_num in range(len(doc)):
                page = doc[page_num]

                # 渲染页面为图片
                zoom = max(self.dpi, 200) / 72  # 至少 200 DPI
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)

                # 转换为 PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img_array = np.array(img)

                # EasyOCR 识别
                results = reader.readtext(img_array, detail=0)
                text = " ".join(results) if results else ""

                pages.append(PageText(page_num=page_num + 1, text=text))
                logger.info(f"  Page {page_num + 1}: OCR extracted {len(text)} chars")

        finally:
            doc.close()

        logger.info(f"EasyOCR extracted {len(pages)} pages")
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

    def extract_cover_image(
        self,
        pdf_path: Path,
        output_path: Path,
        dpi: int = COVER_DPI
    ) -> bool:
        """从 PDF 第一页提取封面图片，并压缩到 100KB 以内.

        Args:
            pdf_path: PDF 文件路径
            output_path: 输出图片路径
            dpi: 渲染分辨率 (默认 150)

        Returns:
            是否成功提取
        """
        self._check_fitz()
        logger.info(f"Extracting cover image from {pdf_path}")

        doc = fitz.open(pdf_path)
        try:
            if len(doc) == 0:
                logger.error("PDF has no pages")
                return False

            page = doc[0]
            zoom = dpi / 72  # 默认 72 DPI
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 压缩图片
            logger.info("Compressing cover image...")
            from PIL import Image
            import io
            import os

            TARGET_SIZE = COVER_TARGET_SIZE_KB * 1024  # 从配置读取
            MAX_DIMENSION = COVER_MAX_DIMENSION  # 从配置读取

            # 将 pixmap 转换为 PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # 调整尺寸
            max_dim = max(img.width, img.height)
            if max_dim > MAX_DIMENSION:
                scale_factor = MAX_DIMENSION / max_dim
                new_width = int(img.width * scale_factor)
                new_height = int(img.height * scale_factor)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # 计算最佳质量
            def calculate_quality(image, target_size):
                low = 10
                high = 95
                best_quality = 95
                best_image = None

                while low <= high:
                    mid = (low + high) // 2
                    img_buffer = io.BytesIO()
                    image.save(img_buffer, format='JPEG', quality=mid, optimize=True)
                    size = img_buffer.tell()

                    if size == target_size:
                        return mid, img_buffer.getvalue()

                    if size < target_size:
                        best_quality = mid
                        best_image = img_buffer.getvalue()
                        low = mid + 1
                    else:
                        high = mid - 1

                return best_quality, best_image

            quality, compressed_data = calculate_quality(img, TARGET_SIZE)

            # 保存压缩后的图片
            with open(output_path, "wb") as f:
                f.write(compressed_data)

            compressed_size = os.path.getsize(output_path)
            logger.info(f"Cover saved: {output_path} ({img.width}x{img.height}) - {compressed_size // 1024}KB")
            return True

        except Exception as e:
            logger.error(f"Failed to extract cover: {e}")
            return False
        finally:
            doc.close()
