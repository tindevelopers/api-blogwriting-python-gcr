# API contract highlights (frontend-focused)

For the full, machine-readable contract:

- OpenAPI JSON: `/openapi.json`
- Swagger UI: `/docs`

## Environment Endpoints

| Environment | Base URL | Interactive Docs |
|------------|----------|------------------|
| **Development** | `https://blog-writer-api-dev-kq42l26tuq-od.a.run.app` | [/docs](https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/docs) |
| **Staging** | `https://blog-writer-api-staging-kq42l26tuq-od.a.run.app` | [/docs](https://blog-writer-api-staging-kq42l26tuq-od.a.run.app/docs) |
| **Production** | `https://blog-writer-api-prod-kq42l26tuq-ue.a.run.app` | [/docs](https://blog-writer-api-prod-kq42l26tuq-ue.a.run.app/docs) |

**Health Check Endpoints:**
- Development: `https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/health`
- Staging: `https://blog-writer-api-staging-kq42l26tuq-od.a.run.app/health`
- Production: `https://blog-writer-api-prod-kq42l26tuq-ue.a.run.app/health`

**OpenAPI JSON:**
- Development: `https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/openapi.json`
- Staging: `https://blog-writer-api-staging-kq42l26tuq-od.a.run.app/openapi.json`
- Production: `https://blog-writer-api-prod-kq42l26tuq-ue.a.run.app/openapi.json`

## Base conventions

- JSON request/response
- Use the exact HTTP status codes; do not rely on parsing error strings
- Timeouts: some operations (AI generation, keyword analysis) can take longer; use client timeouts accordingly

## Common endpoints

- Health: `GET /health`
- Standard generation: `POST /api/v1/generate`
- Enhanced blog generation: `POST /api/v1/blog/generate-enhanced`
- Premium review (evidence-backed): `POST /api/v1/reviews/{review_type}/evidence`
- Premium social (evidence-backed): `POST /api/v1/social/generate-evidence`
- Content analysis (category-based, DataForSEO-backed):
  - Analyze + persist evidence: `POST /api/v1/content/analyze`
  - Refresh sources (deltas): `POST /api/v1/content/refresh?analysis_id=...`
  - Get analysis + evidence: `GET /api/v1/content/analysis/{analysis_id}`
  - Content sentiment analysis: `POST /api/v1/content/analyze-sentiment`
  - URL analysis: `POST /api/v1/content/analyze-url`
- Enhanced keyword analysis: `POST /api/v1/keywords/enhanced`
- Field enhancement (SEO title/meta/slug/alt text): `POST /api/v1/content/enhance-fields`
- Image generation: `POST /api/v1/images/generate`
- Integrations + recommendations: `POST /api/v1/integrations/connect-and-recommend`

## Authentication

Some routes may require auth depending on environment configuration. Use the OpenAPI schema + backend env config as the source of truth.


## Content analysis routes (new)

Purpose: fetch and cache review/listing/social/sentiment evidence per content category (entity reviews, service reviews, product comparisons) using DataForSEO Business Data, Content Analysis, Social, Merchant.

### `POST /api/v1/content/analyze`
- Body:
  - `content` (string) – the article body (used for hashing/cache; not re-fetched)
  - `org_id` (string), `user_id` (string)
  - `content_format` ("blog" | "listicle" | "article" | "how_to" | "review" | "rating" | "todo")
  - `content_category` ("entity_review" | "service_review" | "product_comparison")
  - `entity_type` (optional; "hotel" | "restaurant" | "attraction" | "local_business" | "event" | "service" | "product")
  - Identifiers as applicable:
    - `google_cid`, `google_hotel_identifier`, `tripadvisor_url_path`, `trustpilot_domain`, `canonical_url`, `entity_name`
- Returns: `{ analysis_id, content_id, evidence_count, bundle }`
- Behavior: pulls category-specific sources, stores evidence + analysis summary for reuse.

### `POST /api/v1/content/refresh?analysis_id=...`
- Body: same shape as analyze (identifiers required); `analysis_id` in query.
- Returns: `{ analysis_id, new_evidence }`
- Use: scheduled refresh (weekly/bi-weekly) to pick up new reviews/social/sentiment without re-analyzing unchanged content.

### `GET /api/v1/content/analysis/{analysis_id}`
- Returns: `{ analysis, evidence }`
- Use: dashboard/frontend can display stored evidence and analysis summary.

## Premium evidence-backed generation

- `POST /api/v1/reviews/{review_type}/evidence` — runs the review generator with DataForSEO-backed evidence (Google/Tripadvisor/Trustpilot/social + AI Optimization LLM Responses). Provide identifiers for best results: `google_cid`, `tripadvisor_url_path`, `trustpilot_domain`, `canonical_url`, `entity_name`.
- `POST /api/v1/social/generate-evidence` — generates social copy grounded in fetched signals. Provide `canonical_url` (or at least `cta_url`) and `entity_name`/`topic` to improve evidence quality.

## Polish reuse

- `POST /api/v1/blog/polish` now accepts optional query `analysis_id` so the caller can signal reuse of existing evidence/analysis context (no extra DataForSEO calls are triggered by polish itself, but the ID lets us correlate runs).

## Frontend usage (Next.js starter)

- New client methods in `frontend-starter/lib/api/client.ts`:
  - `api.analyzeContent(body: ContentAnalysisRequest)`
  - `api.refreshContentSources(analysisId, body)`
  - `api.getContentAnalysis(analysisId)`
- Hooks in `frontend-starter/lib/api/hooks.ts`: `useAnalyzeContent`, `useRefreshContentSources`, `useContentAnalysis`.
- Include the category/entity identifiers so the correct sources are hit (Tripadvisor `url_path`, Trustpilot `domain`, Google `cid`/`hotel_identifier`, `canonical_url` for social).

## Content sentiment analysis

- `POST /api/v1/content/analyze-sentiment` — analyzes content sentiment, brand mentions, and engagement signals
  - Sentiment analysis (positive, negative, neutral)
  - Brand mentions and citations
  - Engagement signals and scores
  - Top topics and domains
  - Content summary with brand awareness metrics (if `include_summary=True`)

## URL analysis

- `POST /api/v1/content/analyze-url` — quick URL analysis and content extraction
  - Fetches URL and extracts text content
  - Provides quick analysis summary
  - Useful for content research and analysis

## Usage logging and attribution

- All AI operations automatically log usage to Firestore (when configured)
- Usage logs include attribution fields: `usage_source`, `usage_client`, `request_id`
- Attribution extracted from HTTP headers (`x-usage-source`, `x-usage-client`, `x-request-id`) or request context
- Collection naming: `ai_usage_logs_{environment}` (e.g., `ai_usage_logs_dev`, `ai_usage_logs_prod`)

## Env/config notes

- Required for DataForSEO: `DATAFORSEO_API_KEY`, `DATAFORSEO_API_SECRET`.
- Storage: code currently supports Supabase (if configured) or in-memory fallback; Firestore is supported for usage logging and evidence storage.
- Firestore usage logging: requires Firebase Admin SDK credentials (via `GOOGLE_APPLICATION_CREDENTIALS` or `FIREBASE_SERVICE_ACCOUNT_KEY_PATH`).
- Monitoring: schedule refresh via `POST /api/v1/content/refresh` per `analysis_id` to avoid re-spending credits.

