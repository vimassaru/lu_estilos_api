from fastapi.testclient import TestClient
from app.core.config import settings
from app import schemas
import pytest
from decimal import Decimal

# Fixture to create a product for use in other tests
@pytest.fixture(scope="module")
def test_product_data(client: TestClient, superuser_token_headers) -> dict:
    product_data = {
        "description": "Test Product One",
        "sale_value": "19.99", # Use string for Decimal input
        "barcode": "1234567890123",
        "section": "Test Section",
        "initial_stock": 50,
        # "expiry_date": "2025-12-31T00:00:00", # Optional
        # "image_urls": "http://example.com/image1.jpg" # Optional
    }
    response = client.post(f"{settings.API_V1_STR}/products/", headers=superuser_token_headers, json=product_data)
    if response.status_code == 400 and "Barcode already registered" in response.text:
        # If product exists, try to get its data
        get_response = client.get(f"{settings.API_V1_STR}/products/?limit=1", headers=superuser_token_headers) # Simplistic get
        if get_response.status_code == 200 and get_response.json():
             # Find by barcode if possible, otherwise assume first is ok for test setup
             existing = [p for p in get_response.json() if p.get("barcode") == product_data["barcode"]]
             if existing:
                 return existing[0]
             pytest.fail(f"Failed to create or retrieve conflicting product: {product_data['barcode']}")

    assert response.status_code == 201, f"Failed to create product: {response.text}"
    created_product = response.json()
    # Ensure sale_value is Decimal or float after creation for comparison
    created_product["sale_value"] = Decimal(created_product["sale_value"])
    return created_product

# Test product creation
def test_create_product(client: TestClient, superuser_token_headers):
    product_data = {
        "description": "Test Product Two",
        "sale_value": "9.95",
        "barcode": "9876543210987",
        "section": "Another Section",
        "initial_stock": 10
    }
    response = client.post(f"{settings.API_V1_STR}/products/", headers=superuser_token_headers, json=product_data)
    assert response.status_code == 201
    created_product = response.json()
    assert created_product["description"] == product_data["description"]
    assert Decimal(created_product["sale_value"]) == Decimal(product_data["sale_value"])
    assert created_product["barcode"] == product_data["barcode"]
    assert created_product["initial_stock"] == product_data["initial_stock"]
    assert created_product["current_stock"] == product_data["initial_stock"] # Check current stock init
    assert "id" in created_product

def test_create_product_duplicate_barcode(client: TestClient, superuser_token_headers, test_product_data):
    product_data = {
        "description": "Duplicate Barcode Product",
        "sale_value": "5.00",
        "barcode": test_product_data["barcode"], # Use barcode from fixture
        "initial_stock": 5
    }
    response = client.post(f"{settings.API_V1_STR}/products/", headers=superuser_token_headers, json=product_data)
    assert response.status_code == 400
    assert "Barcode already registered" in response.json()["detail"]

def test_create_product_forbidden(client: TestClient, user_token_headers):
    # Regular user tries to create product
    product_data = {"description": "Forbidden Product", "sale_value": "1.00", "initial_stock": 1}
    response = client.post(f"{settings.API_V1_STR}/products/", headers=user_token_headers, json=product_data)
    assert response.status_code == 403 # Assuming create requires superuser

# Test reading products
def test_read_products(client: TestClient, user_token_headers, test_product_data):
    response = client.get(f"{settings.API_V1_STR}/products/", headers=user_token_headers)
    assert response.status_code == 200
    products = response.json()
    assert isinstance(products, list)
    assert any(p["id"] == test_product_data["id"] for p in products)

def test_read_products_filtered(client: TestClient, user_token_headers, test_product_data):
    # Filter by category (section)
    response_cat = client.get(f"{settings.API_V1_STR}/products/?categoria={test_product_data['section']}", headers=user_token_headers)
    assert response_cat.status_code == 200
    assert len(response_cat.json()) >= 1
    assert response_cat.json()[0]["section"] == test_product_data["section"]

    # Filter by price range
    price = test_product_data["sale_value"]
    response_price = client.get(f"{settings.API_V1_STR}/products/?preco_min={price}&preco_max={price}", headers=user_token_headers)
    assert response_price.status_code == 200
    assert len(response_price.json()) >= 1
    assert Decimal(response_price.json()[0]["sale_value"]) == Decimal(price)

    # Filter by availability (should be available)
    response_avail = client.get(f"{settings.API_V1_STR}/products/?disponibilidade=true", headers=user_token_headers)
    assert response_avail.status_code == 200
    assert any(p["id"] == test_product_data["id"] for p in response_avail.json())
    assert all(p["current_stock"] > 0 for p in response_avail.json())

    # Filter by availability (not available - assuming none are out of stock yet)
    response_not_avail = client.get(f"{settings.API_V1_STR}/products/?disponibilidade=false", headers=user_token_headers)
    assert response_not_avail.status_code == 200
    assert not any(p["id"] == test_product_data["id"] for p in response_not_avail.json())

def test_read_product(client: TestClient, user_token_headers, test_product_data):
    product_id = test_product_data["id"]
    response = client.get(f"{settings.API_V1_STR}/products/{product_id}", headers=user_token_headers)
    assert response.status_code == 200
    fetched_product = response.json()
    assert fetched_product["id"] == product_id
    assert fetched_product["description"] == test_product_data["description"]

def test_read_nonexistent_product(client: TestClient, user_token_headers):
    response = client.get(f"{settings.API_V1_STR}/products/99999", headers=user_token_headers)
    assert response.status_code == 404

# Test updating products
def test_update_product(client: TestClient, superuser_token_headers, test_product_data):
    product_id = test_product_data["id"]
    update_data = {"description": "Updated Product Description", "current_stock": 45}
    response = client.put(f"{settings.API_V1_STR}/products/{product_id}", headers=superuser_token_headers, json=update_data)
    assert response.status_code == 200
    updated_product = response.json()
    assert updated_product["id"] == product_id
    assert updated_product["description"] == update_data["description"]
    assert updated_product["current_stock"] == update_data["current_stock"]
    assert Decimal(updated_product["sale_value"]) == Decimal(test_product_data["sale_value"]) # Price shouldn't change

def test_update_product_negative_stock(client: TestClient, superuser_token_headers, test_product_data):
    product_id = test_product_data["id"]
    update_data = {"current_stock": -5}
    response = client.put(f"{settings.API_V1_STR}/products/{product_id}", headers=superuser_token_headers, json=update_data)
    assert response.status_code == 400 # Or 422 if Pydantic validation catches it earlier
    assert "stock cannot be negative" in response.json()["detail"]

def test_update_product_forbidden(client: TestClient, user_token_headers, test_product_data):
    product_id = test_product_data["id"]
    update_data = {"description": "Forbidden Update"}
    response = client.put(f"{settings.API_V1_STR}/products/{product_id}", headers=user_token_headers, json=update_data)
    assert response.status_code == 403 # Assuming update requires superuser

# Test deleting products
def test_delete_product(client: TestClient, superuser_token_headers):
    # Create a product specifically for deletion test
    product_to_delete = {"description": "Product To Delete", "sale_value": "1.00", "initial_stock": 1, "barcode": "4564564564564"}
    response_create = client.post(f"{settings.API_V1_STR}/products/", headers=superuser_token_headers, json=product_to_delete)
    assert response_create.status_code == 201
    product_id = response_create.json()["id"]

    # Delete the product
    response_delete = client.delete(f"{settings.API_V1_STR}/products/{product_id}", headers=superuser_token_headers)
    assert response_delete.status_code == 200
    assert response_delete.json()["id"] == product_id

    # Verify product is deleted
    response_get = client.get(f"{settings.API_V1_STR}/products/{product_id}", headers=superuser_token_headers)
    assert response_get.status_code == 404

def test_delete_product_forbidden(client: TestClient, user_token_headers, test_product_data):
    product_id = test_product_data["id"]
    response = client.delete(f"{settings.API_V1_STR}/products/{product_id}", headers=user_token_headers)
    assert response.status_code == 403 # Assuming delete requires superuser

def test_delete_nonexistent_product(client: TestClient, superuser_token_headers):
    response = client.delete(f"{settings.API_V1_STR}/products/99999", headers=superuser_token_headers)
    assert response.status_code == 404

