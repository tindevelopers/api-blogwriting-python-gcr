## Keyword API Inventory

This document lists keyword-related API endpoints, where they are implemented, and
which upstream providers they call.

### Keyword endpoints (FastAPI)

Implementation location: `main.py`

- `POST /api/v1/keywords/analyze`
  - Function: `analyze_keywords()`
  - File: `main.py`
  - Providers: internal analyzer; DataForSEO when `max_suggestions_per_keyword` provided

- `POST /api/v1/keywords/enhanced`
  - Function: `analyze_keywords_enhanced()`
  - File: `main.py`
  - Providers: DataForSEO Labs, SERP API, Keywords Data (Google Ads), Autocomplete

- `POST /api/v1/keywords/enhanced/stream`
  - Function: `analyze_keywords_enhanced_stream()`
  - File: `main.py`
  - Providers: same as `/keywords/enhanced`

- `POST /api/v1/keywords/suggest`
  - Function: `suggest_keywords()`
  - File: `main.py`
  - Providers: internal suggestions

- `POST /api/v1/keywords/extract`
  - Function: `extract_keywords()`
  - File: `main.py`
  - Providers: internal extractor + Knowledge Graph (optional)

- `POST /api/v1/keywords/difficulty`
  - Function: `analyze_keyword_difficulty()`
  - File: `main.py`
  - Providers: internal difficulty analyzer

- `POST /api/v1/keywords/ai-optimization`
  - Function: `analyze_keywords_ai_optimization()`
  - File: `main.py`
  - Providers: DataForSEO AI Optimization + Keywords Data (Google Ads) for comparison

- `POST /api/v1/keywords/goal-based-analysis`
  - Function: `analyze_keywords_goal_based()`
  - File: `main.py`
  - Providers: DataForSEO Labs + SERP + Content Analysis + LLM mentions

- `POST /api/v1/keywords/goal-based-analysis/stream`
  - Function: `analyze_keywords_goal_based_stream()`
  - File: `main.py`
  - Providers: same as `/keywords/goal-based-analysis`

- `POST /api/v1/keywords/ai-mentions`
  - Function: `get_llm_mentions()`
  - File: `main.py`
  - Providers: DataForSEO AI Optimization (LLM mentions)

- `POST /api/v1/keywords/ai-topic-suggestions`
  - Function: `get_ai_topic_suggestions()`
  - File: `main.py`
  - Providers: DataForSEO AI Optimization (LLM responses + mentions)

- `POST /api/v1/keywords/ai-topic-suggestions/stream`
  - Function: `get_ai_topic_suggestions_stream()`
  - File: `main.py`
  - Providers: same as `/keywords/ai-topic-suggestions`

- `POST /api/v1/keywords/premium/ai-search`
  - Function: `premium_ai_keyword_search()`
  - File: `main.py`
  - Providers: TopicRecommendationEngine (AI), DataForSEO Labs/SERP/Keywords Data

### DataForSEO integration (all keyword-related calls)

Primary client: `src/blog_writer_sdk/integrations/dataforseo_integration.py`

- **DataForSEO Labs** (`/v3/dataforseo_labs/...`)
  - `google/keyword_overview/live`
  - `google/related_keywords/live`
  - `google/keyword_suggestions/live`
  - `google/keyword_ideas/live`
  - `bulk_keyword_difficulty/live`
  - `search_intent/live`
  - `google/relevant_pages/live`
  - `google/historical_serp/live`
  - `google/competitors_domain/live`

- **Keywords Data API (Google Ads datasource)** (`/v3/keywords_data/...`)
  - `google_ads/search_volume/live`
  - `google_trends_explore/live`

- **SERP API** (`/v3/serp/...`)
  - `google/autocomplete/live/advanced`
  - `google/organic/live/advanced`
  - `ai_summary/live` (if enabled)

- **AI Optimization API** (`/v3/ai_optimization/...`)
  - `ai_keyword_data/keywords_search_volume/live`
  - `llm_mentions/search/live`
  - `llm_mentions/top_pages/live`
  - `llm_mentions/top_domains/live`
  - `{platform}/llm_responses/live`

### Direct Google APIs used (non-AI keyword support)

These are not the source of keyword volume/CPC/competition data; they are used
for research, citations, and clustering.

- Google Custom Search: `src/blog_writer_sdk/integrations/google_custom_search.py`
- Google Search Console: `src/blog_writer_sdk/integrations/google_search_console.py`
- Google Knowledge Graph: `src/blog_writer_sdk/integrations/google_knowledge_graph.py`

### Caching + retention (DataForSEO)

- **Standard (task-based) APIs**: results retained **30 days** and can be re-fetched by `task_id` for free.
- **Live APIs**: results are not retained by DataForSEO; the app caches responses to reduce repeat charges.
- **SERP HTML Standard tasks**: retained **7 days**; **SERP screenshots**: URL valid **1 day** after retrieval.
- **On-Page tasks_ready** list includes tasks not collected within **3 days**.

**App-side caching behavior**
- Shared cache is **tenant-scoped by default**, with **admin opt-in** for shared categories.
- Admin settings endpoints:
  - `GET /api/v1/admin/cache-settings/{org_id}`
  - `PUT /api/v1/admin/cache-settings/{org_id}`
