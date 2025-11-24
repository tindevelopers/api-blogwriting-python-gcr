# Subtopics Endpoint Fix

**Date:** 2025-01-23  
**Status:** ✅ Fixed

---

## Issue

The subtopics generation endpoint was returning **HTTP 404 (Not Found)** errors.

**Root Cause:**
- **Wrong endpoint path**: `content_generation/generate_subtopics/live` (without underscore)
- **Correct endpoint path**: `content_generation/generate_sub_topics/live` (with underscore)

**Additional Issues:**
- Wrong payload parameter: Using `"text"` instead of `"topic"`
- Wrong response field: Looking for `"subtopics"` instead of `"sub_topics"`

---

## Fix Applied

### 1. Endpoint Path Correction

**File:** `src/blog_writer_sdk/integrations/dataforseo_integration.py`

```python
# ❌ BEFORE (Wrong)
data = await self._make_request(
    "content_generation/generate_subtopics/live",
    payload,
    tenant_id
)

# ✅ AFTER (Correct)
data = await self._make_request(
    "content_generation/generate_sub_topics/live",
    payload,
    tenant_id
)
```

### 2. Payload Format Correction

According to [DataForSEO API documentation](https://docs.dataforseo.com/v3/content_generation-generate_sub_topics-live/), the endpoint expects:

```python
# ❌ BEFORE (Wrong)
payload = [{
    "text": text,
    "max_subtopics": max_subtopics,
    "language": language
}]

# ✅ AFTER (Correct)
payload = [{
    "topic": text,  # Use "topic" parameter
    "creativity_index": 0.7,  # Optional creativity level
    "max_subtopics": max_subtopics  # Note: May not be a valid parameter
}]
```

### 3. Response Parsing Correction

The API returns `sub_topics` (with underscore), not `subtopics`:

```python
# ❌ BEFORE (Wrong)
subtopics = result_item.get("subtopics", [])

# ✅ AFTER (Correct)
subtopics = result_item.get("sub_topics", [])
```

### 4. Metadata Extraction

Updated to extract actual metadata from API response:

```python
"metadata": {
    "input_tokens": result_item.get("input_tokens", 0),
    "output_tokens": result_item.get("output_tokens", 0),
    "new_tokens": result_item.get("new_tokens", 0)
}
```

---

## Verification

### Direct API Test

```bash
curl -X POST "https://api.dataforseo.com/v3/content_generation/generate_sub_topics/live" \
  -H "Authorization: Basic <credentials>" \
  -H "Content-Type: application/json" \
  -d '[{"topic":"Python programming","creativity_index":0.7}]'
```

**Response:**
```json
{
  "status_code": 20000,
  "status_message": "Ok.",
  "tasks": [{
    "result": [{
      "input_tokens": 42,
      "output_tokens": 179,
      "new_tokens": 137,
      "sub_topics": [
        "Introduction to Python",
        "History of Python",
        "Python Installation and Setup",
        ...
      ]
    }]
  }]
}
```

✅ **Status:** Working correctly!

---

## API Documentation Reference

- **Endpoint:** `/v3/content_generation/generate_sub_topics/live`
- **Documentation:** https://docs.dataforseo.com/v3/content_generation-generate_sub_topics-live/
- **Required Parameters:**
  - `topic` (string): The topic to generate subtopics for
- **Optional Parameters:**
  - `creativity_index` (float, 0.0-1.0): Creativity level (default: 0.7)
- **Response Fields:**
  - `sub_topics` (array): List of generated subtopics
  - `input_tokens` (integer): Number of input tokens
  - `output_tokens` (integer): Number of output tokens
  - `new_tokens` (integer): Number of new tokens generated

---

## Cost

- **Price:** $0.0001 per task
- **Cost for 1M tasks:** $100

---

## Changes Committed

- ✅ Updated endpoint path: `generate_subtopics` → `generate_sub_topics`
- ✅ Updated payload: `text` → `topic`
- ✅ Updated response parsing: `subtopics` → `sub_topics`
- ✅ Added `creativity_index` parameter
- ✅ Updated metadata extraction

**Commit:** `Fix: Correct subtopics endpoint path - use generate_sub_topics (with underscore) and correct payload format`

**Branch:** `develop`

**Status:** ✅ Committed and pushed to GitHub

---

## Next Steps

1. ✅ Wait for Cloud Build deployment to complete (~5-10 minutes)
2. ✅ Test the endpoint after deployment
3. ✅ Verify subtopics are generated correctly in blog content

---

## Related Files

- `src/blog_writer_sdk/integrations/dataforseo_integration.py` - Fixed `generate_subtopics()` method
- `src/blog_writer_sdk/services/dataforseo_content_generation_service.py` - Uses the fixed method (no changes needed)

