"""Tests for doc_prefill service."""

from unittest.mock import MagicMock, patch

import pytest

from backend.exceptions import BoldSignServiceError
from backend.services.doc_prefill import prefill_form_fields


def test_prefill_empty_document_id_raises():
    """Empty document_id raises BoldSignServiceError."""
    config = MagicMock()
    with pytest.raises(BoldSignServiceError, match="document_id is required"):
        prefill_form_fields(
            document_id="",
            fields=[{"id": "f1", "value": "v1"}],
            configuration=config,
        )
    with pytest.raises(BoldSignServiceError, match="document_id is required"):
        prefill_form_fields(
            document_id="   ",
            fields=[{"id": "f1", "value": "v1"}],
            configuration=config,
        )


def test_prefill_empty_fields_raises():
    """Empty fields list raises BoldSignServiceError."""
    config = MagicMock()
    with pytest.raises(BoldSignServiceError, match="At least one field is required"):
        prefill_form_fields(
            document_id="doc_123",
            fields=[],
            configuration=config,
        )


def test_prefill_field_without_id_raises():
    """Field without id raises BoldSignServiceError."""
    config = MagicMock()
    with pytest.raises(BoldSignServiceError, match="must have a non-empty id"):
        prefill_form_fields(
            document_id="doc_123",
            fields=[{"id": "", "value": "v1"}],
            configuration=config,
        )


def test_prefill_field_without_value_raises():
    """Field with None value raises BoldSignServiceError."""
    config = MagicMock()
    with pytest.raises(BoldSignServiceError, match="must have a value"):
        prefill_form_fields(
            document_id="doc_123",
            fields=[{"id": "f1", "value": None}],
            configuration=config,
        )


def test_prefill_empty_value_raises():
    """Field with empty string value raises BoldSignServiceError."""
    config = MagicMock()
    with pytest.raises(BoldSignServiceError, match="value cannot be empty"):
        prefill_form_fields(
            document_id="doc_123",
            fields=[{"id": "f1", "value": "   "}],
            configuration=config,
        )


def test_prefill_success():
    """Valid prefill calls BoldSign API."""
    config = MagicMock()
    with patch("backend.services.doc_prefill.boldsign.ApiClient") as mock_client:
        mock_api = MagicMock()
        mock_client.return_value.__enter__.return_value = mock_api
        mock_doc_api = MagicMock()
        mock_api.return_value = mock_doc_api

        with patch("backend.services.doc_prefill.DocumentApi", return_value=mock_doc_api):
            prefill_form_fields(
                document_id="doc_123",
                fields=[
                    {"id": "f1", "value": "hello"},
                    {"id": "f2", "value": 42},
                    {"id": "f3", "value": True},
                ],
                configuration=config,
            )

        mock_doc_api.prefill_fields.assert_called_once()
        call_kwargs = mock_doc_api.prefill_fields.call_args.kwargs
        assert call_kwargs["document_id"] == "doc_123"
        prefill_req = call_kwargs["prefill_field_request"]
        assert len(prefill_req.fields) == 3
        assert prefill_req.fields[0].id == "f1"
        assert prefill_req.fields[0].value == "hello"
        assert prefill_req.fields[1].value == "42"
        assert prefill_req.fields[2].value == "True"


def test_prefill_api_exception_raises_boldsign_error():
    """BoldSign API exception is wrapped in BoldSignServiceError."""
    config = MagicMock()
    with patch("backend.services.doc_prefill.boldsign.ApiClient"):
        with patch("backend.services.doc_prefill.DocumentApi") as mock_doc_api_cls:
            mock_doc_api = MagicMock()
            mock_doc_api.prefill_fields.side_effect = Exception("API error")
            mock_doc_api_cls.return_value = mock_doc_api

            with pytest.raises(BoldSignServiceError, match="Prefill failed"):
                prefill_form_fields(
                    document_id="doc_123",
                    fields=[{"id": "f1", "value": "v1"}],
                    configuration=config,
                )
