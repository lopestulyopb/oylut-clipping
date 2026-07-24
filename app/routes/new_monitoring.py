from pathlib import Path
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.services.client_service import client_service
from app.services.monitoring_search_service import monitoring_search_service
from app.services.monitoring_service import monitoring_service

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=BASE_DIR / "templates")
router = APIRouter(tags=["novo-monitoramento"])


@router.get("/novo-monitoramento", response_class=HTMLResponse)
async def new_monitoring_page(request: Request) -> HTMLResponse:
    error = request.query_params.get("erro")
    try:
        clients = await client_service.list_clients()
    except (httpx.HTTPError, RuntimeError) as exc:
        clients = []
        error = f"Não foi possível acessar os clientes: {exc}"

    return templates.TemplateResponse(
        request=request,
        name="new_monitoring.html",
        context={"clients": clients, "error": error},
    )


@router.post("/novo-monitoramento")
async def create_complete_monitoring(
    client_id: str = Form(...),
    name: str = Form(...),
    main_term: str = Form(...),
    secondary_terms: str = Form(""),
) -> RedirectResponse:
    try:
        monitoring = await monitoring_service.create(client_id=client_id, name=name)
        await monitoring_search_service.add_term(monitoring["id"], main_term, True)
        for term in secondary_terms.splitlines():
            if term.strip():
                await monitoring_search_service.add_term(monitoring["id"], term, False)
    except httpx.HTTPStatusError as exc:
        message = "Já existe um cadastro com esses dados." if exc.response.status_code == 409 else "Não foi possível criar o monitoramento."
        return RedirectResponse(url=f"/novo-monitoramento?erro={quote(message)}", status_code=303)
    except (httpx.HTTPError, RuntimeError, ValueError):
        return RedirectResponse(url=f"/novo-monitoramento?erro={quote('Não foi possível criar o monitoramento. Tente novamente.')}", status_code=303)

    return RedirectResponse(url=f"/monitoramentos/{monitoring['id']}", status_code=303)
