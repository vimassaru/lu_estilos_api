from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app import models, schemas
from typing import List, Optional

def get_client(db: Session, client_id: int) -> models.Client | None:
    return db.query(models.Client).filter(models.Client.id == client_id).first()

def get_client_by_email(db: Session, email: str) -> models.Client | None:
    return db.query(models.Client).filter(models.Client.email == email).first()

def get_client_by_cpf(db: Session, cpf: str) -> models.Client | None:
    return db.query(models.Client).filter(models.Client.cpf == cpf).first()

def get_clients(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = None,
    email: Optional[str] = None
) -> List[models.Client]:
    query = db.query(models.Client)
    if name:
        query = query.filter(models.Client.name.ilike(f"%{name}%")) # Case-insensitive search
    if email:
        query = query.filter(models.Client.email.ilike(f"%{email}%"))
    return query.offset(skip).limit(limit).all()

def create_client(db: Session, client: schemas.ClientCreate) -> models.Client:
    # Validate unique email
    db_client_email = get_client_by_email(db, email=client.email)
    if db_client_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    # Validate unique CPF
    db_client_cpf = get_client_by_cpf(db, cpf=client.cpf)
    if db_client_cpf:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CPF already registered")

    # Add CPF validation logic here if needed (e.g., format check)

    db_client = models.Client(**client.model_dump()) # Use model_dump() for Pydantic v2
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

def update_client(db: Session, client_id: int, client_update: schemas.ClientUpdate) -> models.Client | None:
    db_client = get_client(db, client_id)
    if not db_client:
        return None

    update_data = client_update.model_dump(exclude_unset=True)

    # Check for potential unique constraint violations before updating
    if "email" in update_data and update_data["email"] != db_client.email:
        existing_client = get_client_by_email(db, update_data["email"])
        if existing_client:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered by another client")

    if "cpf" in update_data and update_data["cpf"] != db_client.cpf:
        existing_client = get_client_by_cpf(db, update_data["cpf"])
        if existing_client:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CPF already registered by another client")

    for key, value in update_data.items():
        setattr(db_client, key, value)

    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

def delete_client(db: Session, client_id: int) -> models.Client | None:
    db_client = get_client(db, client_id)
    if not db_client:
        return None
    # Consider implications: deleting a client might require handling related orders.
    # Option 1: Cascade delete (defined in model relationship)
    # Option 2: Prevent deletion if orders exist
    # Option 3: Soft delete (add an 'is_deleted' flag)
    # Current implementation: Hard delete (if cascade is set up or no orders exist)
    db.delete(db_client)
    db.commit()
    return db_client

