## 1.1.0 (2025-11-10)

### Added
- New endpoint: `POST /api/v1/integrations/connect-and-recommend`
  - Target-agnostic integration input (`provider` label + opaque `connection` object).
  - Computes backlink and interlink recommendations from selected keywords.
  - Best-effort persistence to Supabase:
    - `integrations_{ENV}` for integration metadata.
    - `recommendations_{ENV}` for computed recommendations (aggregate + per-keyword).
- New Supabase schema file: `supabase_schema.sql` with environment-suffixed tables and optional RLS.
- WordPress import hardening: gracefully returns 501 if WP backend module isn’t installed.
- Enhanced keyword analysis endpoint: `POST /api/v1/keywords/enhanced` (uses DataForSEO when configured; graceful fallback).
- Phrase-mode for extraction: `/api/v1/keywords/extract` now supports `max_ngram` and `dedup_lim` to prefer multi-word keyphrases.
- DataForSEO client additions: keyword overview, related keywords, top searches, search intent helpers.

### Changed
- Documentation updated with version, publish date, new functionality highlights, and endpoint usage.
- DataForSEO credentials now prefer `DATAFORSEO_API_KEY` and `DATAFORSEO_API_SECRET` (fallback to legacy `DATAFORSEO_API_LOGIN`/`DATAFORSEO_API_PASSWORD`).

### Notes
- Develop environment deploys to `blog-writer-api-dev` in `europe-west1`.
- Service health: `/health` returns `{"status":"healthy"}` when deployment is live.


