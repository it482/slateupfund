"""Tests for BoldSignService."""

from unittest.mock import MagicMock, patch

import pytest

from backend.exceptions import BoldSignServiceError
from backend.services.boldsign_service import BoldSignService


@pytest.fixture
def service_pair():
    """BoldSignService with mock template client and settings."""
    settings = MagicMock(
        boldsign_api_key="test-key",
        boldsign_api_host="https://api.boldsign.com",
    )
    template_client = MagicMock()
    svc = BoldSignService(settings=settings, template_client=template_client)
    return svc, template_client


def test_create_document_empty_signers_raises(service_pair):
    """Empty signers raises BoldSignServiceError."""
    service, _ = service_pair
    with pytest.raises(BoldSignServiceError, match="At least one signer is required"):
        service.create_document_from_template(
            template_id="tpl_123",
            signers=[],
        )


def test_create_document_invalid_embed_expiry_raises(service_pair):
    """embed_link_expiry_days outside 1-180 raises."""
    service, _ = service_pair
    signers = [{"role_index": 1, "signer_name": "A", "signer_email": "a@x.com"}]
    with pytest.raises(BoldSignServiceError, match="between 1 and 180"):
        service.create_document_from_template(
            template_id="tpl_123",
            signers=signers,
            embed_link_expiry_days=0,
        )
    with pytest.raises(BoldSignServiceError, match="between 1 and 180"):
        service.create_document_from_template(
            template_id="tpl_123",
            signers=signers,
            embed_link_expiry_days=181,
        )


def test_create_document_invalid_signer_raises(service_pair):
    """Signer with empty name or email raises."""
    service, _ = service_pair
    with pytest.raises(BoldSignServiceError, match="non-empty signer_name and signer_email"):
        service.create_document_from_template(
            template_id="tpl_123",
            signers=[{"role_index": 1, "signer_name": "", "signer_email": "a@x.com"}],
        )
    with pytest.raises(BoldSignServiceError, match="non-empty signer_name and signer_email"):
        service.create_document_from_template(
            template_id="tpl_123",
            signers=[{"role_index": 1, "signer_name": "A", "signer_email": ""}],
        )


def test_create_document_success(service_pair):
    """Successful create returns document_id and signer_links."""
    service, template_client = service_pair
    template_client.send_template.return_value = {"documentId": "doc_abc123"}

    mock_link_result = MagicMock()
    mock_link_result.sign_link = "https://sign.boldsign.com/embed/xyz"

    with patch("backend.services.boldsign_service.boldsign.ApiClient") as mock_client:
        mock_doc_api = MagicMock()
        mock_doc_api.get_embedded_sign_link.return_value = mock_link_result
        mock_client.return_value.__enter__.return_value = mock_doc_api
        with patch(
            "backend.services.boldsign_service.DocumentApi",
            return_value=mock_doc_api,
        ):
            result = service.create_document_from_template(
                template_id="tpl_123",
                signers=[{"role_index": 1, "signer_name": "Alice", "signer_email": "alice@example.com"}],
            )

    assert result["document_id"] == "doc_abc123"
    assert len(result["signer_links"]) == 1
    assert result["signer_links"][0]["signer_email"] == "alice@example.com"
    assert result["signer_links"][0]["sign_link"] == "https://sign.boldsign.com/embed/xyz"
    template_client.send_template.assert_called_once()
    call_args = template_client.send_template.call_args
    assert call_args[0][0] == "tpl_123"
    payload = call_args[0][1]
    assert "existingFormFields" not in payload["roles"][0]


def test_create_document_http_error_raises(service_pair):
    """HTTP error from BoldSign raises BoldSignServiceError."""
    service, template_client = service_pair
    template_client.send_template.side_effect = BoldSignServiceError(
        "Invalid template", code="boldsign_http_error"
    )

    with pytest.raises(BoldSignServiceError, match="Invalid template"):
        service.create_document_from_template(
            template_id="tpl_bad",
            signers=[{"role_index": 1, "signer_name": "A", "signer_email": "a@x.com"}],
        )


def test_create_document_no_document_id_raises(service_pair):
    """Response without documentId raises BoldSignServiceError."""
    service, template_client = service_pair
    template_client.send_template.return_value = {}

    with pytest.raises(BoldSignServiceError, match="did not return a document ID"):
        service.create_document_from_template(
            template_id="tpl_123",
            signers=[{"role_index": 1, "signer_name": "A", "signer_email": "a@x.com"}],
        )


def test_create_document_with_prefill_includes_existing_form_fields(service_pair):
    """Prefill fields are sent as existingFormFields in the template send payload."""
    service, template_client = service_pair
    template_client.send_template.return_value = {"documentId": "doc_xyz"}

    mock_link_result = MagicMock()
    mock_link_result.sign_link = "https://sign.boldsign.com/embed/abc"

    with patch("backend.services.boldsign_service.boldsign.ApiClient") as mock_client:
        mock_doc_api = MagicMock()
        mock_doc_api.get_embedded_sign_link.return_value = mock_link_result
        mock_client.return_value.__enter__.return_value = mock_doc_api
        with patch(
            "backend.services.boldsign_service.DocumentApi",
            return_value=mock_doc_api,
        ):
            service.create_document_from_template(
                template_id="tpl_123",
                signers=[
                    {"role_index": 1, "signer_name": "Alice", "signer_email": "alice@example.com"},
                    {"role_index": 2, "signer_name": "Bob", "signer_email": "bob@example.com"},
                ],
                prefill_fields=[
                    {"id": "field_a", "value": "v1", "role_index": 1},
                    {"id": "field_b", "value": "v2", "role_index": 2},
                ],
            )

    payload = template_client.send_template.call_args[0][1]
    role1 = next(r for r in payload["roles"] if r["roleIndex"] == 1)
    role2 = next(r for r in payload["roles"] if r["roleIndex"] == 2)
    assert role1["existingFormFields"] == [{"id": "field_a", "value": "v1"}]
    assert role2["existingFormFields"] == [{"id": "field_b", "value": "v2"}]


def test_create_document_prefill_defaults_to_first_role(service_pair):
    """Prefill fields without role_index go to first signer's role."""
    service, template_client = service_pair
    template_client.send_template.return_value = {"documentId": "doc_xyz"}

    mock_link_result = MagicMock()
    mock_link_result.sign_link = "https://sign.boldsign.com/embed/abc"

    with patch("backend.services.boldsign_service.boldsign.ApiClient") as mock_client:
        mock_doc_api = MagicMock()
        mock_doc_api.get_embedded_sign_link.return_value = mock_link_result
        mock_client.return_value.__enter__.return_value = mock_doc_api
        with patch(
            "backend.services.boldsign_service.DocumentApi",
            return_value=mock_doc_api,
        ):
            service.create_document_from_template(
                template_id="tpl_123",
                signers=[{"role_index": 1, "signer_name": "Alice", "signer_email": "alice@example.com"}],
                prefill_fields=[{"id": "field_1", "value": "hello"}],
            )

    payload = template_client.send_template.call_args[0][1]
    assert payload["roles"][0]["existingFormFields"] == [{"id": "field_1", "value": "hello"}]


def test_create_document_prefill_invalid_role_index_raises(service_pair):
    """Prefill field with role_index not in signers raises."""
    service, _ = service_pair
    signers = [{"role_index": 1, "signer_name": "A", "signer_email": "a@x.com"}]
    with pytest.raises(BoldSignServiceError, match="role_index 2 which does not match any signer"):
        service.create_document_from_template(
            template_id="tpl_123",
            signers=signers,
            prefill_fields=[{"id": "f1", "value": "v1", "role_index": 2}],
        )


def test_create_document_prefill_empty_id_raises(service_pair):
    """Prefill field with empty id raises."""
    service, _ = service_pair
    signers = [{"role_index": 1, "signer_name": "A", "signer_email": "a@x.com"}]
    with pytest.raises(BoldSignServiceError, match="must have a non-empty id"):
        service.create_document_from_template(
            template_id="tpl_123",
            signers=signers,
            prefill_fields=[{"id": "", "value": "v1"}],
        )


def test_create_document_prefill_empty_value_raises(service_pair):
    """Prefill field with empty value raises."""
    service, _ = service_pair
    signers = [{"role_index": 1, "signer_name": "A", "signer_email": "a@x.com"}]
    with pytest.raises(BoldSignServiceError, match="value cannot be empty"):
        service.create_document_from_template(
            template_id="tpl_123",
            signers=signers,
            prefill_fields=[{"id": "f1", "value": "   "}],
        )


def test_create_document_prefill_none_value_raises(service_pair):
    """Prefill field with None value raises."""
    service, _ = service_pair
    signers = [{"role_index": 1, "signer_name": "A", "signer_email": "a@x.com"}]
    with pytest.raises(BoldSignServiceError, match="must have a value"):
        service.create_document_from_template(
            template_id="tpl_123",
            signers=signers,
            prefill_fields=[{"id": "f1", "value": None}],
        )
