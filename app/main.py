from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.database import engine, Base
import os

from app.api import upload, products, webhooks
from app import views

app = FastAPI(title="Product Importer")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

app.include_router(upload.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")
app.include_router(views.router)

@app.on_event("startup")
async def startup():
    # Create tables (for simplicity in this demo, usually use Alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
async def root():
    return {"message": "Welcome to Product Importer"}
