"""Document API schemas (OpenAPI / future agent tool contracts)."""

from typing import Optional, Union

from pydantic import BaseModel, EmailStr, Field


class SignerInput(BaseModel):
    """Signer mapped to a template role for BoldSign send-from-template."""

    model_config = {"populate_by_name": True}

    role_index: int = Field(
        ge=1,
        le=50,
        description="1-based index matching the role order in the BoldSign template.",
    )
    signer_name: str = Field(
        min_length=1,
        max_length=256,
        alias="signerName",
        description="Display name shown on the signing flow.",
    )
    signer_email: EmailStr = Field(
        max_length=256,
        alias="signerEmail",
        description="Signer email; must match the role when requesting embedded links.",
    )


class PrefillFormFieldInput(BaseModel):
    """Single form field to prefill by BoldSign field id."""

    model_config = {"populate_by_name": True}

    id: str = Field(
        min_length=1,
        description="BoldSign form field id from the template or document.",
    )
    value: Union[str, int, bool] = Field(
        description="Value stored in the field; coerced to string for BoldSign.",
    )
    role_index: Optional[int] = Field(
        default=None,
        ge=1,
        le=50,
        alias="roleIndex",
        description="For template send: assigns the field to this signer's role. Omit to use the first signer.",
    )


class CreateDocumentFromTemplateRequest(BaseModel):
    """Create an envelope from a BoldSign template and obtain embedded signing URLs."""

    template_id: str = Field(
        min_length=1,
        description="BoldSign template id from the BoldSign dashboard.",
    )
    signers: list[SignerInput] = Field(
        min_length=1,
        description="Ordered signers; each role_index must exist on the template.",
    )
    title: Optional[str] = Field(
        None,
        max_length=256,
        description="Optional document title shown to signers.",
    )
    message: Optional[str] = Field(
        None,
        max_length=5000,
        description="Optional message body for signers.",
    )
    disable_emails: bool = Field(
        True,
        description="If true, BoldSign does not email signers; use returned embedded URLs only.",
    )
    embed_link_expiry_days: int = Field(
        default=30,
        ge=1,
        le=180,
        description="Embedded sign link validity in days (BoldSign limits apply).",
    )
    prefill_fields: Optional[list[PrefillFormFieldInput]] = Field(
        default=None,
        description="Optional fields sent as existingFormFields in the same send call.",
    )


class SignerLink(BaseModel):
    """Embedded signing URL for one signer."""

    signer_email: str
    signer_name: str = ""
    sign_link: str
    expires_at: str


class CreateDocumentFromTemplateResponse(BaseModel):
    """Document id and per-signer embedded links."""

    document_id: str = Field(description="BoldSign document id.")
    signer_links: list[SignerLink] = Field(
        description="One entry per signer with an embedded sign_link and expires_at (ISO 8601).",
    )


class PrefillFormFieldsRequest(BaseModel):
    """Standalone prefill for an existing in-progress document."""

    fields: list[PrefillFormFieldInput] = Field(
        min_length=1,
        description="Field id/value pairs; types supported by BoldSign (textbox, dropdown, checkbox, etc.).",
    )
