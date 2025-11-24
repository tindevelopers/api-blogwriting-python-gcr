# API Documentation v1.3.4

**Version:** 1.3.4  
**Date:** 2025-11-20  
**Base URL:** `https://blog-writer-api-dev-kq42l26tuq-od.a.run.app`  
**Interactive Docs:** `/docs` (Swagger UI) | `/redoc` (ReDoc)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Base Information](#base-information)
3. [Health & Status](#health--status)
4. [Blog Generation](#blog-generation)
5. [Keyword Research](#keyword-research)
6. [AI Provider Management](#ai-provider-management)
7. [Image Generation](#image-generation)
8. [Platform Publishing](#platform-publishing)
9. [Content Analysis](#content-analysis)
10. [Batch Processing](#batch-processing)
11. [User Management](#user-management)
12. [Integrations](#integrations)
13. [Media Management](#media-management)
14. [Monitoring & Metrics](#monitoring--metrics)
15. [Error Reference](#error-reference)

---

## Overview

The Blog Writer SDK API provides comprehensive AI-powered content generation, SEO optimization, and multi-platform publishing capabilities.

### API Version

- **Current Version:** 1.3.4
- **API Prefix:** `/api/v1`
- **Content Type:** `application/json`

### Rate Limits

- **Default:** No rate limits (development)
- **Production:** Configurable per organization
- **Batch Operations:** Async processing recommended

### Authentication

Currently using environment-based authentication. JWT token support coming soon.

---

## Base Information

### Root Endpoint

**GET** `/`

Get API information and version.

**Response:**

```json
{
  "name": "Blog Writer SDK API",
  "version": "1.3.4",
  "status": "operational",
  "environment": "development",
  "testing_mode": false
}
```

### API Configuration

**GET** `/api/v1/config`

Get API configuration and capabilities.

**Response:**

```json
{
  "version": "1.3.4",
  "features": {
    "enhanced_blog_generation": true,
    "keyword_research": true,
    "image_generation": true,
    "platform_publishing": true
  },
  "limits": {
    "max_keywords": 200,
    "max_suggestions_per_keyword": 150
  }
}
```

---

## Health & Status

### Health Check

**GET** `/health`

Basic health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "timestamp": 1700000000.0,
  "version": "1.3.4"
}
```

### Readiness Check

**GET** `/ready`

Check if service is ready to accept requests.

**Response:**

```json
{
  "status": "ready",
  "services": {
    "database": "connected",
    "cache": "connected",
    "ai_providers": "available"
  }
}
```

### Liveness Check

**GET** `/live`

Check if service is alive.

**Response:**

```json
{
  "status": "alive",
  "uptime_seconds": 3600
}
```

### Detailed Health

**GET** `/api/v1/health/detailed`

Comprehensive health check with service status.

**Response:**

```json
{
  "status": "healthy",
  "version": "1.3.4",
  "services": {
    "ai_providers": {
      "openai": "available",
      "anthropic": "available"
    },
    "image_providers": {
      "stability_ai": "available"
    },
    "dataforseo": "configured"
  },
  "metrics": {
    "requests_today": 150,
    "average_response_time": 2.5
  }
}
```

---

## Blog Generation

### Unified Blog Generation (Recommended)

**POST** `/api/v1/blog/generate-unified`

Single endpoint for all blog types with intelligent routing.

**Request Body:**

```json
{
  "blog_type": "standard" | "enhanced" | "local_business" | "abstraction",
  "topic": "string (required)",
  "keywords": ["string"],
  "tone": "professional" | "casual" | "academic" | "conversational" | "instructional",
  "length": "short" | "medium" | "long",
  "format": "markdown" | "html" | "json",
  
  // Standard/Enhanced fields
  "target_audience": "string",
  "focus_keyword": "string",
  "include_introduction": true,
  "include_conclusion": true,
  "include_faq": false,
  "include_toc": true,
  "word_count_target": 1000,
  "custom_instructions": "string",
  
  // Enhanced fields
  "use_google_search": true,
  "use_fact_checking": true,
  "use_citations": true,
  "use_serp_optimization": true,
  "use_consensus_generation": false,
  "use_knowledge_graph": true,
  "use_semantic_keywords": true,
  "use_quality_scoring": true,
  "template_type": "string",
  "async_mode": false,
  
  // Local Business fields (required if blog_type="local_business")
  "location": "string",
  "max_businesses": 10,
  "max_reviews_per_business": 20,
  "include_business_details": true,
  "include_review_sentiment": true,
  "use_google": true,
  
  // Abstraction fields
  "content_strategy": "SEO_OPTIMIZED" | "ENGAGEMENT_FOCUSED" | "CONVERSION_OPTIMIZED",
  "quality_target": "GOOD" | "HIGH_QUALITY" | "PUBLICATION_READY",
  "preferred_provider": "string",
  "additional_context": {},
  "seo_requirements": {}
}
```

**Response:** Varies by `blog_type`:

- **Standard/Abstraction:** `BlogGenerationResult`
- **Enhanced:** `EnhancedBlogGenerationResponse` or `CreateJobResponse` (if async_mode=true)
- **Local Business:** `LocalBusinessBlogResponse`

**Example Request:**

```bash
curl -X POST "https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/generate-unified" \
  -H "Content-Type: application/json" \
  -d '{
    "blog_type": "enhanced",
    "topic": "Complete Guide to React Hooks",
    "keywords": ["react", "hooks", "javascript"],
    "tone": "professional",
    "length": "long",
    "use_google_search": true,
    "use_fact_checking": true,
    "use_citations": true
  }'
```

### Standard Blog Generation

**POST** `/api/v1/blog/generate`  
**POST** `/api/v1/generate`

Generate a standard blog post with SEO optimization.

**Request Body:**

```json
{
  "topic": "string (required)",
  "keywords": ["string"],
  "tone": "professional",
  "length": "medium",
  "format": "markdown",
  "target_audience": "string",
  "focus_keyword": "string",
  "include_introduction": true,
  "include_conclusion": true,
  "include_faq": false,
  "include_toc": true,
  "word_count_target": 1000,
  "custom_instructions": "string"
}
```

**Response:**

```json
{
  "success": true,
  "blog_post": {
    "title": "string",
    "content": "string",
    "meta_description": "string"
  },
  "seo_score": 85.5,
  "word_count": 1200,
  "generation_time_seconds": 15.3,
  "error_message": null
}
```

### Enhanced Blog Generation

**POST** `/api/v1/blog/generate-enhanced`

High-quality multi-stage blog generation with research and citations.

**Request Body:**

```json
{
  "topic": "string (required)",
  "keywords": ["string"],
  "tone": "professional",
  "length": "long",
  "use_google_search": true,
  "use_fact_checking": true,
  "use_citations": true,
  "use_serp_optimization": true,
  "use_consensus_generation": false,
  "use_knowledge_graph": true,
  "use_semantic_keywords": true,
  "use_quality_scoring": true,
  "target_audience": "string",
  "custom_instructions": "string",
  "template_type": "string",
  "async_mode": false
}
```

**Response:**

```json
{
  "title": "string",
  "content": "string",
  "meta_description": "string",
  "seo_score": 92.5,
  "quality_scores": {
    "readability": 88,
    "seo": 95,
    "structure": 90,
    "factual": 92,
    "uniqueness": 85,
    "engagement": 87
  },
  "citations": [
    {
      "text": "string",
      "source": "string",
      "url": "string"
    }
  ],
  "word_count": 2500,
  "generation_time_seconds": 45.2
}
```

**Async Mode Response (if async_mode=true):**

```json
{
  "job_id": "uuid",
  "status": "pending",
  "message": "Blog generation job created",
  "estimated_completion_time": 60
}
```

### Local Business Blog Generation

**POST** `/api/v1/blog/generate-local-business`

Generate comprehensive blogs about local businesses with aggregated reviews.

**Request Body:**

```json
{
  "topic": "string (required)",
  "location": "string (required)",
  "max_businesses": 10,
  "max_reviews_per_business": 20,
  "tone": "professional",
  "length": "long",
  "format": "markdown",
  "include_business_details": true,
  "include_review_sentiment": true,
  "use_google": true,
  "custom_instructions": "string"
}
```

**Response:**

```json
{
  "title": "string",
  "content": "string",
  "businesses": [
    {
      "name": "string",
      "google_place_id": "string",
      "address": "string",
      "phone": "string",
      "website": "string",
      "rating": 4.5,
      "review_count": 150,
      "categories": ["string"]
    }
  ],
  "total_reviews_aggregated": 200,
  "generation_time_seconds": 45.2,
  "metadata": {
    "sources_used": ["serp_google", "google_search"],
    "review_sources": ["google"],
    "seo_score": 88,
    "word_count": 3000
  }
}
```

### Abstraction Blog Generation

**POST** `/api/v1/abstraction/blog/generate`

Strategy-based blog generation with content strategies.

**Request Body:**

```json
{
  "topic": "string (required)",
  "keywords": ["string"],
  "target_audience": "string",
  "content_strategy": "SEO_OPTIMIZED" | "ENGAGEMENT_FOCUSED" | "CONVERSION_OPTIMIZED",
  "tone": "professional",
  "length": "long",
  "format": "markdown",
  "quality_target": "GOOD" | "HIGH_QUALITY" | "PUBLICATION_READY",
  "preferred_provider": "string",
  "additional_context": {},
  "seo_requirements": {}
}
```

**Response:**

```json
{
  "success": true,
  "blog_post": {
    "title": "string",
    "content": "string"
  },
  "strategy_used": "SEO_OPTIMIZED",
  "quality_score": 90,
  "word_count": 2000,
  "generation_time_seconds": 30.5
}
```

### Get Abstraction Strategies

**GET** `/api/v1/abstraction/strategies`

Get available content strategies.

**Response:**

```json
{
  "strategies": [
    {
      "name": "SEO_OPTIMIZED",
      "description": "Optimized for search engine rankings",
      "features": ["keyword optimization", "meta tags", "structured data"]
    }
  ]
}
```

### Get Abstraction Quality Levels

**GET** `/api/v1/abstraction/quality-levels`

Get available quality levels.

**Response:**

```json
{
  "quality_levels": [
    {
      "name": "GOOD",
      "description": "Good quality content",
      "min_score": 70
    }
  ]
}
```

### Get Abstraction Presets

**GET** `/api/v1/abstraction/presets`

Get available presets.

**Response:**

```json
{
  "presets": [
    {
      "name": "SEO_BLOG",
      "strategy": "SEO_OPTIMIZED",
      "quality": "HIGH_QUALITY"
    }
  ]
}
```

### Get Abstraction Status

**GET** `/api/v1/abstraction/status`

Get abstraction service status.

**Response:**

```json
{
  "enabled": true,
  "available_providers": ["openai", "anthropic"],
  "default_provider": "openai"
}
```

### Blog Job Status

**GET** `/api/v1/blog/jobs/{job_id}`

Get status of an async blog generation job.

**Response:**

```json
{
  "job_id": "uuid",
  "status": "pending" | "processing" | "completed" | "failed",
  "progress": 75,
  "result": {},
  "error": "string",
  "created_at": "2025-11-20T10:00:00Z",
  "updated_at": "2025-11-20T10:01:00Z"
}
```

---

## Keyword Research

### Enhanced Keyword Analysis

**POST** `/api/v1/keywords/enhanced`

Comprehensive keyword research with DataForSEO integration.

**Request Body:**

```json
{
  "keywords": ["string"] (required, max 200),
  "location": "United States",
  "language": "en",
  "search_type": "enhanced_keyword_analysis",
  "include_serp": false,
  "max_suggestions_per_keyword": 20
}
```

**Response:**

```json
{
  "enhanced_analysis": {
    "keyword": {
      "search_volume": 110000,
      "global_search_volume": 0,
      "monthly_searches": [
        {
          "year": 2025,
          "month": 10,
          "search_volume": 110000
        }
      ],
      "difficulty": "medium",
      "difficulty_score": 50.0,
      "competition": 0.0,
      "cpc": 16.01,
      "trend_score": 0.0,
      "recommended": true,
      "reason": "Good search volume with manageable competition",
      "related_keywords": ["string"],
      "related_keywords_enhanced": [],
      "long_tail_keywords": ["string"],
      "questions": [],
      "topics": [],
      "keyword_ideas": []
    }
  },
  "cluster_summary": {
    "total_keywords": 3,
    "cluster_count": 3,
    "unclustered_count": 0
  },
  "serp_analysis": {
    "organic_results": [
      {
        "title": "string",
        "url": "string",
        "domain": "string",
        "snippet": "string",
        "position": 1
      }
    ],
    "people_also_ask": [
      {
        "question": "string",
        "snippet": "string"
      }
    ],
    "featured_snippet": {
      "title": "string",
      "snippet": "string",
      "url": "string"
    }
  },
  "discovery": {
    "matching_terms": [],
    "related_terms": []
  },
  "total_keywords": 3
}
```

### Standard Keyword Analysis

**POST** `/api/v1/keywords/analyze`

Basic keyword analysis without DataForSEO.

**Request Body:**

```json
{
  "keywords": ["string"] (required),
  "location": "United States",
  "language": "en"
}
```

**Response:**

```json
{
  "keyword_analysis": {
    "keyword": {
      "search_volume": 10000,
      "cpc": 2.5,
      "competition": 0.6,
      "difficulty_score": 45.0,
      "related_keywords": ["string"],
      "long_tail_keywords": ["string"]
    }
  }
}
```

### Keyword Suggestions

**POST** `/api/v1/keywords/suggest`

Get keyword suggestions based on a seed keyword.

**Request Body:**

```json
{
  "keyword": "string (required)",
  "limit": 20
}
```

**Response:**

```json
{
  "suggestions": [
    {
      "keyword": "string",
      "search_volume": 5000,
      "cpc": 1.5
    }
  ]
}
```

### Keyword Extraction

**POST** `/api/v1/keywords/extract`

Extract keywords from existing content.

**Request Body:**

```json
{
  "content": "string (required, min 100 chars)",
  "max_keywords": 20,
  "max_ngram": 3,
  "dedup_lim": 0.7
}
```

**Response:**

```json
{
  "keywords": [
    {
      "keyword": "string",
      "score": 0.95,
      "frequency": 5
    }
  ]
}
```

### Keyword Difficulty

**POST** `/api/v1/keywords/difficulty`

Analyze keyword difficulty.

**Request Body:**

```json
{
  "keyword": "string (required)",
  "search_volume": 10000,
  "difficulty": 50.0,
  "competition": 0.5,
  "location": "United States",
  "language": "en"
}
```

**Response:**

```json
{
  "keyword": "string",
  "difficulty_score": 50.0,
  "difficulty_level": "medium",
  "recommendation": "Good keyword with moderate competition"
}
```

### AI Keyword Optimization

**POST** `/api/v1/keywords/ai-optimization`

AI-powered keyword optimization suggestions.

**Request Body:**

```json
{
  "keywords": ["string"],
  "content": "string",
  "target_audience": "string"
}
```

**Response:**

```json
{
  "optimized_keywords": ["string"],
  "suggestions": ["string"],
  "improvements": ["string"]
}
```

### Topic Recommendations

**POST** `/api/v1/topics/recommend`

Get topic recommendations based on seed keywords.

**Request Body:**

```json
{
  "seed_keywords": ["string"] (required),
  "location": "United States",
  "language": "en",
  "max_topics": 20,
  "min_search_volume": 100,
  "max_difficulty": 70.0,
  "include_ai_suggestions": true
}
```

**Response:**

```json
{
  "topics": [
    {
      "topic": "string",
      "search_volume": 5000,
      "difficulty": 45.0,
      "cpc": 2.5,
      "recommended": true
    }
  ]
}
```

---

## AI Provider Management

### List Providers

**GET** `/api/v1/ai/providers/list`

Get list of configured AI providers.

**Response:**

```json
{
  "providers": [
    {
      "provider_type": "openai",
      "enabled": true,
      "model": "gpt-4",
      "status": "available"
    }
  ],
  "default_provider": "openai"
}
```

### Configure Provider

**POST** `/api/v1/ai/providers/configure`

Configure an AI provider.

**Request Body:**

```json
{
  "provider_type": "openai" | "anthropic",
  "api_key": "string (required)",
  "model": "string",
  "enabled": true
}
```

**Response:**

```json
{
  "provider_type": "openai",
  "status": "configured",
  "model": "gpt-4",
  "enabled": true
}
```

### Test Provider

**POST** `/api/v1/ai/providers/test`

Test an AI provider configuration.

**Request Body:**

```json
{
  "provider_type": "openai" | "anthropic",
  "api_key": "string",
  "test_prompt": "string"
}
```

**Response:**

```json
{
  "success": true,
  "response_time_ms": 1500,
  "test_response": "string"
}
```

### Switch Provider

**POST** `/api/v1/ai/providers/switch`

Switch default AI provider.

**Request Body:**

```json
{
  "provider_type": "openai" | "anthropic"
}
```

**Response:**

```json
{
  "previous_provider": "anthropic",
  "current_provider": "openai",
  "status": "switched"
}
```

### Bulk Configure Providers

**POST** `/api/v1/ai/providers/bulk-configure`

Configure multiple providers at once.

**Request Body:**

```json
{
  "providers": [
    {
      "provider_type": "openai",
      "api_key": "string",
      "enabled": true
    }
  ]
}
```

**Response:**

```json
{
  "configured": 2,
  "failed": 0,
  "results": [
    {
      "provider_type": "openai",
      "status": "configured"
    }
  ]
}
```

### AI Health Check

**GET** `/api/v1/ai/health`

Get AI provider health status.

**Response:**

```json
{
  "status": "healthy",
  "providers": {
    "openai": {
      "status": "available",
      "response_time_ms": 1200,
      "usage_today": 150
    },
    "anthropic": {
      "status": "available",
      "response_time_ms": 1800,
      "usage_today": 75
    }
  },
  "default_provider": "openai"
}
```

---

## Image Generation

### Generate Image

**POST** `/api/v1/images/generate`

Generate an image from a text prompt.

**Request Body:**

```json
{
  "prompt": "string (required)",
  "provider": "stability_ai",
  "style": "photographic" | "digital-art" | "anime" | "3d-model",
  "aspect_ratio": "16:9" | "1:1" | "9:16",
  "quality": "standard" | "hd",
  "num_images": 1
}
```

**Response:**

```json
{
  "images": [
    {
      "url": "string",
      "width": 1024,
      "height": 1024,
      "format": "png"
    }
  ],
  "provider": "stability_ai",
  "generation_time_seconds": 5.2
}
```

### Image Variations

**POST** `/api/v1/images/variations`

Generate variations of an existing image.

**Request Body:**

```json
{
  "image_url": "string (required)",
  "provider": "stability_ai",
  "strength": 0.7,
  "num_variations": 1
}
```

**Response:**

```json
{
  "images": [
    {
      "url": "string",
      "width": 1024,
      "height": 1024
    }
  ],
  "provider": "stability_ai"
}
```

### Upscale Image

**POST** `/api/v1/images/upscale`

Upscale an image to higher resolution.

**Request Body:**

```json
{
  "image_url": "string (required)",
  "provider": "stability_ai",
  "scale": 2
}
```

**Response:**

```json
{
  "image": {
    "url": "string",
    "width": 2048,
    "height": 2048,
    "original_width": 1024,
    "original_height": 1024
  },
  "provider": "stability_ai"
}
```

### Image Providers Status

**GET** `/api/v1/images/providers`

Get status of image generation providers.

**Response:**

```json
{
  "providers": [
    {
      "provider_type": "stability_ai",
      "status": "available",
      "enabled": true
    }
  ]
}
```

---

## Platform Publishing

### Publish to Webflow

**POST** `/api/v1/publish/webflow`

Publish blog content to Webflow.

**Request Body:**

```json
{
  "blog_result": {
    "title": "string",
    "content": "string"
  },
  "platform": "webflow",
  "publish": true,
  "categories": ["string"],
  "tags": ["string"],
  "media_files": []
}
```

**Response:**

```json
{
  "success": true,
  "platform": "webflow",
  "published_url": "string",
  "item_id": "string"
}
```

### Publish to Shopify

**POST** `/api/v1/publish/shopify`

Publish blog content to Shopify.

**Request Body:**

```json
{
  "blog_result": {
    "title": "string",
    "content": "string"
  },
  "platform": "shopify",
  "publish": true
}
```

**Response:**

```json
{
  "success": true,
  "platform": "shopify",
  "published_url": "string",
  "article_id": "string"
}
```

### Publish to WordPress

**POST** `/api/v1/publish/wordpress`

Publish blog content to WordPress.

**Request Body:**

```json
{
  "blog_result": {
    "title": "string",
    "content": "string"
  },
  "platform": "wordpress",
  "publish": true,
  "categories": ["string"]
}
```

**Response:**

```json
{
  "success": true,
  "platform": "wordpress",
  "published_url": "string",
  "post_id": 123
}
```

### Get Webflow Collections

**GET** `/api/v1/platforms/webflow/collections`

Get available Webflow collections.

**Response:**

```json
{
  "collections": [
    {
      "id": "string",
      "name": "Blog Posts",
      "slug": "blog-posts"
    }
  ]
}
```

### Get Shopify Blogs

**GET** `/api/v1/platforms/shopify/blogs`

Get available Shopify blogs.

**Response:**

```json
{
  "blogs": [
    {
      "id": "string",
      "title": "News",
      "handle": "news"
    }
  ]
}
```

### Get WordPress Categories

**GET** `/api/v1/platforms/wordpress/categories`

Get available WordPress categories.

**Response:**

```json
{
  "categories": [
    {
      "id": 1,
      "name": "Technology",
      "slug": "technology"
    }
  ]
}
```

---

## Content Analysis

### Analyze Content

**POST** `/api/v1/analyze`

Analyze existing content for SEO and quality.

**Request Body:**

```json
{
  "content": "string (required)",
  "keywords": ["string"],
  "focus_keyword": "string"
}
```

**Response:**

```json
{
  "seo_score": 85.5,
  "readability_score": 78,
  "keyword_density": {
    "keyword": 2.5
  },
  "suggestions": ["string"]
}
```

### Optimize Content

**POST** `/api/v1/optimize`

Optimize content for SEO.

**Request Body:**

```json
{
  "content": "string (required)",
  "keywords": ["string"],
  "focus_keyword": "string"
}
```

**Response:**

```json
{
  "optimized_content": "string",
  "improvements": ["string"],
  "seo_score_before": 70,
  "seo_score_after": 88
}
```

---

## Batch Processing

### Create Batch Job

**POST** `/api/v1/batch/generate`

Create a batch blog generation job.

**Request Body:**

```json
{
  "requests": [
    {
      "topic": "string",
      "keywords": ["string"]
    }
  ],
  "options": {
    "tone": "professional",
    "length": "medium"
  }
}
```

**Response:**

```json
{
  "job_id": "uuid",
  "status": "pending",
  "total_items": 10,
  "message": "Batch job created"
}
```

### Get Batch Job Status

**GET** `/api/v1/batch/{job_id}/status`

Get status of a batch job.

**Response:**

```json
{
  "job_id": "uuid",
  "status": "processing",
  "progress": 60,
  "completed": 6,
  "total": 10,
  "results": []
}
```

### Stream Batch Results

**GET** `/api/v1/batch/{job_id}/stream`

Stream batch job results as they complete.

**Response:** Server-Sent Events stream

### List Batch Jobs

**GET** `/api/v1/batch`

List all batch jobs.

**Query Parameters:**
- `status` - Filter by status
- `limit` - Limit results
- `offset` - Offset for pagination

**Response:**

```json
{
  "jobs": [
    {
      "job_id": "uuid",
      "status": "completed",
      "created_at": "2025-11-20T10:00:00Z"
    }
  ],
  "total": 10
}
```

### Delete Batch Job

**DELETE** `/api/v1/batch/{job_id}`

Delete a batch job.

**Response:**

```json
{
  "job_id": "uuid",
  "status": "deleted"
}
```

---

## User Management

### Get User Statistics

**GET** `/api/v1/users/stats`

Get user statistics summary.

**Response:**

```json
{
  "total_users": 24,
  "active_users": 18,
  "pending_invites": 3,
  "roles": 5
}
```

### List Users

**GET** `/api/v1/users`

List all users with pagination.

**Query Parameters:**
- `page` - Page number (default: 1)
- `limit` - Items per page (default: 10, max: 100)
- `status` - Filter by status
- `role` - Filter by role

**Response:**

```json
{
  "users": [
    {
      "id": "uuid",
      "email": "user@example.com",
      "name": "John Doe",
      "role": "admin",
      "status": "active",
      "created_at": "2025-01-15T00:00:00Z"
    }
  ],
  "total": 24,
  "page": 1,
  "limit": 10
}
```

### Create User

**POST** `/api/v1/users`

Create a new user (System admin only).

**Request Body:**

```json
{
  "email": "string (required)",
  "password": "string (required)",
  "name": "string",
  "role": "admin" | "manager" | "user" | "viewer",
  "department": "string",
  "status": "active"
}
```

**Response:**

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "role": "admin",
  "status": "active"
}
```

---

## Integrations

### Connect and Recommend

**POST** `/api/v1/integrations/connect-and-recommend`

Connect to a platform and get interlink/backlink recommendations.

**Request Body:**

```json
{
  "provider": "webflow" | "shopify" | "wordpress",
  "tenant_id": "string",
  "connection": {
    "api_token": "string",
    "site_id": "string",
    "structure": {
      "existing_content": [
        {
          "id": "string",
          "title": "string",
          "url": "string",
          "slug": "string",
          "keywords": ["string"],
          "published_at": "2025-01-15T10:00:00Z"
        }
      ]
    }
  },
  "keywords": ["string"]
}
```

**Response:**

```json
{
  "provider": "webflow",
  "tenant_id": "string",
  "saved_integration": true,
  "recommended_interlinks": 15,
  "recommended_backlinks": 0,
  "per_keyword": [
    {
      "keyword": "string",
      "difficulty": 0.5,
      "suggested_interlinks": 5,
      "suggested_backlinks": 0
    }
  ],
  "notes": "string"
}
```

---

## Media Management

### Upload to Cloudinary

**POST** `/api/v1/media/upload/cloudinary`

Upload media to Cloudinary.

**Request Body:**

```json
{
  "media_data": "base64_string (required)",
  "filename": "string (required)",
  "folder": "string",
  "alt_text": "string",
  "caption": "string",
  "metadata": {}
}
```

**Response:**

```json
{
  "url": "string",
  "public_id": "string",
  "format": "png",
  "width": 1024,
  "height": 1024
}
```

### Upload to Cloudflare R2

**POST** `/api/v1/media/upload/cloudflare`

Upload media to Cloudflare R2.

**Request Body:**

```json
{
  "media_data": "base64_string (required)",
  "filename": "string (required)",
  "folder": "string",
  "alt_text": "string",
  "caption": "string",
  "metadata": {}
}
```

**Response:**

```json
{
  "url": "string",
  "key": "string",
  "size": 1024000,
  "content_type": "image/png"
}
```

---

## Monitoring & Metrics

### Get Metrics

**GET** `/api/v1/metrics`

Get system metrics and statistics.

**Response:**

```json
{
  "requests_today": 150,
  "average_response_time": 2.5,
  "success_rate": 0.98,
  "error_rate": 0.02
}
```

### Cache Statistics

**GET** `/api/v1/cache/stats`

Get cache statistics.

**Response:**

```json
{
  "hits": 1000,
  "misses": 200,
  "hit_rate": 0.83,
  "size": 50000
}
```

### Clear Cache

**DELETE** `/api/v1/cache/clear`

Clear all caches.

**Response:**

```json
{
  "status": "cleared",
  "items_cleared": 1000
}
```

### Cloud Run Status

**GET** `/api/v1/cloudrun/status`

Get Cloud Run service status.

**Response:**

```json
{
  "service_name": "blog-writer-api-dev",
  "region": "europe-west9",
  "revision": "string",
  "traffic_percent": 100
}
```

---

## Error Reference

### Error Response Format

```json
{
  "detail": "Error message description",
  "error": "ERROR_CODE",
  "status_code": 400
}
```

### Common Error Codes

| Status Code | Error | Description |
|------------|-------|-------------|
| 400 | `BAD_REQUEST` | Invalid request parameters |
| 401 | `UNAUTHORIZED` | Authentication required |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 404 | `NOT_FOUND` | Resource not found |
| 422 | `VALIDATION_ERROR` | Request validation failed |
| 429 | `RATE_LIMIT_EXCEEDED` | Rate limit exceeded |
| 500 | `INTERNAL_SERVER_ERROR` | Server error |
| 503 | `SERVICE_UNAVAILABLE` | Service unavailable |

### Example Error Responses

**400 Bad Request:**

```json
{
  "detail": "'location' is required for local_business blog type",
  "status_code": 400
}
```

**404 Not Found:**

```json
{
  "detail": "No businesses found for 'plumbers' in Miami, FL",
  "status_code": 404
}
```

**500 Internal Server Error:**

```json
{
  "detail": "Blog generation failed: AI provider unavailable",
  "status_code": 500
}
```

---

## Rate Limits

### Current Limits (Development)

- **No rate limits** - Development environment
- **Production limits** - Configurable per organization

### Recommended Practices

- Use async mode for long-running operations
- Implement client-side retry logic
- Cache responses when appropriate
- Batch multiple requests when possible

---

## Support

- **Interactive API Docs:** `/docs` (Swagger UI)
- **ReDoc:** `/redoc`
- **Health Check:** `/health`
- **Status:** `/api/v1/config`

---

**Version:** 1.3.4  
**Last Updated:** 2025-11-20  
**Maintained by:** Blog Writer SDK Team

