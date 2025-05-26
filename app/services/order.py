from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app import models, schemas
from app.services import client as client_service
from app.services import product as product_service
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

def get_order(db: Session, order_id: int) -> models.Order | None:
    return db.query(models.Order).filter(models.Order.id == order_id).first()

def get_orders(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    product_section: Optional[str] = None,
    order_id: Optional[int] = None,
    status: Optional[str] = None,
    client_id: Optional[int] = None
) -> List[models.Order]:
    query = db.query(models.Order)

    if order_id is not None:
        query = query.filter(models.Order.id == order_id)
    if client_id is not None:
        query = query.filter(models.Order.client_id == client_id)
    if status:
        query = query.filter(models.Order.status.ilike(f"%{status}%"))
    if start_date:
        query = query.filter(models.Order.created_at >= start_date)
    if end_date:
        # Add 1 day to end_date to include the whole day
        # query = query.filter(models.Order.created_at < (end_date + timedelta(days=1)))
        query = query.filter(models.Order.created_at <= end_date)
    if product_section:
        # This requires joining OrderItem and Product tables
        query = query.join(models.OrderItem).join(models.Product)
        query = query.filter(models.Product.section.ilike(f"%{product_section}%"))
        # Ensure distinct orders if multiple items match the section
        query = query.distinct()

    return query.offset(skip).limit(limit).all()

def create_order(db: Session, order_in: schemas.OrderCreate) -> models.Order:
    # 1. Validate Client exists
    db_client = client_service.get_client(db, order_in.client_id)
    if not db_client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Client with id {order_in.client_id} not found")

    total_order_value = Decimal("0.00")
    order_items_to_create = []
    product_stock_updates = [] # Keep track of stock changes

    # 2. Validate Products and Stock for each item
    for item_in in order_in.items:
        db_product = product_service.get_product(db, item_in.product_id)
        if not db_product:
            db.rollback() # Rollback if any product is invalid
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with id {item_in.product_id} not found")

        if db_product.current_stock < item_in.quantity:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Insufficient stock for product id {item_in.product_id}. Available: {db_product.current_stock}, Requested: {item_in.quantity}")

        # Calculate item total and add to order total
        item_total = db_product.sale_value * item_in.quantity
        total_order_value += item_total

        # Prepare OrderItem data
        order_item_data = {
            "product_id": item_in.product_id,
            "quantity": item_in.quantity,
            "unit_price": db_product.sale_value # Store price at time of order
        }
        order_items_to_create.append(order_item_data)

        # Track stock update needed for this product
        product_stock_updates.append({"product_id": item_in.product_id, "change": -item_in.quantity})

    # 3. Create Order and OrderItems within a transaction
    try:
        db_order = models.Order(
            client_id=order_in.client_id,
            status=order_in.status or "pending",
            total_value=total_order_value
        )
        db.add(db_order)
        db.flush() # Flush to get the db_order.id for OrderItems

        for item_data in order_items_to_create:
            db_order_item = models.OrderItem(**item_data, order_id=db_order.id)
            db.add(db_order_item)

        # 4. Update Product Stock
        for stock_update in product_stock_updates:
            # Use the adjust_stock function (or similar logic)
            # Ensure product is fetched again within the session if needed, or pass db_product
            product_to_update = product_service.get_product(db, stock_update["product_id"])
            if product_to_update: # Should always exist based on earlier check
                product_to_update.current_stock += stock_update["change"]
                db.add(product_to_update)
            else:
                 # This case should ideally not happen due to prior checks
                 raise Exception(f"Product {stock_update['product_id']} not found during stock update.")

        db.commit()
        db.refresh(db_order)
        # Eager load relationships if needed for the response schema
        # db.refresh(db_order, relationship_names=["items", "client"]) # Check attribute names
        return db_order

    except Exception as e:
        db.rollback()
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create order: {str(e)}")

def update_order(db: Session, order_id: int, order_update: schemas.OrderUpdate) -> models.Order | None:
    db_order = get_order(db, order_id)
    if not db_order:
        return None

    update_data = order_update.model_dump(exclude_unset=True)

    # Primarily handle status updates
    if "status" in update_data:
        # Add validation for allowed status transitions if needed
        db_order.status = update_data["status"]

    # Updating items or client_id is generally complex and might be disallowed
    # If allowed, ensure stock adjustments and total value recalculations are handled

    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

def delete_order(db: Session, order_id: int) -> int | None:
    db_order = get_order(db, order_id)
    if not db_order:
        return None

    # Consider implications: Deleting an order might require stock adjustments
    # if items are returned to inventory, depending on the order status and business rules.
    # Soft delete (adding 'is_deleted' flag) is often safer.
    # Current implementation: Hard delete (requires cascade delete on OrderItems)

    # Optional: Add stock back if order is cancelled/deleted (complex logic based on status)
    # if db_order.status == 'cancelled': # Example condition
    #     for item in db_order.items:
    #         product_service.adjust_stock(db, item.product_id, item.quantity)

    deleted_order_id = db_order.id # Store ID before deleting
    db.delete(db_order)
    db.commit()
    # No need to refresh a deleted object
    return deleted_order_id # Return only the ID

