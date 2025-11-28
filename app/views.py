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
async def products_ui(
    request: Request, 
    page: int = 1, 
    limit: int = 20, 
    search: str = None, 
    is_active: str = None,
    db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * limit
    query = select(Product)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Product.sku.ilike(search_filter)) | 
            (Product.name.ilike(search_filter)) |
            (Product.description.ilike(search_filter))
        )
    
    if is_active and is_active != "all":
        active_bool = is_active.lower() == "true"
        query = query.filter(Product.is_active == active_bool)
        
    # Get total count for pagination (optional but good for UX, skipping for now to keep it simple)
    
    result = await db.execute(query.offset(offset).limit(limit))
    products = result.scalars().all()
    
    return templates.TemplateResponse(
        "products.html", 
        {
            "request": request, 
            "products": products, 
            "page": page, 
            "search": search, 
            "is_active": is_active
        }
    )

@router.get("/webhooks-ui")
async def webhooks_ui(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Webhook))
    webhooks = result.scalars().all()
    return templates.TemplateResponse("webhooks.html", {"request": request, "webhooks": webhooks})

@router.get("/products-ui/row/{sku}")
async def get_product_row(request: Request, sku: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).filter(Product.sku == sku))
    product = result.scalars().first()
    return templates.TemplateResponse("partials/product_row.html", {"request": request, "product": product})

@router.get("/products-ui/row/{sku}/edit")
async def get_product_edit_row(request: Request, sku: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).filter(Product.sku == sku))
    product = result.scalars().first()
    return templates.TemplateResponse("partials/product_edit_row.html", {"request": request, "product": product})

from app.schemas import ProductUpdate
from fastapi import Form

@router.put("/products-ui/row/{sku}")
async def update_product_row(
    request: Request, 
    sku: str, 
    name: str = Form(...), 
    description: str = Form(None), 
    is_active: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Product).filter(Product.sku == sku))
    product = result.scalars().first()
    
    if product:
        product.name = name
        product.description = description
        product.is_active = is_active.lower() == 'true'
        await db.commit()
        await db.refresh(product)
        
        # Trigger webhook
        from app.tasks import trigger_webhooks
        trigger_webhooks.delay("product.updated", {"sku": sku})
        
    return templates.TemplateResponse("partials/product_row.html", {"request": request, "product": product})

@router.get("/webhooks-ui/row/{webhook_id}")
async def get_webhook_row(request: Request, webhook_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Webhook).filter(Webhook.id == webhook_id))
    webhook = result.scalars().first()
    return templates.TemplateResponse("partials/webhook_row.html", {"request": request, "webhook": webhook})

@router.get("/webhooks-ui/row/{webhook_id}/edit")
async def get_webhook_edit_row(request: Request, webhook_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Webhook).filter(Webhook.id == webhook_id))
    webhook = result.scalars().first()
    return templates.TemplateResponse("partials/webhook_edit_row.html", {"request": request, "webhook": webhook})

@router.put("/webhooks-ui/row/{webhook_id}")
async def update_webhook_row(
    request: Request, 
    webhook_id: int, 
    url: str = Form(...), 
    event_type: str = Form(...), 
    is_active: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Webhook).filter(Webhook.id == webhook_id))
    webhook = result.scalars().first()
    
    if webhook:
        webhook.url = url
        webhook.event_type = event_type
        webhook.is_active = is_active.lower() == 'true'
        await db.commit()
        await db.refresh(webhook)
        
    return templates.TemplateResponse("partials/webhook_row.html", {"request": request, "webhook": webhook})
