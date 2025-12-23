from pydantic_settings import BaseSettings
from pydantic import EmailStr, field_validator
from typing import List, Optional
from functools import lru_cache
import os


class Settings(BaseSettings):
    APP_NAME: str = "Jira Clone API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    API_V1_PREFIX: str = "/api/v1"
    
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 3306
    DATABASE_USER: str = "root"
    DATABASE_PASSWORD: str = ""
    DATABASE_NAME: str = "jira_clone"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_RECYCLE: int = 3600
    DATABASE_ECHO: bool = False
    
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )
    
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return (
            f"mysql+aiomysql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )
    
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MAGIC_LINK_EXPIRE_MINUTES: int = 15
    
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: EmailStr = "noreply@jiraclone.com"
    MAIL_FROM_NAME: str = "Jira Clone"
    MAIL_TLS: bool = True
    MAIL_SSL: bool = False
    MAIL_USE_CREDENTIALS: bool = True
    MAIL_VALIDATE_CERTS: bool = True
    
    FRONTEND_URL: str = "http://localhost:3000"
    MAGIC_LINK_CALLBACK_URL: str = "/auth/verify"
    
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_AUTH_REQUESTS: int = 10
    RATE_LIMIT_AUTH_WINDOW_SECONDS: int = 300
    RATE_LIMIT_SEARCH_REQUESTS: int = 30
    RATE_LIMIT_SEARCH_WINDOW_SECONDS: int = 60
    
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024
    ALLOWED_EXTENSIONS: List[str] = [
        ".jpg", ".jpeg", ".png", ".gif", ".pdf", 
        ".doc", ".docx", ".xls", ".xlsx", ".txt", ".csv"
    ]
    
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "logs/app.log"
    LOG_ROTATION: str = "10 MB"
    LOG_RETENTION: str = "30 days"
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    PAGINATION_DEFAULT_LIMIT: int = 20
    PAGINATION_MAX_LIMIT: int = 100
    
    SEARCH_MIN_QUERY_LENGTH: int = 2
    SEARCH_MAX_RESULTS: int = 50
    
    PROJECT_KEY_MIN_LENGTH: int = 2
    PROJECT_KEY_MAX_LENGTH: int = 10
    
    TASK_TITLE_MAX_LENGTH: int = 255
    TASK_DESCRIPTION_MAX_LENGTH: int = 10000
    
    ACTIVITY_RETENTION_DAYS: int = 90
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("ALLOWED_EXTENSIONS", mode="before")
    @classmethod
    def parse_allowed_extensions(cls, v):
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


class DevelopmentSettings(Settings):
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    DATABASE_ECHO: bool = True
    LOG_LEVEL: str = "DEBUG"


class TestingSettings(Settings):
    DEBUG: bool = True
    ENVIRONMENT: str = "testing"
    DATABASE_NAME: str = "jira_clone_test"
    RATE_LIMIT_ENABLED: bool = False
    MAIL_SUPPRESS_SEND: bool = True


class ProductionSettings(Settings):
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40


@lru_cache()
def get_settings() -> Settings:
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    settings_map = {
        "development": DevelopmentSettings,
        "testing": TestingSettings,
        "production": ProductionSettings,
    }
    
    settings_class = settings_map.get(environment, DevelopmentSettings)
    return settings_class()


settings = get_settings()