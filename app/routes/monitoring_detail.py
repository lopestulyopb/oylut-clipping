from pathlib import Path

import httpx
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.services.monitoring_search_service import monitoring_search_service

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=BASE_DIR / "templates")
router = APIRouter(prefix="/monitoramentos", tags=["termos", "pesquisas"])


@router.get("/{monitoring_id}", response_class=HTMLResponse)
async def detail(request: Request, monitoring_id: str, message: str | None = None) -> HTMLResponse:
    error = None
    try:
        monitoring = await monitoring_search_service.get_monitoring(monitoring_id)
        terms = await monitoring_search_service.list_terms(monitoring_id)
    except (httpx.HTTPError, RuntimeError) as exc:
        monitoring, terms = None, []
        error = f"Não foi possível acessar o banco: {exc}"
    return templates.TemplateResponse(
        request=request,
        name="monitoring_detail.html",
        context={"monitoring": monitoring, "terms": terms, "error": error, "message": message},
    )


@router.post("/{monitoring_id}/termos")
async def add_term(monitoring_id: str, text: str = Form(...), is_primary: bool = Form(False)) -> RedirectResponse:
    try:
        await monitoring_search_service.add_term(monitoring_id, text, is_primary)
        msg = "Termo cadastrado."
    except httpx.HTTPStatusError as exc:
        msg = "Esse termo já está cadastrado neste monitoramento." if exc.response.status_code == 409 else "Não foi possível cadastrar o termo."
    return RedirectResponse(url=f"/monitoramentos/{monitoring_id}?message={msg}", status_code=303)


@router.post("/{monitoring_id}/termos/{term_id}/editar")
async def edit_term(monitoring_id: str, term_id: str, text: str = Form(...)) -> RedirectResponse:
    try:
        await monitoring_search_service.update_term(term_id, text)
        msg = "Termo atualizado."
    except httpx.HTTPStatusError as exc:
        msg = "Esse termo já está cadastrado neste monitoramento." if exc.response.status_code == 409 else "Não foi possível atualizar o termo."
    return RedirectResponse(url=f"/monitoramentos/{monitoring_id}?message={msg}", status_code=303)


@router.post("/{monitoring_id}/termos/{term_id}/status")
async def term_status(monitoring_id: str, term_id: str, is_active: bool = Form(...)) -> RedirectResponse:
    await monitoring_search_service.set_term_active(term_id, is_active)
    return RedirectResponse(url=f"/monitoramentos/{monitoring_id}", status_code=303)


@router.post("/{monitoring_id}/termos/{term_id}/excluir")
async def delete_term(monitoring_id: str, term_id: str) -> RedirectResponse:
    await monitoring_search_service.delete_term(term_id)
    return RedirectResponse(url=f"/monitoramentos/{monitoring_id}?message=Termo excluído.", status_code=303)


@router.post("/{monitoring_id}/pesquisar", response_class=HTMLResponse)
async def run_search(request: Request, monitoring_id: str, period_hours: int = Form(24)) -> HTMLResponse:
    monitoring = await monitoring_search_service.get_monitoring(monitoring_id)
    terms = await monitoring_search_service.list_terms(monitoring_id)
    try:
        search, mentions, errors = await monitoring_search_service.execute(monitoring_id, period_hours)
        return templates.TemplateResponse(
            request=request,
            name="results.html",
            context={
                "app_name": "Oylut Clipping",
                "mentions": mentions,
                "errors": errors,
                "terms": [term["text"] for term in terms if term.get("is_active")],
                "period_hours": period_hours,
                "total": len(mentions),
                "monitoring": monitoring,
                "search_saved": True,
                "search": search,
            },
        )
    except (ValueError, httpx.HTTPError, RuntimeError) as exc:
        return templates.TemplateResponse(
            request=request,
            name="monitoring_detail.html",
            status_code=422,
            context={"monitoring": monitoring, "terms": terms, "error": str(exc), "message": None},
        )
