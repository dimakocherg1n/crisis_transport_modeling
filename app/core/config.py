# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./crisis_transport.db"
    APP_NAME: str = "Crisis Transport Optimization API"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]
    SECRET_KEY: str = "your-secret-key-change-in-production-for-real-app"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    FIRST_SUPERUSER_EMAIL: Optional[str] = "admin@crisis-transport.com"
    FIRST_SUPERUSER_PASSWORD: Optional[str] = "admin123"
    class Config:
        env_file = ".env"
        case_sensitive = True
settings = Settings()