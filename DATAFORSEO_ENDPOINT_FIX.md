# DataForSEO API Endpoint Fix

**Date**: 2025-01-15  
**Issue**: Incorrect API endpoint paths causing "Invalid Path" errors

---

## 🔍 Findings from Direct API Testing

### Test Results with API Key: `developer@tin.info:725ec88e0af0c905`

#### 1. AI Search Volume Endpoint ❌

**Current Code Uses**: `keywords_data/ai_optimization/search_volume/live`  
**API Response**: `40402 Invalid Path`

**Tested Alternatives**:
- `ai_optimization/keyword_data/search_volume/live` → `40400 Not Found`
- `ai_optimization/search_volume/live` → `40400 Not Found`
- `ai_optimization/keyword_data/live` → `40400 Not Found`

**Status**: ❌ **Endpoint path is incorrect or endpoint doesn't exist**

#### 2. LLM Mentions Endpoint ✅ (Path Correct, Access Needed)

**Current Code Uses**: `ai_optimization/llm_mentions/search/live`  
**API Response**: `40204 Access denied. Visit Plans and Subscriptions to activate your subscription`

**Status**: ✅ **Path is CORRECT** - The account just needs subscription access

---

## 📋 Analysis

### LLM Mentions Endpoint
- ✅ **Path is correct**: `ai_optimization/llm_mentions/search/live`
- ⚠️ **Subscription required**: Account needs to activate AI optimization subscription
- ✅ **Code is correct**: No changes needed to endpoint path

### AI Search Volume Endpoint  
- ❌ **Path is incorrect**: `keywords_data/ai_optimization/search_volume/live` doesn't exist
- ❓ **Correct path unknown**: Need to check DataForSEO API documentation
- 🔧 **Action needed**: Update endpoint path once correct path is identified

---

## 🔧 Recommended Actions

### 1. Verify Correct Endpoint Paths

Check DataForSEO API documentation at:
- https://app.dataforseo.com/api-detail/ai-optimization

Look for:
- AI Search Volume endpoint path
- Correct API structure for keyword data in AI optimization

### 2. Update Code Once Correct Path is Found

**File**: `src/blog_writer_sdk/integrations/dataforseo_integration.py`

**Current** (line 481):
```python
data = await self._make_request("keywords_data/ai_optimization/search_volume/live", payload, tenant_id)
```

**Update to correct path** (once identified):
```python
data = await self._make_request("CORRECT_PATH_HERE", payload, tenant_id)
```

### 3. Handle Subscription Access

For LLM Mentions endpoint:
- Path is correct: `ai_optimization/llm_mentions/search/live`
- Account needs subscription activation
- Code should handle 40204 errors gracefully
- Show helpful error message about subscription

---

## 📝 Next Steps

1. **Check DataForSEO API Documentation**
   - Visit https://app.dataforseo.com/api-detail/ai-optimization
   - Find correct endpoint path for AI search volume
   - Verify API structure

2. **Update Endpoint Path**
   - Once correct path is identified, update the code
   - Test with provided API credentials
   - Verify response structure

3. **Handle Subscription Errors**
   - Add better error handling for 40204 (Access denied)
   - Provide helpful error messages
   - Guide users to activate subscription

---

## 🧪 Test Commands

### Test AI Search Volume (once correct path is found):
```bash
curl -X POST "https://api.dataforseo.com/v3/CORRECT_PATH_HERE" \
  -H "Authorization: Basic ZGV2ZWxvcGVyQHRpbi5pbmZvOjcyNWVjODhlMGFmMGM5MDU=" \
  -H "Content-Type: application/json" \
  -d '[{
    "keywords": ["chatgpt"],
    "location_name": "United States",
    "language_code": "en"
  }]'
```

### Test LLM Mentions (path is correct, needs subscription):
```bash
curl -X POST "https://api.dataforseo.com/v3/ai_optimization/llm_mentions/search/live" \
  -H "Authorization: Basic ZGV2ZWxvcGVyQHRpbi5pbmZvOjcyNWVjODhlMGFmMGM5MDU=" \
  -H "Content-Type: application/json" \
  -d '[{
    "target": [{"keyword": "chatgpt"}],
    "location_name": "United States",
    "language_code": "en",
    "platform": "chat_gpt",
    "limit": 10
  }]'
```

---

## ✅ Summary

- **LLM Mentions**: Path is correct (`ai_optimization/llm_mentions/search/live`), needs subscription
- **AI Search Volume**: Path is incorrect, need to find correct path from documentation
- **Action**: Check DataForSEO API documentation for correct AI search volume endpoint path

