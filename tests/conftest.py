import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session # Import Session here
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import Base, get_db
from app.core.config import settings
import os
from decimal import Decimal # Added Decimal import

# Use a separate SQLite DB for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_db.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool, # Use StaticPool for SQLite in tests
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables before tests run
Base.metadata.create_all(bind=engine)

# Dependency override for test database session
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def cleanup_db():
    """Clean up the test database file after the test session."""
    yield
    # Teardown: remove the test database file
    if os.path.exists("./test_db.db"):
        os.remove("./test_db.db")

@pytest.fixture(scope="module")
def client() -> TestClient:
    """Provides a TestClient instance for making API requests."""
    # Reset tables for each module if necessary, or manage state within tests
    # Base.metadata.drop_all(bind=engine)
    # Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def db() -> Session:
    """Provides a test database session."""
    # This fixture provides a session for direct DB manipulation in tests if needed,
    # but most tests should interact via the API client.
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

# You might want fixtures to create test users (regular and superuser)
@pytest.fixture(scope="module")
def test_user_password() -> str:
    return "testpassword123"

@pytest.fixture(scope="module")
def test_user(client: TestClient, test_user_password) -> dict:
    """Creates a regular test user via the API."""    
    user_data = {
        "email": "testuser@example.com",
        "password": test_user_password,
        "is_superuser": False
    }
    response = client.post(f"{settings.API_V1_STR}/auth/register", json=user_data)
    # Handle potential conflict if user already exists from previous runs
    if response.status_code == 400 and "Email already registered" in response.text:
        # If user already exists, just return its email for login
        # Tests depending on the full user object might need adjustment
        print(f"Test user {user_data['email']} already exists, proceeding...") # Corrected f-string
        return {"email": user_data["email"], "id": -1} # Return dummy ID or fetch actual ID if needed
    assert response.status_code == 201, f"Failed to create test user: {response.text}"
    return response.json() # Returns the created user data (excluding password)

@pytest.fixture(scope="module")
def test_superuser_password() -> str:
    return "superpassword123"

@pytest.fixture(scope="module")
def test_superuser(client: TestClient, test_superuser_password) -> dict:
    """Creates a superuser test user via the API."""
    user_data = {
        "email": "superuser@example.com",
        "password": test_superuser_password,
        "is_superuser": True
    }
    response = client.post(f"{settings.API_V1_STR}/auth/register", json=user_data)
    # Handle potential conflict if user already exists from previous runs
    if response.status_code == 400 and "Email already registered" in response.text:
        # If superuser already exists, just return its email for login
        return {"email": user_data["email"]}
    assert response.status_code == 201
    return response.json()

@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient, test_superuser, test_superuser_password) -> dict:
    """Provides authentication headers for the superuser."""
    login_data = {
        "username": test_superuser["email"],
        "password": test_superuser_password,
    }
    response = client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    assert response.status_code == 200
    tokens = response.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers

@pytest.fixture(scope="module")
def user_token_headers(client: TestClient, test_user, test_user_password) -> dict:
    """Provides authentication headers for the regular user."""
    login_data = {
        "username": test_user["email"],
        "password": test_user_password,
    }
    response = client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    assert response.status_code == 200
    tokens = response.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers




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
         print(f"Client creation conflict: {response.json()}")
         # Attempt to find the client by email to get the ID
         get_response = client.get(f"{settings.API_V1_STR}/clients/?email={client_data['email']}", headers=superuser_token_headers) # Corrected f-string
         if get_response.status_code == 200 and get_response.json():
             print(f"Found existing client: {get_response.json()[0]}")
             return get_response.json()[0] # Return the first match
         else:
             pytest.fail(f"Failed to create or retrieve conflicting client: {client_data['email']}") # Corrected f-string

    assert response.status_code == 201, f"Failed to create client: {response.text}"
    return response.json()

# Fixture to create a product for use in other tests
@pytest.fixture(scope="module")
def test_product_data(client: TestClient, superuser_token_headers) -> dict:
    product_data = {
        "description": "Test Product One",
        "sale_value": "19.99", # Use string for Decimal input
        "barcode": "1234567890123",
        "section": "Test Section",
        "initial_stock": 50,
    }
    response = client.post(f"{settings.API_V1_STR}/products/", headers=superuser_token_headers, json=product_data)
    if response.status_code == 400 and "Barcode already registered" in response.text:
        # If product exists, try to get its data
        print(f"Product creation conflict: {response.json()}")
        get_response = client.get(f"{settings.API_V1_STR}/products/?barcode={product_data['barcode']}", headers=superuser_token_headers) # Corrected f-string
        if get_response.status_code == 200 and get_response.json():
            print(f"Found existing product: {get_response.json()[0]}")
            existing_product = get_response.json()[0]
            existing_product["sale_value"] = Decimal(existing_product["sale_value"]) # Uses Decimal
            return existing_product # Return the first match
        else:
             pytest.fail(f"Failed to create or retrieve conflicting product: {product_data['barcode']}") # Corrected f-string

    assert response.status_code == 201, f"Failed to create product: {response.text}"
    created_product = response.json()
    created_product["sale_value"] = Decimal(created_product["sale_value"]) # Uses Decimal
    return created_product
