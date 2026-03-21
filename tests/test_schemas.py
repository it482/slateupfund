"""Tests for Pydantic document schemas."""

import pytest
from pydantic import ValidationError

from backend.schemas.documents_model import (
    CreateDocumentFromTemplateRequest,
    CreateDocumentFromTemplateResponse,
    PrefillFormFieldInput,
    PrefillFormFieldsRequest,
    SignerInput,
    SignerLink,
)


class TestSignerInput:
    """Tests for SignerInput schema."""

    def test_valid_signer(self):
        """Valid signer passes validation."""
        s = SignerInput(role_index=1, signer_name="Alice", signer_email="alice@example.com")
        assert s.role_index == 1
        assert s.signer_name == "Alice"
        assert s.signer_email == "alice@example.com"

    def test_signer_alias(self):
        """Signer accepts camelCase aliases."""
        s = SignerInput(role_index=1, signerName="Bob", signerEmail="bob@example.com")
        assert s.signer_name == "Bob"
        assert s.signer_email == "bob@example.com"

    def test_role_index_bounds(self):
        """role_index must be 1-50."""
        SignerInput(role_index=1, signer_name="A", signer_email="a@x.com")
        SignerInput(role_index=50, signer_name="A", signer_email="a@x.com")
        with pytest.raises(ValidationError):
            SignerInput(role_index=0, signer_name="A", signer_email="a@x.com")
        with pytest.raises(ValidationError):
            SignerInput(role_index=51, signer_name="A", signer_email="a@x.com")

    def test_empty_name_rejected(self):
        """Empty signer_name is rejected."""
        with pytest.raises(ValidationError):
            SignerInput(role_index=1, signer_name="", signer_email="a@x.com")

    def test_empty_email_rejected(self):
        """Empty signer_email is rejected."""
        with pytest.raises(ValidationError):
            SignerInput(role_index=1, signer_name="Alice", signer_email="")

    def test_invalid_email_format_rejected(self):
        """Invalid email format is rejected."""
        with pytest.raises(ValidationError):
            SignerInput(role_index=1, signer_name="Alice", signer_email="not-an-email")


class TestPrefillFormFieldInput:
    """Tests for PrefillFormFieldInput schema."""

    def test_valid_string_value(self):
        """String value passes."""
        f = PrefillFormFieldInput(id="field_1", value="hello")
        assert f.id == "field_1"
        assert f.value == "hello"

    def test_valid_int_value(self):
        """Integer value passes (stringified by BoldSign)."""
        f = PrefillFormFieldInput(id="field_2", value=42)
        assert f.value == 42

    def test_valid_bool_value(self):
        """Boolean value passes."""
        f = PrefillFormFieldInput(id="field_3", value=True)
        assert f.value is True

    def test_empty_id_rejected(self):
        """Empty id is rejected."""
        with pytest.raises(ValidationError):
            PrefillFormFieldInput(id="", value="x")

    def test_role_index_optional(self):
        """role_index is optional and defaults to None."""
        f = PrefillFormFieldInput(id="f1", value="v1")
        assert f.role_index is None

    def test_role_index_valid_range(self):
        """role_index 1-50 is accepted."""
        f = PrefillFormFieldInput(id="f1", value="v1", role_index=1)
        assert f.role_index == 1
        f = PrefillFormFieldInput(id="f1", value="v1", role_index=50)
        assert f.role_index == 50

    def test_role_index_alias(self):
        """roleIndex camelCase alias works."""
        f = PrefillFormFieldInput(id="f1", value="v1", roleIndex=2)
        assert f.role_index == 2

    def test_role_index_out_of_range_rejected(self):
        """role_index outside 1-50 is rejected."""
        with pytest.raises(ValidationError):
            PrefillFormFieldInput(id="f1", value="v1", role_index=0)
        with pytest.raises(ValidationError):
            PrefillFormFieldInput(id="f1", value="v1", role_index=51)


class TestCreateDocumentFromTemplateRequest:
    """Tests for CreateDocumentFromTemplateRequest schema."""

    def test_minimal_valid_request(self):
        """Minimal valid request passes."""
        req = CreateDocumentFromTemplateRequest(
            template_id="tpl_123",
            signers=[SignerInput(role_index=1, signer_name="A", signer_email="a@x.com")],
        )
        assert req.template_id == "tpl_123"
        assert len(req.signers) == 1
        assert req.disable_emails is True
        assert req.embed_link_expiry_days == 30

    def test_full_request(self):
        """Full request with optional fields passes."""
        req = CreateDocumentFromTemplateRequest(
            template_id="tpl_456",
            signers=[
                SignerInput(role_index=1, signer_name="A", signer_email="a@x.com"),
                SignerInput(role_index=2, signer_name="B", signer_email="b@x.com"),
            ],
            title="Doc Title",
            message="Please sign",
            disable_emails=False,
            embed_link_expiry_days=90,
            prefill_fields=[PrefillFormFieldInput(id="f1", value="v1")],
        )
        assert req.title == "Doc Title"
        assert req.message == "Please sign"
        assert req.disable_emails is False
        assert req.embed_link_expiry_days == 90
        assert len(req.prefill_fields) == 1

    def test_empty_template_id_rejected(self):
        """Empty template_id is rejected."""
        with pytest.raises(ValidationError):
            CreateDocumentFromTemplateRequest(
                template_id="",
                signers=[SignerInput(role_index=1, signer_name="A", signer_email="a@x.com")],
            )

    def test_empty_signers_rejected(self):
        """Empty signers list is rejected."""
        with pytest.raises(ValidationError):
            CreateDocumentFromTemplateRequest(
                template_id="tpl_123",
                signers=[],
            )

    def test_embed_link_expiry_bounds(self):
        """embed_link_expiry_days must be 1-180."""
        with pytest.raises(ValidationError):
            CreateDocumentFromTemplateRequest(
                template_id="tpl",
                signers=[SignerInput(role_index=1, signer_name="A", signer_email="a@x.com")],
                embed_link_expiry_days=0,
            )
        with pytest.raises(ValidationError):
            CreateDocumentFromTemplateRequest(
                template_id="tpl",
                signers=[SignerInput(role_index=1, signer_name="A", signer_email="a@x.com")],
                embed_link_expiry_days=181,
            )


class TestCreateDocumentFromTemplateResponse:
    """Tests for CreateDocumentFromTemplateResponse schema."""

    def test_valid_response(self):
        """Valid response passes."""
        resp = CreateDocumentFromTemplateResponse(
            document_id="doc_abc",
            signer_links=[
                SignerLink(
                    signer_email="a@x.com",
                    signer_name="Alice",
                    sign_link="https://sign.link/1",
                    expires_at="2025-04-17T12:00:00Z",
                ),
            ],
        )
        assert resp.document_id == "doc_abc"
        assert len(resp.signer_links) == 1
        assert resp.signer_links[0].signer_email == "a@x.com"
        assert resp.signer_links[0].signer_name == "Alice"


class TestPrefillFormFieldsRequest:
    """Tests for PrefillFormFieldsRequest schema."""

    def test_valid_request(self):
        """Valid prefill request passes."""
        req = PrefillFormFieldsRequest(
            fields=[PrefillFormFieldInput(id="f1", value="v1")],
        )
        assert len(req.fields) == 1

    def test_empty_fields_rejected(self):
        """Empty fields list is rejected."""
        with pytest.raises(ValidationError):
            PrefillFormFieldsRequest(fields=[])
