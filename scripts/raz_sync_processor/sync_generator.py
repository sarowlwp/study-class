"""同步生成器：生成 JSON 文件和阅读器 HTML."""

import json
import logging
from pathlib import Path
from typing import List

from .models import PageTiming, WordTimingWithLocation
from .config import OUTPUT_JSON, WORD_TIMINGS_JSON, READER_HTML, PDF_FILENAME, AUDIO_FILENAME

logger = logging.getLogger(__name__)


class SyncGenerator:
    """生成同步所需的输出文件."""

    def __init__(self, output_dir: Path):
        """初始化生成器."""
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_book_json(
        self,
        book_id: str,
        title: str,
        level: str,
        pages: List[PageTiming]
    ) -> Path:
        """生成 book.json."""
        data = {
            "id": book_id,
            "title": title,
            "level": level,
            "pdf": PDF_FILENAME,
            "audio": AUDIO_FILENAME,
            "page_count": len(pages),
            "pages": [
                {
                    "page": p.page_num,
                    "start_time": p.start_time,
                    "end_time": p.end_time,
                    "text": p.text
                }
                for p in pages
            ]
        }

        output_path = self.output_dir / OUTPUT_JSON
        output_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        logger.info(f"Generated: {output_path}")
        return output_path

    def generate_word_timings(
        self,
        word_timings: List[WordTimingWithLocation]
    ) -> Path:
        """生成 word_timings.json."""
        data = {
            "version": "1.0",
            "total_words": len(word_timings),
            "timings": [
                {
                    "word": w.word,
                    "start": w.start,
                    "end": w.end,
                    "page": w.page,
                    "char_start": w.char_start,
                    "char_end": w.char_end
                }
                for w in word_timings
            ]
        }

        output_path = self.output_dir / WORD_TIMINGS_JSON
        output_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        logger.info(f"Generated: {output_path}")
        return output_path

    def create_symlinks(self, source_dir: Path) -> None:
        """创建源文件软链接."""
        pdf_source = source_dir / PDF_FILENAME
        audio_source = source_dir / AUDIO_FILENAME

        if pdf_source.exists():
            pdf_link = self.output_dir / PDF_FILENAME
            if pdf_link.exists() or pdf_link.is_symlink():
                pdf_link.unlink()
            pdf_link.symlink_to(pdf_source.resolve())
            logger.info(f"Created symlink: {pdf_link}")

        if audio_source.exists():
            audio_link = self.output_dir / AUDIO_FILENAME
            if audio_link.exists() or audio_link.is_symlink():
                audio_link.unlink()
            audio_link.symlink_to(audio_source.resolve())
            logger.info(f"Created symlink: {audio_link}")

    def generate_reader_html(self) -> Path:
        """生成阅读器 HTML."""
        html_content = self._get_html_template()
        output_path = self.output_dir / READER_HTML
        output_path.write_text(html_content, encoding="utf-8")
        logger.info(f"Generated: {output_path}")
        return output_path

    def _get_html_template(self) -> str:
        """获取 HTML 模板."""
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAZ 同步阅读器</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    <style>
        .word-highlight {
            background-color: #fef08a;
            padding: 2px 4px;
            border-radius: 4px;
            transition: background-color 0.2s;
        }
        #text-display { line-height: 2; }
    </style>
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="max-w-4xl mx-auto p-4">
        <header class="bg-white rounded-lg shadow p-4 mb-4">
            <h1 id="book-title" class="text-xl font-bold text-gray-800">加载中...</h1>
            <p id="book-info" class="text-sm text-gray-500"></p>
        </header>

        <div class="bg-white rounded-lg shadow p-4 mb-4">
            <canvas id="pdf-canvas" class="w-full border rounded"></canvas>
        </div>

        <div class="bg-white rounded-lg shadow p-4 mb-4">
            <div id="text-display" class="text-lg text-gray-800"></div>
        </div>

        <div class="bg-white rounded-lg shadow p-4 mb-4">
            <audio id="audio-player" controls class="w-full"></audio>
        </div>

        <div class="flex justify-between items-center bg-white rounded-lg shadow p-4">
            <button id="prev-btn" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
                ← 上一页
            </button>
            <span id="page-indicator" class="text-gray-600">第 1 / 10 页</span>
            <button id="next-btn" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
                下一页 →
            </button>
        </div>
    </div>

    <script>
        let bookData = null;
        let wordTimings = null;
        let currentPage = 1;
        let pdfDoc = null;
        let audioPlayer = null;

        async function init() {
            bookData = await fetch('book.json').then(r => r.json());
            wordTimings = await fetch('word_timings.json').then(r => r.json());

            document.getElementById('book-title').textContent = bookData.title;
            document.getElementById('book-info').textContent =
                `Level ${bookData.level.toUpperCase()} · ${bookData.page_count} 页`;

            audioPlayer = document.getElementById('audio-player');
            audioPlayer.src = bookData.audio;

            pdfjsLib.GlobalWorkerOptions.workerSrc =
                'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
            pdfDoc = await pdfjsLib.getDocument(bookData.pdf).promise;

            document.getElementById('prev-btn').addEventListener('click', () => changePage(-1));
            document.getElementById('next-btn').addEventListener('click', () => changePage(1));
            audioPlayer.addEventListener('timeupdate', onTimeUpdate);

            renderPage(1);
        }

        async function renderPage(pageNum) {
            currentPage = pageNum;
            const page = await pdfDoc.getPage(pageNum);
            const canvas = document.getElementById('pdf-canvas');
            const ctx = canvas.getContext('2d');
            const scale = canvas.width / page.getViewport({scale: 1}).width;
            const viewport = page.getViewport({scale});

            canvas.height = viewport.height;
            await page.render({canvasContext: ctx, viewport}).promise;

            const pageData = bookData.pages.find(p => p.page === pageNum);
            document.getElementById('text-display').textContent = pageData?.text || '';
            document.getElementById('page-indicator').textContent =
                `第 ${pageNum} / ${bookData.page_count} 页`;
        }

        function changePage(delta) {
            const newPage = currentPage + delta;
            if (newPage >= 1 && newPage <= bookData.page_count) {
                renderPage(newPage);
                const pageData = bookData.pages.find(p => p.page === newPage);
                if (pageData) {
                    audioPlayer.currentTime = pageData.start_time;
                    audioPlayer.play();
                }
            }
        }

        function onTimeUpdate() {
            const currentTime = audioPlayer.currentTime;
            const currentWord = wordTimings.timings.find(
                w => w.start <= currentTime && w.end >= currentTime
            );

            if (currentWord) {
                if (currentWord.page !== currentPage) {
                    renderPage(currentWord.page);
                }
                highlightWord(currentWord);
            }
        }

        function highlightWord(wordTiming) {
            const display = document.getElementById('text-display');
            const text = display.textContent;
            const before = text.slice(0, wordTiming.char_start);
            const word = text.slice(wordTiming.char_start, wordTiming.char_end);
            const after = text.slice(wordTiming.char_end);
            display.innerHTML = `${before}<span class="word-highlight">${word}</span>${after}`;
        }

        init().catch(err => {
            console.error('初始化失败:', err);
            document.getElementById('book-title').textContent = '加载失败';
        });
    </script>
</body>
</html>'''
