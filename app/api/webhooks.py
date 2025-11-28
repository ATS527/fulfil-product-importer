from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from typing import List
from app.database import get_db
from app.models import Webhook
from app.schemas import WebhookCreate, WebhookResponse

router = APIRouter()

@router.get("/webhooks", response_model=List[WebhookResponse])
async def list_webhooks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Webhook))
    return result.scalars().all()

from fastapi import Form, Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

@router.post("/webhooks")
async def create_webhook(
    request: Request,
    url: str = Form(...), 
    event_type: str = Form(...), 
    db: AsyncSession = Depends(get_db)
):
    webhook_data = WebhookCreate(url=url, event_type=event_type)
    new_webhook = Webhook(**webhook_data.dict())
    db.add(new_webhook)
    await db.commit()
    await db.refresh(new_webhook)
    
    return templates.TemplateResponse("partials/webhook_row.html", {"request": request, "webhook": new_webhook})

@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Webhook).filter(Webhook.id == webhook_id))
    webhook = result.scalars().first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    await db.delete(webhook)
    await db.commit()
    return {"message": "Webhook deleted successfully"}

@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(request: Request, webhook_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Webhook).filter(Webhook.id == webhook_id))
    webhook = result.scalars().first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    import requests
    import time
    
    start_time = time.time()
    try:
        response = requests.post(
            webhook.url, 
            json={
                "event": "test", 
                "message": "This is a test event from Acme Importer",
                "timestamp": time.time()
            }, 
            timeout=5
        )
        duration = int((time.time() - start_time) * 1000)
        status_code = response.status_code
        success = 200 <= status_code < 300
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        status_code = "Error"
        success = False
        
    return templates.TemplateResponse(
        "partials/webhook_test_result.html", 
        {
            "request": request, 
            "success": success, 
            "status_code": status_code, 
            "duration": duration
        }
    )
