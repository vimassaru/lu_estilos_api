from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Shared properties
class ClientBase(BaseModel):
    name: str
    email: EmailStr
    cpf: str # Add validation in service layer
    phone: Optional[str] = None
    address: Optional[str] = None

# Properties to receive via API on creation
class ClientCreate(ClientBase):
    pass

# Properties to receive via API on update
class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    cpf: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class ClientInDBBase(ClientBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Additional properties stored in DB
class ClientInDB(ClientInDBBase):
    pass

# Additional properties to return via API
class Client(ClientInDBBase):
    pass

