# Frontend & Backend Integration Guide – Multi-Content Expansion

## Scope & Goals
- Expand the consumer-facing app to generate **blogs (existing), reviews, social posts, and email campaigns** without regressing current flows.
- Keep the **blog pipeline, async queue/SSE, editing, publishing, and site-context/linking** intact.
- Add **new per-type backend endpoints** (Python Cloud Run) so the frontend doesn’t overload blog semantics.
- Provide a **test-ready plan** (regressions + new coverage) for the planning system.

## Current Frontend Extension Points (what we keep)
- Draft creation UI & async generation wiring live in `src/app/contentmanagement/drafts/new/page.tsx` and proxy generation via `src/app/api/workflow/generate-content/route.ts`.
- Content analysis is already plumbed through `src/app/api/blog-writer/analyze/route.ts` and the reusable panel in `src/components/content/ContentAnalysisPanel.tsx`.
- Workflow selection exists via `src/lib/workflow-models/registry.ts` with specializations like `models/comparison.ts`; these can route to new per-type workflows.
- Multi-content publishing scaffolding (sites, content type profiles, field mappings) is in place per `MULTI_CONTENT_TYPE_TEST_RESULTS.md`.

## New Backend Endpoints (per-type, to be added in Python Cloud Run)
All endpoints follow the existing pattern (`POST`, JSON, optional Bearer auth). Keep `warnings` arrays for non-blocking degradations and 503/504 for upstream outages. Use DataForSEO where noted.

### Reviews
- `POST /api/v1/reviews/product`
- `POST /api/v1/reviews/company`
- `POST /api/v1/reviews/local-business` (restaurants/attractions/hotels/contractors/industry)
- `POST /api/v1/reviews/event`

**Request (shared core)**
```json
{
  "entity_name": "Acme 3D Printer",
  "entity_url": "https://example.com/product",
  "industry": "construction",
  "category": "equipment",
  "location": "Austin, TX",
  "target_audience": "SMB contractors",
  "tone": "professional",
  "word_count": 1200,
  "include_citations": true,
  "rating_methodology": "evidence_based",   // optional
  "pros_cons_required": true,
  "schema": true,                           // return JSON-LD
  "include_comparison_table": true,        // if multiple entities supplied
  "keywords": ["3d printing", "construction tools"]
}
```

**Response (excerpt)**
```json
{
  "title": "...",
  "content_markdown": "...",
  "excerpt": "...",
  "schema_org": {...},              // optional JSON-LD
  "citations": [...],
  "pros_cons": {...},
  "comparison_table_md": "...",     // when comparison enabled
  "quality": { "seo_score": 82, "readability_score": 70 },
  "warnings": []
}
```

### Social Media Posts
- `POST /api/v1/social/generate`

**Request**
```json
{
  "platforms": ["linkedin", "twitter", "instagram"],
  "campaign_goal": "traffic",
  "cta_url": "https://example.com/offer",
  "brand_voice": "friendly",
  "variants": 5,
  "max_chars": 260,
  "include_hashtags": true,
  "topic": "AI tools for contractors",
  "target_audience": "construction PMs"
}
```

**Response**
```json
{
  "posts": [
    { "platform": "linkedin", "text": "...", "hashtags": ["#AI", "#Construction"], "hook": "..." }
  ],
  "image_prompts": ["..."],   // optional
  "warnings": []
}
```

### Email Campaigns
- `POST /api/v1/email/generate-campaign`

**Request**
```json
{
  "campaign_type": "drip",            // newsletter | promo | drip
  "emails_count": 4,
  "offer": "15% off annual plan",
  "audience_segment": "existing customers",
  "personalization_tokens": ["{{first_name}}", "{{company}}"],
  "tone": "friendly",
  "topic": "AI-powered scheduling for contractors",
  "include_subject_variants": true
}
```

**Response**
```json
{
  "sequence": [
    {
      "subject_lines": ["...", "..."],
      "preview_text": "...",
      "html_body": "...",
      "markdown_body": "..."
    }
  ],
  "warnings": []
}
```

### Competitive & URL Analysis (Phase 2, designed now)
- `POST /api/v1/content/analyze-url` — fetch URL → extract main content → quality/SEO scores + recommendations.
- `POST /api/v1/seo/competitive-gap` — SERP gap analysis via DataForSEO + suggested topics/angles.
- `POST /api/v1/seo/top-pages` and `POST /api/v1/seo/domain-summary` — top traffic pages, intents, backlinks (best-effort if DataForSEO not configured).

## Frontend Changes (tin-multi-tenant-blog-writer-v1)

### 1) Content Type selection & dynamic forms
- Add a **Content Type** selector to `src/app/contentmanagement/drafts/new/page.tsx`:
  - Blog (existing, default)
  - Review (entity name/url, industry/category, location, citations toggle, comparison checkbox)
  - Social Post (platforms, variants, max chars, CTA URL, hashtags toggle)
  - Email Campaign (campaign type, emails count, offer, personalization tokens)
- Persist `content_type` and type-specific payload into the draft metadata (short-term reuse of existing draft table; mark with `content_type`).

### 2) Generation routing (Next.js API proxies)
- Extend `src/app/api/workflow/generate-content/route.ts` to branch by `content_type` and call the new backend endpoints above (keep Cloud Run health wake-up logic and writing_style_overrides).
- Keep async mode + SSE queue status as-is; ensure queue items include `content_type` so the editor renders appropriate panels.

### 3) Workflow selection
- In `src/lib/workflow-models/registry.ts`, register new models for review, social, email:
  - Review model: multi-phase with product/entity research → pros/cons → schema → citations.
  - Social model: variant generator with per-platform constraints.
  - Email model: sequence planner → subject/preview scoring → body generation.
- Map `content_type` → model in the registry selection logic (contentType match has priority today).

### 4) Editing & QA
- Reuse `ContentAnalysisPanel` for blogs/reviews; add lightweight adapters for social/email (character counts, spammy-language flags, CTA/link presence).
- Add a “Claims & citations” checklist for reviews (e.g., verify citation count, schema presence).
- Keep existing blog field configuration and writing-style overrides; apply only when relevant.

### 5) Publishing / Export
- Blogs/Reviews: continue to use existing CMS publishing flows and field mappings; ensure new `content_type` is respected when picking mappings.
- Social/Email MVP: provide **Copy/Export** actions (CSV/JSON/download) instead of CMS publish; later can add provider-specific integrations.

### 6) UI/UX guardrails
- Prevent submission without required per-type fields.
- Show platform-specific limits (Twitter/X chars, LinkedIn max, etc.).
- Show async progress + warnings returned by backend (service sleep, DataForSEO unavailable).

## Data Model Notes
- Short term: store non-blog generated content as drafts with `content_type` + `metadata` (payload per type).
- Medium term: migrate to `content_items` + `content_type_profiles`/field mappings (already scaffolded in DB migrations).

## Regression + New Coverage (planning-system test matrix)

### Core regressions (must pass)
- Auth + org context; draft create/edit/view flows.
- Generation queue creation, SSE progress display, fetch of generated content.
- Site context lookup + internal link opportunities (blogs/reviews).
- CMS publishing targets & field mappings (blogs) unchanged.
- Content analysis panel (local + backend) still works.

### New feature coverage
- Review generation (product/company/local-business/event) returns markdown + citations + optional schema; comparison table when requested.
- Social generation returns per-platform variants respecting max chars, hashtags flag, CTA link presence.
- Email campaign generation returns sequence (subject/preview/body) with requested count and personalization tokens intact.
- Error/warning handling: Cloud Run cold-start, DataForSEO unavailable, missing required fields, timeout.
- Export/copy for social/email works.

### Edge cases
- Empty or oversized inputs per type (length/char limits).
- Missing citations when requested → warning shown.
- Multi-entity review with comparison_table.
- Multiple platforms in one social request.
- Email sequence length 1 vs many.

## Rollout Steps (frontend)
1) Add `content_type` selector + per-type form sections in draft creation.
2) Update `generate-content` API proxy to call new backend endpoints; keep SSE/queue IDs.
3) Register new workflow models; map content_type → model; add UI gating for quality level if needed.
4) Store per-type metadata in drafts; surface in edit/view.
5) Add type-specific QA widgets (char counts, claims/citations, spam checks).
6) Wire export/copy for social/email; keep CMS publish for blogs/reviews.
7) Run regression + new-feature test matrix; fix any broken warnings display.

## File References (current code to extend)

```120:158:src/app/contentmanagement/drafts/new/page.tsx
const [formData, setFormData] = useState({
  title: "",
  topic: "",
  keywords: "",
  target_audience: "",
  tone: "professional",
  word_count: 800,
  preset: "seo_focused",
  template_type: "expert_authority",
  custom_instructions: "",
  length: "medium",
  use_google_search: false,
  use_fact_checking: false,
  use_citations: false,
  use_serp_optimization: false,
  use_consensus_generation: false,
  use_knowledge_graph: false,
  use_semantic_keywords: false,
  use_quality_scoring: false
});
```

```31:75:src/app/api/workflow/generate-content/route.ts
/**
 * POST /api/workflow/generate-content
 * Phase 1: Generate blog content using enhanced generation endpoint
 * Checks Cloud Run health, wakes it if needed, then calls /api/v1/blog/generate-enhanced
 */
export async function POST(request: NextRequest) {
  ...
  const response = await fetch(`${apiUrl}/api/v1/blog/generate-enhanced`, { ... })
}
```

```20:63:src/lib/workflow-models/registry.ts
class WorkflowRegistryClass {
  private models: Map<string, WorkflowModel> = new Map();
  private defaultModelId: string = 'standard';
  ...
  selectModel(params: WorkflowSelectionParams): WorkflowModel {
    // selects by contentType, qualityLevel, platform, or default
  }
}
```

## Open Items to Confirm (with backend team)
- Final endpoint names and response schemas for reviews/social/email.
- Where to persist social/email outputs (drafts vs dedicated table).
- Which review subtype is MVP-first (product vs company vs local-business).
- Whether to add provider-specific social/email integrations in phase 1 or keep export-only.

## Deliverable
- This document is the handoff for frontend + backend to implement the multi-content expansion while preserving existing blog flows.

