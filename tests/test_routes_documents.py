"""Tests for document API routes."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.dependencies.services import get_boldsign_service
from backend.exceptions import BoldSignServiceError
from backend.main import create_app


@pytest.fixture
def mock_boldsign():
    """Mock BoldSignService behavior."""
    m = MagicMock()
    m.create_document_from_template.return_value = {
        "document_id": "doc_xyz",
        "signer_links": [
            {
                "signer_email": "alice@example.com",
                "signer_name": "Alice",
                "sign_link": "https://sign.link/1",
                "expires_at": "2025-04-17T12:00:00Z",
            },
        ],
    }
    m.prefill_form_fields.return_value = None
    return m


@pytest.fixture
def client(mock_boldsign):
    """Test client with dependency-injected BoldSign mock and patched settings."""
    mock_settings = MagicMock(
        boldsign_api_key="test-key",
        boldsign_api_host="https://api.boldsign.com",
        api_key="test-api-key",
        cors_origins="",
        debug=True,
    )
    with patch("backend.config.get_settings", return_value=mock_settings):
        app = create_app()
        app.dependency_overrides[get_boldsign_service] = lambda: mock_boldsign
        yield TestClient(app)
        app.dependency_overrides.clear()


def test_create_document_from_template_success(client: TestClient):
    """POST /documents/from-template returns 200 with document_id and signer_links."""
    response = client.post(
        "/documents/from-template",
        headers={"X-API-Key": "test-api-key"},
        json={
            "template_id": "tpl_123",
            "signers": [
                {"role_index": 1, "signer_name": "Alice", "signer_email": "alice@example.com"},
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == "doc_xyz"
    assert len(data["signer_links"]) == 1
    assert data["signer_links"][0]["signer_email"] == "alice@example.com"
    assert data["signer_links"][0]["sign_link"] == "https://sign.link/1"


def test_create_document_from_template_with_prefill_passes_fields(
    client: TestClient, mock_boldsign: MagicMock
):
    """POST with prefill_fields forwards them to the service including role_index."""
    response = client.post(
        "/documents/from-template",
        headers={"X-API-Key": "test-api-key"},
        json={
            "template_id": "tpl_123",
            "signers": [
                {"role_index": 1, "signer_name": "Alice", "signer_email": "alice@example.com"},
                {"role_index": 2, "signer_name": "Bob", "signer_email": "bob@example.com"},
            ],
            "prefill_fields": [
                {"id": "field_a", "value": "v1", "role_index": 1},
                {"id": "field_b", "value": "v2", "roleIndex": 2},
            ],
        },
    )
    assert response.status_code == 200
    mock_boldsign.create_document_from_template.assert_called_once()
    call_kwargs = mock_boldsign.create_document_from_template.call_args.kwargs
    assert call_kwargs["prefill_fields"] == [
        {"id": "field_a", "value": "v1", "role_index": 1},
        {"id": "field_b", "value": "v2", "role_index": 2},
    ]


def test_create_document_from_template_missing_api_key_returns_401(client: TestClient):
    """Missing X-API-Key header returns 401."""
    response = client.post(
        "/documents/from-template",
        json={
            "template_id": "tpl_123",
            "signers": [
                {"role_index": 1, "signer_name": "Alice", "signer_email": "alice@example.com"},
            ],
        },
    )
    assert response.status_code == 401
    assert "Invalid or missing API key" in response.json()["detail"]


def test_create_document_from_template_invalid_api_key_returns_401(client: TestClient):
    """Invalid X-API-Key returns 401."""
    response = client.post(
        "/documents/from-template",
        headers={"X-API-Key": "wrong-key"},
        json={
            "template_id": "tpl_123",
            "signers": [
                {"role_index": 1, "signer_name": "Alice", "signer_email": "alice@example.com"},
            ],
        },
    )
    assert response.status_code == 401
    assert "Invalid or missing API key" in response.json()["detail"]


def test_create_document_from_template_validation_error(client: TestClient):
    """Invalid request body returns 422."""
    response = client.post(
        "/documents/from-template",
        headers={"X-API-Key": "test-api-key"},
        json={
            "template_id": "tpl_123",
            "signers": [],
        },
    )
    assert response.status_code == 422


def test_create_document_from_template_service_error(mock_boldsign):
    """BoldSignServiceError returns 400 with structured detail."""
    mock_boldsign.create_document_from_template.side_effect = BoldSignServiceError(
        "Template not found", code="boldsign_http_error"
    )
    mock_settings = MagicMock(
        boldsign_api_key="test-key",
        boldsign_api_host="https://api.boldsign.com",
        api_key="test-api-key",
        cors_origins="",
        debug=True,
    )
    with patch("backend.config.get_settings", return_value=mock_settings):
        app = create_app()
        app.dependency_overrides[get_boldsign_service] = lambda: mock_boldsign
        try:
            test_client = TestClient(app)
            response = test_client.post(
                "/documents/from-template",
                headers={"X-API-Key": "test-api-key"},
                json={
                    "template_id": "tpl_bad",
                    "signers": [
                        {
                            "role_index": 1,
                            "signer_name": "A",
                            "signer_email": "a@x.com",
                        },
                    ],
                },
            )
            assert response.status_code == 400
            body = response.json()["detail"]
            assert body["code"] == "boldsign_http_error"
            assert "Template not found" in body["message"]
        finally:
            app.dependency_overrides.clear()


def test_prefill_form_fields_success(client: TestClient):
    """PATCH /documents/{id}/prefill returns 204."""
    response = client.patch(
        "/documents/doc_123/prefill",
        headers={"X-API-Key": "test-api-key"},
        json={"fields": [{"id": "f1", "value": "v1"}]},
    )
    assert response.status_code == 204


def test_prefill_form_fields_validation_error(client: TestClient):
    """Invalid prefill request returns 422."""
    response = client.patch(
        "/documents/doc_123/prefill",
        headers={"X-API-Key": "test-api-key"},
        json={"fields": []},
    )
    assert response.status_code == 422


def test_prefill_form_fields_service_error(mock_boldsign):
    """BoldSignServiceError on prefill returns 400 with structured detail."""
    mock_boldsign.prefill_form_fields.side_effect = BoldSignServiceError(
        "Document not found", code="boldsign_api_error"
    )
    mock_settings = MagicMock(
        boldsign_api_key="test-key",
        boldsign_api_host="https://api.boldsign.com",
        api_key="test-api-key",
        cors_origins="",
        debug=True,
    )
    with patch("backend.config.get_settings", return_value=mock_settings):
        app = create_app()
        app.dependency_overrides[get_boldsign_service] = lambda: mock_boldsign
        try:
            test_client = TestClient(app)
            response = test_client.patch(
                "/documents/doc_bad/prefill",
                headers={"X-API-Key": "test-api-key"},
                json={"fields": [{"id": "f1", "value": "v1"}]},
            )
            assert response.status_code == 400
            body = response.json()["detail"]
            assert body["code"] == "boldsign_api_error"
            assert "Document not found" in body["message"]
        finally:
            app.dependency_overrides.clear()
