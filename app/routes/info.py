from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=BASE_DIR / "templates")
router = APIRouter(tags=["informacoes"])


@router.get("/minha-conta", response_class=HTMLResponse)
async def account_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="info_page.html",
        context={
            "page_title": "Minha Conta",
            "page_kicker": "CONFIGURAÇÕES",
            "page_content": [
                "Defina como as pesquisas rápidas devem ser tratadas no Oylut Clipping.",
                "Os monitoramentos vinculados a clientes continuam sendo registrados automaticamente no histórico.",
            ],
            "version": "0.8.0",
        },
    )


@router.get("/nosso-proposito", response_class=HTMLResponse)
async def purpose_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="info_page.html",
        context={
            "page_title": "Nosso propósito",
            "page_kicker": "OYLUT CLIPPING",
            "page_content": [
                "O Oylut Clipping foi criado para apoiar assessorias e profissionais de comunicação no acompanhamento de menções a clientes, marcas e instituições.",
                "A proposta é concentrar buscas, resultados e histórico em um fluxo simples, mantendo a avaliação editorial sob responsabilidade humana.",
            ],
            "version": "0.8.0",
        },
    )


@router.get("/instrucoes", response_class=HTMLResponse)
async def instructions_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="info_page.html",
        context={
            "page_title": "Instruções",
            "page_kicker": "COMO USAR",
            "steps": [
                "Cadastre um cliente ou selecione um cliente existente.",
                "Crie um monitoramento para organizar o assunto acompanhado.",
                "Defina um termo principal e adicione termos secundários.",
                "Abra o monitoramento e toque em Pesquisar.",
                "Ative em Minha Conta o salvamento das pesquisas rápidas, quando desejar.",
                "Consulte e reabra pesquisas anteriores na página Histórico.",
            ],
            "version": "0.8.0",
        },
    )