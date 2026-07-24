from pathlib import Path

import httpx
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.services.client_service import client_service

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=BASE_DIR / "templates")
router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.get("", response_class=HTMLResponse)
async def clients_page(request: Request) -> HTMLResponse:
    error = None
    try:
        clients = await client_service.list_clients()
    except (httpx.HTTPError, RuntimeError) as exc:
        clients = []
        error = f"Não foi possível acessar o banco: {exc}"

    return templates.TemplateResponse(
        request=request,
        name="clients.html",
        context={"clients": clients, "error": error},
    )


@router.post("")
async def create_client(
    name: str = Form(...),
    logo_url: str = Form(""),
) -> RedirectResponse:
    await client_service.create_client(name=name, logo_url=logo_url)
    return RedirectResponse(url="/clientes", status_code=303)


@router.post("/{client_id}/editar")
async def edit_client(
    client_id: str,
    name: str = Form(...),
    logo_url: str = Form(""),
) -> RedirectResponse:
    await client_service.update_client(client_id, name, logo_url)
    return RedirectResponse(url="/clientes", status_code=303)


@router.post("/{client_id}/status")
async def change_client_status(
    client_id: str,
    is_active: bool = Form(...),
) -> RedirectResponse:
    await client_service.set_client_active(client_id, is_active)
    return RedirectResponse(url="/clientes", status_code=303)


@router.post("/{client_id}/excluir")
async def delete_client(client_id: str) -> RedirectResponse:
    await client_service.delete_client(client_id)
    return RedirectResponse(url="/clientes", status_code=303)
