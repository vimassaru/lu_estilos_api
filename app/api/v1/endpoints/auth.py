from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app import schemas, services, models # Adjust imports based on your structure
from app.database import get_db
from app.core import security

router = APIRouter()

@router.post("/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED, tags=["auth"])
def register_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.

    - **email**: User's email address (must be unique).
    - **password**: User's password.
    - **is_active**: (Optional) Whether the user is active. Defaults to True.
    - **is_superuser**: (Optional) Whether the user has admin privileges. Defaults to False.
    """
    # Check if user already exists is handled in services.create_user
    try:
        user = services.auth.create_user(db=db, user=user_in)
        return user
    except HTTPException as e:
        raise e # Re-raise HTTPException from service layer
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not register user")

@router.post("/login", response_model=schemas.Token, tags=["auth"])
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate a user and return JWT tokens.

    Uses OAuth2PasswordRequestForm, expects 'username' (which is email here) and 'password'.
    """
    user = services.auth.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    # Generate access and potentially refresh tokens
    tokens = services.auth.generate_tokens(user)
    return tokens

@router.post("/refresh-token", response_model=schemas.Token, tags=["auth"])
def refresh_token(refresh_token_data: schemas.Token, db: Session = Depends(get_db)):
    """
    Refresh the access token using a valid refresh token.
    (Note: Current implementation uses the provided token directly for simplicity,
    assuming it's the refresh token. A more robust implementation would handle
    refresh token storage and validation separately).
    """
    # This endpoint expects the *refresh* token in the request body
    # The service function `refresh_access_token` expects the refresh token string
    try:
        # Assuming the input schema `Token` contains the refresh token in `access_token` field for this example
        # Adjust schema if you have a dedicated RefreshToken schema
        new_tokens = services.auth.refresh_access_token(refresh_token=refresh_token_data.access_token, db=db)
        return new_tokens
    except HTTPException as e:
        raise e
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not refresh token")

# Example protected endpoint to test authentication
@router.get("/users/me", response_model=schemas.User, tags=["users"])
def read_users_me(current_user: models.User = Depends(security.get_current_active_user)):
    """
    Get current logged-in user's details.
    """
    return current_user

