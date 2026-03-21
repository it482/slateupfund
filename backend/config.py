"""Application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env paths: backend/.env and project root .env
_BACKEND_DIR = Path(__file__).resolve().parent
_ENV_PATHS = [
    _BACKEND_DIR / ".env",
    _BACKEND_DIR.parent / ".env",
]


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=next((str(p) for p in _ENV_PATHS if p.exists()), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # BoldSign
    boldsign_api_key: str = ""
    boldsign_api_host: str = "https://api.boldsign.com"

    # API auth and CORS
    api_key: str = ""
    cors_origins: str = ""
    rate_limit: str = "100/minute"

    # API
    api_title: str = "SlateUp Funding API"
    api_version: str = "1.0.0"
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


def get_settings_dependency() -> Settings:
    """FastAPI dependency: delegates to get_settings() so tests can patch `backend.config.get_settings`."""
    return get_settings()
