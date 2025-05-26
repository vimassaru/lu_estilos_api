from fastapi.testclient import TestClient
from app.core.config import settings
from app import schemas
import pytest

# Fixture to create a client for use in other tests
@pytest.fixture(scope="module")
def test_client_data(client: TestClient, superuser_token_headers) -> dict:
    client_data = {
        "name": "Test Client One",
        "email": "client.one@example.com",
        "cpf": "11122233344",
        "phone": "1234567890",
        "address": "123 Test St"
    }
    response = client.post(f"{settings.API_V1_STR}/clients/", headers=superuser_token_headers, json=client_data)
    # Handle potential conflict if client already exists from previous runs
    if response.status_code == 400 and ("Email already registered" in response.text or "CPF already registered" in response.text):
         # If client exists, try to get its data (assuming GET works)
         # This part is tricky as we don't know the ID. A better approach might be to clean DB or use unique data.
         # For simplicity, we'll assume tests run on a clean slate or handle cleanup.
         # Let's just return the input data for potential use, though the ID will be missing.
         print(f"Client creation conflict: {response.json()}")
         # Attempt to find the client by email to get the ID
         get_response = client.get(f"{settings.API_V1_STR}/clients/?email={client_data['email']}", headers=superuser_token_headers)
         if get_response.status_code == 200 and get_response.json():
             return get_response.json()[0] # Return the first match
         else:
             pytest.fail(f"Failed to create or retrieve conflicting client: {client_data['email']}")

    assert response.status_code == 201, f"Failed to create client: {response.text}"
    return response.json()

# Test client creation
def test_create_client(client: TestClient, superuser_token_headers):
    client_data = {
        "name": "Test Client Two",
        "email": "client.two@example.com",
        "cpf": "55566677788",
        "phone": "0987654321",
        "address": "456 Test Ave"
    }
    response = client.post(f"{settings.API_V1_STR}/clients/", headers=superuser_token_headers, json=client_data)
    assert response.status_code == 201
    created_client = response.json()
    assert created_client["email"] == client_data["email"]
    assert created_client["cpf"] == client_data["cpf"]
    assert "id" in created_client

def test_create_client_duplicate_email(client: TestClient, superuser_token_headers, test_client_data):
    client_data = {
        "name": "Duplicate Email Client",
        "email": test_client_data["email"], # Use email from the fixture client
        "cpf": "99988877766"
    }
    response = client.post(f"{settings.API_V1_STR}/clients/", headers=superuser_token_headers, json=client_data)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_create_client_duplicate_cpf(client: TestClient, superuser_token_headers, test_client_data):
    client_data = {
        "name": "Duplicate CPF Client",
        "email": "duplicate.cpf@example.com",
        "cpf": test_client_data["cpf"] # Use CPF from the fixture client
    }
    response = client.post(f"{settings.API_V1_STR}/clients/", headers=superuser_token_headers, json=client_data)
    assert response.status_code == 400
    assert "CPF already registered" in response.json()["detail"]

def test_create_client_unauthenticated(client: TestClient):
    client_data = {"name": "Unauthorized Client", "email": "unauth@example.com", "cpf": "12312312312"}
    response = client.post(f"{settings.API_V1_STR}/clients/", json=client_data)
    assert response.status_code == 401 # Assuming create requires auth

# Test reading clients
def test_read_clients(client: TestClient, user_token_headers, test_client_data):
    response = client.get(f"{settings.API_V1_STR}/clients/", headers=user_token_headers)
    assert response.status_code == 200
    clients = response.json()
    assert isinstance(clients, list)
    # Check if the client created in the fixture is present
    assert any(c["id"] == test_client_data["id"] for c in clients)

def test_read_clients_filtered(client: TestClient, user_token_headers, test_client_data):
    # Filter by name
    response_name = client.get(f"{settings.API_V1_STR}/clients/?name={test_client_data['name']}", headers=user_token_headers)
    assert response_name.status_code == 200
    assert len(response_name.json()) >= 1
    assert response_name.json()[0]["name"] == test_client_data["name"]

    # Filter by email
    response_email = client.get(f"{settings.API_V1_STR}/clients/?email={test_client_data['email']}", headers=user_token_headers)
    assert response_email.status_code == 200
    assert len(response_email.json()) == 1
    assert response_email.json()[0]["email"] == test_client_data["email"]

def test_read_client(client: TestClient, user_token_headers, test_client_data):
    client_id = test_client_data["id"]
    response = client.get(f"{settings.API_V1_STR}/clients/{client_id}", headers=user_token_headers)
    assert response.status_code == 200
    fetched_client = response.json()
    assert fetched_client["id"] == client_id
    assert fetched_client["email"] == test_client_data["email"]

def test_read_nonexistent_client(client: TestClient, user_token_headers):
    response = client.get(f"{settings.API_V1_STR}/clients/99999", headers=user_token_headers)
    assert response.status_code == 404

# Test updating clients
def test_update_client(client: TestClient, superuser_token_headers, test_client_data):
    client_id = test_client_data["id"]
    update_data = {"name": "Updated Client Name", "phone": "1111111111"}
    response = client.put(f"{settings.API_V1_STR}/clients/{client_id}", headers=superuser_token_headers, json=update_data)
    assert response.status_code == 200
    updated_client = response.json()
    assert updated_client["id"] == client_id
    assert updated_client["name"] == update_data["name"]
    assert updated_client["phone"] == update_data["phone"]
    assert updated_client["email"] == test_client_data["email"] # Email should not change unless specified

def test_update_client_duplicate_email(client: TestClient, superuser_token_headers, test_client_data):
    # Create another client first
    other_client_data = {"name": "Other Client", "email": "other.client@example.com", "cpf": "10101010101"}
    response_create = client.post(f"{settings.API_V1_STR}/clients/", headers=superuser_token_headers, json=other_client_data)
    assert response_create.status_code == 201
    other_client_id = response_create.json()["id"]

    # Try to update test_client_data to use other_client's email
    client_id = test_client_data["id"]
    update_data = {"email": other_client_data["email"]}
    response_update = client.put(f"{settings.API_V1_STR}/clients/{client_id}", headers=superuser_token_headers, json=update_data)
    assert response_update.status_code == 400
    assert "Email already registered" in response_update.json()["detail"]

    # Clean up the other client (optional, depends on test isolation needs)
    client.delete(f"{settings.API_V1_STR}/clients/{other_client_id}", headers=superuser_token_headers)

# Test deleting clients
def test_delete_client(client: TestClient, superuser_token_headers):
    # Create a client specifically for deletion test
    client_to_delete = {"name": "Client To Delete", "email": "delete.me@example.com", "cpf": "45645645645"}
    response_create = client.post(f"{settings.API_V1_STR}/clients/", headers=superuser_token_headers, json=client_to_delete)
    assert response_create.status_code == 201
    client_id = response_create.json()["id"]

    # Delete the client
    response_delete = client.delete(f"{settings.API_V1_STR}/clients/{client_id}", headers=superuser_token_headers)
    assert response_delete.status_code == 200
    assert response_delete.json()["id"] == client_id

    # Verify client is deleted
    response_get = client.get(f"{settings.API_V1_STR}/clients/{client_id}", headers=superuser_token_headers)
    assert response_get.status_code == 404

def test_delete_client_forbidden(client: TestClient, user_token_headers, test_client_data):
    # Regular user tries to delete a client
    client_id = test_client_data["id"]
    response = client.delete(f"{settings.API_V1_STR}/clients/{client_id}", headers=user_token_headers)
    assert response.status_code == 403 # Assuming delete requires superuser

def test_delete_nonexistent_client(client: TestClient, superuser_token_headers):
    response = client.delete(f"{settings.API_V1_STR}/clients/99999", headers=superuser_token_headers)
    assert response.status_code == 404

