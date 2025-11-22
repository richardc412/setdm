from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Go up three levels: config.py -> core/ -> app/ -> backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    """Application configuration sourced from environment variables."""

    # Unipile API Settings
    unipile_dsn: str = ""
    unipile_api_key: str = ""
    
    # Webhook Settings
    webhook_base_url: str = ""  # e.g., "https://yourdomain.com" or ngrok URL
    
    # Database Settings
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/setdm_db"
    
    # Application Settings
    debug: bool = False
    
    # JWT Settings
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # AI Settings
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_history_limit: int = 20

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance so we only read the env file once."""

    return Settings()

