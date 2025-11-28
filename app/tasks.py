from celery import Celery
import os
import csv
import asyncio
from app.database import AsyncSessionLocal
from app.models import Product
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert
import redis
import json
from sqlalchemy.sql import func

from app.config import settings

CELERY_BROKER_URL = settings.CELERY_BROKER_URL
CELERY_RESULT_BACKEND = settings.CELERY_RESULT_BACKEND

celery_app = Celery(
    "worker",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

redis_client = redis.Redis.from_url(CELERY_BROKER_URL)

async def upsert_chunk(chunk):
    async with AsyncSessionLocal() as session:
        values = [
            {
                "sku": row["sku"],
                "name": row["name"],
                "description": row["description"],
                "is_active": str(row.get("is_active", "true")).lower() == "true"
            }
            for row in chunk
        ]
        
        stmt = insert(Product).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=['sku'],
            set_={
                "name": stmt.excluded.name,
                "description": stmt.excluded.description,
                "is_active": stmt.excluded.is_active,
                "updated_at": func.now()
            }
        )
        await session.execute(stmt)
        await session.commit()

@celery_app.task(bind=True)
def process_csv_upload(self, file_path: str, task_id: str):
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    total_rows = 0
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        total_rows = sum(1 for _ in reader)

    chunk_size = 1000
    processed_rows = 0
    
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        chunk = []
        for row in reader:
            row['sku'] = row['sku'].lower()
            chunk.append(row)
            
            if len(chunk) >= chunk_size:
                # Deduplicate chunk to avoid CardinalityViolationError
                # If multiple rows in the same chunk have the same SKU, the last one wins
                deduplicated_chunk = list({r['sku']: r for r in chunk}.values())
                
                loop.run_until_complete(upsert_chunk(deduplicated_chunk))
                processed_rows += len(chunk) # Count total rows processed from CSV, even if some were deduped
                chunk = []
                
                progress = int((processed_rows / total_rows) * 100)
                redis_client.set(f"progress:{task_id}", progress)
                print(f"Updated progress for {task_id}: {progress}%")
                self.update_state(state='PROGRESS', meta={'current': processed_rows, 'total': total_rows, 'percent': progress})

        if chunk:
            deduplicated_chunk = list({r['sku']: r for r in chunk}.values())
            loop.run_until_complete(upsert_chunk(deduplicated_chunk))
            processed_rows += len(chunk)
            redis_client.set(f"progress:{task_id}", 100)
    
    os.remove(file_path)
    
    # Trigger webhooks after successful import
    if processed_rows > 0:
        trigger_webhooks.delay("product.import_completed", {"count": processed_rows})

    return {"status": "Completed", "total_processed": processed_rows}

@celery_app.task
def trigger_webhooks(event_type: str, payload: dict):
    import requests
    from app.database import AsyncSessionLocal
    from app.models import Webhook
    from sqlalchemy.future import select
    
    # Helper for async DB access in sync task
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    async def get_active_webhooks():
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Webhook).filter(Webhook.event_type == event_type, Webhook.is_active == True))
            return result.scalars().all()

    webhooks = loop.run_until_complete(get_active_webhooks())
    
    results = []
    for webhook in webhooks:
        try:
            response = requests.post(webhook.url, json=payload, timeout=5)
            results.append({"url": webhook.url, "status": response.status_code})
        except Exception as e:
            results.append({"url": webhook.url, "error": str(e)})
            
    return results
