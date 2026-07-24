from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.services.monitoring_service import monitoring_service
from app.services.schedule_service import schedule_service

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=BASE_DIR / "templates")
router = APIRouter(tags=["agendamentos"])


@router.get("/agendamentos", response_class=HTMLResponse)
async def schedules_page(request: Request) -> HTMLResponse:
    try:
        schedules = await schedule_service.list_all()
        monitorings = await monitoring_service.list_all()
        setup_pending = False
    except (httpx.HTTPError, RuntimeError):
        schedules, monitorings, setup_pending = [], [], True
    return templates.TemplateResponse(
        request=request,
        name="schedules.html",
        context={
            "schedules": schedules,
            "monitorings": monitorings,
            "setup_pending": setup_pending,
        },
    )


@router.post("/agendamentos")
async def create_schedule(
    monitoring_id: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(""),
    delivery_time: str = Form(...),
) -> RedirectResponse:
    now = datetime.now(timezone.utc)
    await schedule_service.create(
        {
            "monitoring_id": monitoring_id,
            "frequency": "daily",
            "weekday": None,
            "window_start_time": None,
            "run_time": delivery_time,
            "start_date": start_date,
            "end_date": end_date or None,
            "period_hours": 24,
            "timezone": "America/Fortaleza",
            "is_active": True,
            "last_run_at": now.isoformat(),
        }
    )
    return RedirectResponse(url="/agendamentos", status_code=303)


@router.post("/agendamentos/{schedule_id}/status")
async def schedule_status(schedule_id: str, is_active: bool = Form(...)) -> RedirectResponse:
    await schedule_service.set_active(schedule_id, is_active)
    return RedirectResponse(url="/agendamentos", status_code=303)


@router.post("/agendamentos/{schedule_id}/excluir")
async def delete_schedule(schedule_id: str) -> RedirectResponse:
    await schedule_service.delete(schedule_id)
    return RedirectResponse(url="/agendamentos", status_code=303)


@router.post("/tarefas/agendamentos/executar")
async def run_schedules() -> dict:
    executions = await schedule_service.run_due()
    return {"executions": executions, "count": len(executions)}
