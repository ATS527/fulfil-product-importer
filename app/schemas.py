from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True

class ProductCreate(ProductBase):
    sku: str

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class ProductResponse(ProductBase):
    sku: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class WebhookBase(BaseModel):
    url: str
    event_type: str
    is_active: bool = True

class WebhookCreate(WebhookBase):
    pass

class WebhookResponse(WebhookBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
