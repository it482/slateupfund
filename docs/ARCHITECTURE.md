# Architecture

This backend is structured in layers so HTTP, future agent/MCP adapters, or workers can reuse the same BoldSign logic without duplicating use-case code.

## Layers

| Layer | Package / module | Role |
|--------|------------------|------|
| Configuration | `backend.config` | `Settings` from environment; `get_settings()` is cached. `get_settings_dependency()` wraps it for FastAPI so tests can patch `backend.config.get_settings`. |
| Domain / integration | `backend.services` | `BoldSignService` orchestrates BoldSign; `BoldSignTemplateClient` owns REST template send; `field_validation` owns shared field rules; `doc_prefill` owns standalone prefill. |
| HTTP API | `backend.routes` | FastAPI routers; map request bodies to service calls only. |
| Cross-cutting | `backend.dependencies` | `verify_api_key` (API key via `Security` for OpenAPI); `get_boldsign_service` builds `BoldSignService` from `Settings`. |
| Errors | `backend.exceptions` | `BoldSignServiceError` carries `message` and `code` for structured API responses. |

## Import convention

All application code uses the **`backend.*`** package prefix (e.g. `from backend.config import get_settings`). Run the app with `uvicorn backend.main:app` from the project root after `pip install -e .` so imports resolve without extra `PYTHONPATH`.

## Dependency injection

- **Settings**: `get_settings` is injected where needed (e.g. `get_boldsign_service` uses `Depends(get_settings)`).
- **BoldSignService**: Created per request via `get_boldsign_service`. Tests override `app.dependency_overrides[get_boldsign_service]` instead of patching multiple import paths.

## API contract and future tooling

- **`GET /openapi.json`** is always available (even when Swagger UI is disabled in production) for codegen and future tool definitions.
- **`X-API-Key`** is documented in OpenAPI via `Security` on the auth dependency.
- **BoldSign errors** return `400` with `{"detail": {"code": "<string>", "message": "<string>"}}` for machine-readable handling.

## Security notes

- Secrets live only in environment variables; never log API keys or full sign URLs at info level.
- CORS: `allow_credentials=True` is used only with explicit origin lists. In `DEBUG` with default `*`, credentials are disabled to match browser rules and avoid unsafe combinations.

## Related docs

- Root `README.md`: setup, env vars, endpoints, and a directory of all `docs/*.md` files.
- `docs/SECURITY.md`: secrets, transport, and operational security expectations.
- `docs/REFACTOR_PREFILL_TO_EXISTING_FORM_FIELDS.md`: prefill-at-send design (`existingFormFields`).
- `CHANGELOG.md`: dated structural changes.
