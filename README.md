# SlateUp Funding Backend API

Production-ready backend API for creating BoldSign documents from templates with multiple signers. Returns document ID and embedded sign URLs with configurable expiration.

## Setup

1. **Install dependencies** (from project root):

   ```bash
   pip install -e .
   # or
   pip install -r backend/requirements.txt
   ```

2. **Configure environment** – create `.env` in the project root:

   ```env
   BOLDSIGN_API_KEY=your_boldsign_api_key
   API_KEY=your_api_key_for_auth
   ```

   Copy from `.env.example` for all options. Default `DEBUG` is `false` (production-safe). Set `DEBUG=true` for local development: startup logs a warning if BoldSign/API keys are missing. When `DEBUG=false`, the process **still starts** if keys are unset (critical log only)—this keeps `GET /health` reachable on platforms like Cloud Run while secrets are wired up; document routes require `BOLDSIGN_API_KEY` and `API_KEY` at runtime via dependencies. All `/documents/*` endpoints require the `X-API-Key` header. Set `CORS_ORIGINS` (comma-separated) for browser clients; when `DEBUG=true` and empty, defaults to `*` with **credentials disabled** (safe combination). Set `RATE_LIMIT` (e.g. `100/minute`) for rate limiting; default is `100/minute`.

3. **Run the API**:

   ```bash
   uvicorn backend.main:app --reload
   ```

   - Interactive API docs: http://localhost:8000/docs (only when `DEBUG=true`).
   - **OpenAPI JSON** (for codegen / future agents): http://localhost:8000/openapi.json — always available when the server is running, including in production.

4. **Health check**: `GET /health` returns `{"status": "ok"}` for load balancers and monitoring. No auth required.

5. **Container / Cloud Run** (optional): build and run with the repo `Dockerfile` (Python 3.12-slim, installs the package, listens on `PORT`, default `8080`). Example:

   ```bash
   docker build -t slateupfunding-api .
   docker run -p 8080:8080 -e PORT=8080 -e BOLDSIGN_API_KEY=... -e API_KEY=... slateupfunding-api
   ```

## Recent updates (post-deployment)

- **Container image**: Added `Dockerfile` and `.dockerignore` for standard deployments; uvicorn binds `0.0.0.0` and uses the `PORT` env var (Cloud Run–compatible).
- **Startup on missing secrets**: In production (`DEBUG=false`), missing `BOLDSIGN_API_KEY` or `API_KEY` no longer prevents the app from listening on the port; critical logs are emitted instead so health checks succeed while you configure the service. Authenticated routes still enforce the API key; BoldSign calls need a valid BoldSign key.
- **API response**: Each entry in `signer_links` now includes optional **`embed_id`**—the opaque `documentId` query value parsed from BoldSign’s `sign_link` (useful for embedded signing flows where that token is distinct from the top-level `document_id`).
- **Request JSON**: Create-from-template accepts **camelCase** field names (`signerName`, `signerEmail`, `roleIndex`) as well as snake_case, matching common client conventions.

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for layers, dependency injection, and API contract choices. Structural changes are summarized in [CHANGELOG.md](CHANGELOG.md). Security expectations: [docs/SECURITY.md](docs/SECURITY.md).

## Testing

Run the test suite with pytest:

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

All tests use mocks for external APIs (BoldSign); no API key is required to run them.

## API

### GET /health

Returns `{"status": "ok"}`. No authentication required. Use for load balancer health checks and monitoring.

### POST /documents/from-template

Creates a document from an existing BoldSign template with multiple signers.

**Request body:**

```json
{
  "template_id": "your-template-id-from-boldsign",
  "signers": [
    {"role_index": 1, "signer_name": "Alice", "signer_email": "alice@example.com"},
    {"role_index": 2, "signer_name": "Bob", "signer_email": "bob@example.com"}
  ],
  "title": "Funding Agreement",
  "message": "Please review and sign.",
  "disable_emails": true,
  "embed_link_expiry_days": 30,
  "prefill_fields": [
    {"id": "applicant_name", "value": "John Doe"},
    {"id": "approver_notes", "value": "Pre-approved", "role_index": 2}
  ]
}
```

- `role_index`: Maps to template roles (1 = first role, 2 = second, etc.). Create the template in the BoldSign web app and note role indices. You may send `signerName`, `signerEmail`, and `roleIndex` instead of the snake_case names.
- `prefill_fields`: Optional. Prefills form fields via BoldSign `existingFormFields` (single API call). Use `role_index` for multi-signer templates; omit to assign to the first signer's role.
- `signer_email`: Must be a valid email format.
- `disable_emails`: If `true`, signers get no email; use embedded URLs only.
- `embed_link_expiry_days`: 1–180 days until sign links expire.

**Response:**

```json
{
  "document_id": "abc123-...",
  "signer_links": [
    {
      "signer_email": "alice@example.com",
      "signer_name": "Alice",
      "sign_link": "https://app.boldsign.com/document/sign/?documentId=...",
      "embed_id": "opaque-token-from-sign-link",
      "expires_at": "2025-04-15T12:00:00+00:00"
    },
    {
      "signer_email": "bob@example.com",
      "signer_name": "Bob",
      "sign_link": "https://app.boldsign.com/document/sign/?documentId=...",
      "embed_id": "opaque-token-from-sign-link",
      "expires_at": "2025-04-15T12:00:00+00:00"
    }
  ]
}
```

**BoldSign / validation errors** (HTTP 400) return a structured body:

```json
{
  "detail": {
    "code": "validation_error",
    "message": "Human-readable description"
  }
}
```

Codes include `validation_error`, `boldsign_http_error`, `boldsign_api_error`, `boldsign_response_error`, and generic `boldsign_error`.

### PATCH /documents/{document_id}/prefill

Prefills fields on an existing in-progress document by field id (standalone path). Prefer `prefill_fields` on `POST /documents/from-template` when creating from a template (single BoldSign call). Same `X-API-Key` auth. Returns **204** with no body on success.

**Request body:**

```json
{
  "fields": [
    {"id": "field_id_from_boldsign", "value": "value"}
  ]
}
```

## Template setup

1. Create a template in the [BoldSign web app](https://app.boldsign.com).
2. Add roles (e.g., Role 1, Role 2) and assign signature fields to each role.
3. Use the template ID when calling the API.
4. Map each signer to a role via `role_index` (1 = first role, 2 = second, etc.).
