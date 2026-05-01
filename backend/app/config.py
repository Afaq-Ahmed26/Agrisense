import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Firebase configuration
    FIREBASE_CONFIG_PATH: str = os.getenv("FIREBASE_CONFIG_PATH", "")
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")
    FIREBASE_ADMIN_SDK_CONFIG: str = os.getenv("FIREBASE_ADMIN_SDK_CONFIG", "")
    FIREBASE_API_KEY: Optional[str] = os.getenv("FIREBASE_API_KEY") # Added
    ADMIN_EMAIL: Optional[str] = os.getenv("ADMIN_EMAIL") # Added
    ADMIN_PASSWORD: Optional[str] = os.getenv("ADMIN_PASSWORD") # Added

    # JWT configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours

    # Database configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # ML Model configuration
    ML_MODEL_PATH: str = os.getenv("ML_MODEL_PATH", "model/irrigation_model.pkl")
    SOIL_MOISTURE_THRESHOLD: float = float(os.getenv("SOIL_MOISTURE_THRESHOLD", "30.0")) # Default to 30%

    # SMTP configuration for OTP emails
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: Optional[str] = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    SMTP_FROM_EMAIL: Optional[str] = os.getenv("SMTP_FROM_EMAIL")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    # Device connect OTP policy
    DEVICE_OTP_EXPIRE_MINUTES: int = int(os.getenv("DEVICE_OTP_EXPIRE_MINUTES", "10"))
    DEVICE_OTP_MAX_ATTEMPTS: int = int(os.getenv("DEVICE_OTP_MAX_ATTEMPTS", "3"))
    DEVICE_ASSIGNMENT_ENFORCEMENT: bool = os.getenv("DEVICE_ASSIGNMENT_ENFORCEMENT", "false").lower() == "true"

    class Config:
        env_file = ".env"


settings = Settings()
