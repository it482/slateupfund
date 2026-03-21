"""Pytest fixtures and configuration."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.main import create_app


@pytest.fixture
def mock_settings() -> Settings:
    """Settings with test values (no real API keys)."""
    return Settings(
        _env_file=None,
        boldsign_api_key="test-api-key",
        boldsign_api_host="https://api.boldsign.com",
        api_key="test-api-key",
        cors_origins="",
        rate_limit="100/minute",
        api_title="SlateUp Funding API",
        api_version="1.0.0",
        debug=True,
    )


@pytest.fixture
def app(mock_settings: Settings):
    """FastAPI app with mocked settings."""
    with patch("backend.config.get_settings", return_value=mock_settings):
        yield create_app()


@pytest.fixture
def client(app):
    """Test client for FastAPI app."""
    return TestClient(app)
