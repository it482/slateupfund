"""Tests for main application."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app


def test_create_app_returns_fastapi_instance():
    """create_app returns a FastAPI instance."""
    mock_settings = type(
        "Settings",
        (),
        {
            "boldsign_api_key": "test",
            "boldsign_api_host": "https://api.boldsign.com",
            "api_key": "test-key",
            "cors_origins": "",
            "rate_limit": "100/minute",
            "api_title": "SlateUp Funding API",
            "api_version": "1.0.0",
            "debug": True,
        },
    )()
    with patch("backend.config.get_settings", return_value=mock_settings):
        app = create_app()
        assert app.title == "SlateUp Funding API"
        assert app.version == "1.0.0"


def test_app_has_docs_routes():
    """App exposes /docs and /redoc when DEBUG=true."""
    with patch("backend.config.get_settings") as mock_config:
        mock_config.return_value = type(
            "Settings",
            (),
            {
                "boldsign_api_key": "test",
                "boldsign_api_host": "https://api.boldsign.com",
                "api_key": "test-key",
                "cors_origins": "",
                "rate_limit": "100/minute",
                "api_title": "SlateUp Funding API",
                "api_version": "1.0.0",
                "debug": True,
            },
        )()
        app = create_app()
        client = TestClient(app)
        assert client.get("/docs").status_code == 200
        assert client.get("/redoc").status_code == 200


def test_app_docs_disabled_when_not_debug_openapi_still_available():
    """Swagger UI disabled when DEBUG=false; OpenAPI JSON remains for contracts."""
    with patch("backend.config.get_settings") as mock_config:
        mock_config.return_value = type(
            "Settings",
            (),
            {
                "boldsign_api_key": "test",
                "boldsign_api_host": "https://api.boldsign.com",
                "api_key": "test-key",
                "cors_origins": "",
                "rate_limit": "100/minute",
                "api_title": "SlateUp Funding API",
                "api_version": "1.0.0",
                "debug": False,
            },
        )()
        app = create_app()
        client = TestClient(app)
        assert client.get("/docs").status_code == 404
        assert client.get("/redoc").status_code == 404
        assert client.get("/openapi.json").status_code == 200


def test_app_has_health_endpoint():
    """App exposes /health for load balancers."""
    with patch("backend.config.get_settings") as mock_config:
        mock_config.return_value = type(
            "Settings",
            (),
            {
                "boldsign_api_key": "test",
                "boldsign_api_host": "https://api.boldsign.com",
                "api_key": "test-key",
                "cors_origins": "",
                "rate_limit": "100/minute",
                "api_title": "SlateUp Funding API",
                "api_version": "1.0.0",
                "debug": True,
            },
        )()
        app = create_app()
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_app_has_documents_router():
    """App includes documents router."""
    with patch("backend.config.get_settings") as mock_config:
        mock_config.return_value = type(
            "Settings",
            (),
            {
                "boldsign_api_key": "test",
                "boldsign_api_host": "https://api.boldsign.com",
                "api_key": "test-key",
                "cors_origins": "",
                "rate_limit": "100/minute",
                "api_title": "SlateUp Funding API",
                "api_version": "1.0.0",
                "debug": True,
            },
        )()
        app = create_app()
        assert any("/documents" in str(r) for r in app.routes)
