from pathlib import Path

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.services.history_service import history_service

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=BASE_DIR / "templates")
router = APIRouter(prefix="/historico", tags=["historico"])


@router.get("", response_class=HTMLResponse)
async def history_page(request: Request) -> HTMLResponse:
    error = None
    try:
        searches = await history_service.list_searches()
    except (httpx.HTTPError, RuntimeError) as exc:
        searches = []
        error = f"Não foi possível acessar o histórico: {exc}"

    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={"searches": searches, "error": error},
    )


@router.post("/limpar")
async def clear_history() -> RedirectResponse:
    await history_service.clear_history()
    return RedirectResponse(url="/historico", status_code=303)


@router.post("/{search_id}/excluir")
async def delete_history_search(search_id: str) -> RedirectResponse:
    await history_service.delete_search(search_id)
    return RedirectResponse(url="/historico", status_code=303)


@router.get("/{search_id}", response_class=HTMLResponse)
async def history_results(request: Request, search_id: str) -> HTMLResponse:
    try:
        search = await history_service.get_search(search_id)
        results = await history_service.list_results(search_id)
    except (httpx.HTTPError, RuntimeError) as exc:
        return templates.TemplateResponse(
            request=request,
            name="history.html",
            status_code=502,
            context={"searches": [], "error": f"Não foi possível abrir a pesquisa: {exc}"},
        )

    if search is None:
        return templates.TemplateResponse(
            request=request,
            name="history.html",
            status_code=404,
            context={"searches": [], "error": "Pesquisa não encontrada."},
        )

    return templates.TemplateResponse(
        request=request,
        name="results.html",
        context={
            "app_name": "Oylut Clipping",
            "mentions": results,
            "errors": [search["error_message"]] if search.get("error_message") else [],
            "terms": [],
            "period_hours": search["period_hours"],
            "total": len(results),
            "monitoring": search.get("monitorings"),
            "search": search,
            "from_history": True,
        },
    )
