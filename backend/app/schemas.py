from pydantic import BaseModel
from typing import Optional

class ProductBase(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    weight: Optional[float] = None
    volume: Optional[float] = None

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int

    class Config:
        from_attributes = True