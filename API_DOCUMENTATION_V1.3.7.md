# API Documentation v1.3.7

**Version:** 1.3.7  
**Date:** 2026-02-05

### Environment Endpoints

| Environment | Base URL | Interactive Docs |
|------------|----------|------------------|
| **Development** | `https://blog-writer-api-dev-613248238610.europe-west9.run.app` | [/docs](https://blog-writer-api-dev-613248238610.europe-west9.run.app/docs) \| [/redoc](https://blog-writer-api-dev-613248238610.europe-west9.run.app/redoc) |
| **Staging** | `https://blog-writer-api-staging-kq42l26tuq-od.a.run.app` | [/docs](https://blog-writer-api-staging-kq42l26tuq-od.a.run.app/docs) \| [/redoc](https://blog-writer-api-staging-kq42l26tuq-od.a.run.app/redoc) |
| **Production** | `https://blog-writer-api-prod-kq42l26tuq-ue.a.run.app` | [/docs](https://blog-writer-api-prod-kq42l26tuq-ue.a.run.app/docs) \| [/redoc](https://blog-writer-api-prod-kq42l26tuq-ue.a.run.app/redoc) |

**Note:** All examples in this documentation use the development endpoint. Replace the base URL with your target environment.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Version History](#version-history)
3. [What's New in v1.3.7](#whats-new-in-v137)
4. [Base Information](#base-information)
5. [Enhanced Blog Generation](#enhanced-blog-generation)
6. [Blog Types](#blog-types)
7. [Keyword Research Endpoints](#keyword-research-endpoints)
8. [SEO Optimization](#seo-optimization)
9. [Backlink Analysis](#backlink-analysis)
10. [Content Analysis & Sentiment](#content-analysis--sentiment)
11. [Premium Evidence-Tier Endpoints](#premium-evidence-tier-endpoints)
12. [Error Reference](#error-reference)

---

## Overview

The Blog Writer SDK API provides comprehensive AI-powered content generation, SEO optimization, and multi-platform publishing capabilities.

### API Version

- **Current Version:** 1.3.7
- **API Prefix:** `/api/v1`
- **Content Type:** `application/json`

### Rate Limits

- **Default:** No rate limits (development)
- **Production:** Configurable per organization
- **Batch Operations:** Async processing recommended

### Authentication

Currently using environment-based authentication. JWT token support coming soon.

---

## Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| **v1.3.7** | 2026-02-05 | Fixed DataForSEO response parsing for related keywords and keyword ideas. Added dedicated `/api/v1/keywords/longtail` endpoint with intent bucketing. Improved longtail keyword quality and diversity. |
| **v1.3.6** | 2025-12-20 | Firestore usage logging with attribution, premium evidence-tier endpoints, category-based content analysis, content sentiment analysis, URL analysis, expanded blog types (28 total), word count tolerance, SEO post-processing, backlink analysis |
| **v1.3.5** | 2025-11-XX | Premium AI keyword search, AI optimization endpoints, goal-based keyword analysis, AI mentions, AI topic suggestions |
| **v1.3.4** | 2025-11-20 | Enhanced keyword analysis with DataForSEO integration, SERP analysis, autocomplete suggestions |
| **v1.3.2** | 2025-XX-XX | Blog generation improvements, quality scoring enhancements |
| **v1.3.0** | 2025-XX-XX | Enhanced metrics, AI optimization features |
| **v1.2.0** | 2025-XX-XX | Multi-stage pipeline, intent-based optimization, few-shot learning, content length optimization, multi-model consensus, Knowledge Graph integration, semantic keywords, quality scoring |
| **v1.1.0** | 2025-XX-XX | Initial enhanced features |
| **v1.0.0** | 2025-XX-XX | Initial release - Enterprise ready |

---

## What's New in v1.3.7

### ✨ Major Enhancements

1. **Improved Longtail Keyword Extraction** - Real query sources instead of templates
   - Fixed DataForSEO response parsing for `related_keywords` and `keyword_ideas` endpoints
   - Correctly extracts nested keyword data from DataForSEO responses
   - Aggregates keywords from multiple sources: autocomplete, PAA, related keywords, keyword ideas
   - Improved keyword diversity and intent coverage

2. **New Longtail Keywords Endpoint** - Dedicated endpoint for longtail keyword research
   - `POST /api/v1/keywords/longtail` - Extract longtail keywords with intent bucketing
   - Returns keywords organized by intent: `commercial`, `informational`, `local_service`, `other`
   - Includes source metadata (autocomplete, PAA, related_keywords, keyword_ideas)
   - Optional evidence URLs for later verification
   - Filters by minimum word count (default: 3 words)

3. **Enhanced Keyword Quality** - Ahrefs-comparable keyword research
   - Real user queries instead of templated phrases
   - Better intent classification and bucketing
   - Improved source diversity (no longer dominated by autocomplete)
   - Commercial and informational keywords properly extracted

4. **Fixed Keyword Parsing** - Critical bug fixes
   - Correctly parses nested DataForSEO `related_keywords` response structure
   - Correctly parses nested DataForSEO `keyword_ideas` response structure
   - Ensures all keyword sources contribute to final results

### 🔧 Technical Improvements

- **DataForSEO Integration**: Fixed parsing logic in `dataforseo_integration.py` to handle nested response structures
- **Longtail Extractor**: New utility module (`longtail_extractor.py`) for centralized keyword processing
- **Intent Classification**: Improved intent detection for better keyword bucketing

---

## Base Information

### Root Endpoint

**GET** `/`

Get API information and version.

**Response:**

```json
{
  "message": "Blog Writer SDK API",
  "version": "1.3.7",
  "environment": "cloud-run",
  "testing_mode": false,
  "docs": "/docs",
  "health": "/health"
}
```

### API Configuration

**GET** `/api/v1/config`

Get API configuration and capabilities.

**Response:**

```json
{
  "version": "1.3.7",
  "features": {
    "enhanced_blog_generation": true,
    "dataforseo_content_generation": true,
    "seo_optimization": true,
    "backlink_analysis": true,
    "expanded_blog_types": true,
    "longtail_keywords": true,
    "improved_keyword_parsing": true
  }
}
```

---

## Enhanced Blog Generation

### Endpoint

**POST** `/api/v1/blog/generate-enhanced`

Generate high-quality blog content using DataForSEO Content Generation API with SEO optimization.

### Request Body

```json
{
  "topic": "string (required, 3-200 chars)",
  "keywords": ["string (required, min 1)"],
  "blog_type": "string (optional, default: 'custom')",
  "tone": "string (optional, default: 'professional')",
  "length": "string (optional, default: 'medium')",
  "word_count_target": "number (optional, 100-10000)",
  "optimize_for_traffic": "boolean (optional, default: true)",
  "analyze_backlinks": "boolean (optional, default: false)",
  "backlink_url": "string (optional, required if analyze_backlinks=true)",
  "use_dataforseo_content_generation": "boolean (optional, default: true)",
  "target_audience": "string (optional)",
  "custom_instructions": "string (optional, max 5000 chars)",
  "brand_name": "string (optional, for 'brand' type)",
  "category": "string (optional, for 'top_10' or 'listicle' type)",
  "product_name": "string (optional, for 'product_review' type)",
  "comparison_items": ["string (optional, for 'comparison' type)"]
}
```

### Blog Types

Available blog types (28 total):

**Core Types:**
- `custom`, `brand`, `top_10`, `product_review`, `how_to`, `comparison`, `guide`

**Popular Content Types:**
- `tutorial`, `listicle`, `case_study`, `news`, `opinion`, `interview`, `faq`, `checklist`, `tips`, `definition`, `benefits`, `problem_solution`, `trend_analysis`, `statistics`, `resource_list`, `timeline`, `myth_busting`, `best_practices`, `getting_started`, `advanced`, `troubleshooting`

### Response

```json
{
  "title": "string",
  "content": "string",
  "meta_title": "string",
  "meta_description": "string",
  "readability_score": 75.0,
  "seo_score": 85.0,
  "seo_metadata": {
    "semantic_keywords": ["string"],
    "subtopics": ["string"],
    "blog_type": "string",
    "keyword_density": {
      "keyword": {
        "count": 5,
        "density": 1.2
      }
    },
    "headings_count": 5,
    "avg_sentence_length": 17.5,
    "seo_factors": ["Keyword in title", "Optimal keyword density", "Good heading structure"],
    "word_count_range": {
      "min": 225,
      "max": 375,
      "actual": 320
    },
    "backlink_keywords": ["string"],
    "long_tail_keywords": ["string"]
  },
  "total_tokens": 76,
  "total_cost": 0.0038,
  "generation_time": 2.5,
  "success": true,
  "warnings": []
}
```

### Example Request

```bash
# Example using Development endpoint
BASE_URL="https://blog-writer-api-dev-613248238610.europe-west9.run.app"

curl -X POST "${BASE_URL}/api/v1/blog/generate-enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Introduction to Python Programming",
    "keywords": ["python", "programming"],
    "blog_type": "tutorial",
    "tone": "professional",
    "length": "short",
    "word_count_target": 300,
    "optimize_for_traffic": true
  }'
```

---

## Keyword Research Endpoints

### 1. Enhanced Keyword Analysis

**POST** `/api/v1/keywords/enhanced`

Comprehensive keyword analysis with DataForSEO integration, including search volume, difficulty, related keywords, keyword ideas, autocomplete suggestions, and SERP analysis.

**Request Body:**

```json
{
  "keywords": ["dog groomer"],
  "location": "United States",
  "language": "en",
  "max_suggestions_per_keyword": 50,
  "include_serp": true,
  "include_autocomplete": true,
  "include_related_keywords": true,
  "include_keyword_ideas": true
}
```

**Response:**

```json
{
  "enhanced_analysis": {
    "dog groomer": {
      "search_volume": 8100,
      "difficulty_score": 50.0,
      "difficulty": "medium",
      "competition": 0.0,
      "cpc": 1.28,
      "trend_score": 0.0,
      "parent_topic": "dog groomer",
      "primary_intent": "local_service",
      "suggested_keywords": [...],
      "related_keywords": [...],
      "keyword_ideas": [...],
      "long_tail_keywords": [
        "how to become a dog groomer",
        "dog grooming cost",
        "mobile dog grooming"
      ],
      "autocomplete_suggestions": [...],
      "serp_analysis": {...}
    }
  }
}
```

**Streaming Version:**

**POST** `/api/v1/keywords/enhanced/stream`

Returns Server-Sent Events (SSE) stream with real-time progress updates.

---

### 2. Longtail Keywords (NEW in v1.3.7)

**POST** `/api/v1/keywords/longtail`

Extract longtail keywords from real query sources (autocomplete, PAA, related keywords, keyword ideas) with intent bucketing.

**Request Body:**

```json
{
  "keyword": "elevated dog bowl",
  "location": "United States",
  "language": "en",
  "min_words": 3,
  "include_autocomplete": true,
  "include_paa": true,
  "include_related": true,
  "include_keyword_ideas": true,
  "include_evidence_urls": false,
  "limit": 100
}
```

**Response:**

```json
{
  "seed_keyword": "elevated dog bowl",
  "location": "United States",
  "language": "en",
  "min_words": 3,
  "total": 100,
  "buckets": {
    "commercial": [
      {
        "phrase": "best elevated dog bowls",
        "source": "keyword_ideas",
        "search_volume": 1200,
        "cpc": 2.50,
        "intent": "commercial"
      }
    ],
    "informational": [
      {
        "phrase": "how to choose elevated dog bowl",
        "source": "serp_paa",
        "search_volume": 0,
        "cpc": 0.0,
        "intent": "informational"
      }
    ],
    "local_service": [
      {
        "phrase": "elevated dog bowls near me",
        "source": "google_autocomplete",
        "search_volume": 0,
        "cpc": 0.0,
        "intent": "local_service"
      }
    ],
    "other": [
      {
        "phrase": "elevated dog bowls for large dogs",
        "source": "google_autocomplete",
        "search_volume": 0,
        "cpc": 0.0,
        "intent": "other"
      }
    ]
  },
  "items": [
    {
      "phrase": "best elevated dog bowls",
      "source": "keyword_ideas",
      "type": "Keyword Idea",
      "search_volume": 1200,
      "cpc": 2.50,
      "competition": 0.5,
      "keyword_difficulty": 45.0,
      "intent": "commercial",
      "evidence_urls": []
    }
  ]
}
```

**Key Features:**
- Extracts real user queries (not templated phrases)
- Organizes keywords by intent (commercial, informational, local_service, other)
- Includes source metadata for each keyword
- Optional evidence URLs for verification
- Filters by minimum word count

---

### 3. Goal-Based Keyword Analysis

**POST** `/api/v1/keywords/goal-based-analysis`

Analyze keywords based on content goals: SEO Rankings, Engagement, Conversions, or Brand Awareness.

**Request Body:**

```json
{
  "keywords": ["dog groomer"],
  "content_goal": "SEO & Rankings",
  "location": "United States",
  "language": "en"
}
```

**Content Goals:**
- `"SEO & Rankings"` - Focus on search volume, difficulty, SERP analysis
- `"Engagement"` - Focus on questions, topics, social signals
- `"Conversions"` - Focus on CPC, commercial intent, shopping results
- `"Brand Awareness"` - Focus on LLM mentions, citations, sentiment

**Streaming Version:**

**POST** `/api/v1/keywords/goal-based-analysis/stream`

Returns Server-Sent Events (SSE) stream with real-time progress updates.

---

### 4. AI Optimization

**POST** `/api/v1/keywords/ai-optimization`

Analyze keywords for AI search optimization, including AI search volume and trends.

**Request Body:**

```json
{
  "keywords": ["dog groomer"],
  "location": "United States",
  "language": "en"
}
```

---

### 5. AI Mentions

**POST** `/api/v1/keywords/ai-mentions`

Get LLM mentions data - what AI agents cite for keywords or domains.

**Request Body:**

```json
{
  "target": "dog groomer",
  "target_type": "keyword",
  "platform": "chat_gpt",
  "location": "United States",
  "language": "en",
  "limit": 10
}
```

**Parameters:**
- `target_type`: `"keyword"` or `"domain"`
- `platform`: `"chat_gpt"` or `"google"`

---

### 6. AI Topic Suggestions

**POST** `/api/v1/keywords/ai-topic-suggestions`

Get AI-optimized topic suggestions combining AI Search Volume, LLM Mentions, and LLM Responses.

**Request Body:**

```json
{
  "keywords": ["dog groomer"],
  "location": "United States",
  "language": "en",
  "limit": 20
}
```

**Alternative (using content objective):**

```json
{
  "content_objective": "Write about dog grooming services",
  "location": "United States",
  "language": "en",
  "limit": 20
}
```

**Streaming Version:**

**POST** `/api/v1/keywords/ai-topic-suggestions/stream`

Returns Server-Sent Events (SSE) stream with real-time progress updates.

---

### 7. Topics Recommend

**POST** `/api/v1/topics/recommend`

Recommend high-ranking blog topics based on seed keywords using DataForSEO, Google Custom Search, and Claude AI.

**Request Body:**

```json
{
  "keywords": ["dog groomer"],
  "location": "United States",
  "language": "en",
  "max_topics": 10
}
```

---

### 8. Other Keyword Endpoints

- **POST** `/api/v1/keywords/analyze` - Basic keyword analysis
- **POST** `/api/v1/keywords/suggest` - Keyword suggestions
- **POST** `/api/v1/keywords/extract` - Extract keywords from content
- **POST** `/api/v1/keywords/difficulty` - Analyze keyword difficulty
- **POST** `/api/v1/keywords/cluster-content` - Generate content recommendations for keyword clusters
- **POST** `/api/v1/keywords/premium/ai-search` - Premium AI keyword search

---

## Blog Types

### Complete List (28 Types)

| Type | Description | Best For |
|------|-------------|----------|
| `custom` | Custom content | Flexible content needs |
| `brand` | Brand overviews | Brand awareness |
| `top_10` | Ranking lists | Product comparisons |
| `product_review` | Product analysis | E-commerce |
| `how_to` | Step-by-step guides | Tutorials |
| `comparison` | Side-by-side comparisons | Decision-making |
| `guide` | Comprehensive guides | Educational content |
| `tutorial` | Step-by-step learning | Educational content |
| `listicle` | Numbered lists | Viral content |
| `case_study` | Real-world examples | B2B content |
| `news` | Current events | News sites |
| `opinion` | Editorial content | Thought leadership |
| `interview` | Q&A with experts | Authority building |
| `faq` | Frequently asked questions | Support content |
| `checklist` | Actionable checklists | Productivity |
| `tips` | Tips and tricks | Quick value |
| `definition` | What is X? | SEO content |
| `benefits` | Benefits-focused | Marketing |
| `problem_solution` | Problem-solving | Support |
| `trend_analysis` | Industry trends | Thought leadership |
| `statistics` | Data-driven content | Research |
| `resource_list` | Curated resources | Link building |
| `timeline` | Historical timelines | Educational |
| `myth_busting` | Debunking myths | Educational |
| `best_practices` | Industry best practices | Professional |
| `getting_started` | Beginner guides | Onboarding |
| `advanced` | Advanced topics | Expert content |
| `troubleshooting` | Problem-solving guides | Support |

---

## SEO Optimization

### Word Count Tolerance

All blog types support **±25% word count tolerance**:

- **Target:** 300 words
- **Acceptable Range:** 225-375 words
- **Priority:** Quality over exact word count

### Automatic SEO Post-Processing

When `optimize_for_traffic: true` (default), the API automatically:

1. **Keyword Density Analysis** - Ensures optimal keyword density (1-2%)
2. **Heading Structure** - Optimizes heading hierarchy
3. **Readability Scoring** - Calculates readability metrics
4. **SEO Score Calculation** - Provides comprehensive SEO score (0-100)
5. **Word Count Validation** - Checks if content is within ±25% tolerance

### SEO Metrics

The response includes comprehensive SEO metrics:

- `seo_score` - Overall SEO score (0-100)
- `readability_score` - Readability score (0-100)
- `keyword_density` - Keyword density per keyword
- `headings_count` - Number of headings
- `avg_sentence_length` - Average sentence length
- `seo_factors` - List of SEO factors applied
- `word_count_range` - Word count validation data
- `long_tail_keywords` - Longtail keyword suggestions (from real query sources)

---

## Backlink Analysis

### Premium Feature

Extract high-performing keywords from premium blog URLs by analyzing their backlinks.

### Usage

Set `analyze_backlinks: true` and provide `backlink_url`:

```json
{
  "topic": "Advanced Python Techniques",
  "keywords": ["python", "programming"],
  "blog_type": "advanced",
  "analyze_backlinks": true,
  "backlink_url": "https://example.com/premium-blog-post"
}
```

### How It Works

1. Analyzes backlinks from the provided URL
2. Extracts keywords from anchor texts
3. Merges extracted keywords with your provided keywords
4. Generates content optimized with proven keywords

### Response

Extracted keywords are included in `seo_metadata.backlink_keywords`:

```json
{
  "seo_metadata": {
    "backlink_keywords": ["extracted", "keywords", "from", "backlinks"]
  }
}
```

---

## Content Analysis & Sentiment

### Content Analysis with Evidence Caching

**POST** `/api/v1/content/analyze`

Analyze content and fetch evidence from DataForSEO, storing results for reuse.

**Request Body:**
```json
{
  "content": "article body text...",
  "org_id": "org123",
  "user_id": "user456",
  "content_format": "review",
  "content_category": "entity_review",
  "entity_name": "Hotel Example",
  "google_cid": "123456789",
  "tripadvisor_url_path": "/Hotel_Review-...",
  "trustpilot_domain": "example.com",
  "canonical_url": "https://example.com/hotel"
}
```

**Response:**
```json
{
  "analysis_id": "abc123",
  "content_id": "content456",
  "evidence_count": 15,
  "bundle": "entity_review"
}
```

### Refresh Evidence Sources

**POST** `/api/v1/content/refresh?analysis_id={analysis_id}`

Refresh evidence sources for existing analysis (delta updates).

### Get Analysis and Evidence

**GET** `/api/v1/content/analysis/{analysis_id}`

Retrieve stored analysis and evidence.

### Content Sentiment Analysis

**POST** `/api/v1/content/analyze-sentiment`

Analyze content sentiment, brand mentions, and engagement signals.

**Request Body:**
```json
{
  "keyword": "your brand or topic",
  "location": "United States",
  "language": "en",
  "limit": 10,
  "include_summary": true
}
```

### URL Analysis

**POST** `/api/v1/content/analyze-url`

Quick URL analysis and content extraction.

**Request Body:**
```json
{
  "url": "https://example.com/article"
}
```

---

## Premium Evidence-Tier Endpoints

### Evidence-Backed Review Generation

**POST** `/api/v1/reviews/{review_type}/evidence`

Generate high-quality reviews with DataForSEO-backed evidence.

**Path Parameters:**
- `review_type`: `hotel` | `restaurant` | `product` | `service`

**Request Body:**
```json
{
  "entity_name": "Hotel Example",
  "google_cid": "123456789",
  "tripadvisor_url_path": "/Hotel_Review-...",
  "trustpilot_domain": "example.com",
  "canonical_url": "https://example.com/hotel",
  "focus_keywords": ["luxury hotel", "spa resort"]
}
```

### Evidence-Backed Social Content Generation

**POST** `/api/v1/social/generate-evidence`

Generate social posts grounded in fetched signals.

**Request Body:**
```json
{
  "topic": "Your campaign topic",
  "platforms": ["twitter", "linkedin", "facebook"],
  "entity_name": "Your Brand",
  "canonical_url": "https://example.com",
  "campaign_goal": "engagement",
  "variants": 3,
  "max_chars": 280,
  "include_hashtags": true
}
```

---

## Usage Logging & Attribution

All AI operations automatically log usage to Firestore (when configured).

**Collection:** `ai_usage_logs_{environment}` (e.g., `ai_usage_logs_dev`, `ai_usage_logs_prod`)

**Usage Log Fields:**
- `org_id`: Organization identifier
- `user_id`: User identifier
- `operation`: Operation type (e.g., "blog_generation", "keyword_analysis")
- `model`: AI model used
- `prompt_tokens`: Input tokens
- `completion_tokens`: Output tokens
- `cost_usd`: Cost in USD
- `latency_ms`: Request latency
- `cached`: Whether result was cached
- `usage_source`: Attribution source (from header `x-usage-source` or context)
- `usage_client`: Attribution client (from header `x-usage-client` or context)
- `request_id`: Request identifier (from header `x-request-id` or context)
- `created_at`: Timestamp

**Setting Attribution Headers:**
```bash
curl -X POST "$BASE/api/v1/blog/generate-enhanced" \
  -H "Content-Type: application/json" \
  -H "x-usage-source: dashboard" \
  -H "x-usage-client: web-app" \
  -H "x-request-id: req-12345" \
  -d '{"primary_keyword": "example"}'
```

---

## Error Reference

### Common Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | Bad Request | Invalid request parameters |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Service not configured |

### Error Response Format

```json
{
  "detail": "Error message",
  "error": "Error type",
  "status_code": 500
}
```

### Example Error Handling

```typescript
try {
  const response = await fetch(`${API_BASE_URL}/api/v1/blog/generate-enhanced`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  });

  if (!response.ok) {
    const error = await response.json();
    console.error('Error:', error.detail);
    return;
  }

  const data = await response.json();
} catch (error) {
  console.error('Network Error:', error);
}
```

---

## Cost Information

**Typical Cost per Blog Post:**
- Generate Text: ~$0.0038 (76 tokens × $0.00005)
- Generate Subtopics: $0.0001
- Generate Meta Tags: $0.001
- **Total: ~$0.005 per blog post** (300 words)

**With Backlink Analysis:**
- Additional cost for backlink API calls (varies by subscription)

**Keyword Research:**
- DataForSEO API costs vary by subscription tier
- Longtail keyword extraction: included in DataForSEO usage

---

## Migration from v1.3.6

### Changes

1. **New Longtail Keywords Endpoint** - `POST /api/v1/keywords/longtail` for dedicated longtail research
2. **Improved Keyword Quality** - Real user queries instead of templated phrases in `enhanced_analysis[keyword].long_tail_keywords`
3. **Fixed Keyword Parsing** - Related keywords and keyword ideas now properly extracted from DataForSEO responses
4. **Intent Bucketing** - Longtail keywords organized by intent (commercial, informational, local_service, other)

### No Breaking Changes

All existing code continues to work. New features are opt-in via new request fields or new endpoints.

### Recommended Updates

1. **Use New Longtail Endpoint**: For better longtail keyword research, use `POST /api/v1/keywords/longtail` instead of filtering `long_tail_keywords` from enhanced analysis
2. **Check Keyword Quality**: The `enhanced_analysis[keyword].long_tail_keywords` field now contains real queries (improved quality)

---

## Support

- **Interactive API Docs:** `/docs` (Swagger UI)
- **ReDoc:** `/redoc`
- **Health Check:** `/health`
- **Frontend Integration Guide:** See `FRONTEND_INTEGRATION_V1.3.7.md` (if available)
- **OpenAPI JSON:** `/openapi.json`

---

## Additional Resources

- **Keyword Research Guide:** See `FRONTEND_LONGTAIL_KEYWORDS_GUIDE.md`
- **Goal-Based Analysis Guide:** See `FRONTEND_GOAL_BASED_KEYWORD_ANALYSIS.md`
- **AI Topic Suggestions Guide:** See `FRONTEND_AI_TOPIC_SUGGESTIONS.md`
- **Enhanced Blog Generation Guide:** See `ENHANCED_BLOG_GENERATION_GUIDE.md`
