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

### Added

- **Embedded signing**: Optional `redirectUrl` / `redirect_url` on `POST /documents/from-template` is forwarded to BoldSign when generating embedded sign links (post-sign redirect).

### Documentation

- Added `docs/ARCHITECTURE.md` describing layers, DI, and contract/security choices.
- **README**: Table of all `docs/*.md` files, `redirectUrl` and role limits, expanded setup notes (`.gitignore` / `.env.example`), and refreshed examples.
