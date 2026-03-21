# Security

## Secrets

- Never commit `.env`, API keys, or BoldSign credentials. `.gitignore` excludes `.env`; rotate any key that was ever committed.
- The application API key (`API_KEY`) and BoldSign key (`BOLDSIGN_API_KEY`) must only be configured via environment or a secrets manager in production.

## Transport and clients

- Terminate TLS at your reverse proxy or platform; do not expose this service plain HTTP in production.
- Treat embedded sign URLs and PII in API responses as sensitive; avoid logging full URLs or emails at info level.

## Defaults

- `DEBUG` defaults to `false`. Interactive OpenAPI UI is disabled when `DEBUG=false`; machine-readable `/openapi.json` remains available for trusted automation only—protect the route with network policy if needed.

## Reporting

- Report security issues through your organization’s preferred private channel (not a public issue tracker if credentials could be involved).
