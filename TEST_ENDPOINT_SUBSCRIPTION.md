# Test AI Search Volume Endpoint - Subscription Check

**Date**: 2025-01-15  
**Endpoint**: `ai_optimization/ai_keyword_data/keywords_search_volume/live`

---

## 🔧 Test Command

Run this command in your terminal to test the endpoint and check subscription status:

```bash
curl -X POST "https://api.dataforseo.com/v3/ai_optimization/ai_keyword_data/keywords_search_volume/live" \
  -H "Authorization: Basic ZGV2ZWxvcGVyQHRpbi5pbmZvOjcyNWVjODhlMGFmMGM5MDU=" \
  -H "Content-Type: application/json" \
  -d '[{
    "keywords": ["chatgpt"],
    "language_code": "en",
    "location_name": "United States"
  }]' | python3 -m json.tool
```

---

## 📊 Response Interpretation

### ✅ Success (20000)
```json
{
  "status_code": 20000,
  "tasks": [{
    "status_code": 20000,
    "result": [...]
  }]
}
```
**Meaning**: ✅ **Subscription is ACTIVE** - Endpoint works and returns data

---

### ✅ Path Correct, Subscription Needed (40204)
```json
{
  "status_code": 20000,
  "tasks": [{
    "status_code": 40204,
    "status_message": "Access denied. Visit Plans and Subscriptions..."
  }]
}
```
**Meaning**: 
- ✅ **Path is CORRECT** - Endpoint path is valid
- ❌ **Subscription NOT ACTIVE** - Need to activate AI Optimization subscription
- **Action**: Visit DataForSEO Plans and Subscriptions to activate

---

### ❌ Invalid Path (40402)
```json
{
  "tasks": [{
    "status_code": 40402,
    "status_message": "Invalid Path."
  }]
}
```
**Meaning**: ❌ Endpoint path is incorrect

---

### ❌ Not Found (40400)
```json
{
  "status_code": 40400,
  "status_message": "Not Found."
}
```
**Meaning**: ❌ Endpoint doesn't exist

---

## 🧪 Python Test Script

You can also run the Python test script:

```bash
python3 test_endpoint_subscription_check.py
```

Or use the bash script:

```bash
bash test_endpoint_curl.sh
```

---

## ✅ Expected Results

Based on previous testing:
- **LLM Mentions Endpoint**: Returns `40204` (path correct, subscription needed)
- **AI Search Volume Endpoint**: Should return `40204` or `20000`

If you get `40204`:
- ✅ The endpoint path is **CORRECT**
- ❌ You need to **activate the subscription**
- The code will work once subscription is active

If you get `20000`:
- ✅ The endpoint path is **CORRECT**
- ✅ Subscription is **ACTIVE**
- ✅ The endpoint will return data

---

## 📝 Next Steps

1. **Run the test command** above
2. **Check the response**:
   - `20000` = ✅ Works, subscription active
   - `40204` = ✅ Path correct, need subscription
   - `40402` = ❌ Invalid path
   - `40400` = ❌ Not found
3. **If 40204**: Activate subscription in DataForSEO dashboard
4. **If 20000**: Endpoint is working correctly!

---

## 🎯 Code Status

The code is already updated with the correct endpoint path:
- **First Priority**: `ai_optimization/ai_keyword_data/keywords_search_volume/live` ✅
- **Fallback**: LLM mentions endpoint (if subscription not available)

**The feature will work once subscription is activated!** ✅

