# Backend ↔ Frontend alignment notes

This folder is served by the backend at:

- `/project-docs/` (this page is at `/project-docs/backend-frontend-alignment.md`)

FastAPI interactive docs remain at:

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI spec: `/openapi.json`

## Environments / base URLs

- Use the environment-specific deployment URL for all requests.
- Prefer calling the backend by its canonical URL (avoid hardcoding preview URLs).

## CORS

The backend configures CORS for local dev and allowed deployment domains. If your frontend origin changes, update CORS in `main.py`.

## Health + observability

- Health: `GET /health`
- Metrics: `GET /api/v1/metrics` (if enabled in the deployment)

## Versioning

The backend exposes versioned endpoints under `/api/v1/...`. Use v1 routes unless explicitly agreed otherwise.

## Source of truth for contract changes

When backend behavior changes, update:

1. OpenAPI schema (automatic for FastAPI routes)
2. This `/project-docs/` content (human notes)
3. Any frontend API client types / adapters


