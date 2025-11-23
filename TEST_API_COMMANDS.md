# Test DataForSEO API Endpoints - Commands to Run

**Date**: 2025-01-15  
**API Key**: `developer@tin.info:725ec88e0af0c905`  
**Status**: Subscription updated - ready to test

---

## Test Commands

### 1. Test LLM Mentions Endpoint (Should Work Now)

```bash
curl -X POST "https://api.dataforseo.com/v3/ai_optimization/llm_mentions/search/live" \
  -H "Authorization: Basic ZGV2ZWxvcGVyQHRpbi5pbmZvOjcyNWVjODhlMGFmMGM5MDU=" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "target": [{"keyword": "chatgpt"}],
      "location_name": "United States",
      "language_code": "en",
      "platform": "chat_gpt",
      "limit": 10
    }
  ]' | python3 -m json.tool
```

**Expected**: Should return `20000` status with LLM mentions data

---

### 2. Test AI Search Volume - Path 1

```bash
curl -X POST "https://api.dataforseo.com/v3/ai_optimization/keyword_data/live" \
  -H "Authorization: Basic ZGV2ZWxvcGVyQHRpbi5pbmZvOjcyNWVjODhlMGFmMGM5MDU=" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "keywords": ["chatgpt"],
      "location_name": "United States",
      "language_code": "en"
    }
  ]' | python3 -m json.tool
```

**Expected**: Should return `20000` if this is the correct path

---

### 3. Test AI Search Volume - Path 2

```bash
curl -X POST "https://api.dataforseo.com/v3/ai_optimization/ai_keyword_data/live" \
  -H "Authorization: Basic ZGV2ZWxvcGVyQHRpbi5pbmZvOjcyNWVjODhlMGFmMGM5MDU=" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "keywords": ["chatgpt"],
      "location_name": "United States",
      "language_code": "en"
    }
  ]' | python3 -m json.tool
```

**Expected**: Should return `20000` if this is the correct path

---

## What to Look For

### Success Indicators:
- `"status_code": 20000` - API call succeeded
- `"status_message": "Ok."` - Request was processed
- `"result"` array contains data

### Error Indicators:
- `"status_code": 40204` - Still needs subscription (shouldn't happen now)
- `"status_code": 40402` - Invalid Path (wrong endpoint)
- `"status_code": 40400` - Not Found (wrong endpoint)

---

## After Testing

Once you identify which endpoint path works:
1. Update the code in `src/blog_writer_sdk/integrations/dataforseo_integration.py`
2. Remove the fallback paths that don't work
3. Update the endpoint path to the correct one

---

## Quick Test Script

You can also run the Python test script:

```bash
cd /Users/gene/Projects/api-blogwriting-python-gcr
python3 test_api_with_subscription.py
```

Or the bash script:

```bash
cd /Users/gene/Projects/api-blogwriting-python-gcr
bash test_endpoints_simple.sh
```

