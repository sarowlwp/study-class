from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.character_service import CharacterService
from app.services.record_service import RecordService
from app.services.quiz_service import QuizService
from app.services.pdf_service import get_pdf_files
from app.models.record import ResultType

router = APIRouter()

char_service = CharacterService()
record_service = RecordService()
quiz_service = QuizService(char_service, record_service)


@router.get("/pdfs")
async def get_pdfs():
    """获取 PDF 文件列表"""
    return {"pdfs": get_pdf_files()}


class StartQuizRequest(BaseModel):
    semester: str
    lessons: List[str]
    count: int = 20
    mode_mix: float = 0.5


class SubmitResultRequest(BaseModel):
    session_id: str
    index: int
    result: str


class FinishQuizRequest(BaseModel):
    session_id: str


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.get("/semesters")
async def get_semesters():
    return {"semesters": char_service.get_semesters()}


@router.get("/lessons")
async def get_lessons(semester: str):
    return {
        "semester": semester,
        "lessons": char_service.get_lessons(semester)
    }


@router.get("/characters")
async def get_characters(
    semester: str,
    lessons: Optional[str] = None
):
    lesson_list = lessons.split(",") if lessons else None
    chars = char_service.get_characters(semester, lesson_list)
    return {"characters": [c.to_dict() for c in chars]}


@router.post("/quiz/start")
async def start_quiz(request: StartQuizRequest):
    try:
        count = max(10, min(50, request.count))
        session = quiz_service.generate_quiz(
            request.semester,
            request.lessons,
            count,
            request.mode_mix
        )
        return {
            "session_id": session.session_id,
            "total": session.total,
            "characters": session.characters
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/quiz/session/{session_id}")
async def get_session(session_id: str):
    session = quiz_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session.session_id,
        "total": session.total,
        "current_index": session.current_index,
        "completed": session.completed,
        "characters": session.characters
    }


@router.post("/quiz/submit")
async def submit_result(request: SubmitResultRequest):
    try:
        result = ResultType(request.result)
        success = quiz_service.submit_result(
            request.session_id,
            request.index,
            result
        )
        session = quiz_service.get_session(request.session_id)
        return {
            "success": success,
            "next_index": session.current_index if session else None,
            "completed": session.completed if session else True
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/quiz/finish")
async def finish_quiz(request: FinishQuizRequest):
    try:
        summary = quiz_service.finish_quiz(request.session_id)
        return {
            "success": True,
            "summary": summary
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/mistakes")
async def get_mistakes(semester: Optional[str] = None):
    return {"mistakes": record_service.get_mistakes(semester)}


@router.get("/stats")
async def get_stats(semester: Optional[str] = None):
    return record_service.get_stats(semester)
