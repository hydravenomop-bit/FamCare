"""
FamCARE Multi-Service Bulk Scheduler — Configuration.

Loads settings from environment variables / .env file.
Supports SQLite (dev) and PostgreSQL (production) via DATABASE_URL.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DATABASE_URL: str = "sqlite+aiosqlite:///./famcare.db"

    SLOT_START_HOUR: int = 8   # 8:00 AM
    SLOT_END_HOUR: int = 20    # 8:00 PM

    SLOT_GRANULARITY_MINUTES: int = 15

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — avoids re-reading .env on every request."""
    return Settings()
