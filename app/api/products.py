from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, func
from typing import List, Optional
from app.database import get_db
from app.models import Product
from app.schemas import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter()

@router.get("/products", response_model=List[ProductResponse])
async def list_products(
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Product)
    
    if search:
        # Simple case-insensitive search on SKU or Name
        search_filter = f"%{search}%"
        query = query.filter(
            (Product.sku.ilike(search_filter)) | 
            (Product.name.ilike(search_filter))
        )
    
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

from fastapi import Form, Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

@router.post("/products")
async def create_product(
    request: Request,
    sku: str = Form(...),
    name: str = Form(...),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    # Check if SKU exists
    existing = await db.execute(select(Product).filter(Product.sku == sku))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Product with this SKU already exists")
    
    new_product = Product(sku=sku, name=name, description=description, is_active=True)
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    
    # Trigger webhook
    from app.tasks import trigger_webhooks
    trigger_webhooks.delay("product.created", {"sku": sku})

    return templates.TemplateResponse("partials/product_row.html", {"request": request, "product": new_product})

@router.get("/products/{sku}", response_model=ProductResponse)
async def get_product(sku: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).filter(Product.sku == sku))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/products/{sku}", response_model=ProductResponse)
async def update_product(sku: str, product_update: ProductUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).filter(Product.sku == sku))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    
    await db.commit()
    await db.refresh(product)
    
    # Trigger webhook
    from app.tasks import trigger_webhooks
    trigger_webhooks.delay("product.updated", {"sku": sku})
    
    return product

@router.delete("/products/{sku}")
async def delete_product(sku: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).filter(Product.sku == sku))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    await db.delete(product)
    await db.commit()
    
    # Trigger webhook
    from app.tasks import trigger_webhooks
    trigger_webhooks.delay("product.deleted", {"sku": sku})
    
    return {"message": "Product deleted successfully"}

@router.delete("/products")
async def delete_all_products(db: AsyncSession = Depends(get_db)):
    # Using delete() instead of truncate for compatibility, though truncate is faster
    await db.execute(delete(Product))
    await db.commit()
    
    # Trigger webhook
    from app.tasks import trigger_webhooks
    trigger_webhooks.delay("product.deleted_all", {})
    
    return {"message": "All products deleted successfully"}
