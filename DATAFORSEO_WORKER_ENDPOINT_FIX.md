# DataForSEO Worker Endpoint Fix

**Date:** 2025-01-15  
**Issue:** Worker endpoint doesn't use DataForSEO Content Generation API  
**Status:** 🔴 **BUG IDENTIFIED**

---

## 🔍 Root Cause

The `/api/v1/blog/worker` endpoint (which processes async jobs) **does NOT check or use** the `use_dataforseo_content_generation` flag. It always uses the old `MultiStageGenerationPipeline` instead of DataForSEO Content Generation Service.

### Current Flow (BROKEN)

```
Request with async_mode=true (default)
  ↓
Create Cloud Task → Returns job_id immediately ✅
  ↓
Worker endpoint (/api/v1/blog/worker) receives job
  ↓
Uses MultiStageGenerationPipeline ❌ (ignores use_dataforseo_content_generation flag)
  ↓
Uses Anthropic/OpenAI for content generation ❌
```

### Expected Flow (SHOULD BE)

```
Request with async_mode=true (default)
  ↓
Create Cloud Task → Returns job_id immediately ✅
  ↓
Worker endpoint (/api/v1/blog/worker) receives job
  ↓
Check use_dataforseo_content_generation flag ✅
  ↓
If true: Use DataForSEO Content Generation Service ✅
If false: Use MultiStageGenerationPipeline ✅
```

---

## 📋 Code Analysis

### Main Endpoint (`/api/v1/blog/generate-enhanced`)

**Lines 1180-1359:** ✅ **CORRECTLY IMPLEMENTS** DataForSEO check
```python
# Check if DataForSEO Content Generation should be used (default: True)
if hasattr(request, 'use_dataforseo_content_generation'):
    USE_DATAFORSEO = request.use_dataforseo_content_generation
else:
    USE_DATAFORSEO = os.getenv("USE_DATAFORSEO_CONTENT_GENERATION", "true").lower() == "true"

# Use DataForSEO Content Generation Service (only in sync mode now)
if USE_DATAFORSEO:
    logger.info("🔷 Using DataForSEO Content Generation API for blog generation")
    # ... uses DataForSEOContentGenerationService
```

**Problem:** This code only runs when `async_mode=False` (synchronous mode)

### Worker Endpoint (`/api/v1/blog/worker`)

**Lines 1706-1720:** ❌ **DOES NOT CHECK** DataForSEO flag
```python
# Initialize pipeline (same as synchronous endpoint)
pipeline = MultiStageGenerationPipeline(
    ai_generator=ai_generator,
    google_search=google_custom_search_client if blog_request.use_google_search else None,
    # ... other parameters
    dataforseo_client=dataforseo_client_global,  # ← Only used for SEO research, NOT content generation
    progress_callback=progress_callback
)
```

**Problem:** 
- ❌ No check for `use_dataforseo_content_generation` flag
- ❌ Always uses `MultiStageGenerationPipeline` (Anthropic/OpenAI)
- ❌ `dataforseo_client` is only passed for SEO research, not content generation

---

## ✅ Solution

Add DataForSEO Content Generation logic to the worker endpoint, mirroring the synchronous endpoint.

### Required Changes

**File:** `main.py`  
**Location:** `blog_generation_worker` function (around line 1690)

**Add after line 1690** (after parsing `blog_request`):

```python
# Parse request
request_data = request.get("request", {})
blog_request = EnhancedBlogGenerationRequest(**request_data)

# ✅ ADD THIS: Check if DataForSEO Content Generation should be used
USE_DATAFORSEO = getattr(blog_request, 'use_dataforseo_content_generation', True)
if not USE_DATAFORSEO:
    USE_DATAFORSEO = os.getenv("USE_DATAFORSEO_CONTENT_GENERATION", "true").lower() == "true"

# ✅ ADD THIS: Use DataForSEO Content Generation Service if enabled
if USE_DATAFORSEO:
    logger.info("🔷 Worker: Using DataForSEO Content Generation API for blog generation")
    
    # Initialize DataForSEO Content Generation Service
    content_service = DataForSEOContentGenerationService(dataforseo_client=dataforseo_client_global)
    await content_service.initialize(tenant_id="default")
    
    if not content_service.is_configured:
        logger.warning("Worker: DataForSEO Content Generation not configured, falling back to pipeline")
        USE_DATAFORSEO = False
    else:
        # Map blog type (same mapping as synchronous endpoint)
        blog_type_map = {
            BlogContentType.BRAND: DataForSEOBlogType.BRAND,
            BlogContentType.TOP_10: DataForSEOBlogType.TOP_10,
            # ... (all 28 blog types)
        }
        df_blog_type = blog_type_map.get(blog_request.blog_type or BlogContentType.CUSTOM, DataForSEOBlogType.CUSTOM)
        
        # Calculate word count
        word_count_map = {
            ContentLength.SHORT: 500,
            ContentLength.MEDIUM: 1500,
            ContentLength.LONG: 2500,
            ContentLength.EXTENDED: 4000,
        }
        word_count = blog_request.word_count_target or word_count_map.get(blog_request.length, 1500)
        
        # Map tone
        tone_map = {
            ContentTone.PROFESSIONAL: "professional",
            ContentTone.CASUAL: "casual",
            # ... (all tones)
        }
        tone_str = tone_map.get(blog_request.tone, "professional")
        
        try:
            # Generate blog content using DataForSEO
            logger.info(f"Worker: Calling DataForSEO generate_blog_content: topic={blog_request.topic}, blog_type={df_blog_type.value}")
            
            result = await content_service.generate_blog_content(
                topic=blog_request.topic,
                keywords=blog_request.keywords,
                blog_type=df_blog_type,
                tone=tone_str,
                word_count=word_count,
                target_audience=blog_request.target_audience,
                language="en",
                tenant_id="default",
                optimize_for_traffic=getattr(blog_request, 'optimize_for_traffic', True),
                analyze_backlinks=getattr(blog_request, 'analyze_backlinks', False),
                backlink_url=getattr(blog_request, 'backlink_url', None),
                brand_name=getattr(blog_request, 'brand_name', None),
                category=getattr(blog_request, 'category', None),
                product_name=getattr(blog_request, 'product_name', None),
                items=getattr(blog_request, 'comparison_items', None),
                custom_instructions=blog_request.custom_instructions
            )
            
            # Validate content
            generated_content = result.get("content", "")
            if not generated_content or len(generated_content.strip()) < 50:
                raise Exception(f"DataForSEO returned empty content: length={len(generated_content)}")
            
            # Build response (same as synchronous endpoint)
            seo_metrics = result.get("seo_metrics", {})
            readability_score = seo_metrics.get("readability_score", 75.0)
            seo_score = seo_metrics.get("seo_score", 85.0)
            
            seo_metadata = {
                "semantic_keywords": result.get("keywords", blog_request.keywords),
                "subtopics": result.get("subtopics", []),
                "blog_type": result.get("blog_type", "custom"),
                "keyword_density": seo_metrics.get("keyword_density", {}),
                "headings_count": seo_metrics.get("headings_count", 0),
                "avg_sentence_length": seo_metrics.get("avg_sentence_length", 0),
                "seo_factors": seo_metrics.get("seo_factors", []),
                "word_count_range": seo_metrics.get("word_count_range", {}),
                "backlink_keywords": result.get("backlink_keywords", [])
            }
            
            quality_dimensions = {
                "readability": readability_score,
                "seo": seo_score,
                "structure": min(100, seo_metrics.get("headings_count", 0) * 20),
                "keyword_optimization": min(100, seo_score * 0.8)
            }
            
            excerpt = extract_excerpt(generated_content, max_length=250)
            
            # Update job with result
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.result = EnhancedBlogGenerationResponse(
                title=result.get("title", blog_request.topic),
                content=generated_content,
                excerpt=excerpt,
                meta_title=result.get("meta_title", result.get("title", blog_request.topic)),
                meta_description=result.get("meta_description", ""),
                readability_score=readability_score,
                seo_score=seo_score,
                stage_results=[],
                citations=[],
                total_tokens=result.get("tokens_used", 0),
                total_cost=result.get("cost", 0.0),
                generation_time=time.time() - start_time,
                seo_metadata=seo_metadata,
                internal_links=[],
                quality_score=seo_score,
                quality_dimensions=quality_dimensions,
                structured_data=None,
                semantic_keywords=result.get("keywords", blog_request.keywords),
                content_metadata={},
                success=True,
                warnings=[] if seo_metrics.get("within_tolerance", True) else ["Content length outside ±25% tolerance"],
                progress_updates=progress_updates
            )
            
            logger.info(f"Worker: DataForSEO generation completed successfully for job {job_id}")
            return JSONResponse(
                status_code=200,
                content={"status": "completed", "job_id": job_id}
            )
            
        except Exception as e:
            logger.error(f"Worker: DataForSEO content generation failed: {e}", exc_info=True)
            USE_DATAFORSEO = False
            logger.warning(f"Worker: Falling back to pipeline due to DataForSEO error: {str(e)}")
            # Fall through to pipeline fallback below

# Fallback to pipeline if DataForSEO is disabled or failed
if not USE_DATAFORSEO:
    logger.info("Worker: Using multi-stage pipeline for blog generation")
    # ... existing pipeline code ...
```

---

## 🧪 Testing

### Test Case 1: Async Mode with DataForSEO Enabled

```bash
curl -X POST "https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/generate-enhanced?async_mode=true" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Python programming benefits",
    "keywords": ["python", "programming"],
    "use_dataforseo_content_generation": true,
    "tone": "professional",
    "length": "medium"
  }'
```

**Expected:**
1. Returns `job_id` immediately ✅
2. Worker processes using DataForSEO ✅
3. Job result contains DataForSEO-generated content ✅

### Test Case 2: Async Mode with DataForSEO Disabled

```bash
curl -X POST "...?async_mode=true" \
  -d '{
    "topic": "...",
    "use_dataforseo_content_generation": false,
    ...
  }'
```

**Expected:**
1. Returns `job_id` immediately ✅
2. Worker processes using MultiStageGenerationPipeline ✅
3. Job result contains pipeline-generated content ✅

---

## 📊 Impact

### Before Fix
- ❌ Async requests (`async_mode=true`) always use Anthropic/OpenAI
- ❌ `use_dataforseo_content_generation` flag ignored in async mode
- ❌ DataForSEO only works in synchronous mode (`async_mode=false`)

### After Fix
- ✅ Async requests respect `use_dataforseo_content_generation` flag
- ✅ DataForSEO works in both sync and async modes
- ✅ Consistent behavior across all request types

---

## 🚀 Implementation Steps

1. **Add DataForSEO check** to worker endpoint (around line 1690)
2. **Copy DataForSEO generation logic** from synchronous endpoint (lines 1189-1352)
3. **Update job result** with DataForSEO response
4. **Test async mode** with DataForSEO enabled
5. **Test async mode** with DataForSEO disabled (fallback)
6. **Deploy** to Cloud Run

---

## 📝 Notes

- The synchronous endpoint (`async_mode=false`) already works correctly ✅
- The issue only affects async mode (`async_mode=true`, which is the default)
- This explains why the frontend sees DataForSEO only used for SEO research, not content generation

