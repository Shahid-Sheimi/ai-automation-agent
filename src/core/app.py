from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from src.core.whatsapp_webhook import whatsapp_router
from src.api.rest_api import api_router

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

app.include_router(whatsapp_router)
app.include_router(api_router)


@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})


@app.get("/track", response_class=HTMLResponse)
async def track_page(request: Request):
    return templates.TemplateResponse(request, "track.html", {"request": request})


@app.get("/order", response_class=HTMLResponse)
async def order_page(request: Request):
    return templates.TemplateResponse(request, "order.html", {"request": request})


@app.get("/shipping", response_class=HTMLResponse)
async def shipping_page(request: Request):
    return templates.TemplateResponse(request, "shipping.html", {"request": request})


@app.get("/lost", response_class=HTMLResponse)
async def lost_page(request: Request):
    return templates.TemplateResponse(request, "policy.html", {"request": request, "page_type": "lost"})


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse(request, "chat.html", {"request": request})
