# DataForSEO Content Generation API Fix

## Issue Identified

**Error:** `40501 - Invalid Field: 'word_count'`

The DataForSEO Content Generation API was rejecting the `word_count` field in the request payload.

## Root Cause

The API endpoint `/v3/content_generation/generate_text/live` has changed its parameter structure:
- ❌ Old: `topic` and `word_count` fields
- ✅ New: `text` and `max_new_tokens` fields

## Fix Applied

### Updated Parameters

**Before:**
```python
payload = [{
    "topic": prompt,
    "word_count": word_count,
    "creativity_index": creativity_index
}]
```

**After:**
```python
payload = [{
    "text": prompt,  # Changed from "topic" to "text"
    "max_new_tokens": max_new_tokens,  # Changed from "word_count" to "max_new_tokens"
    "creativity_index": creativity_index
}]
```

### Token Conversion

- Word count to tokens: `max_new_tokens = int(word_count * 1.33)` (approximately 1 word = 1.33 tokens)
- If `word_count` not provided, uses `max_tokens` directly

## Files Modified

1. `src/blog_writer_sdk/integrations/dataforseo_integration.py`
   - Updated `generate_text` method payload structure
   - Changed field names to match current API specification
   - Updated logging to reflect new parameter names

## Next Steps

1. ✅ Code updated with correct field names
2. ⏳ Deploy to Cloud Run and test
3. ⏳ Verify subscription status (check for 40204 errors)

## Subscription Verification

To verify DataForSEO Content Generation API subscription:
1. Log in to DataForSEO dashboard: https://app.dataforseo.com/
2. Navigate to "Plans and Subscriptions"
3. Verify Content Generation API is included in active plan
4. Check API credits/limits

If subscription is inactive, you may see error `40204 - Access denied. Visit Plans and Subscriptions to activate your subscription and get access to this API.`

