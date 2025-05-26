from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Lu Estilo API"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "a_very_secret_key_for_dev") # Load from .env in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test_db.db") # Default to SQLite for local dev/test if not set

    # Add other settings as needed, e.g., Sentry DSN, WhatsApp API keys
    # SENTRY_DSN: Optional[str] = None
    # WHATSAPP_API_TOKEN: Optional[str] = None
    # WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None

    class Config:
        case_sensitive = True
        # If using a .env file:
        # env_file = ".env"

settings = Settings()

