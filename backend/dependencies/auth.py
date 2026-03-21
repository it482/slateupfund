"""API Key authentication dependency."""

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from backend import config

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str | None = Security(api_key_header)) -> None:
    """Verify the X-API-Key header against the configured API key."""
    settings = config.get_settings()
    if not settings.api_key:
        raise HTTPException(
            status_code=500,
            detail="API key authentication is not configured",
        )
    if not api_key or api_key != settings.api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
        )
