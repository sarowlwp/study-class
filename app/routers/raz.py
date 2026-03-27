import os
import re as _re
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.config import BASE_DIR, RAZ_DIR, RAZ_RECORDS_DIR, RAZ_CONFIG_FILE
from app.models.raz import RazPracticeRecord
from app.services.raz_service import RazService
from app.services.raz_practice_service import RazPracticeService
from app.services.speech_assessment import get_assessor

import logging

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory=BASE_DIR / "app" / "templates")

raz_service = RazService(raz_dir=RAZ_DIR, records_dir=RAZ_RECORDS_DIR, config_file=RAZ_CONFIG_FILE)
practice_service = RazPracticeService(raz_service=raz_service, records_dir=RAZ_RECORDS_DIR)
assessor = get_assessor()


# ── 页面路由 ──────────────────────────────────────────────────────────────────

@router.get("/raz")
async def raz_index(request: Request):
    config = raz_service.get_config()
    books = raz_service.get_books(config.current_level)
    today_count = practice_service.get_today_count(date.today())
    goal_met = practice_service.is_daily_goal_met(date.today(), config)
    return templates.TemplateResponse("raz/index.html", {
        "request": request,
        "page_title": "RAZ 跟读",
        "books": books,
        "config": config,
        "today_count": today_count,
        "goal_met": goal_met,
    })


@router.get("/raz/book/{level}/{book_dir}")
async def raz_book(request: Request, level: str, book_dir: str):
    book_id = f"level-{level}/{book_dir}"
    book = raz_service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return templates.TemplateResponse("raz/book.html", {
        "request": request,
        "page_title": book.title,
        "book": book,
    })


@router.get("/raz/practice/{level}/{book_dir}")
async def raz_practice(request: Request, level: str, book_dir: str):
    book_id = f"level-{level}/{book_dir}"
    book = raz_service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    config = raz_service.get_config()
    # Convert dataclass to dict for JSON serialization
    book_dict = {
        "id": book.id,
        "title": book.title,
        "level": book.level,
        "video": book.video,
        "pages": [
            {"page": p.page, "pdf": p.pdf, "audio": p.audio, "sentences": p.sentences}
            for p in book.pages
        ],
    }
    return templates.TemplateResponse("raz/practice.html", {
        "request": request,
        "page_title": f"{book.title} - 练习",
        "book": book_dict,
        "config": config,
    })


@router.get("/raz/reader/{level}/{book_dir}")
async def raz_reader(request: Request, level: str, book_dir: str):
    """RAZ 阅读器页面（pdf.js + TTS + 评测）"""
    book_id = f"level-{level}/{book_dir}"
    book = raz_service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # 检查是否使用静态资源服务器
    static_server = os.environ.get("StaticServer", "").rstrip("/")

    return templates.TemplateResponse("raz/reader.html", {
        "request": request,
        "page_title": book.title,
        "book": book,
        "book_dir": book_dir,
        "static_server": static_server,
    })


@router.get("/raz/progress")
async def raz_progress(request: Request):
    config = raz_service.get_config()
    records = raz_service.get_records_by_date(date.today())
    return templates.TemplateResponse("raz/progress.html", {
        "request": request,
        "page_title": "学习进度",
        "config": config,
        "today_records": records,
        "today_count": len(records),
    })


@router.get("/raz/speech-test")
async def raz_speech_test(request: Request):
    """Azure Speech 发音评估测试页面。"""
    assessor_type = os.environ.get("SPEECH_ASSESSOR", "mock")
    return templates.TemplateResponse("raz/speech_test.html", {
        "request": request,
        "page_title": "Azure Speech 测试",
        "assessor_type": assessor_type,
        "assessor_class": type(assessor).__name__,
    })


# ── API 路由 ──────────────────────────────────────────────────────────────────

@router.get("/api/raz/books")
async def api_get_books(level: Optional[str] = None):
    config = raz_service.get_config()
    target_level = level or config.current_level
    books = raz_service.get_books(target_level)
    return [{"id": b.id, "title": b.title, "level": b.level, "page_count": len(b.pages)} for b in books]


@router.get("/api/raz/book/{level}/{book_dir}")
async def api_get_book(level: str, book_dir: str):
    book_id = f"level-{level}/{book_dir}"
    book = raz_service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return {
        "id": book.id,
        "title": book.title,
        "level": book.level,
        "video": book.video,
        "pages": [
            {"page": p.page, "pdf": p.pdf, "audio": p.audio, "sentences": p.sentences}
            for p in book.pages
        ],
    }


@router.get("/api/raz/book-detail/{level}/{book_dir}")
async def api_get_book_detail(level: str, book_dir: str):
    """获取书籍详情（含时间轴，供阅读器使用）"""
    book_id = f"level-{level}/{book_dir}"
    book = raz_service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    return {
        "id": book.id,
        "title": book.title,
        "level": book.level,
        "pdf": f"/raz/media/{book.level}/{book_dir}/{book.pdf}" if book.pdf else None,
        "audio": f"/raz/media/{book.level}/{book_dir}/{book.audio}" if book.audio else None,
        "total_pages": book.total_pages,
        "sentences": [
            {"start": s.start, "end": s.end, "text": s.text, "page": s.page}
            for s in book.sentences
        ],
    }


@router.post("/api/raz/assess")
async def api_assess(
    audio: UploadFile = File(...),
    text: str = Form(...),
    book_id: str = Form(...),
    book_title: str = Form(...),
    level: str = Form(...),
    page: int = Form(...),
):
    audio_bytes = await audio.read()

    if len(audio_bytes) < 1000:
        raise HTTPException(status_code=400, detail="录音过短，请重新录制")

    # 记录传入给 speech service 的信息
    logger.info(f"[Speech Assessment] book_id={book_id}, page={page}, text_length={len(text)}, text={text!r}")

    result = await assessor.assess(audio_bytes, text)

    # 记录评测结果
    logger.info(f"[Speech Assessment Result] score={result.score}, level={result.level}, text={text!r}")

    record = RazPracticeRecord(
        book_id=book_id,
        book_title=book_title,
        level=level,
        page=page,
        sentence=text,
        score=result.score,
        timestamp=datetime.now(),
    )
    raz_service.save_record(record)

    return {
        "score": result.score,
        "level": result.level,
        "feedback": result.feedback,
        "word_scores": [{"word": w.word, "score": w.score, "status": w.status} for w in result.word_scores],
    }


class UpdateSessionRequest(BaseModel):
    book_id: str
    page: int
    sentence_index: int


@router.post("/api/raz/session")
async def api_update_session(req: UpdateSessionRequest):
    practice_service.update_session(req.book_id, req.page, req.sentence_index)
    return {"ok": True}


class UpdateConfigRequest(BaseModel):
    current_level: Optional[str] = None
    daily_mode: Optional[str] = None
    daily_count: Optional[int] = None


@router.post("/api/raz/config")
async def api_update_config(req: UpdateConfigRequest):
    config = raz_service.get_config()
    if req.current_level is not None:
        config.current_level = req.current_level
    if req.daily_mode is not None:
        config.daily_mode = req.daily_mode
    if req.daily_count is not None:
        config.daily_count = max(1, req.daily_count)
    raz_service.save_config(config)
    return {"ok": True}


@router.get("/api/raz/config")
async def api_get_config():
    config = raz_service.get_config()
    today = date.today()
    today_count = practice_service.get_today_count(today)
    smart_rec = practice_service.get_smart_recommendation(reference_date=today)
    return {
        "current_level": config.current_level,
        "daily_mode": config.daily_mode,
        "daily_count": config.daily_count,
        "current_session": config.current_session,
        "today_count": today_count,
        "smart_recommendation": smart_rec,
    }


# ── 静态文件（书库 PDF/MP3/MP4） ───────────────────────────────────────────────

_SAFE_PATH_PATTERN = _re.compile(r'^[a-zA-Z0-9_\-\.]+$')


@router.get("/raz/media/{level}/{book_dir}/{filename}")
async def raz_media(level: str, book_dir: str, filename: str):
    """安全地提供书库媒体文件。路径参数严格校验，防止路径穿越。"""
    if not all(_SAFE_PATH_PATTERN.match(p) for p in [level, book_dir, filename]):
        raise HTTPException(status_code=400, detail="Invalid path")

    file_path = RAZ_DIR / f"level-{level}" / book_dir / filename
    try:
        file_path.resolve().relative_to(RAZ_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)
