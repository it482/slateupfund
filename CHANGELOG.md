# Changelog

All notable structural changes to this project are documented here.

### Changed

- **`DEBUG` default** is `false` (secure production default). Set `DEBUG=true` in `.env` for interactive docs and relaxed key checks during local development.
- **Package imports**: Application modules use the `backend.*` namespace consistently.
- **Dependency injection**: `BoldSignService` is provided via `get_boldsign_service`; route modules no longer construct a global service instance.
- **BoldSign HTTP**: Template `send` is implemented in `BoldSignTemplateClient` (timeouts, error mapping in one place).
- **Shared validation**: Prefill field id/value rules live in `backend.services.field_validation` (used by template send grouping and standalone prefill).
- **Errors**: `BoldSignServiceError` includes a `code`; HTTP 400 responses use `{"detail": {"code", "message"}}`.
- **OpenAPI**: `/openapi.json` is always served; interactive docs remain gated by `DEBUG`.
- **CORS**: Wildcard origins (`*`) are not combined with `allow_credentials=True`.
- **Routes**: `PATCH /documents/{document_id}/prefill` is active (standalone prefill).

### Documentation

- Added `docs/ARCHITECTURE.md` describing layers, DI, and contract/security choices.
