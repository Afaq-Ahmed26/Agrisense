import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Firebase configuration
    FIREBASE_CONFIG_PATH: str = os.getenv("FIREBASE_CONFIG_PATH", "")
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")

    # JWT configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours

    # Database configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # ML Model configuration
    ML_MODEL_PATH: str = os.getenv("ML_MODEL_PATH", "./ml_model/model.pkl")

    class Config:
        env_file = ".env"


settings = Settings()