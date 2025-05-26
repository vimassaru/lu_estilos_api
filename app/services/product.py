from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app import models, schemas
from typing import List, Optional
from decimal import Decimal

def get_product(db: Session, product_id: int) -> models.Product | None:
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def get_product_by_barcode(db: Session, barcode: str) -> models.Product | None:
    if not barcode:
        return None
    return db.query(models.Product).filter(models.Product.barcode == barcode).first()

def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None, # Assuming 'section' is the category
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    available: Optional[bool] = None
) -> List[models.Product]:
    query = db.query(models.Product)
    if category:
        query = query.filter(models.Product.section.ilike(f"%{category}%"))
    if min_price is not None:
        query = query.filter(models.Product.sale_value >= min_price)
    if max_price is not None:
        query = query.filter(models.Product.sale_value <= max_price)
    if available is not None:
        if available:
            query = query.filter(models.Product.current_stock > 0)
        else:
            query = query.filter(models.Product.current_stock <= 0)

    return query.offset(skip).limit(limit).all()

def create_product(db: Session, product: schemas.ProductCreate) -> models.Product:
    # Validate unique barcode if provided
    if product.barcode:
        db_product_barcode = get_product_by_barcode(db, barcode=product.barcode)
        if db_product_barcode:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Barcode already registered")

    # Set current_stock equal to initial_stock on creation
    db_product = models.Product(**product.model_dump(), current_stock=product.initial_stock)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, product_update: schemas.ProductUpdate) -> models.Product | None:
    db_product = get_product(db, product_id)
    if not db_product:
        return None

    update_data = product_update.model_dump(exclude_unset=True)

    # Check for potential unique constraint violations before updating barcode
    if "barcode" in update_data and update_data["barcode"] and update_data["barcode"] != db_product.barcode:
        existing_product = get_product_by_barcode(db, update_data["barcode"])
        if existing_product:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Barcode already registered by another product")

    # Handle stock updates carefully - direct update vs dedicated stock adjustment logic
    # If current_stock is updated, ensure it's not negative unless allowed
    if "current_stock" in update_data and update_data["current_stock"] < 0:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current stock cannot be negative")

    for key, value in update_data.items():
        setattr(db_product, key, value)

    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def delete_product(db: Session, product_id: int) -> models.Product | None:
    db_product = get_product(db, product_id)
    if not db_product:
        return None
    # Consider implications: deleting a product might affect existing orders.
    # Usually, products are marked inactive rather than deleted if they are part of orders.
    # Add an 'is_active' flag to the Product model for soft deletes.
    # Current implementation: Hard delete.
    db.delete(db_product)
    db.commit()
    return db_product

# Function to adjust stock (example - could be more complex)
def adjust_stock(db: Session, product_id: int, quantity_change: int) -> models.Product:
    db_product = get_product(db, product_id)
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    new_stock = db_product.current_stock + quantity_change
    if new_stock < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock")

    db_product.current_stock = new_stock
    db.add(db_product)
    # Note: Commit might happen within the calling function (e.g., create_order)
    # db.commit()
    # db.refresh(db_product)
    return db_product

