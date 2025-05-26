from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import timedelta # Import timedelta
from app import models, schemas
from app.core import security
from app.core.config import settings

def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = security.get_password_hash(user.password)
    # Create user instance (adjust if you have more fields in UserCreate/User model)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        is_active=user.is_active if user.is_active is not None else True,
        is_superuser=user.is_superuser
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str) -> models.User | None:
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not security.verify_password(password, user.hashed_password):
        return None
    return user

def generate_tokens(user: models.User) -> schemas.Token:
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    # Optionally add more data to refresh token if needed, but keep it minimal
    # refresh_token = security.create_refresh_token(
    #     data={"sub": user.email}, expires_delta=refresh_token_expires
    # )

    return schemas.Token(
        access_token=access_token,
        # refresh_token=refresh_token, # Include if implementing refresh logic fully
        token_type="bearer"
    )

def refresh_access_token(refresh_token: str, db: Session) -> schemas.Token:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = security.decode_token(refresh_token)
    if payload is None:
        raise credentials_exception

    email: str = payload.get("sub")
    # Optional: Check token expiry explicitly if needed, though decode_token handles it
    # exp = payload.get("exp")
    # if exp is None or datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    if email is None:
        raise credentials_exception

    user = get_user_by_email(db, email=email)
    if user is None or not user.is_active:
        raise credentials_exception

    # Generate a new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return schemas.Token(
        access_token=new_access_token,
        token_type="bearer"
    )

# Note: The refresh token logic here assumes the refresh token itself is valid
# and the user exists. In a production scenario, you might want to store
# refresh tokens (or their hashes) in the DB and invalidate them on logout
# or password change for better security.
# The current implementation uses the refresh token primarily to re-identify the user.

