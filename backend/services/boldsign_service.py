"""BoldSign eSignature integration service."""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import boldsign
from boldsign.api.document_api import DocumentApi

from backend.config import Settings
from backend.exceptions import BoldSignServiceError
from backend.services.boldsign_template_client import BoldSignTemplateClient
from backend.services.doc_prefill import prefill_form_fields as _prefill_form_fields
from backend.services.field_validation import group_template_prefill_by_role


class BoldSignService:
    """Service for BoldSign document and template operations."""

    def __init__(
        self,
        settings: Settings,
        *,
        template_client: BoldSignTemplateClient | None = None,
    ) -> None:
        self._settings = settings
        self._api_key = settings.boldsign_api_key
        self._configuration = boldsign.Configuration(
            api_key=self._api_key,
            host=settings.boldsign_api_host,
        )
        self._template_client = template_client or BoldSignTemplateClient(
            api_key=self._api_key,
            base_url=settings.boldsign_api_host,
        )

    def create_document_from_template(
        self,
        template_id: str,
        signers: list[dict],
        *,
        title: Optional[str] = None,
        message: Optional[str] = None,
        disable_emails: bool = True,
        embed_link_expiry_days: int = 30,
        prefill_fields: Optional[list[dict[str, Any]]] = None,
    ) -> dict:
        """
        Create a document from a template and return document ID with embedded sign URLs.

        Uses existingFormFields in the template send request for prefill (single API call).
        Supports per-role prefill for multi-signer templates via role_index on each field.

        Args:
            template_id: BoldSign template ID.
            signers: List of signer dicts with keys: role_index (int), signer_name (str), signer_email (str).
            title: Optional document title.
            message: Optional message for signers.
            disable_emails: If True, signers won't receive email (use embedded URLs only).
            embed_link_expiry_days: Days until embedded sign links expire (1-180).
            prefill_fields: Optional list of {"id", "value", "role_index"?}. role_index defaults to first signer.

        Returns:
            {
                "document_id": str,
                "signer_links": [
                    {"signer_email": str, "sign_link": str, "expires_at": "ISO8601"}
                ]
            }
        """
        if not signers:
            raise BoldSignServiceError(
                "At least one signer is required",
                code="validation_error",
            )

        if not 1 <= embed_link_expiry_days <= 180:
            raise BoldSignServiceError(
                "embed_link_expiry_days must be between 1 and 180",
                code="validation_error",
            )

        signer_role_indices = {s["role_index"] for s in signers}
        first_role_index = signers[0]["role_index"]

        prefill_by_role: dict[int, list[dict[str, str]]] = {}
        if prefill_fields:
            prefill_by_role = group_template_prefill_by_role(
                prefill_fields,
                signer_role_indices,
                first_role_index,
            )

        roles_payload = []
        for i, s in enumerate(signers):
            name = (s.get("signer_name") or "").strip()
            email = (s.get("signer_email") or "").strip()
            if not name or not email:
                raise BoldSignServiceError(
                    f"Signer at index {i} must have non-empty signer_name and signer_email",
                    code="validation_error",
                )
            role_obj: dict[str, Any] = {
                "roleIndex": s["role_index"],
                "signerName": name,
                "signerEmail": email,
                "signerType": s.get("signer_type", "Signer"),
                "locale": s.get("locale", "EN"),
            }
            if s["role_index"] in prefill_by_role:
                role_obj["existingFormFields"] = [
                    {"id": pf["id"], "value": pf["value"]} for pf in prefill_by_role[s["role_index"]]
                ]
            roles_payload.append(role_obj)

        payload: dict[str, Any] = {
            "roles": roles_payload,
            "disableEmails": disable_emails,
        }
        if title is not None:
            payload["title"] = title
        if message is not None:
            payload["message"] = message

        data = self._template_client.send_template(template_id, payload)
        document_id = data.get("documentId")
        if not document_id:
            raise BoldSignServiceError(
                "BoldSign did not return a document ID",
                code="boldsign_response_error",
            )

        expires_at = datetime.now(timezone.utc) + timedelta(days=embed_link_expiry_days)
        sign_link_valid_till = expires_at

        signer_links = []
        with boldsign.ApiClient(self._configuration) as api_client:
            document_api = DocumentApi(api_client)
            for signer in signers:
                signer_email = signer["signer_email"]
                try:
                    link_result = document_api.get_embedded_sign_link(
                        document_id=document_id,
                        signer_email=signer_email,
                        sign_link_valid_till=sign_link_valid_till,
                    )
                except Exception as e:
                    raise BoldSignServiceError(
                        f"Failed to get embedded sign link for {signer_email}: {e}",
                        code="boldsign_api_error",
                    ) from e

                if link_result.sign_link:
                    signer_links.append(
                        {
                            "signer_email": signer_email,
                            "signer_name": signer.get("signer_name", ""),
                            "sign_link": link_result.sign_link,
                            "expires_at": expires_at.isoformat(),
                        }
                    )

        return {
            "document_id": document_id,
            "signer_links": signer_links,
        }

    def prefill_form_fields(
        self,
        document_id: str,
        fields: list[dict[str, Any]],
    ) -> None:
        """
        Prefill form fields in a document (standalone use, e.g. documents not from templates).
        For template-based documents, use existingFormFields in create_document_from_template instead.
        """
        _prefill_form_fields(
            document_id=document_id,
            fields=fields,
            configuration=self._configuration,
        )
