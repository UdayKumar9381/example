# app/config.py
"""
Configuration settings for the application.
Uses pydantic-settings for type-safe environment variable loading.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path
import os


# Get the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    
    # Database Configuration
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""  # Will be loaded from .env
    db_name: str = "user_story_db"
    
    # Application Settings
    app_name: str = "User Story Manager"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # File Upload Settings
    upload_dir: str = "uploads"
    max_file_size_mb: int = 50
    
    @property
    def database_url(self) -> str:
        """
        Constructs MySQL connection URL for SQLAlchemy.
        """
        # URL encode the password in case it contains special characters
        from urllib.parse import quote_plus
        encoded_password = quote_plus(self.db_password)
        
        return (
            f"mysql+pymysql://{self.db_user}:{encoded_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
    
    @property
    def max_file_size_bytes(self) -> int:
        """Converts MB to bytes for file size validation."""
        return self.max_file_size_mb * 1024 * 1024
    
    # Pydantic v2 configuration
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields in .env
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance.
    """
    settings = Settings()
    
    # Debug: Print loaded settings (remove in production)
    print(f"📁 Looking for .env at: {BASE_DIR / '.env'}")
    print(f"🔧 DB_HOST: {settings.db_host}")
    print(f"🔧 DB_USER: {settings.db_user}")
    print(f"🔧 DB_NAME: {settings.db_name}")
    print(f"🔧 DB_PASSWORD: {'*' * len(settings.db_password) if settings.db_password else '(empty!)'}")
    
    if not settings.db_password:
        print("⚠️  WARNING: DB_PASSWORD is empty! Check your .env file.")
    
    return settings