from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app import schemas, services, models
from app.schemas import message # Corrected import
from app.database import get_db
from app.core import security

router = APIRouter()

@router.post("/", response_model=schemas.Order, status_code=status.HTTP_201_CREATED, tags=["orders"])
def create_order(
    order_in: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user) # Require authentication
):
    """
    Create a new order.

    Requires authentication. Validates product existence and stock availability.
    - **client_id**: ID of the client placing the order.
    - **status**: (Optional) Initial status of the order (defaults to 'pending').
    - **items**: List of items in the order:
        - **product_id**: ID of the product.
        - **quantity**: Quantity of the product.
    """
    # Authorization: Any active user can create an order for now.
    # Could add logic to check if client_id matches user or if user is admin.
    try:
        return services.order.create_order(db=db, order_in=order_in)
    except HTTPException as e:
        raise e
    except Exception as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not create order: {str(e)}")

@router.get("/", response_model=List[schemas.Order], tags=["orders"])
def read_orders(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[datetime] = Query(None, alias="periodo_inicio", description="Filter orders created on or after this date/time"),
    end_date: Optional[datetime] = Query(None, alias="periodo_fim", description="Filter orders created on or before this date/time"),
    product_section: Optional[str] = Query(None, alias="secao_produto", description="Filter orders containing products from a specific section"),
    order_id: Optional[int] = Query(None, alias="id_pedido", description="Filter by specific order ID"),
    status: Optional[str] = Query(None, description="Filter orders by status (case-insensitive partial match)"),
    client_id: Optional[int] = Query(None, alias="cliente_id", description="Filter orders by client ID"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user) # Require authentication
):
    """
    Retrieve a list of orders with pagination and filtering.

    Requires authentication.
    - **skip**: Number of orders to skip.
    - **limit**: Maximum number of orders to return.
    - **periodo_inicio**: Filter by start date/time.
    - **periodo_fim**: Filter by end date/time.
    - **secao_produto**: Filter by product section.
    - **id_pedido**: Filter by order ID.
    - **status**: Filter by order status.
    - **cliente_id**: Filter by client ID.
    """
    # Authorization: Allow any authenticated user to list orders for now.
    # Could restrict to own orders or admin view.
    orders = services.order.get_orders(
        db, skip=skip, limit=limit,
        start_date=start_date, end_date=end_date,
        product_section=product_section, order_id=order_id,
        status=status, client_id=client_id
    )
    return orders

@router.get("/{order_id}", response_model=schemas.Order, tags=["orders"])
def read_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user) # Require authentication
):
    """
    Get a specific order by ID.

    Requires authentication.
    """
    db_order = services.order.get_order(db, order_id=order_id)
    if db_order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    # Authorization: Allow user to see any order if authenticated.
    # Could add check: if not current_user.is_superuser and db_order.client_id != current_user.client_id (if users are linked to clients)
    return db_order

@router.put("/{order_id}", response_model=schemas.Order, tags=["orders"])
def update_order(
    order_id: int,
    order_in: schemas.OrderUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user) # Require authentication
    # Potentially require superuser for certain status changes
):
    """
    Update an order's information, primarily its status.

    Requires authentication.
    - **status**: New status for the order.
    """
    # Authorization: Allow authenticated user to update status.
    # Could restrict based on current status or user role.
    # Example: if not current_user.is_superuser and order_in.status == 'cancelled': raise HTTPException(...) 
    try:
        updated_order = services.order.update_order(db=db, order_id=order_id, order_update=order_in)
        if updated_order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        return updated_order
    except HTTPException as e:
        raise e
    except Exception as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update order")

@router.delete("/{order_id}", response_model=schemas.message.OrderDeleteResponse, tags=["orders"])
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_superuser) # Require superuser
):
    """
    Delete an order.

    Requires superuser authentication.
    Note: Consider implications like stock adjustments if deleting cancelled orders.
    """
    deleted_order_id = services.order.delete_order(db=db, order_id=order_id)
    if deleted_order_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    # Consider stock adjustment logic here or in the service based on business rules
    return {"id": deleted_order_id, "detail": "Order deleted successfully"}

