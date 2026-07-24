from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.schemas.search import SearchRequest
from app.services.search_service import search_mentions
from app.services.term_service import prepare_terms

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.post("/pesquisar", response_class=HTMLResponse)
async def search(
    request: Request,
    main_term: str = Form(...),
    variations: str = Form(default=""),
    period_hours: int = Form(default=24),
) -> HTMLResponse:
    variation_list = [line for line in variations.splitlines() if line.strip()]

    try:
        search_request = SearchRequest(
            main_term=main_term,
            variations=variation_list,
            period_hours=period_hours,
        )
    except ValidationError:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            status_code=422,
            context={
                "app_name": "Oylut Clipping",
                "error": "Preencha um termo com pelo menos dois caracteres.",
                "form": {
                    "main_term": main_term,
                    "variations": variations,
                    "period_hours": period_hours,
                },
            },
        )

    terms = prepare_terms(search_request.main_term, search_request.variations)
    mentions, errors = await search_mentions(terms, search_request.period_hours)

    return templates.TemplateResponse(
        request=request,
        name="results.html",
        context={
            "app_name": "Oylut Clipping",
            "mentions": mentions,
            "errors": errors,
            "terms": terms,
            "period_hours": search_request.period_hours,
            "total": len(mentions),
        },
    )
