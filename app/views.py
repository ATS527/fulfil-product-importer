from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models import Product, Webhook

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@router.get("/products-ui")
async def products_ui(request: Request, page: int = 1, limit: int = 20, db: AsyncSession = Depends(get_db)):
    offset = (page - 1) * limit
    result = await db.execute(select(Product).offset(offset).limit(limit))
    products = result.scalars().all()
    return templates.TemplateResponse("products.html", {"request": request, "products": products, "page": page})

@router.get("/webhooks-ui")
async def webhooks_ui(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Webhook))
    webhooks = result.scalars().all()
    return templates.TemplateResponse("webhooks.html", {"request": request, "webhooks": webhooks})
