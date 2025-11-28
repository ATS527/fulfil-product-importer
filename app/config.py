from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    UPLOAD_DIR: str = "uploads"
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()
