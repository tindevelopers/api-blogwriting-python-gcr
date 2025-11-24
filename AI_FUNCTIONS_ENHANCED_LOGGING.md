# AI Functions Enhanced Logging Update

**Date**: 2025-01-15

## Changes Made

### 1. Enhanced Logging in `main.py`

Added detailed logging to the AI topic suggestions endpoint to track:
- When AI search volume is requested
- The actual data returned from the API
- When LLM mentions are requested
- The actual mentions data returned

**Location**: `main.py` lines ~4656-4735

**Changes**:
```python
# Before AI search volume call
logger.info(f"Getting AI search volume for keywords: {seed_keywords[:5]}")

# After AI search volume call
logger.info(f"AI search volume data received: {json.dumps(ai_search_volume_data, default=str)[:500]}")

# Before LLM mentions call
logger.info(f"Getting LLM mentions for keyword: {keyword}")

# After LLM mentions call
logger.info(f"LLM mentions for '{keyword}': ai_search_volume={mentions.get('ai_search_volume', 0)}, mentions_count={mentions.get('mentions_count', 0)}, top_pages={len(mentions.get('top_pages', []))}")
```

### 2. Enhanced Logging in `dataforseo_integration.py`

Added detailed logging to track the actual API response structure:

**AI Search Volume (`get_ai_search_volume`)**:
- Logs task status code and message
- Logs result count
- Logs `keyword_data` structure if present
- Logs `keyword_info` structure if present
- Logs actual `ai_search_volume` value from `keyword_info`
- Warns if result is empty array or None

**LLM Mentions (`get_llm_mentions_search`)**:
- Logs task status code and message
- Logs result count
- Logs `aggregated_metrics` structure if present
- Logs actual `ai_search_volume` and `mentions_count` from metrics
- Logs sample result structure

## How to Check Logs

After deploying these changes, check Cloud Run logs with:

```bash
# Check for AI search volume logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=blog-writer-api-dev AND jsonPayload.message=~\"AI search volume\"" --limit 50

# Check for LLM mentions logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=blog-writer-api-dev AND jsonPayload.message=~\"LLM mentions\"" --limit 50

# Check for DataForSEO API response structure logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=blog-writer-api-dev AND jsonPayload.message=~\"keyword_info\"" --limit 50
```

## Expected Log Output

When the endpoint is called, you should see logs like:

```
Getting AI search volume for keywords: ['chatgpt']
DataForSEO AI optimization API response: status_code=20000, tasks_count=1
Task status_code: 20000, status_message: Ok., result_count=1
keyword_data keys: ['keyword_info']
keyword_info keys: ['ai_search_volume', 'monthly_searches', ...]
keyword_info ai_search_volume: 12345
AI search volume data received: {"chatgpt": {"ai_search_volume": 12345, ...}}

Getting LLM mentions for keyword: chatgpt
LLM mentions API response: status_code=20000, tasks_count=1
LLM mentions task status_code: 20000, status_message: Ok., result_count=1
aggregated_metrics keys: ['ai_search_volume', 'mentions_count', ...]
aggregated_metrics ai_search_volume: 12345, mentions_count: 567
LLM mentions for 'chatgpt': ai_search_volume=12345, mentions_count=567, top_pages=10
```

## Next Steps

1. **Deploy the updated code** to Cloud Run
2. **Test the endpoint** with a keyword like "chatgpt"
3. **Check the logs** to see the actual API response structure
4. **Update parsing logic** if the response structure is different than expected

## Troubleshooting

If logs show:
- **Empty result arrays**: The API might not have data for those keywords
- **Different structure**: Update parsing logic to match actual structure
- **Status code errors**: Check API credentials and endpoint URLs
- **No logs appearing**: Check that logging is enabled and logs are being written

