import io
import json
from pathlib import Path

import httpx
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

from app.services.clipping_service import clipping_service

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=BASE_DIR / "templates")
router = APIRouter(prefix="/clippings", tags=["clippings"])

async def clipping_storage_available() -> bool:
    try:
        await clipping_service.list_clippings(); return True
    except (httpx.HTTPError, RuntimeError):
        return False

@router.get("/revisar", response_class=HTMLResponse)
async def review_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="clipping_review.html", context={"app_name":"Oylut Clipping","setup_pending":not await clipping_storage_available()})

@router.post("", response_class=HTMLResponse)
async def create_clipping(request: Request, title: str=Form(...), items_json: str=Form(...), monitoring_id: str=Form(""), search_id: str=Form(""), client_name: str=Form(""), monitoring_name: str=Form("")) -> HTMLResponse:
    try:
        items=json.loads(items_json)
        if not isinstance(items,list) or not items: raise ValueError("Selecione ao menos uma publicação.")
        clipping=await clipping_service.create(title=title,items=items,monitoring_id=monitoring_id or None,search_id=search_id or None,client_name=client_name or None,monitoring_name=monitoring_name or None)
    except (ValueError,json.JSONDecodeError) as exc:
        return templates.TemplateResponse(request=request,name="clipping_review.html",status_code=422,context={"app_name":"Oylut Clipping","form_message":str(exc),"setup_pending":False})
    except (httpx.HTTPError,RuntimeError):
        return templates.TemplateResponse(request=request,name="clipping_review.html",status_code=503,context={"app_name":"Oylut Clipping","setup_pending":True})
    return RedirectResponse(url=f"/clippings/{clipping['id']}",status_code=303)

@router.get("", response_class=HTMLResponse)
async def clipping_history(request: Request) -> HTMLResponse:
    try: clippings=await clipping_service.list_clippings(); setup_pending=False
    except (httpx.HTTPError,RuntimeError): clippings=[]; setup_pending=True
    return templates.TemplateResponse(request=request,name="clippings.html",context={"clippings":clippings,"setup_pending":setup_pending})

@router.get("/{clipping_id}", response_class=HTMLResponse)
async def clipping_detail(request: Request, clipping_id: str) -> HTMLResponse:
    try: clipping=await clipping_service.get(clipping_id); items=await clipping_service.list_items(clipping_id) if clipping else []
    except (httpx.HTTPError,RuntimeError): return RedirectResponse(url="/clippings",status_code=303)
    if not clipping: return RedirectResponse(url="/clippings",status_code=303)
    return templates.TemplateResponse(request=request,name="clipping_detail.html",context={"clipping":clipping,"items":items})

@router.post("/{clipping_id}/excluir")
async def delete_clipping(clipping_id: str) -> RedirectResponse:
    try: await clipping_service.delete(clipping_id)
    except (httpx.HTTPError,RuntimeError): pass
    return RedirectResponse(url="/clippings",status_code=303)

@router.get("/{clipping_id}/pdf")
async def clipping_pdf(clipping_id: str) -> StreamingResponse:
    clipping=await clipping_service.get(clipping_id); items=await clipping_service.list_items(clipping_id) if clipping else []
    if not clipping: return StreamingResponse(io.BytesIO(b""),status_code=404,media_type="application/pdf")
    buffer=io.BytesIO(); document=SimpleDocTemplate(buffer,pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=18*mm,bottomMargin=18*mm,title=clipping["title"],author="Oylut Clipping")
    styles=getSampleStyleSheet(); title_style=ParagraphStyle("OylutTitle",parent=styles["Title"],fontSize=22,leading=27,spaceAfter=8); meta_style=ParagraphStyle("OylutMeta",parent=styles["Normal"],fontSize=9,textColor="#555555",spaceAfter=14); item_title=ParagraphStyle("ItemTitle",parent=styles["Heading2"],fontSize=13,leading=17,spaceAfter=5)
    labels={"positive":"Positivo","neutral":"Neutro","negative":"Negativo"}; counts={key:sum(1 for item in items if item.get("sentiment")==key) for key in labels}
    body=[Paragraph(clipping["title"],title_style)]; metadata="Oylut Clipping"
    if clipping.get("client_name"): metadata+=f" · {clipping['client_name']}"
    if clipping.get("monitoring_name"): metadata+=f" · {clipping['monitoring_name']}"
    metadata+=f" · {len(items)} publicações"; body.append(Paragraph(metadata,meta_style)); body.append(Paragraph(f"<b>Sentimento:</b> {counts['positive']} positivas · {counts['neutral']} neutras · {counts['negative']} negativas",styles["Normal"])); body.append(Spacer(1,12))
    for index,item in enumerate(items,start=1):
        body.append(Paragraph(f"{index}. {item['title']}",item_title)); body.append(Paragraph(f"<b>Fonte:</b> {item['source']}",styles["Normal"]))
        if item.get("sentiment"): body.append(Paragraph(f"<b>Sentimento:</b> {labels.get(item['sentiment'],item['sentiment'])}",styles["Normal"]))
        if item.get("matched_term"): body.append(Paragraph(f"<b>Termo encontrado:</b> {item['matched_term']}",styles["Normal"]))
        if item.get("published_at"): body.append(Paragraph(f"<b>Publicado em:</b> {item['published_at']}",styles["Normal"]))
        if item.get("excerpt"): body.extend([Spacer(1,4),Paragraph(item["excerpt"],styles["BodyText"])])
        body.extend([Spacer(1,4),Paragraph(f"<link href='{item['url']}' color='blue'>{item['url']}</link>",styles["Normal"]),Spacer(1,12)])
        if index%5==0 and index<len(items): body.append(PageBreak())
    document.build(body); buffer.seek(0)
    return StreamingResponse(buffer,media_type="application/pdf",headers={"Content-Disposition":f'attachment; filename="clipping-{clipping_id}.pdf"'})
