from fastapi.testclient import TestClient
from app.core.config import settings
from app import schemas

# Test user registration
def test_register_user(client: TestClient):
    user_data = {"email": "newuser@example.com", "password": "newpassword123"}
    response = client.post(f"{settings.API_V1_STR}/auth/register", json=user_data)
    assert response.status_code == 201
    created_user = response.json()
    assert created_user["email"] == user_data["email"]
    assert "id" in created_user
    assert "hashed_password" not in created_user # Ensure password is not returned

def test_register_existing_user(client: TestClient, test_user):
    # test_user fixture already created 'testuser@example.com'
    user_data = {"email": test_user["email"], "password": "anotherpassword"}
    response = client.post(f"{settings.API_V1_STR}/auth/register", json=user_data)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

# Test user login
def test_login_user(client: TestClient, test_user, test_user_password):
    login_data = {"username": test_user["email"], "password": test_user_password}
    response = client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"

def test_login_wrong_password(client: TestClient, test_user):
    login_data = {"username": test_user["email"], "password": "wrongpassword"}
    response = client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

def test_login_nonexistent_user(client: TestClient):
    login_data = {"username": "nosuchuser@example.com", "password": "password"}
    response = client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    assert response.status_code == 401 # Or 404 depending on how authenticate_user handles it
    assert "Incorrect email or password" in response.json()["detail"]

# Test getting current user
def test_read_users_me(client: TestClient, user_token_headers, test_user):
    response = client.get(f"{settings.API_V1_STR}/auth/users/me", headers=user_token_headers)
    assert response.status_code == 200
    current_user = response.json()
    assert current_user["email"] == test_user["email"]
    assert current_user["id"] == test_user["id"]

def test_read_users_me_unauthenticated(client: TestClient):
    response = client.get(f"{settings.API_V1_STR}/auth/users/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]

# Add tests for inactive users if implemented
# Add tests for refresh token if fully implemented

