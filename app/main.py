from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR
from app.routers import pages, api
from app.routers import math_quiz
from app.routers import english
from app.routers import raz

app = FastAPI(
    title="语文学习小工具",
    description="帮助小学生每日学习汉字和英语",
    version="1.1.0"
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")
app.mount("/data/pdfs", StaticFiles(directory=BASE_DIR / "data" / "pdfs"), name="pdfs")
app.include_router(pages.router)
app.include_router(api.router, prefix="/api")
app.include_router(math_quiz.router)
app.include_router(english.router)
app.include_router(raz.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
