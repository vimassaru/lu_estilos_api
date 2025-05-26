from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app import schemas, services, models
from app.database import get_db
from app.core import security

router = APIRouter()

@router.post("/", response_model=schemas.Client, status_code=status.HTTP_201_CREATED, tags=["clients"])
def create_client(
    client_in: schemas.ClientCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user) # Require authentication
    # Add authorization if needed, e.g., Depends(security.get_current_active_superuser)
):
    """
    Create a new client.

    Requires authentication. Only admins might be allowed based on rules.
    - **name**: Client's full name.
    - **email**: Client's email (must be unique).
    - **cpf**: Client's CPF (must be unique).
    - **phone**: (Optional) Client's phone number.
    - **address**: (Optional) Client's address.
    """
    # Authorization check (example: only superusers can create clients)
    # if not current_user.is_superuser:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    try:
        return services.client.create_client(db=db, client=client_in)
    except HTTPException as e:
        raise e
    except Exception as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create client")

@router.get("/", response_model=List[schemas.Client], tags=["clients"])
def read_clients(
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = Query(None, description="Filter clients by name (case-insensitive partial match)"),
    email: Optional[str] = Query(None, description="Filter clients by email (case-insensitive partial match)"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user) # Require authentication
):
    """
    Retrieve a list of clients with pagination and filtering.

    Requires authentication.
    - **skip**: Number of clients to skip.
    - **limit**: Maximum number of clients to return.
    - **name**: Filter by client name.
    - **email**: Filter by client email.
    """
    clients = services.client.get_clients(db, skip=skip, limit=limit, name=name, email=email)
    return clients

@router.get("/{client_id}", response_model=schemas.Client, tags=["clients"])
def read_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user) # Require authentication
):
    """
    Get a specific client by ID.

    Requires authentication.
    """
    db_client = services.client.get_client(db, client_id=client_id)
    if db_client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    # Add authorization check if users should only see specific clients (e.g., related orders)
    return db_client

@router.put("/{client_id}", response_model=schemas.Client, tags=["clients"])
def update_client(
    client_id: int,
    client_in: schemas.ClientUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user) # Require authentication
    # Add authorization if needed, e.g., Depends(security.get_current_active_superuser)
):
    """
    Update a client's information.

    Requires authentication. Only admins might be allowed based on rules.
    """
    # Authorization check (example: only superusers can update clients)
    # if not current_user.is_superuser:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    try:
        updated_client = services.client.update_client(db=db, client_id=client_id, client_update=client_in)
        if updated_client is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        return updated_client
    except HTTPException as e:
        raise e
    except Exception as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update client")

@router.delete("/{client_id}", response_model=schemas.Client, tags=["clients"])
def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_superuser) # Require superuser authentication
):
    """
    Delete a client.

    Requires superuser authentication.
    Note: Consider implications for related orders (cascade delete, soft delete, prevent deletion).
    """
    deleted_client = services.client.delete_client(db=db, client_id=client_id)
    if deleted_client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return deleted_client # Returns the client object that was deleted

