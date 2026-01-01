# API contract highlights (frontend-focused)

For the full, machine-readable contract:

- OpenAPI JSON: `/openapi.json`
- Swagger UI: `/docs`

## Base conventions

- JSON request/response
- Use the exact HTTP status codes; do not rely on parsing error strings
- Timeouts: some operations (AI generation, keyword analysis) can take longer; use client timeouts accordingly

## Common endpoints

- Health: `GET /health`
- Standard generation: `POST /api/v1/generate`
- Enhanced blog generation: `POST /api/v1/blog/generate-enhanced`
- Enhanced keyword analysis: `POST /api/v1/keywords/enhanced`
- Field enhancement (SEO title/meta/slug/alt text): `POST /api/v1/content/enhance-fields`
- Image generation: `POST /api/v1/images/generate`
- Integrations + recommendations: `POST /api/v1/integrations/connect-and-recommend`

## Authentication

Some routes may require auth depending on environment configuration. Use the OpenAPI schema + backend env config as the source of truth.


