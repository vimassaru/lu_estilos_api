from fastapi.testclient import TestClient
from app.core.config import settings
from app import schemas
import pytest
from decimal import Decimal

# Fixture to create an order for use in other tests
@pytest.fixture(scope="module")
def test_order_data(client: TestClient, user_token_headers, test_client_data, test_product_data) -> dict:
    # Ensure product has enough stock first
    product_id = test_product_data["id"]
    initial_stock = test_product_data["initial_stock"]
    if initial_stock < 2:
        # Update stock if needed for the test order
        update_payload = {"current_stock": 10} # Set a reasonable stock
        response_stock = client.put(f"{settings.API_V1_STR}/products/{product_id}", headers=superuser_token_headers, json=update_payload)
        assert response_stock.status_code == 200
        test_product_data["current_stock"] = 10 # Update fixture data locally
    else:
        test_product_data["current_stock"] = initial_stock # Use initial if sufficient

    order_payload = {
        "client_id": test_client_data["id"],
        "items": [
            {"product_id": product_id, "quantity": 1}
        ]
    }
    response = client.post(f"{settings.API_V1_STR}/orders/", headers=user_token_headers, json=order_payload)
    assert response.status_code == 201, f"Failed to create order: {response.text}"
    created_order = response.json()
    # Add product details back for easier assertion later if needed
    created_order["_test_product_id"] = product_id
    created_order["_test_client_id"] = test_client_data["id"]
    created_order["_test_quantity"] = 1
    created_order["_test_unit_price"] = test_product_data["sale_value"]
    return created_order

# Test order creation
def test_create_order(client: TestClient, user_token_headers, test_client_data, test_product_data):
    # Use the product created in test_product_data fixture
    product_id = test_product_data["id"]
    product_price = test_product_data["sale_value"]
    order_quantity = 1

    # Check current stock before creating order
    response_get_prod = client.get(f"{settings.API_V1_STR}/products/{product_id}", headers=user_token_headers)
    assert response_get_prod.status_code == 200
    stock_before = response_get_prod.json()["current_stock"]

    order_payload = {
        "client_id": test_client_data["id"],
        "items": [
            {"product_id": product_id, "quantity": order_quantity}
        ]
    }
    response = client.post(f"{settings.API_V1_STR}/orders/", headers=user_token_headers, json=order_payload)
    assert response.status_code == 201
    created_order = response.json()
    assert created_order["client_id"] == test_client_data["id"]
    assert created_order["status"] == "pending" # Default status
    assert len(created_order["items"]) == 1
    assert created_order["items"][0]["product_id"] == product_id
    assert created_order["items"][0]["quantity"] == order_quantity
    assert Decimal(created_order["items"][0]["unit_price"]) == Decimal(str(product_price))
    assert Decimal(created_order["total_value"]) == Decimal(str(product_price)) * order_quantity
    assert "id" in created_order

    # Verify stock deduction
    response_get_prod_after = client.get(f"{settings.API_V1_STR}/products/{product_id}", headers=user_token_headers)
    assert response_get_prod_after.status_code == 200
    stock_after = response_get_prod_after.json()["current_stock"]
    assert stock_after == stock_before - order_quantity

def test_create_order_insufficient_stock(client: TestClient, user_token_headers, test_client_data, test_product_data):
    product_id = test_product_data["id"]
    # Get current stock
    response_get_prod = client.get(f"{settings.API_V1_STR}/products/{product_id}", headers=user_token_headers)
    assert response_get_prod.status_code == 200
    current_stock = response_get_prod.json()["current_stock"]

    order_payload = {
        "client_id": test_client_data["id"],
        "items": [
            {"product_id": product_id, "quantity": current_stock + 1} # Request more than available
        ]
    }
    response = client.post(f"{settings.API_V1_STR}/orders/", headers=user_token_headers, json=order_payload)
    assert response.status_code == 400
    assert "Insufficient stock" in response.json()["detail"]

def test_create_order_nonexistent_product(client: TestClient, user_token_headers, test_client_data):
    order_payload = {
        "client_id": test_client_data["id"],
        "items": [
            {"product_id": 99999, "quantity": 1}
        ]
    }
    response = client.post(f"{settings.API_V1_STR}/orders/", headers=user_token_headers, json=order_payload)
    assert response.status_code == 404
    assert "Product with id 99999 not found" in response.json()["detail"]

def test_create_order_nonexistent_client(client: TestClient, user_token_headers, test_product_data):
    order_payload = {
        "client_id": 99999,
        "items": [
            {"product_id": test_product_data["id"], "quantity": 1}
        ]
    }
    response = client.post(f"{settings.API_V1_STR}/orders/", headers=user_token_headers, json=order_payload)
    assert response.status_code == 404
    assert "Client with id 99999 not found" in response.json()["detail"]

def test_create_order_unauthenticated(client: TestClient, test_client_data, test_product_data):
    order_payload = {"client_id": test_client_data["id"], "items": [{"product_id": test_product_data["id"], "quantity": 1}]}
    response = client.post(f"{settings.API_V1_STR}/orders/", json=order_payload)
    assert response.status_code == 401

# Test reading orders
def test_read_orders(client: TestClient, user_token_headers, test_order_data):
    response = client.get(f"{settings.API_V1_STR}/orders/", headers=user_token_headers)
    assert response.status_code == 200
    orders = response.json()
    assert isinstance(orders, list)
    assert any(o["id"] == test_order_data["id"] for o in orders)

def test_read_orders_filtered(client: TestClient, user_token_headers, test_order_data, test_product_data):
    # Filter by client_id
    client_id = test_order_data["_test_client_id"]
    response_client = client.get(f"{settings.API_V1_STR}/orders/?cliente_id={client_id}", headers=user_token_headers)
    assert response_client.status_code == 200
    assert len(response_client.json()) >= 1
    assert all(o["client"]["id"] == client_id for o in response_client.json())

    # Filter by status
    status = test_order_data["status"]
    response_status = client.get(f"{settings.API_V1_STR}/orders/?status={status}", headers=user_token_headers)
    assert response_status.status_code == 200
    assert len(response_status.json()) >= 1
    assert all(o["status"] == status for o in response_status.json())

    # Filter by product section
    section = test_product_data["section"]
    response_section = client.get(f"{settings.API_V1_STR}/orders/?secao_produto={section}", headers=user_token_headers)
    assert response_section.status_code == 200
    # Check if the specific order is in the results (might be others with same section)
    assert any(o["id"] == test_order_data["id"] for o in response_section.json())

def test_read_order(client: TestClient, user_token_headers, test_order_data):
    order_id = test_order_data["id"]
    response = client.get(f"{settings.API_V1_STR}/orders/{order_id}", headers=user_token_headers)
    assert response.status_code == 200
    fetched_order = response.json()
    assert fetched_order["id"] == order_id
    assert fetched_order["client"]["id"] == test_order_data["_test_client_id"]
    assert len(fetched_order["items"]) == 1
    assert fetched_order["items"][0]["product"]["id"] == test_order_data["_test_product_id"]

def test_read_nonexistent_order(client: TestClient, user_token_headers):
    response = client.get(f"{settings.API_V1_STR}/orders/99999", headers=user_token_headers)
    assert response.status_code == 404

# Test updating orders
def test_update_order_status(client: TestClient, user_token_headers, test_order_data):
    order_id = test_order_data["id"]
    update_data = {"status": "processing"}
    response = client.put(f"{settings.API_V1_STR}/orders/{order_id}", headers=user_token_headers, json=update_data)
    assert response.status_code == 200
    updated_order = response.json()
    assert updated_order["id"] == order_id
    assert updated_order["status"] == update_data["status"]

def test_update_order_forbidden(client: TestClient, superuser_token_headers, test_order_data):
    # Example: Test if a superuser *can* update (adjust based on actual permissions)
    order_id = test_order_data["id"]
    update_data = {"status": "shipped"}
    response = client.put(f"{settings.API_V1_STR}/orders/{order_id}", headers=superuser_token_headers, json=update_data)
    assert response.status_code == 200 # Assuming superuser can update
    assert response.json()["status"] == "shipped"

# Test deleting orders
def test_delete_order(client: TestClient, superuser_token_headers, user_token_headers, test_client_data, test_product_data):
    # Create an order specifically for deletion test
    order_payload = {"client_id": test_client_data["id"], "items": [{"product_id": test_product_data["id"], "quantity": 1}]}
    response_create = client.post(f"{settings.API_V1_STR}/orders/", headers=user_token_headers, json=order_payload)
    assert response_create.status_code == 201
    order_id = response_create.json()["id"]

    # Delete the order (requires superuser)
    response_delete = client.delete(f"{settings.API_V1_STR}/orders/{order_id}", headers=superuser_token_headers)
    assert response_delete.status_code == 200
    assert response_delete.json()["id"] == order_id

    # Verify order is deleted
    response_get = client.get(f"{settings.API_V1_STR}/orders/{order_id}", headers=superuser_token_headers)
    assert response_get.status_code == 404

def test_delete_order_forbidden(client: TestClient, user_token_headers, test_order_data):
    # Regular user tries to delete order
    order_id = test_order_data["id"]
    response = client.delete(f"{settings.API_V1_STR}/orders/{order_id}", headers=user_token_headers)
    assert response.status_code == 403 # Assuming delete requires superuser

def test_delete_nonexistent_order(client: TestClient, superuser_token_headers):
    response = client.delete(f"{settings.API_V1_STR}/orders/99999", headers=superuser_token_headers)
    assert response.status_code == 404

