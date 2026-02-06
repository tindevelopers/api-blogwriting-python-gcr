# Frontend Handoff: Topic Recommendations (Recent Fixes + Non‑Breaking Integration Guide)
**Date:** 2026‑02‑06  
**Scope:** Fix poor “Topic Recommendations” output (e.g. “Website For”, “For Business”, fake “0% competitor coverage” content gaps) while keeping the frontend integration **non‑breaking**.

---

## 1) Current frontend → backend call chain (unchanged)

When a user clicks **Get Recommendations** on the Objective step (`/admin/workflow/objective`), the frontend currently calls the backend via this primary path:

- **UI** → calls `recommendTopics(...)`
- **Hook** → `useTopicRecommendations.ts` → calls `blogWriterAPI.recommendTopics(...)`
- **Client** → `blog-writer-api.ts` → first tries:
  - **Next.js API route**: `POST /api/keywords/ai-topic-suggestions`
  - which proxies to: `POST {BLOG_WRITER_API_URL}/api/v1/keywords/ai-topic-suggestions`
- **Fallbacks (only if the primary path fails):**
  - `POST /api/blog-writer/topics/recommend` → `{BLOG_WRITER_API_URL}/api/v1/topics/recommend`
  - then `POST /api/blog-writer/topics/recommend-ai` (frontend-specific)

**Important:** the **Website URL** is *not* the source of topics. It can be used to extract a small keyword list (e.g. via `POST /api/site/extract-keywords`) which should be passed as `keywords` to improve the backend results.

---

## 2) What was wrong (root cause)

Two backend behaviors combined to produce the low-quality recommendations you saw:

### A) Naive objective → seed keyword extraction produced junk seeds
If the request to `/api/v1/keywords/ai-topic-suggestions` did not include `keywords`, the backend would extract up to 5 seed keywords from `content_objective` using simple regex + stopwords + 2-word phrase stitching. This frequently produced junk like:

- `"website for"`
- `"for business"`

Those junk seeds then drove the downstream recommendation engine.

### B) “Content gap” logic treated **0 Google results** as a big opportunity
The topic recommender’s “content gap” step uses Google Custom Search. When Google Custom Search is not configured (or returns empty), the client returns `[]`. Previously, the recommender would still compute “coverage” and create a “content gap” recommendation with default/fallback metrics (e.g. `search_volume=500`, `difficulty=50`), leading to cards like:

- “Content gap: **0% competitor coverage, 0% your coverage**”
- Ranking scores that looked “great” but were actually fabricated due to missing data.

---

## 3) What changed (backend fixes applied on 2026‑02‑06)

### 3.1 Content gap step now **skips** when Google returns no results
File: `src/blog_writer_sdk/seo/topic_recommender.py`

- **Old behavior:** if Google search returned `[]`, the engine still created “gap topics” with default metrics.
- **New behavior:** if `results` is empty, the engine logs a skip and **does not** generate gap topics for that keyword.

**Expected outcome:** You should no longer see “0% competitor coverage, 0% your coverage” cards created from empty Google results.

### 3.2 Seed keyword extraction is now cleaned + noise-filtered
File: `main.py` (`POST /api/v1/keywords/ai-topic-suggestions`)

Changes:
- Added stronger stopword handling (e.g. `for`, `in`, `of`, etc.)
- Added “generic noise” filters (e.g. `website`, `business`, `content`, `marketing`, etc.)
- Added explicit banned phrases (`website for`, `for business`, …)
- Added a final `_clean_seed_keywords(...)` pass that:
  - removes seeds starting/ending with glue words
  - requires at least one meaningful token
  - deduplicates and caps to 5

**Expected outcome:** If the frontend only supplies `content_objective`, seed keywords should now be more like:
- `pet grooming`
- `increase traffic`
and **not** “website for”.

---

## 4) API contracts (unchanged) + behavior differences (frontend should expect)

### 4.1 Primary endpoint (unchanged): AI Topic Suggestions
**Backend:** `POST {BLOG_WRITER_API_URL}/api/v1/keywords/ai-topic-suggestions`

**Request shape (existing):**

```json
{
  "keywords": ["pet grooming", "dog grooming cocoa fl"],
  "content_objective": "I want to create a website for my pet grooming business to increase traffic to my website",
  "target_audience": "pet owners",
  "industry": "Pet grooming",
  "content_goals": ["SEO & Rankings", "Engagement"],
  "location": "United States",
  "language": "en",
  "include_ai_search_volume": true,
  "include_llm_mentions": true,
  "include_llm_responses": false,
  "limit": 50
}
```

**Response shape:** unchanged (same keys), but with these **behavior changes**:
- `seed_keywords` may be **different** (cleaned) and can be **shorter**
- `topic_suggestions` will no longer include fabricated “content gap” items produced from empty Google results
- if the objective text is extremely generic and all extracted seeds are removed, the backend can return **400** (“Either 'keywords' or 'content_objective' must be provided”) because cleaned seeds become empty.

> **Frontend guidance:** treat 400 as “need better seeds” and prompt the user (or re-call with extracted site keywords).

### 4.2 Fallback endpoint (unchanged): Topic Recommendations
**Backend:** `POST {BLOG_WRITER_API_URL}/api/v1/topics/recommend`

Use this as fallback when `/ai-topic-suggestions` fails.

---

## 5) Recommended frontend changes (non‑breaking)

These are optional improvements. The backend fixes are backwards compatible, but the frontend will get better, more stable results if it does the following:

### 5.1 Always pass explicit `keywords` when available
If you have site-extracted keywords (`/api/site/extract-keywords`), pass them into the topic suggestion request.

**Why:** relying on objective-text extraction alone is inherently lossy. Keywords improve relevance and reduce the chance of returning empty seeds after cleanup.

### 5.2 Handle “empty or small `seed_keywords`” gracefully
If `seed_keywords.length === 0` or the response has very few suggestions, show a UX message like:
- “We need a few more specific keywords. Try adding your service + location (e.g. ‘dog grooming cocoa fl’, ‘pet grooming near me’).”

### 5.3 Don’t assume content gaps always exist
After the fix, content gaps may be empty if Google search isn’t configured or returns no results. That’s normal. The UI should not treat “missing content gap fields” as an error.

---

## 6) TypeScript reference implementation (copy/paste safe)

### 6.1 Types (minimal, compatible with existing backend response)

```ts
export type AITopicSuggestionsRequest = {
  keywords?: string[]; // recommended
  content_objective?: string; // allowed (but can be too generic)
  target_audience?: string;
  industry?: string;
  content_goals?: string[];
  location?: string; // default: United States
  language?: string; // default: en
  include_ai_search_volume?: boolean; // default: true
  include_llm_mentions?: boolean; // default: true
  include_llm_responses?: boolean; // default: false
  limit?: number; // default: 50
};

export type TopicSuggestion = {
  topic: string;
  source_keyword: string;
  ai_search_volume?: number;
  mentions?: number;
  search_volume?: number;
  difficulty?: number;
  competition?: number;
  cpc?: number;
  ranking_score?: number;
  opportunity_score?: number;
  estimated_traffic?: number;
  reason?: string;
  related_keywords?: string[];
  source?: string; // e.g. "ai_generated" | "perplexity_llm"
  ai_optimization_score?: number;
};

export type AITopicSuggestionsResponse = {
  seed_keywords: string[];
  content_objective?: string | null;
  target_audience?: string | null;
  industry?: string | null;
  content_goals?: string[];
  location: string;
  language: string;
  topic_suggestions: TopicSuggestion[];
  content_gaps: any[]; // currently empty in this endpoint (reserved)
  citation_opportunities: any[]; // currently empty in this endpoint (reserved)
  ai_metrics?: Record<string, any>;
  summary?: Record<string, any>;
};
```

### 6.2 Primary call (Next.js API route) + safe fallback

```ts
async function postJson<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
  }

  return (await res.json()) as T;
}

export async function getTopicRecommendationsNonBreaking(input: {
  websiteUrl?: string;
  contentObjective: string;
  targetAudience?: string;
  industry?: string;
  contentGoals?: string[];
  extractedSiteKeywords?: string[]; // from /api/site/extract-keywords
}) {
  const request: AITopicSuggestionsRequest = {
    // Always pass explicit keywords when you have them:
    keywords: (input.extractedSiteKeywords || []).slice(0, 10),
    content_objective: input.contentObjective,
    target_audience: input.targetAudience,
    industry: input.industry,
    content_goals: input.contentGoals,
    location: "United States",
    language: "en",
    include_ai_search_volume: true,
    include_llm_mentions: true,
    include_llm_responses: false,
    limit: 50,
  };

  try {
    // Primary (proxy): /api/keywords/ai-topic-suggestions → backend /api/v1/keywords/ai-topic-suggestions
    return await postJson<AITopicSuggestionsResponse>("/api/keywords/ai-topic-suggestions", request);
  } catch (primaryErr) {
    // Fallback 1: /api/blog-writer/topics/recommend → backend /api/v1/topics/recommend
    // (Keep this fallback unchanged to avoid breaking existing flows.)
    try {
      return await postJson<any>("/api/blog-writer/topics/recommend", {
        seed_keywords: (request.keywords && request.keywords.length > 0)
          ? request.keywords.slice(0, 10)
          : undefined,
        location: request.location,
        language: request.language,
        max_topics: 20,
        min_search_volume: 10,
        max_difficulty: 80,
        include_ai_suggestions: true,
      });
    } catch (fallbackErr) {
      // Bubble up the original error for easier debugging
      throw primaryErr;
    }
  }
}
```

### 6.3 UX guardrail for “objective too generic”

```ts
function isObjectiveTooGeneric(obj: string) {
  const t = obj.toLowerCase();
  return t.includes("create a website") && t.includes("increase traffic");
}

// Example:
if (isObjectiveTooGeneric(contentObjective) && extractedSiteKeywords.length === 0) {
  // show a nudge to add service + location keywords
}
```

---

## 7) Verification checklist (frontend + backend)

### Backend verification
After deploying/restarting the backend:

- Call `/api/v1/keywords/ai-topic-suggestions` using only the objective:
  - confirm `seed_keywords` does **not** include “website for” / “for business”
- If Google Custom Search is not configured:
  - confirm the response does **not** contain “content gap: 0% competitor coverage, 0% your coverage” style recommendations
  - backend logs may show: “Skipping content gap analysis for … (no search results returned)”

### Frontend verification
- Click **Get Recommendations**
- In DevTools → Network, open the response from the proxy route
- Confirm:
  - no junk seeds
  - no fabricated 0%/0% gap cards
  - UI handles fewer/empty suggestions without rendering weird “recommended” badges

---

## 8) Configuration (affects recommendation quality)

These backend environment variables materially impact output quality:

- **DataForSEO (core metrics & suggestions)**
  - `DATAFORSEO_API_KEY`
  - `DATAFORSEO_API_SECRET`
- **Google Custom Search (content gap enrichment)**
  - `GOOGLE_CUSTOM_SEARCH_API_KEY`
  - `GOOGLE_CUSTOM_SEARCH_ENGINE_ID`
- **AI topic generation**
  - `ANTHROPIC_API_KEY`

If Google Custom Search is not configured, the system can still provide useful recommendations (DataForSEO + AI), but it will not generate true “content gap” insights based on SERPs.

---

## 9) Notes on non‑breaking behavior

- No endpoint URLs were changed.
- No request fields were removed.
- Response shape remains the same.
- The only differences are *quality improvements*:
  - seed keywords are cleaned (less junk)
  - content gap recommendations are not fabricated from empty Google results

