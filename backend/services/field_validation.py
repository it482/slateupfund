"""Shared validation for BoldSign form field id/value payloads."""

from collections import defaultdict
from typing import Any

from backend.exceptions import BoldSignServiceError


def _normalize_field_entry(
    f: dict[str, Any],
    index: int,
    *,
    item_label: str,
) -> tuple[str, str]:
    field_id = f.get("id")
    value = f.get("value")
    if not field_id or not str(field_id).strip():
        raise BoldSignServiceError(
            f"{item_label} at index {index} must have a non-empty id",
            code="validation_error",
        )
    if value is None:
        raise BoldSignServiceError(
            f"{item_label} at index {index} must have a value",
            code="validation_error",
        )
    str_value = str(value).strip()
    if not str_value:
        raise BoldSignServiceError(
            f"{item_label} at index {index} value cannot be empty",
            code="validation_error",
        )
    return str(field_id).strip(), str_value


def parse_flat_field_items(
    fields: list[dict[str, Any]],
    *,
    item_label: str = "Field",
) -> list[dict[str, str]]:
    """Validate a list of {id, value} dicts for standalone document prefill."""
    if not fields:
        raise BoldSignServiceError(
            "At least one field is required",
            code="validation_error",
        )
    out: list[dict[str, str]] = []
    for i, f in enumerate(fields):
        fid, val = _normalize_field_entry(f, i, item_label=item_label)
        out.append({"id": fid, "value": val})
    return out


def group_template_prefill_by_role(
    prefill_fields: list[dict[str, Any]],
    signer_role_indices: set[int],
    first_role_index: int,
) -> dict[int, list[dict[str, str]]]:
    """Group template prefill entries by signer role_index (BoldSign existingFormFields)."""
    prefill_by_role: dict[int, list[dict[str, str]]] = defaultdict(list)
    for i, f in enumerate(prefill_fields):
        fid, val = _normalize_field_entry(f, i, item_label="Prefill field")
        role_idx = f.get("role_index") or first_role_index
        if role_idx not in signer_role_indices:
            raise BoldSignServiceError(
                f"Prefill field '{fid}' has role_index {role_idx} which does not match any signer",
                code="validation_error",
            )
        prefill_by_role[role_idx].append({"id": fid, "value": val})
    return prefill_by_role
