"""Document API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from backend.dependencies.auth import verify_api_key
from backend.dependencies.services import get_boldsign_service
from backend.schemas.documents_model import (
    CreateDocumentFromTemplateRequest,
    CreateDocumentFromTemplateResponse,
    PrefillFormFieldsRequest,
)
from backend.services.boldsign_service import BoldSignService

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(verify_api_key)],
)


@router.post(
    "/from-template",
    response_model=CreateDocumentFromTemplateResponse,
    summary="Create document from template",
    description=(
        "Creates a BoldSign document from an existing template with one or more signers. "
        "Returns the document ID and per-signer embedded signing URLs. "
        "Side effect: sends or prepares the document in BoldSign according to disable_emails. "
        "Requires X-API-Key. Machine clients may use GET /openapi.json for the full contract."
    ),
    response_description="BoldSign document ID and embedded sign links with expiry timestamps.",
)
async def create_document_from_template(
    body: CreateDocumentFromTemplateRequest,
    boldsign: Annotated[BoldSignService, Depends(get_boldsign_service)],
) -> CreateDocumentFromTemplateResponse:
    """Create a document from a BoldSign template and return document ID with embed URLs."""
    result = boldsign.create_document_from_template(
        template_id=body.template_id,
        signers=[
            {
                "role_index": s.role_index,
                "signer_name": s.signer_name,
                "signer_email": s.signer_email,
            }
            for s in body.signers
        ],
        title=body.title,
        message=body.message,
        disable_emails=body.disable_emails,
        embed_link_expiry_days=body.embed_link_expiry_days,
        prefill_fields=(
            [
                {"id": f.id, "value": f.value, "role_index": f.role_index}
                for f in body.prefill_fields
            ]
            if body.prefill_fields
            else None
        ),
    )
    return CreateDocumentFromTemplateResponse(**result)


@router.patch(
    "/{document_id}/prefill",
    status_code=204,
    summary="Prefill form fields on a document",
    description=(
        "Prefills form fields on an in-progress BoldSign document by field ID. "
        "For documents created from templates, prefer prefill_fields on POST /documents/from-template "
        "(single BoldSign call). Requires X-API-Key."
    ),
)
async def prefill_form_fields(
    document_id: str,
    body: PrefillFormFieldsRequest,
    boldsign: Annotated[BoldSignService, Depends(get_boldsign_service)],
) -> None:
    """Prefill form fields in a BoldSign document (standalone use)."""
    boldsign.prefill_form_fields(
        document_id=document_id,
        fields=[{"id": f.id, "value": f.value} for f in body.fields],
    )
