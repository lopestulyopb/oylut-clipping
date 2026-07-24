from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.routes.clients import router as clients_router
from app.routes.history import router as history_router
from app.routes.info import router as info_router
from app.routes.monitoring_detail import router as monitoring_detail_router
from app.routes.monitorings import router as monitorings_router
from app.routes.new_monitoring import router as new_monitoring_router
from app.routes.search import router as search_router

BASE_DIR = Path(__file__).resolve().parent
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    version="0.6.2",
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
app.include_router(search_router)
app.include_router(clients_router)
app.include_router(monitorings_router)
app.include_router(monitoring_detail_router)
app.include_router(history_router)
app.include_router(new_monitoring_router)
app.include_router(info_router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"app_name": settings.app_name},
    )


@app.get("/saude")
async def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "produto": settings.app_name,
        "versao": "0.6.2",
        "banco_configurado": settings.database_configured,
    }
