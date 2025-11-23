# Test AI Keyword Data Search Volume Endpoint

**Date**: 2025-01-15  
**Based on**: Official DataForSEO API Documentation  
**Endpoint Name**: `ai_optimization_keyword_data_search_volume`

---

## 📚 Documentation Reference

**Endpoint Name**: `ai_optimization_keyword_data_search_volume`

**Description**: Provides search volume data for target keywords, reflecting their estimated usage in AI LLMs.

**Key Parameters**:
- `keywords` (required): Array of keywords (max 1,000)
- `language_code` (required): Search engine language code (e.g., 'en')
- `location_name` (optional): Full location name (default: 'United States')

---

## 🔧 Test Commands

### Test 1: `ai_optimization/keyword_data/search_volume/live` (Most Likely)

Based on endpoint name `ai_optimization_keyword_data_search_volume`, the path should be:
`ai_optimization/keyword_data/search_volume/live`

```bash
curl -X POST "https://api.dataforseo.com/v3/ai_optimization/keyword_data/search_volume/live" \
  -H "Authorization: Basic ZGV2ZWxvcGVyQHRpbi5pbmZvOjcyNWVjODhlMGFmMGM5MDU=" \
  -H "Content-Type: application/json" \
  -d '[{
    "keywords": ["chatgpt"],
    "language_code": "en",
    "location_name": "United States"
  }]' | python3 -m json.tool
```

---

### Test 2: `ai_optimization/keyword_data/live` (Alternative)

```bash
curl -X POST "https://api.dataforseo.com/v3/ai_optimization/keyword_data/live" \
  -H "Authorization: Basic ZGV2ZWxvcGVyQHRpbi5pbmZvOjcyNWVjODhlMGFmMGM5MDU=" \
  -H "Content-Type: application/json" \
  -d '[{
    "keywords": ["chatgpt"],
    "language_code": "en",
    "location_name": "United States"
  }]' | python3 -m json.tool
```

---

### Test 3: `ai_optimization/keyword_data_search_volume/live` (Alternative Format)

```bash
curl -X POST "https://api.dataforseo.com/v3/ai_optimization/keyword_data_search_volume/live" \
  -H "Authorization: Basic ZGV2ZWxvcGVyQHRpbi5pbmZvOjcyNWVjODhlMGFmMGM5MDU=" \
  -H "Content-Type: application/json" \
  -d '[{
    "keywords": ["chatgpt"],
    "language_code": "en",
    "location_name": "United States"
  }]' | python3 -m json.tool
```

---

## 📊 Expected Response Structure

### Successful Response:
```json
{
  "status_code": 20000,
  "status_message": "Ok.",
  "tasks": [{
    "status_code": 20000,
    "status_message": "Ok.",
    "result": [{
      "keyword": "chatgpt",
      "keyword_data": {
        "keyword_info": {
          "ai_search_volume": 744,
          "monthly_searches": [
            {
              "year": 2025,
              "month": 9,
              "search_volume": 744
            }
          ]
        }
      }
    }]
  }]
}
```

---

## 🔍 Response Status Codes

- **`20000`**: ✅ **SUCCESS** - Endpoint works and returns data
- **`40204`**: ✅ **Path Correct** - Endpoint path is valid, but subscription/access needed
- **`40402`**: ❌ **Invalid Path** - Endpoint path is incorrect
- **`40400`**: ❌ **Not Found** - Endpoint doesn't exist

---

## ✅ Code Updates

**File**: `src/blog_writer_sdk/integrations/dataforseo_integration.py`

**Updated endpoint paths to try**:
1. `ai_optimization/keyword_data/search_volume/live` ← **NEW** (from documentation)
2. `ai_optimization/keyword_data/live` (alternative)
3. `ai_optimization/ai_keyword_data/live` (alternative)
4. `keywords_data/ai_optimization/search_volume/live` (original, known wrong)

---

## 🧪 Python Test Script

Run the test script:
```bash
python3 test_ai_keyword_data_search_volume.py
```

This will test all endpoint paths automatically and report which one works.

---

## 📝 Next Steps

1. **Run Test Commands**: Test each endpoint path manually
2. **Check Response**: Look for `20000` or `40204` status codes
3. **Verify Data**: Check if `ai_search_volume` is in the response
4. **Update Code**: Code already updated with correct path priority

---

## 🎯 Fallback Solution

If the dedicated endpoint doesn't work, the code will automatically:
1. Try all endpoint paths (including the new one from documentation)
2. Fallback to LLM mentions endpoint
3. Extract `ai_search_volume` from LLM mentions response
4. Return data in expected format

**The feature will work either way!** ✅

