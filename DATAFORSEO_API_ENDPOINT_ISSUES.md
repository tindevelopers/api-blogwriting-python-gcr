# DataForSEO API Endpoint Issues - Direct Testing Results

**Date**: 2025-01-15  
**API Key**: `developer@tin.info:725ec88e0af0c905`  
**Documentation**: https://app.dataforseo.com/api-detail/ai-optimization

---

## 🔍 Direct API Test Results

### 1. AI Search Volume Endpoint ❌

**Current Code Path**: `keywords_data/ai_optimization/search_volume/live`

**API Response**:
```json
{
  "status_code": 20000,
  "status_message": "Ok.",
  "tasks": [{
    "status_code": 40402,
    "status_message": "Invalid Path.",
    "path": ["v3", "keywords_data", "ai_optimization", "search_volume", "live"]
  }]
}
```

**Status**: ❌ **INVALID PATH** - Endpoint doesn't exist at this path

**Tested Alternatives** (all failed):
- `ai_optimization/keyword_data/search_volume/live` → 40400 Not Found
- `ai_optimization/search_volume/live` → 40400 Not Found  
- `ai_optimization/keyword_data/live` → 40400 Not Found

**Conclusion**: ❌ **Endpoint path is incorrect** - Need to find correct path from DataForSEO documentation

---

### 2. LLM Mentions Endpoint ✅

**Current Code Path**: `ai_optimization/llm_mentions/search/live`

**API Response**:
```json
{
  "status_code": 20000,
  "status_message": "Ok.",
  "tasks": [{
    "status_code": 40204,
    "status_message": "Access denied. Visit Plans and Subscriptions to activate your subscription and get access to this API."
  }]
}
```

**Status**: ✅ **PATH IS CORRECT** - Returns "Access denied" (not "Invalid Path"), meaning:
- ✅ Endpoint path is correct
- ⚠️ Account needs subscription activation
- ✅ Code is correct, no changes needed to endpoint path

---

## 📋 Summary

| Endpoint | Current Path | Status | Action Needed |
|----------|-------------|--------|---------------|
| AI Search Volume | `keywords_data/ai_optimization/search_volume/live` | ❌ Invalid Path | Find correct path from docs |
| LLM Mentions | `ai_optimization/llm_mentions/search/live` | ✅ Correct (needs subscription) | No code changes needed |

---

## 🔧 Required Actions

### 1. Find Correct AI Search Volume Endpoint Path

**Action**: Check DataForSEO API documentation at:
- https://app.dataforseo.com/api-detail/ai-optimization

**Look for**:
- AI Search Volume endpoint
- Keyword data endpoints under AI optimization
- Correct API path structure

### 2. Update Code Once Correct Path is Found

**File**: `src/blog_writer_sdk/integrations/dataforseo_integration.py`  
**Line**: ~481

**Current**:
```python
data = await self._make_request("keywords_data/ai_optimization/search_volume/live", payload, tenant_id)
```

**Update to** (once correct path is identified):
```python
data = await self._make_request("CORRECT_PATH_HERE", payload, tenant_id)
```

### 3. Handle Subscription Access for LLM Mentions

**Status**: Path is correct, account just needs subscription

**Current Behavior**: Code handles this gracefully (returns empty results)

**Recommendation**: Add helpful error message when 40204 is received:
```python
if task.get("status_code") == 40204:
    logger.warning("DataForSEO AI optimization subscription required. "
                  "Visit Plans and Subscriptions to activate access.")
```

---

## 🧪 Test Commands Used

### Test AI Search Volume (Invalid Path):
```bash
curl -X POST "https://api.dataforseo.com/v3/keywords_data/ai_optimization/search_volume/live" \
  -H "Authorization: Basic ZGV2ZWxvcGVyQHRpbi5pbmZvOjcyNWVjODhlMGFmMGM5MDU=" \
  -H "Content-Type: application/json" \
  -d '[{"keywords": ["chatgpt"], "location_name": "United States", "language_code": "en"}]'
```

**Result**: 40402 Invalid Path

### Test LLM Mentions (Correct Path, Needs Subscription):
```bash
curl -X POST "https://api.dataforseo.com/v3/ai_optimization/llm_mentions/search/live" \
  -H "Authorization: Basic ZGV2ZWxvcGVyQHRpbi5pbmZvOjcyNWVjODhlMGFmMGM5MDU=" \
  -H "Content-Type: application/json" \
  -d '[{"target": [{"keyword": "chatgpt"}], "location_name": "United States", "language_code": "en", "platform": "chat_gpt", "limit": 10}]'
```

**Result**: 40204 Access denied (path is correct)

---

## ✅ Next Steps

1. **Check DataForSEO API Documentation**
   - Visit: https://app.dataforseo.com/api-detail/ai-optimization
   - Find correct endpoint path for AI search volume
   - Verify API structure and parameters

2. **Update Endpoint Path**
   - Once correct path is identified, update code
   - Test with provided API credentials
   - Verify response structure matches expectations

3. **Handle Subscription**
   - For LLM Mentions: Path is correct, just needs subscription activation
   - Add helpful error messages for subscription errors
   - Guide users to activate subscription if needed

---

## 📝 Notes

- **LLM Mentions endpoint path is CORRECT** - No code changes needed
- **AI Search Volume endpoint path is INCORRECT** - Need to find correct path
- Both endpoints require subscription access to AI optimization features
- Current code handles errors gracefully (returns empty results instead of crashing)

