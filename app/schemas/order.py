from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from .product import Product # Import Product schema for response model
from .client import Client # Import Client schema for response model

# Properties for items within an order
class OrderItemBase(BaseModel):
    product_id: int
    quantity: int

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemUpdate(BaseModel):
    quantity: Optional[int] = None

class OrderItemInDBBase(OrderItemBase):
    id: int
    order_id: int
    unit_price: Decimal # Price at the time of order
    product: Product # Include product details in the response

    class Config:
        from_attributes = True

class OrderItem(OrderItemInDBBase):
    pass

# Shared properties for Order
class OrderBase(BaseModel):
    client_id: int
    status: Optional[str] = "pending"

# Properties to receive via API on creation
class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

# Properties to receive via API on update
class OrderUpdate(BaseModel):
    status: Optional[str] = None
    # Updating items might be complex, potentially handled separately or disallowed
    # items: Optional[List[OrderItemUpdate]] = None

class OrderInDBBase(OrderBase):
    id: int
    total_value: Decimal
    created_at: datetime
    updated_at: Optional[datetime] = None
    client: Client # Include client details
    items: List[OrderItem] # Include item details

    class Config:
        from_attributes = True

# Additional properties stored in DB
class OrderInDB(OrderInDBBase):
    pass

# Additional properties to return via API
class Order(OrderInDBBase):
    pass

