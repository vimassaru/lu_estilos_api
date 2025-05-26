from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from app import schemas, services, models
from app.database import get_db
from app.core import security

router = APIRouter()

@router.post("/", response_model=schemas.Product, status_code=status.HTTP_201_CREATED, tags=["products"])
def create_product(
    product_in: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_superuser) # Require superuser
):
    """
    Create a new product.

    Requires superuser authentication.
    - **description**: Product description.
    - **sale_value**: Selling price.
    - **barcode**: (Optional) Unique barcode.
    - **section**: (Optional) Product category/section.
    - **initial_stock**: Initial stock quantity.
    - **expiry_date**: (Optional) Expiry date.
    - **image_urls**: (Optional) Comma-separated string of image URLs.
    """
    try:
        return services.product.create_product(db=db, product=product_in)
    except HTTPException as e:
        raise e
    except Exception as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create product")

@router.get("/", response_model=List[schemas.Product], tags=["products"])
def read_products(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = Query(None, alias="categoria", description="Filter by category/section (case-insensitive partial match)"),
    min_price: Optional[Decimal] = Query(None, alias="preco_min", description="Filter by minimum price"),
    max_price: Optional[Decimal] = Query(None, alias="preco_max", description="Filter by maximum price"),
    available: Optional[bool] = Query(None, alias="disponibilidade", description="Filter by availability (true=in stock, false=out of stock)"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user) # Require authentication
):
    """
    Retrieve a list of products with pagination and filtering.

    Requires authentication.
    - **skip**: Number of products to skip.
    - **limit**: Maximum number of products to return.
    - **categoria**: Filter by category/section.
    - **preco_min**: Filter by minimum price.
    - **preco_max**: Filter by maximum price.
    - **disponibilidade**: Filter by stock availability.
    """
    products = services.product.get_products(
        db, skip=skip, limit=limit, category=category, min_price=min_price, max_price=max_price, available=available
    )
    return products

@router.get("/{product_id}", response_model=schemas.Product, tags=["products"])
def read_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user) # Require authentication
):
    """
    Get a specific product by ID.

    Requires authentication.
    """
    db_product = services.product.get_product(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return db_product

@router.put("/{product_id}", response_model=schemas.Product, tags=["products"])
def update_product(
    product_id: int,
    product_in: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_superuser) # Require superuser
):
    """
    Update a product's information.

    Requires superuser authentication.
    """
    try:
        updated_product = services.product.update_product(db=db, product_id=product_id, product_update=product_in)
        if updated_product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return updated_product
    except HTTPException as e:
        raise e
    except Exception as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update product")

@router.delete("/{product_id}", response_model=schemas.Product, tags=["products"])
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_superuser) # Require superuser
):
    """
    Delete a product.

    Requires superuser authentication.
    Note: Consider implications (e.g., soft delete) if product is part of existing orders.
    """
    deleted_product = services.product.delete_product(db=db, product_id=product_id)
    if deleted_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return deleted_product

