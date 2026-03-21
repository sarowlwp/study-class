from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional

from app.config import BASE_DIR
from app.services.english_service import EnglishService
from app.services.english_quiz_service import EnglishQuizService
from app.services.record_service import RecordService

router = APIRouter()
templates = Jinja2Templates(directory=BASE_DIR / "app" / "templates")

# Service instances
english_service = EnglishService()
record_service = RecordService()
english_quiz_service = EnglishQuizService(english_service, record_service)


class StartQuizRequest(BaseModel):
    semester_id: str
    lessons: List[str]
    count: int = 20


class SubmitAnswerRequest(BaseModel):
    session_id: str
    index: int
    answer: str


# ========== Page Routes ==========

@router.get("/english")
async def english_index(request: Request):
    """English quiz home page"""
    semesters = english_service.get_semesters()
    return templates.TemplateResponse("english/index.html", {
        "request": request,
        "semesters": semesters,
        "page_title": "英语抽测",
    })


@router.get("/english/quiz")
async def english_quiz_page(request: Request, session: str):
    """English quiz page"""
    return templates.TemplateResponse("english/quiz.html", {
        "request": request,
        "session_id": session,
        "page_title": "英语抽测进行中",
    })


@router.get("/english/result")
async def english_result_page(request: Request, session: str):
    """English result page"""
    return templates.TemplateResponse("english/result.html", {
        "request": request,
        "session_id": session,
        "page_title": "英语抽测结果",
    })


@router.get("/english/mistakes")
async def english_mistakes_page(request: Request):
    """English mistakes book page"""
    return templates.TemplateResponse("english/mistakes.html", {
        "request": request,
        "page_title": "英语错词本",
    })


# ========== API Routes ==========

@router.get("/api/english/semesters")
async def api_english_semesters():
    """Get all semesters"""
    return english_service.get_semesters()


@router.get("/api/english/lessons")
async def api_english_lessons(semester: str):
    """Get lessons for a semester"""
    return english_service.get_lessons(semester)


@router.post("/api/english/quiz/start")
async def api_start_quiz(request: StartQuizRequest):
    """Start a quiz"""
    try:
        count = max(5, min(50, request.count))
        session = english_quiz_service.generate_quiz(
            semester_id=request.semester_id,
            lessons=request.lessons,
            count=count
        )
        return {"session_id": session.session_id, "total": session.total}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/english/quiz/session/{session_id}")
async def api_get_session(session_id: str):
    """Get session state"""
    session = english_quiz_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session.session_id,
        "total": session.total,
        "current_index": session.current_index,
        "words": session.words,
        "completed": session.completed,
        "records": [
            {
                "word": r.word,
                "meaning": r.meaning,
                "lesson": r.lesson,
                "result": r.result.value,
            }
            for r in session.records
        ]
    }


@router.post("/api/english/quiz/submit")
async def api_submit_answer(request: SubmitAnswerRequest):
    """Submit an answer"""
    try:
        result = english_quiz_service.submit_answer(
            session_id=request.session_id,
            index=request.index,
            answer=request.answer
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/english/quiz/finish")
async def api_finish_quiz(request: dict):
    """Finish quiz"""
    session_id = request.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    try:
        summary = english_quiz_service.finish_quiz(session_id)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/english/mistakes")
async def api_get_mistakes():
    """Get mistakes"""
    return record_service.get_english_mistakes()


@router.get("/api/english/stats")
async def api_get_stats():
    """Get learning statistics"""
    records = record_service.get_all_english_records()

    from collections import defaultdict
    from datetime import date

    daily_stats = defaultdict(lambda: {"total": 0, "mastered": 0})
    for r in records:
        date_str = r.timestamp.strftime("%Y-%m-%d")
        daily_stats[date_str]["total"] += 1
        if r.result.value == "mastered":
            daily_stats[date_str]["mastered"] += 1

    dates = sorted(daily_stats.keys(), reverse=True)
    streak = 0
    today = date.today().isoformat()
    yesterday = date.fromordinal(date.today().toordinal() - 1).isoformat()

    if dates and (dates[0] == today or dates[0] == yesterday):
        streak = 1
        for i in range(1, len(dates)):
            expected = date.fromordinal(date.fromisoformat(dates[i-1]).toordinal() - 1).isoformat()
            if dates[i] == expected:
                streak += 1
            else:
                break

    return {
        "total_records": len(records),
        "streak_days": streak,
        "daily_stats": [
            {"date": d, **stats}
            for d, stats in sorted(daily_stats.items())[-7:]
        ]
    }
