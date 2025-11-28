from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from app.tasks import process_csv_upload
import shutil
import os
import uuid
import asyncio
import redis

from app.config import settings

router = APIRouter()

UPLOAD_DIR = settings.UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)

redis_client = redis.Redis.from_url(settings.CELERY_BROKER_URL)

@router.post("/upload")
async def upload_products(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a CSV file.")

    task_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{task_id}.csv")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    task = process_csv_upload.delay(file_path, task_id)

    return {"task_id": task_id, "message": "File uploaded successfully. Processing started."}

@router.get("/progress/{task_id}")
async def get_progress(task_id: str):
    async def event_generator():
        while True:
            progress = redis_client.get(f"progress:{task_id}")
            if progress:
                yield f"data: {int(progress)}\n\n"
                if int(progress) >= 100:
                    break
            else:
                yield f"data: 0\n\n"
            
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
