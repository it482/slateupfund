"""Service factories for FastAPI dependency injection."""

from typing import Annotated

from fastapi import Depends

from backend.config import Settings, get_settings_dependency
from backend.services.boldsign_service import BoldSignService


def get_boldsign_service(
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> BoldSignService:
    """Construct BoldSignService from application settings (per request; instance is cheap)."""
    return BoldSignService(settings=settings)
