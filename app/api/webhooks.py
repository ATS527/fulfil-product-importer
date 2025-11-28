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
async def list_webhooks():
    db = get_db()
    result = await db.execute(select(Webhook))
    return result.scalars().all()

@router.post("/webhooks", response_model=WebhookResponse)
async def create_webhook(webhook: WebhookCreate):
    db = get_db()
    new_webhook = Webhook(**webhook.dict())
    db.add(new_webhook)
    await db.commit()
    await db.refresh(new_webhook)
    return new_webhook

@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: int):
    db = get_db()
    result = await db.execute(select(Webhook).filter(Webhook.id == webhook_id))
    webhook = result.scalars().first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    await db.delete(webhook)
    await db.commit()
    return {"message": "Webhook deleted successfully"}
