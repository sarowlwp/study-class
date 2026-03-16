from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates
from app.config import BASE_DIR
from app.services.character_service import CharacterService
from app.services.record_service import RecordService
from app.services.quiz_service import QuizService
from app.models.math_quiz import PROBLEM_TYPES, GRADE_DEFAULTS

router = APIRouter()
templates = Jinja2Templates(directory=BASE_DIR / "app" / "templates")

char_service = CharacterService()
record_service = RecordService()
quiz_service = QuizService(char_service, record_service)

@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/quiz")
async def quiz(request: Request, session: str):
    return templates.TemplateResponse("quiz.html", {"request": request, "session_id": session})

@router.get("/result")
async def result(request: Request):
    return templates.TemplateResponse("result.html", {"request": request})

@router.get("/mistakes")
async def mistakes(request: Request):
    return templates.TemplateResponse("mistakes.html", {"request": request})

@router.get("/print")
async def print_page(request: Request):
    return templates.TemplateResponse("print.html", {"request": request})


@router.get("/pdfs")
async def pdfs_page(request: Request):
    return templates.TemplateResponse("pdfs.html", {"request": request})


@router.get("/pdf-viewer")
async def pdf_viewer(request: Request, file: str):
    return templates.TemplateResponse("pdf-viewer.html", {"request": request, "filename": file})


@router.get("/worksheet")
async def worksheet_page(request: Request):
    return templates.TemplateResponse("worksheet.html", {"request": request})


@router.get("/math-quiz")
async def math_quiz_page(request: Request):
    """数学小测配置页面"""
    return templates.TemplateResponse("math_quiz.html", {
        "request": request,
        "problem_types": PROBLEM_TYPES,
        "grade_defaults": GRADE_DEFAULTS,
    })


@router.get("/math-quiz/preview")
async def math_preview_page(
    request: Request,
    grade: int = Query(..., ge=1, le=6),
    count: int = Query(30, ge=10, le=30),
    types: str = Query(...),
    show_answers: bool = Query(False),
):
    """数学小测预览/打印页面"""
    from app.services.math_generator import MathGenerator

    type_list = [int(t) for t in types.split(",") if t]
    generator = MathGenerator(grade)
    problems = generator.generate_quiz(count, type_list)

    return templates.TemplateResponse("math_preview.html", {
        "request": request,
        "grade": grade,
        "count": count,
        "problems": problems,
        "show_answers": show_answers,
        "today": __import__("datetime").datetime.now().strftime("%Y年%m月%d日"),
    })
