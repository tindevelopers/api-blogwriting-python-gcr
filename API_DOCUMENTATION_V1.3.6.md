# API Documentation v1.3.6

**Version:** 1.3.6  
**Date:** 2025-12-20  

### Environment Endpoints

| Environment | Base URL | Interactive Docs |
|------------|----------|------------------|
| **Development** | `https://blog-writer-api-dev-kq42l26tuq-od.a.run.app` | [/docs](https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/docs) \| [/redoc](https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/redoc) |
| **Staging** | `https://blog-writer-api-staging-kq42l26tuq-od.a.run.app` | [/docs](https://blog-writer-api-staging-kq42l26tuq-od.a.run.app/docs) \| [/redoc](https://blog-writer-api-staging-kq42l26tuq-od.a.run.app/redoc) |
| **Production** | `https://blog-writer-api-prod-kq42l26tuq-ue.a.run.app` | [/docs](https://blog-writer-api-prod-kq42l26tuq-ue.a.run.app/docs) \| [/redoc](https://blog-writer-api-prod-kq42l26tuq-ue.a.run.app/redoc) |

**Note:** All examples in this documentation use the development endpoint. Replace the base URL with your target environment.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [What's New in v1.3.6](#whats-new-in-v136)
3. [Base Information](#base-information)
4. [Enhanced Blog Generation](#enhanced-blog-generation)
5. [Blog Types](#blog-types)
6. [SEO Optimization](#seo-optimization)
7. [Backlink Analysis](#backlink-analysis)
8. [Error Reference](#error-reference)

---

## Overview

The Blog Writer SDK API provides comprehensive AI-powered content generation, SEO optimization, and multi-platform publishing capabilities.

### API Version

- **Current Version:** 1.3.6
- **API Prefix:** `/api/v1`
- **Content Type:** `application/json`

### Rate Limits

- **Default:** No rate limits (development)
- **Production:** Configurable per organization
- **Batch Operations:** Async processing recommended

### Authentication

Currently using environment-based authentication. JWT token support coming soon.

---

## What's New in v1.3.6

### ✨ Major Enhancements

1. **Firestore Usage Logging with Attribution** - Comprehensive AI usage tracking
   - Automatic usage logging to Firestore with attribution (usage_source, usage_client, request_id)
   - Request context tracking for usage attribution
   - Environment-based collection naming (ai_usage_logs_{env})
   - Cost tracking and analytics support

2. **Premium Evidence-Tier Endpoints** - High-quality evidence-backed content generation
   - Evidence-backed review generation (`POST /api/v1/reviews/{review_type}/evidence`)
   - Evidence-backed social content generation (`POST /api/v1/social/generate-evidence`)
   - DataForSEO integration for reviews, social signals, and sentiment

3. **Category-Based Content Analysis** - Advanced content analysis with evidence caching
   - Content analysis with evidence storage (`POST /api/v1/content/analyze`)
   - Evidence refresh for delta updates (`POST /api/v1/content/refresh`)
   - Analysis retrieval (`GET /api/v1/content/analysis/{analysis_id}`)
   - Supports multiple content categories (entity_review, service_review, product_comparison)

4. **Content Sentiment Analysis** - Brand perception and engagement insights
   - Sentiment analysis endpoint (`POST /api/v1/content/analyze-sentiment`)
   - Brand mentions and citations
   - Engagement signals and scores
   - Top topics and domains analysis

5. **URL Analysis** - Quick content extraction and analysis
   - URL analysis endpoint (`POST /api/v1/content/analyze-url`)
   - Text extraction and summarization
   - Content research support

6. **Natural Blog Writing** - Dashboard-controlled prompts
   - Enhanced prompt customization from dashboard
   - Natural writing style options
   - Phase modes for different generation strategies

7. **Expanded Blog Types** - 28 content types (top 80% of popular formats)
   - Added 21 new blog types: tutorial, listicle, case_study, news, opinion, interview, faq, checklist, tips, definition, benefits, problem_solution, trend_analysis, statistics, resource_list, timeline, myth_busting, best_practices, getting_started, advanced, troubleshooting

8. **Word Count Tolerance** - ±25% flexibility for natural content
   - Quality prioritized over exact word count
   - Automatic validation and reporting

9. **SEO Post-Processing** - Automatic traffic optimization
   - Keyword density analysis (optimal: 1-2%)
   - Heading structure optimization
   - Readability scoring
   - Comprehensive SEO score (0-100)

10. **Backlink Analysis** - Extract keywords from premium blogs
    - Analyze backlinks from URLs
    - Extract keywords from anchor texts
    - Merge with provided keywords

---

## Base Information

### Root Endpoint

**GET** `/`

Get API information and version.

**Response:**

```json
{
  "message": "Blog Writer SDK API",
  "version": "1.3.6",
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
  "version": "1.3.6",
  "features": {
    "enhanced_blog_generation": true,
    "dataforseo_content_generation": true,
    "seo_optimization": true,
    "backlink_analysis": true,
    "expanded_blog_types": true
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
    "backlink_keywords": ["string"]
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
# Example using Production endpoint (replace with your target environment)
BASE_URL="https://blog-writer-api-prod-kq42l26tuq-ue.a.run.app"
# Development: https://blog-writer-api-dev-kq42l26tuq-od.a.run.app
# Staging: https://blog-writer-api-staging-kq42l26tuq-od.a.run.app

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

**Request Body:** Same as `/api/v1/content/analyze`

**Response:**
```json
{
  "analysis_id": "abc123",
  "new_evidence": 3
}
```

### Get Analysis and Evidence

**GET** `/api/v1/content/analysis/{analysis_id}`

Retrieve stored analysis and evidence.

**Response:**
```json
{
  "analysis": {
    "analysis_id": "abc123",
    "content_id": "content456",
    "content_category": "entity_review",
    "created_at": "2025-12-20T10:00:00Z"
  },
  "evidence": [
    {
      "source": "google_reviews",
      "payload": {...},
      "collected_at": "2025-12-20T10:00:00Z"
    }
  ]
}
```

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

**Response:**
```json
{
  "citations": [
    {
      "text": "Citation text...",
      "sentiment": "positive",
      "url": "https://example.com",
      "title": "Source Title"
    }
  ],
  "sentiment": {
    "positive": 8,
    "negative": 1,
    "neutral": 1
  },
  "engagement_signals": [...],
  "top_domains": [...],
  "summary": "Brand awareness summary..." // if include_summary=true
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

**Response:**
```json
{
  "url": "https://example.com/article",
  "text": "Extracted text content...",
  "summary": "Content summary..."
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

**Response:**
```json
{
  "title": "Review Title",
  "content": "Review content with evidence citations...",
  "rating": 4.5,
  "evidence_sources": [
    "google_reviews",
    "tripadvisor",
    "trustpilot"
  ]
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

**Response:**
```json
{
  "posts": [
    {
      "platform": "twitter",
      "text": "Post content...",
      "hashtags": ["#hashtag1", "#hashtag2"]
    }
  ],
  "warnings": []
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

---

## Migration from v1.3.5

### Changes

1. **New Blog Types** - 21 additional blog types available
2. **Word Count Tolerance** - Automatic ±25% tolerance (no code changes needed)
3. **SEO Metrics** - Enhanced `seo_metadata` with more detailed metrics
4. **Backlink Analysis** - New optional fields: `analyze_backlinks` and `backlink_url`

### No Breaking Changes

All existing code continues to work. New features are opt-in via new request fields.

---

## Support

- **Interactive API Docs:** `/docs` (Swagger UI)
- **ReDoc:** `/redoc`
- **Health Check:** `/health`
- **Frontend Integration Guide:** See `FRONTEND_INTEGRATION_V1.3.6.md`

