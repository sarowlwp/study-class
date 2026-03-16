from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR
from app.routers import pages, api

app = FastAPI(
    title="汉字抽测卡",
    description="帮助小学生每日校验汉字掌握情况",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")
app.include_router(pages.router)
app.include_router(api.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
