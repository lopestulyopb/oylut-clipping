from pathlib import Path

import httpx
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.services.client_service import client_service
from app.services.monitoring_service import monitoring_service

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=BASE_DIR / "templates")
router = APIRouter(prefix="/clientes", tags=["monitoramentos"])


@router.get("/{client_id}", response_class=HTMLResponse)
async def client_monitorings_page(request: Request, client_id: str) -> HTMLResponse:
    error = None
    try:
        client = await client_service.get_client(client_id)
        monitorings = await monitoring_service.list_by_client(client_id)
    except (httpx.HTTPError, RuntimeError) as exc:
        client = None
        monitorings = []
        error = f"Não foi possível acessar o banco: {exc}"

    if client is None and error is None:
        error = "Cliente não encontrado."

    return templates.TemplateResponse(
        request=request,
        name="monitorings.html",
        context={"client": client, "monitorings": monitorings, "error": error},
    )


@router.post("/{client_id}/monitoramentos")
async def create_monitoring(client_id: str, name: str = Form(...)) -> RedirectResponse:
    await monitoring_service.create(client_id=client_id, name=name)
    return RedirectResponse(url=f"/clientes/{client_id}", status_code=303)


@router.post("/{client_id}/monitoramentos/{monitoring_id}/editar")
async def edit_monitoring(
    client_id: str,
    monitoring_id: str,
    name: str = Form(...),
) -> RedirectResponse:
    await monitoring_service.update_name(monitoring_id, name)
    return RedirectResponse(url=f"/clientes/{client_id}", status_code=303)


@router.post("/{client_id}/monitoramentos/{monitoring_id}/status")
async def change_monitoring_status(
    client_id: str,
    monitoring_id: str,
    is_active: bool = Form(...),
) -> RedirectResponse:
    await monitoring_service.set_active(monitoring_id, is_active)
    return RedirectResponse(url=f"/clientes/{client_id}", status_code=303)
