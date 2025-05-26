from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# Shared properties
class ProductBase(BaseModel):
    description: str
    sale_value: Decimal
    barcode: Optional[str] = None
    section: Optional[str] = None
    initial_stock: int
    expiry_date: Optional[datetime] = None
    image_urls: Optional[str] = None # Could be a list of HttpUrl if validated/parsed

# Properties to receive via API on creation
class ProductCreate(ProductBase):
    pass

# Properties to receive via API on update
class ProductUpdate(BaseModel):
    description: Optional[str] = None
    sale_value: Optional[Decimal] = None
    barcode: Optional[str] = None
    section: Optional[str] = None
    # Stock updates might need a separate endpoint/logic (e.g., add/remove stock)
    # initial_stock: Optional[int] = None # Usually not updated directly
    current_stock: Optional[int] = None # Allow updating current stock
    expiry_date: Optional[datetime] = None
    image_urls: Optional[str] = None

class ProductInDBBase(ProductBase):
    id: int
    current_stock: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Additional properties stored in DB
class ProductInDB(ProductInDBBase):
    pass

# Additional properties to return via API
class Product(ProductInDBBase):
    pass

