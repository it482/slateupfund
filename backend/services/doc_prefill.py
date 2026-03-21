"""Prefill form fields in BoldSign documents. Form-agnostic: accepts any field IDs and values."""

from typing import Any

import boldsign
from boldsign.api.document_api import DocumentApi
from boldsign.models.prefill_field import PrefillField
from boldsign.models.prefill_field_request import PrefillFieldRequest

from backend.exceptions import BoldSignServiceError
from backend.services.field_validation import parse_flat_field_items


def prefill_form_fields(
    document_id: str,
    fields: list[dict[str, Any]],
    configuration: boldsign.Configuration,
) -> None:
    """
    Prefill form fields in a document. Form-agnostic: accepts any field IDs and values.

    Args:
        document_id: BoldSign document ID (must be in-progress, not yet signed).
        fields: List of {"id": str, "value": str|int|bool} - field IDs and values to prefill.
                Values are stringified for BoldSign (supports textbox, dropdown, checkbox, etc.).
        configuration: BoldSign API configuration (api_key, host).

    Raises:
        BoldSignServiceError: If prefill fails (e.g. document signed, invalid field, etc.).
    """
    if not document_id or not document_id.strip():
        raise BoldSignServiceError("document_id is required", code="validation_error")

    normalized = parse_flat_field_items(fields, item_label="Field")
    prefill_items = [PrefillField(id=item["id"], value=item["value"]) for item in normalized]
    prefill_request = PrefillFieldRequest(fields=prefill_items)

    with boldsign.ApiClient(configuration) as api_client:
        document_api = DocumentApi(api_client)
        try:
            document_api.prefill_fields(
                document_id=document_id.strip(),
                prefill_field_request=prefill_request,
            )
        except Exception as e:
            raise BoldSignServiceError(
                f"Prefill failed: {e}",
                code="boldsign_api_error",
            ) from e
