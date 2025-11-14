from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    #  This is for theDatabase
    DATABASE_URL: str = "postgresql://user:password@localhost/product_importer"
    
    # This is for the Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # This is for the Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # This is for the Application
    APP_NAME: str = "Product Importer API"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

