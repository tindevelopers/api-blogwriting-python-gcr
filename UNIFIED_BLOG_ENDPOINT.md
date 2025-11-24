# Unified Blog Generation Endpoint

**Date**: 2025-11-16  
**Status**: ✅ Implemented

---

## Overview

The unified blog generation endpoint (`POST /api/v1/blog/generate-unified`) provides a single interface for all blog generation types, routing internally to the appropriate handler based on the `blog_type` parameter.

---

## Endpoint

```
POST /api/v1/blog/generate-unified
```

---

## Request Model

```typescript
{
  // Required
  blog_type: "standard" | "enhanced" | "local_business" | "abstraction";
  topic: string;  // Main topic (3-200 characters)
  
  // Common fields (all blog types)
  keywords?: string[];
  tone?: "professional" | "casual" | "academic" | "conversational" | "instructional";
  length?: "short" | "medium" | "long";
  format?: "markdown" | "html" | "json";
  target_audience?: string;
  custom_instructions?: string;
  
  // Standard & Enhanced fields
  include_introduction?: boolean;
  include_conclusion?: boolean;
  include_faq?: boolean;
  include_toc?: boolean;
  focus_keyword?: string;
  word_count_target?: number;
  
  // Enhanced-specific fields
  use_google_search?: boolean;
  use_fact_checking?: boolean;
  use_citations?: boolean;
  use_serp_optimization?: boolean;
  use_consensus_generation?: boolean;
  use_knowledge_graph?: boolean;
  use_semantic_keywords?: boolean;
  use_quality_scoring?: boolean;
  template_type?: string;
  async_mode?: boolean;
  
  // Local Business-specific fields
  location?: string;  // Required for local_business
  max_businesses?: number;
  max_reviews_per_business?: number;
  include_business_details?: boolean;
  include_review_sentiment?: boolean;
  use_google?: boolean;
  
  // Abstraction-specific fields
  content_strategy?: string;
  quality_target?: string;
  preferred_provider?: string;
  seo_requirements?: object;
}
```

---

## Blog Types

### 1. Standard (`blog_type: "standard"`)

Basic blog generation with SEO optimization.

**Example:**
```json
{
  "blog_type": "standard",
  "topic": "Introduction to Python Programming",
  "keywords": ["python", "programming", "tutorial"],
  "tone": "professional",
  "length": "medium"
}
```

**Routes to:** `/api/v1/blog/generate`

---

### 2. Enhanced (`blog_type: "enhanced"`)

High-quality multi-stage blog generation with research, fact-checking, and citations.

**Example:**
```json
{
  "blog_type": "enhanced",
  "topic": "Best Practices for SEO in 2025",
  "keywords": ["SEO", "search engine optimization"],
  "use_google_search": true,
  "use_fact_checking": true,
  "use_citations": true,
  "use_serp_optimization": true,
  "async_mode": false
}
```

**Routes to:** `/api/v1/blog/generate-enhanced`

---

### 3. Local Business (`blog_type: "local_business"`)

Comprehensive blogs about local businesses with aggregated reviews.

**Example:**
```json
{
  "blog_type": "local_business",
  "topic": "best plumbers in Miami",
  "location": "Miami, FL",
  "max_businesses": 10,
  "max_reviews_per_business": 20,
  "use_google": true,
  "include_business_details": true,
  "include_review_sentiment": true
}
```

**Routes to:** `/api/v1/blog/generate-local-business`

**Required Fields:**
- `location` - Must be provided for local_business type

---

### 4. Abstraction (`blog_type: "abstraction"`)

Strategy-based blog generation with content strategies (SEO, Engagement, Conversion).

**Example:**
```json
{
  "blog_type": "abstraction",
  "topic": "Complete Guide to Content Marketing",
  "keywords": ["content marketing", "SEO"],
  "content_strategy": "SEO_OPTIMIZED",
  "quality_target": "PUBLICATION_READY",
  "preferred_provider": "openai"
}
```

**Routes to:** `/api/v1/abstraction/blog/generate`

**Available Strategies:**
- `SEO_OPTIMIZED`
- `ENGAGEMENT_FOCUSED`
- `CONVERSION_OPTIMIZED`

**Available Quality Targets:**
- `GOOD`
- `HIGH_QUALITY`
- `PUBLICATION_READY`

---

## Response Models

The response type depends on the `blog_type`:

- **Standard**: `BlogGenerationResult`
- **Enhanced**: `EnhancedBlogGenerationResponse` or `CreateJobResponse` (if async_mode=true)
- **Local Business**: `LocalBusinessBlogResponse`
- **Abstraction**: `AbstractionBlogGenerationResult`

---

## Benefits

✅ **Single Endpoint**: One endpoint for all blog types  
✅ **Consistent API**: Unified request/response structure  
✅ **Type-Safe**: Conditional fields based on blog_type  
✅ **Backward Compatible**: Existing endpoints still work  
✅ **Easier Frontend**: Simpler integration with single method  

---

## Error Handling

- **400 Bad Request**: Invalid `blog_type` or missing required fields (e.g., `location` for local_business)
- **500 Internal Server Error**: Generation failed

**Example Error Response:**
```json
{
  "detail": "'location' is required for local_business blog type"
}
```

---

## Migration Guide

### Current Approach (Multiple Endpoints)
```typescript
// Need different methods for each type
await generateStandard({ topic: "..." });
await generateEnhanced({ topic: "...", use_google_search: true });
await generateLocalBusiness({ topic: "...", location: "Miami, FL" });
```

### Unified Approach (Single Endpoint)
```typescript
// Single method with blog_type parameter
await generateBlog({
  blog_type: "local_business",
  topic: "best plumbers in Miami",
  location: "Miami, FL"
});
```

---

## Backward Compatibility

All existing endpoints remain available:
- ✅ `/api/v1/blog/generate` - Still works
- ✅ `/api/v1/blog/generate-enhanced` - Still works
- ✅ `/api/v1/blog/generate-local-business` - Still works
- ✅ `/api/v1/abstraction/blog/generate` - Still works

The unified endpoint routes internally to these handlers, so you can migrate gradually.

---

## Frontend Integration

See `FRONTEND_BLOG_GENERATION_GUIDE.md` for complete frontend integration examples and TypeScript types.

---

## Testing

```bash
# Standard blog
curl -X POST "https://your-api.com/api/v1/blog/generate-unified" \
  -H "Content-Type: application/json" \
  -d '{
    "blog_type": "standard",
    "topic": "Introduction to Python"
  }'

# Local business blog
curl -X POST "https://your-api.com/api/v1/blog/generate-unified" \
  -H "Content-Type: application/json" \
  -d '{
    "blog_type": "local_business",
    "topic": "best plumbers in Miami",
    "location": "Miami, FL",
    "max_businesses": 10
  }'
```

---

**Implementation Complete** ✅  
**Ready for Production** ✅  
**Backward Compatible** ✅

