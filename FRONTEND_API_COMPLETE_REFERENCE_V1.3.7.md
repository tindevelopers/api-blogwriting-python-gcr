# Frontend API Complete Reference + Recent Changes (v1.3.7)

**Version:** 1.3.7  
**Date:** 2026-02-05  
**Purpose:** One-stop document for frontend integration. Includes recent changes and full endpoint index with sample usage for new APIs.

---

## Environment Endpoints

| Environment | Base URL | Interactive Docs |
|------------|----------|------------------|
| **Development** | `https://blog-writer-api-dev-613248238610.europe-west9.run.app` | `/docs` • `/redoc` |
| **Staging** | `https://blog-writer-api-staging-kq42l26tuq-od.a.run.app` | `/docs` • `/redoc` |
| **Production** | `https://blog-writer-api-prod-kq42l26tuq-ue.a.run.app` | `/docs` • `/redoc` |

**OpenAPI JSON:** `/openapi.json`  
**Health:** `/health`  
**API Prefix:** `/api/v1`  
**Content-Type:** `application/json`

---

## Recent Changes (Frontend-Relevant)

### v1.3.7 (2026-02-05)
- **New endpoint:** `POST /api/v1/keywords/longtail` for longtail keyword extraction with intent bucketing.
- **Improved keyword quality:** `enhanced_analysis[*].long_tail_keywords` now uses real queries from DataForSEO sources (autocomplete, PAA, related keywords, keyword ideas).
- **Fixed DataForSEO parsing:** `related_keywords` and `keyword_ideas` are now correctly extracted.

### v1.3.6 (2025-12-20)
- **Evidence-tier generation:** `POST /api/v1/reviews/{review_type}/evidence` and `POST /api/v1/social/generate-evidence`.
- **Content analysis with evidence caching:** `POST /api/v1/content/analyze`, `POST /api/v1/content/refresh`, `GET /api/v1/content/analysis/{analysis_id}`.
- **Sentiment and URL analysis:** `POST /api/v1/content/analyze-sentiment`, `POST /api/v1/content/analyze-url`.
- **Usage logging:** attribution headers (`x-usage-source`, `x-usage-client`, `x-request-id`) recorded when Firestore is configured.
- **Expanded blog types:** 28 supported blog types; word-count tolerance ±25%; SEO post-processing by default.

---

## Non‑Breaking Change Notes

- All new features are **opt-in** via new endpoints or new optional fields.
- Existing requests remain valid; responses may now include additional fields (e.g., `long_tail_keywords`).
- For best longtail keyword quality, use `POST /api/v1/keywords/longtail` instead of filtering `long_tail_keywords` from enhanced analysis.

---

## Request Headers (Recommended)

```http
Content-Type: application/json
x-usage-source: dashboard
x-usage-client: web-app
x-request-id: req-12345
```

Attribution headers are optional but strongly recommended for usage analytics.

---

## Error Format (All Endpoints)

```json
{
  "detail": "Error message",
  "error": "Error type",
  "status_code": 500
}
```

---

## Endpoint Index (Full List)

### Health & Config
- `GET /` — API info & version
- `GET /health` — basic health check
- `GET /api/v1/health/detailed` — extended health
- `GET /api/v1/config` — features & capabilities
- `GET /api/v1/metrics` — metrics summary
- `GET /api/v1/ai/health` — AI provider health

### Blog Generation & Content Ops
- `POST /api/v1/blog/generate-gateway` — AI gateway blog generation
- `POST /api/v1/blog/generate-enhanced` — DataForSEO enhanced generation
- `POST /api/v1/blog/generate-enhanced/stream` — SSE stream
- `POST /api/v1/blog/polish` — polish content (supports `analysis_id` query)
- `POST /api/v1/blog/quality-check` — quality score & grade
- `POST /api/v1/blog/meta-tags` — generate meta tags
- `GET /api/v1/blog/jobs/{job_id}` — async job status
- `POST /api/v1/batch/generate` — batch generation
- `GET /api/v1/batch/{job_id}/status` — batch status
- `GET /api/v1/batch/{job_id}/stream` — batch SSE stream
- `GET /api/v1/batch` — list batch jobs
- `DELETE /api/v1/batch/{job_id}` — cancel batch job

### Content Analysis (NEW v1.3.6)
- `POST /api/v1/content/analyze` — analyze & cache evidence
- `POST /api/v1/content/refresh?analysis_id=...` — refresh evidence
- `GET /api/v1/content/analysis/{analysis_id}` — fetch analysis + evidence
- `POST /api/v1/content/analyze-sentiment` — sentiment + brand signals
- `POST /api/v1/content/analyze-url` — URL extraction & summary

### Evidence‑Tier Generation (NEW v1.3.6)
- `POST /api/v1/reviews/{review_type}/evidence` — evidence-backed reviews
- `POST /api/v1/social/generate-evidence` — evidence-backed social posts

### Keywords & Topics
- `POST /api/v1/keywords/enhanced` — DataForSEO enhanced analysis
- `POST /api/v1/keywords/enhanced/stream` — SSE stream
- `POST /api/v1/keywords/longtail` — longtail intent buckets (NEW v1.3.7)
- `POST /api/v1/keywords/analyze` — basic analysis
- `POST /api/v1/keywords/suggest` — suggestions
- `POST /api/v1/keywords/extract` — extract from content
- `POST /api/v1/keywords/difficulty` — difficulty score
- `POST /api/v1/keywords/cluster-content` — cluster recommendations
- `POST /api/v1/keywords/goal-based-analysis` — goal-based analysis
- `POST /api/v1/keywords/goal-based-analysis/stream` — SSE stream
- `POST /api/v1/keywords/ai-optimization` — AI search optimization metrics
- `POST /api/v1/keywords/ai-mentions` — LLM mentions
- `POST /api/v1/keywords/ai-topic-suggestions` — AI topic ideas
- `POST /api/v1/keywords/ai-topic-suggestions/stream` — SSE stream
- `POST /api/v1/keywords/premium/ai-search` — premium AI keyword search
- `POST /api/v1/topics/recommend` — topic recommendations

### SEO & Competitive Analysis
- `POST /api/v1/seo/competitive-gap`
- `POST /api/v1/seo/top-pages`
- `POST /api/v1/seo/domain-summary`

### Integrations & Publishing
- `POST /api/v1/integrations/connect-and-recommend`
- `POST /api/v1/publish/webflow`
- `POST /api/v1/publish/shopify`
- `POST /api/v1/publish/wordpress`
- `GET /api/v1/platforms/webflow/collections`
- `GET /api/v1/platforms/shopify/blogs`
- `GET /api/v1/platforms/wordpress/categories`

### Media & Images
- `POST /api/v1/media/upload/cloudinary`
- `POST /api/v1/media/upload/cloudflare`
- `POST /api/v1/images/generate`
- `POST /api/v1/images/generate/stream`
- `POST /api/v1/images/generate-async`
- `POST /api/v1/images/batch-generate`
- `GET /api/v1/images/jobs/{job_id}`
- `GET /api/v1/images/jobs`
- `GET /api/v1/images/providers`
- `GET /api/v1/images/providers/health`

### Reviews, Social, Email
- `POST /api/v1/reviews/{review_type}` — standard review generation
- `POST /api/v1/social/generate` — standard social posts
- `POST /api/v1/email/generate-campaign` — email campaign generation

### Admin & Quotas (if enabled)
- `GET /api/v1/quota/{organization_id}`
- `POST /api/v1/quota/{organization_id}/set-limits`
- `GET /api/v1/cache/stats`
- `DELETE /api/v1/cache/clear`

---

## Sample Code (New Endpoints)

### 1) Longtail Keywords (NEW v1.3.7)

```typescript
const response = await fetch(`${API_BASE_URL}/api/v1/keywords/longtail`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    keyword: 'elevated dog bowl',
    location: 'United States',
    language: 'en',
    min_words: 3,
    include_autocomplete: true,
    include_paa: true,
    include_related: true,
    include_keyword_ideas: true,
    include_evidence_urls: false,
    limit: 100
  })
});

const data = await response.json();
console.log(data.buckets.commercial);
```

### 2) Content Analysis + Evidence Caching (NEW v1.3.6)

```typescript
const analyze = await fetch(`${API_BASE_URL}/api/v1/content/analyze`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    content: 'Full article body text...',
    org_id: 'org123',
    user_id: 'user456',
    content_format: 'review',
    content_category: 'entity_review',
    entity_name: 'Hotel Example',
    google_cid: '123456789',
    tripadvisor_url_path: '/Hotel_Review-...',
    trustpilot_domain: 'example.com',
    canonical_url: 'https://example.com/hotel'
  })
});

const { analysis_id } = await analyze.json();

// Refresh evidence (delta update)
await fetch(`${API_BASE_URL}/api/v1/content/refresh?analysis_id=${analysis_id}`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    content: 'Full article body text...',
    org_id: 'org123',
    user_id: 'user456',
    content_format: 'review',
    content_category: 'entity_review',
    entity_name: 'Hotel Example',
    google_cid: '123456789',
    tripadvisor_url_path: '/Hotel_Review-...',
    trustpilot_domain: 'example.com',
    canonical_url: 'https://example.com/hotel'
  })
});

// Retrieve stored analysis + evidence
const analysis = await fetch(`${API_BASE_URL}/api/v1/content/analysis/${analysis_id}`);
const analysisData = await analysis.json();
```

### 3) Evidence‑Backed Review Generation (NEW v1.3.6)

```typescript
const response = await fetch(`${API_BASE_URL}/api/v1/reviews/hotel/evidence`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    entity_name: 'Hotel Example',
    google_cid: '123456789',
    tripadvisor_url_path: '/Hotel_Review-...',
    trustpilot_domain: 'example.com',
    canonical_url: 'https://example.com/hotel',
    focus_keywords: ['luxury hotel', 'spa resort']
  })
});

const review = await response.json();
```

### 4) Evidence‑Backed Social Generation (NEW v1.3.6)

```typescript
const response = await fetch(`${API_BASE_URL}/api/v1/social/generate-evidence`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    topic: 'Your campaign topic',
    platforms: ['twitter', 'linkedin'],
    entity_name: 'Your Brand',
    canonical_url: 'https://example.com',
    campaign_goal: 'engagement',
    variants: 3,
    max_chars: 280,
    include_hashtags: true
  })
});

const social = await response.json();
```

### 5) Content Sentiment Analysis (NEW v1.3.6)

```typescript
const response = await fetch(`${API_BASE_URL}/api/v1/content/analyze-sentiment`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    keyword: 'your brand or topic',
    location: 'United States',
    language: 'en',
    limit: 10,
    include_summary: true
  })
});

const sentiment = await response.json();
```

### 6) URL Analysis (NEW v1.3.6)

```typescript
const response = await fetch(`${API_BASE_URL}/api/v1/content/analyze-url`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ url: 'https://example.com/article' })
});

const urlAnalysis = await response.json();
```

---

## Notes for Smooth Frontend Upgrades

- Keep existing integrations; add new endpoints behind feature flags.
- Store `analysis_id` in UI state so evidence refresh and retrieval are one-click.
- Adopt attribution headers early for usage analytics.
- For keyword research, prefer `keywords/longtail` when showing longtail lists.

---

## Additional References

- `API_DOCUMENTATION_V1.3.7.md`
- `docs/api-contract.md`
- `docs/keyword-api-inventory.md`
- `FRONTEND_INTEGRATION_V1.3.6.md`
- `FRONTEND_LONGTAIL_KEYWORDS_GUIDE.md`
- `IMAGE_GENERATION_GUIDE.md`
