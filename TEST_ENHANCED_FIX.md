# Enhanced Endpoint Fix - Testing Guide

## Issue Fixed
The enhanced blog generation endpoint (`/api/v1/blog/generate-enhanced`) was failing with:
```
'str' object has no attribute 'value'
```

## Root Cause
The code was trying to access `.value` on `tone` and `length` parameters without properly handling cases where they might be strings instead of enum instances.

## Fixes Applied

### 1. `src/blog_writer_sdk/ai/multi_stage_pipeline.py`
- Added `_safe_enum_to_str()` helper function
- Fixed enum conversion in consensus generation (lines 230-231)
- Fixed enum conversion in intent analysis (line 165)
- Fixed enum conversion in SEO metadata (line 299)

### 2. `src/blog_writer_sdk/ai/enhanced_prompts.py`
- Added `_safe_enum_to_str()` helper function
- Updated `build_draft_prompt()` to accept `Union[ContentTone, str]` and `Union[ContentLength, str]`
- Fixed `tone.value` access in prompt building (lines 141, 155)
- Updated `_get_word_count()` to handle both enum and string inputs

## Testing

### Test File
The test file `test_notary_california.json` contains:
```json
{
  "topic": "Best Notary Services in California: Complete Guide 2025",
  "keywords": [...],
  "tone": "professional",
  "length": "medium",
  ...
}
```

### Expected Behavior
- The endpoint should accept both enum instances and string values for `tone` and `length`
- The `_safe_enum_to_str()` function should handle:
  - Enum instances → returns `.value`
  - Strings → returns as-is
  - Other types → tries `.value`, falls back to `str()`

### Testing Commands

#### Test against deployed service (after deployment):
```bash
curl -X POST https://blog-writer-api-dev-613248238610.europe-west1.run.app/api/v1/blog/generate-enhanced \
  -H 'Content-Type: application/json' \
  -d @test_notary_california.json
```

#### Test locally (if service is running):
```bash
curl -X POST http://localhost:8000/api/v1/blog/generate-enhanced \
  -H 'Content-Type: application/json' \
  -d @test_notary_california.json
```

### Expected Response
- **Status**: 200 OK
- **Response**: Full blog generation result with:
  - `title`: Generated blog title
  - `content`: Full blog content
  - `seo_score`: SEO optimization score
  - `readability_score`: Readability score
  - `quality_score`: Overall quality score (if enabled)
  - `stage_results`: Results from each pipeline stage
  - `total_tokens`: Total tokens used
  - `total_cost`: Total cost in USD
  - `generation_time`: Time taken in seconds

### Before Fix
- Error: `{"error":"HTTP 500","message":"Enhanced blog generation failed: 'str' object has no attribute 'value'",...}`

### After Fix
- Success: Full blog generation response with all metadata

## Deployment
The fix needs to be deployed to the Cloud Run service for it to take effect. The changes are backward compatible and should not affect existing functionality.

## Verification
After deployment, verify the fix by:
1. Testing with the provided JSON file
2. Checking that the response includes all expected fields
3. Verifying that no enum conversion errors occur in logs

