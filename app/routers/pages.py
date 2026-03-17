from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.config import BASE_DIR
from app.services.character_service import CharacterService
from app.services.record_service import RecordService
from app.services.quiz_service import QuizService

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
