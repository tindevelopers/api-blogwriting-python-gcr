# Test AI Search Volume Endpoints Directly

**Date**: 2025-01-15  
**Purpose**: Find the correct DataForSEO AI Search Volume endpoint path

---

## 🔧 Manual Testing Commands

Run these commands in your terminal to test each endpoint path:

### Test 1: `ai_optimization/keyword_data/live` (Most Likely)

```bash
curl -X POST "https://api.dataforseo.com/v3/ai_optimization/keyword_data/live" \
  -H "Authorization: Basic ZGV2ZWxvcGVyQHRpbi5pbmZvOjcyNWVjODhlMGFmMGM5MDU=" \
  -H "Content-Type: application/json" \
  -d '[{
    "keywords": ["chatgpt"],
    "location_name": "United States",
    "language_code": "en"
  }]' | python3 -m json.tool
```

**Expected Results**:
- `20000` = ✅ Success (endpoint works!)
- `40204` = ✅ Path correct (subscription needed)
- `40402` = ❌ Invalid Path
- `40400` = ❌ Not Found

---

### Test 2: `ai_optimization/ai_keyword_data/live` (Alternative)

```bash
curl -X POST "https://api.dataforseo.com/v3/ai_optimization/ai_keyword_data/live" \
  -H "Authorization: Basic ZGV2ZWxvcGVyQHRpbi5pbmZvOjcyNWVjODhlMGFmMGM5MDU=" \
  -H "Content-Type: application/json" \
  -d '[{
    "keywords": ["chatgpt"],
    "location_name": "United States",
    "language_code": "en"
  }]' | python3 -m json.tool
```

---

### Test 3: `ai_optimization/keywords_data/live`

```bash
curl -X POST "https://api.dataforseo.com/v3/ai_optimization/keywords_data/live" \
  -H "Authorization: Basic ZGV2ZWxvcGVyQHRpbi5pbmZvOjcyNWVjODhlMGFmMGM5MDU=" \
  -H "Content-Type: application/json" \
  -d '[{
    "keywords": ["chatgpt"],
    "location_name": "United States",
    "language_code": "en"
  }]' | python3 -m json.tool
```

---

### Test 4: `keywords_data/ai_optimization/keyword_data/live`

```bash
curl -X POST "https://api.dataforseo.com/v3/keywords_data/ai_optimization/keyword_data/live" \
  -H "Authorization: Basic ZGV2ZWxvcGVyQHRpbi5pbmZvOjcyNWVjODhlMGFmMGM5MDU=" \
  -H "Content-Type: application/json" \
  -d '[{
    "keywords": ["chatgpt"],
    "location_name": "United States",
    "language_code": "en"
  }]' | python3 -m json.tool
```

---

### Test 5: `keywords_data/ai_optimization/search_volume/live` (Original - Known Wrong)

```bash
curl -X POST "https://api.dataforseo.com/v3/keywords_data/ai_optimization/search_volume/live" \
  -H "Authorization: Basic ZGV2ZWxvcGVyQHRpbi5pbmZvOjcyNWVjODhlMGFmMGM5MDU=" \
  -H "Content-Type: application/json" \
  -d '[{
    "keywords": ["chatgpt"],
    "location_name": "United States",
    "language_code": "en"
  }]' | python3 -m json.tool
```

**Expected**: `40402 Invalid Path` (confirmed wrong)

---

### Test 6: `ai_optimization/search_volume/live`

```bash
curl -X POST "https://api.dataforseo.com/v3/ai_optimization/search_volume/live" \
  -H "Authorization: Basic ZGV2ZWxvcGVyQHRpbi5pbmZvOjcyNWVjODhlMGFmMGM5MDU=" \
  -H "Content-Type: application/json" \
  -d '[{
    "keywords": ["chatgpt"],
    "location_name": "United States",
    "language_code": "en"
  }]' | python3 -m json.tool
```

---

## 📊 Response Status Codes

- **`20000`**: ✅ **SUCCESS** - Endpoint works and returns data
- **`40204`**: ✅ **Path Correct** - Endpoint path is valid, but subscription/access needed
- **`40402`**: ❌ **Invalid Path** - Endpoint path is incorrect
- **`40400`**: ❌ **Not Found** - Endpoint doesn't exist

---

## 🔍 What to Look For

### Successful Response Structure:
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
          "monthly_searches": [...]
        }
      }
    }]
  }]
}
```

### Key Fields:
- `keyword_data.keyword_info.ai_search_volume` - The AI search volume value
- `keyword_data.keyword_info.monthly_searches` - Historical trend data

---

## ✅ Current Status

- **LLM Mentions Endpoint**: ✅ Working (`ai_optimization/llm_mentions/search/live`)
- **AI Search Volume Endpoint**: ⏳ Testing paths (will fallback to LLM mentions if needed)

---

## 📝 Next Steps

1. Run each test command above
2. Note which endpoint returns `20000` or `40204` (both mean path is correct)
3. Update the code with the correct path
4. If none work, the fallback to LLM mentions will handle it automatically

---

## 🎯 Fallback Solution

If no dedicated endpoint works, the code will automatically:
1. Use LLM mentions endpoint (`ai_optimization/llm_mentions/search/live`)
2. Extract `ai_search_volume` from the LLM mentions response
3. Return data in the same format

This ensures the feature works even without a dedicated endpoint! ✅

