# Refactor: Prefill Endpoint → existingFormFields

## Impact Analysis

### Current Flow
1. `POST /v1/template/send` (no prefill)
2. `PATCH /v1/document/prefillFields` (separate API call)
3. `GET` embedded sign links

### Proposed Flow
1. `POST /v1/template/send` with `existingFormFields` in roles (prefill at send time)
2. `GET` embedded sign links

---

## Codebase Impact

| Component | Impact | Notes |
|-----------|--------|-------|
| **boldsign_service.py** | High | Remove prefill endpoint call; add existingFormFields to roles payload |
| **doc_prefill.py** | Low | No longer used by `create_document_from_template`; can deprecate or keep for standalone prefill |
| **routes/documents.py** | None | Same request/response shape; no route changes |
| **schemas/documents_model.py** | None | `prefill_fields` stays; same structure |
| **tests/test_boldsign_service.py** | Medium | Remove `_prefill_form_fields` mock; assert payload includes existingFormFields |
| **tests/test_routes_documents.py** | Low | Prefill route tests are already commented out |
| **tests/test_doc_prefill.py** | None | doc_prefill still exists; tests remain valid |

---

## Behavioral Considerations

### 1. Per-Role vs Document-Level Prefill
- **BoldSign API**: `existingFormFields` is **per role** (inside each role object).
- **Current API**: `prefill_fields` is a **flat document-level** list.
- **Strategy**: Add all prefill fields to the **first role** (roleIndex of first signer). This works for:
  - Single-signer templates (all fields belong to that role)
  - Multi-signer templates with shared/label fields (BoldSign supports labels visible to all signers when in first role)
- **Limitation**: Role-specific fields for signer 2+ would need to be in that role. For full support, we could later add `prefill_fields_per_role` if needed.

### 2. Label Field Support
- **existingFormFields** supports **label** fields (read-only, visible to all signers).
- **Prefill endpoint** does **not** support labels.
- **Benefit**: Refactor enables label prefilling.

### 3. No Race Condition
- Prefill happens atomically with document creation.
- Signers never see empty fields.

---

## Efficiency Gains

| Metric | Before | After |
|--------|--------|-------|
| API calls (with prefill) | 2 (send + prefill) | 1 (send only) |
| Latency | ~2× round-trip | ~1× round-trip |
| Failure modes | Send can succeed, prefill can fail | Single atomic operation |
| Label fields | Not supported | Supported |

---

## Implementation Plan

### Phase 1: BoldSignService Refactor
1. **boldsign_service.py**
   - Remove import of `_prefill_form_fields`.
   - When building `roles_payload`, add `existingFormFields` to the **first role** when `prefill_fields` is provided.
   - Convert `prefill_fields` to BoldSign format: `[{"id": "...", "value": "..."}]` (camelCase: `id`, `value`).
   - Remove the post-send prefill block (lines 118–124).
   - Remove commented-out `prefill_form_fields` method and related code.

### Phase 2: doc_prefill Module
- **Option A (recommended)**: Keep `doc_prefill.py` for potential future use (e.g. prefilling documents created without templates, or post-send prefill). No changes.
- **Option B**: Delete `doc_prefill.py` and its tests if we are certain we will never need standalone prefill. Higher risk.

### Phase 3: Tests
1. **test_boldsign_service.py**
   - `test_create_document_success`: Remove `_prefill_form_fields` patch; add assertion that `requests.post` was called with payload containing `existingFormFields` in the first role when prefill_fields is passed.
   - Add `test_create_document_with_prefill_includes_existing_form_fields`: Verify payload structure.
   - Remove or update `test_prefill_form_fields_delegates` (that method is commented out; test may already fail—verify).

2. **test_routes_documents.py**
   - Add test: `test_create_document_from_template_with_prefill_passes_fields` to ensure prefill_fields are forwarded to the service.

### Phase 4: Cleanup
- Remove unused imports in `boldsign_service.py`.
- Update docstrings to mention existingFormFields instead of prefill endpoint.

---

## Rollback Plan
If issues arise: revert `boldsign_service.py` to call prefill endpoint after send. No schema or route changes, so rollback is localized.

---

## Checklist

- [x] Phase 1: Refactor BoldSignService
- [x] Phase 2: Keep doc_prefill for standalone prefill
- [x] Phase 3: Update tests
- [x] Phase 4: Cleanup and docstrings
- [ ] Manual test: Create document from template with prefill_fields
- [ ] Verify label field prefill works (if applicable)

## Implemented (Mar 2025)

- BoldSignService uses existingFormFields in template send; no separate prefill API call
- Per-role prefill: optional `role_index` on PrefillFormFieldInput (defaults to first signer)
- Validation: role_index must match a signer; empty id/value rejected
- Standalone prefill route and `prefill_form_fields` method retained for non-template documents
