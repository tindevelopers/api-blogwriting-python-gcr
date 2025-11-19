# Keyword Research Improvements: Matching Ahrefs-Level Results

## Current Issue

**Problem:** Portal shows limited results (0 search volume, $0.00 CPC) while Ahrefs shows comprehensive data:
- Search Volume: 17K
- CPC: $0.90
- Difficulty: 11 (Medium)
- Related keywords, questions, topics

**Root Cause:** Current implementation uses single endpoint or doesn't combine multiple DataForSEO endpoints effectively.

---

## Available DataForSEO Endpoints

### Currently Used ✅

1. **`dataforseo_labs/google/keyword_overview/live`**
   - Used in: `get_keyword_overview()`
   - Returns: Search volume, CPC, competition, monthly searches
   - **Issue:** May not return all fields or may require paid plan

2. **`keywords_data/google_ads/search_volume/live`**
   - Used in: `get_search_volume_data()`
   - Returns: Search volume, CPC, competition, trends
   - **Status:** Working but may not be called in enhanced endpoint

3. **`dataforseo_labs/bulk_keyword_difficulty/live`**
   - Used in: `get_keyword_difficulty()`
   - Returns: Keyword difficulty scores (0-100)
   - **Issue:** May require Labs subscription

4. **`dataforseo_labs/google/keyword_suggestions/live`**
   - Used in: `get_keyword_suggestions()`
   - Returns: Long-tail keyword variations with metrics
   - **Status:** Working

5. **`dataforseo_labs/google/related_keywords/live`**
   - Used in: `get_related_keywords()`
   - Returns: Related keywords via graph traversal
   - **Status:** Working

### Available But Not Fully Utilized 🔄

6. **`dataforseo_labs/google/keyword_ideas/live`**
   - Used in: `get_keyword_ideas()`
   - Returns: Keyword ideas based on seed keywords
   - **Status:** Implemented but may not be called

7. **`dataforseo_labs/google/keyword_overview/live`** (Alternative)
   - More comprehensive than basic search volume
   - Returns: Full keyword metrics including global volume, country breakdown

8. **`keywords_data/google_trends_explore`**
   - Returns: Google Trends data, related topics, queries
   - **Status:** Commented out in code, needs implementation

---

## Recommended Solution: Multi-Endpoint Combination

### Strategy: Combine Multiple Endpoints for Comprehensive Results

Similar to how Ahrefs combines multiple data sources, we should:

1. **Primary Keyword Metrics** (use multiple sources)
2. **Related Keywords** (use graph-based + suggestions)
3. **Questions & Topics** (use keyword ideas + trends)
4. **Global Data** (use keyword overview for country breakdown)

---

## Implementation Plan

### Phase 1: Fix Current Endpoint (Immediate)

**File:** `src/blog_writer_sdk/seo/enhanced_keyword_analyzer.py`

**Changes:**
1. Ensure `get_keyword_overview()` is called for primary metrics
2. Fallback to `get_search_volume_data()` if overview fails
3. Combine results from both endpoints

**Code Update:**
```python
async def _get_dataforseo_metrics(self, keyword: str, tenant_id: str = "default") -> Dict[str, Any]:
    """Get comprehensive keyword metrics from DataForSEO using multiple endpoints."""
    if not (self.use_dataforseo and self._df_client):
        return self._default_metrics()
    
    try:
        await self._df_client.initialize_credentials(tenant_id)
        
        # Try keyword overview first (most comprehensive)
        overview_data = {}
        try:
            overview_response = await self._df_client.get_keyword_overview(
                keywords=[keyword],
                location_name=self.location,
                language_code=self.language_code,
                tenant_id=tenant_id
            )
            # Parse overview response
            if overview_response.get("tasks") and overview_response["tasks"][0].get("result"):
                result = overview_response["tasks"][0]["result"][0]
                overview_data = {
                    "search_volume": result.get("keyword_info", {}).get("search_volume", 0) or 0,
                    "cpc": result.get("keyword_info", {}).get("cpc", 0.0) or 0.0,
                    "competition": result.get("keyword_info", {}).get("competition", 0.0) or 0.0,
                    "global_search_volume": result.get("keyword_info", {}).get("global_search_volume", 0) or 0,
                    "monthly_searches": result.get("keyword_info", {}).get("monthly_searches", []),
                }
        except Exception as e:
            logger.warning(f"Keyword overview failed, trying search volume: {e}")
        
        # Fallback to search volume endpoint if overview didn't work
        if not overview_data.get("search_volume"):
            sv_data = await self._df_client.get_search_volume_data(
                keywords=[keyword],
                location_name=self.location,
                language_code=self.language_code,
                tenant_id=tenant_id
            )
            m = sv_data.get(keyword, {})
            overview_data.update({
                "search_volume": m.get("search_volume", 0) or 0,
                "cpc": m.get("cpc", 0.0) or 0.0,
                "competition": m.get("competition", 0.0) or 0.0,
                "monthly_searches": m.get("monthly_searches", []),
            })
        
        # Get difficulty (may fail if Labs not available)
        difficulty_score = 50.0  # Default
        try:
            diff_data = await self._df_client.get_keyword_difficulty(
                keywords=[keyword],
                location_name=self.location,
                language_code=self.language_code,
                tenant_id=tenant_id
            )
            difficulty_score = diff_data.get(keyword, 50.0) or 50.0
        except Exception as e:
            logger.warning(f"Difficulty fetch failed: {e}")
        
        return {
            "search_volume": overview_data.get("search_volume", 0),
            "global_search_volume": overview_data.get("global_search_volume", 0),
            "cpc": overview_data.get("cpc", 0.0),
            "competition": overview_data.get("competition", 0.0),
            "monthly_searches": overview_data.get("monthly_searches", []),
            "difficulty_score": difficulty_score,
            "trend_score": self._calculate_trend_score(overview_data.get("monthly_searches", [])),
        }
    except Exception as e:
        logger.error(f"Error fetching DataForSEO metrics: {e}")
        return self._default_metrics()
```

### Phase 2: Add Related Keywords & Questions (Next)

**Enhancement:** Add related keywords, questions, and topics to response

**Update:** `main.py` - `/api/v1/keywords/enhanced` endpoint

```python
# After getting primary keyword analysis, add:

# Get related keywords
related_keywords_data = {}
try:
    for keyword in limited_keywords:
        related = await enhanced_analyzer._df_client.get_related_keywords(
            keyword=keyword,
            location_name=effective_location,
            language_code=request.language or "en",
            tenant_id=tenant_id,
            depth=1,  # Start with depth 1 for speed
            limit=20
        )
        related_keywords_data[keyword] = related
except Exception as e:
    logger.warning(f"Related keywords failed: {e}")

# Get keyword ideas (includes questions and topics)
keyword_ideas_data = {}
try:
    for keyword in limited_keywords:
        ideas = await enhanced_analyzer._df_client.get_keyword_ideas(
            keywords=[keyword],
            location_name=effective_location,
            language_code=request.language or "en",
            tenant_id=tenant_id,
            limit=50
        )
        keyword_ideas_data[keyword] = ideas
except Exception as e:
    logger.warning(f"Keyword ideas failed: {e}")
```

### Phase 3: Add Global Search Volume Breakdown (Future)

**Enhancement:** Show search volume by country (like Ahrefs)

**Implementation:** Use `keyword_overview` endpoint which includes `global_search_volume` and country breakdown.

---

## Expected Results After Implementation

### Before (Current):
```json
{
  "pet grooming": {
    "search_volume": 0,
    "cpc": 0.00,
    "difficulty": "medium",
    "competition": 0.35
  }
}
```

### After (Expected):
```json
{
  "pet grooming": {
    "search_volume": 17000,
    "global_search_volume": 38000,
    "cpc": 0.90,
    "difficulty": "medium",
    "difficulty_score": 11,
    "competition": 0.35,
    "clicks": 10000,
    "cps": 0.58,
    "monthly_searches": [
      {"month": "2024-11", "search_volume": 17000},
      {"month": "2024-10", "search_volume": 16500}
    ],
    "search_volume_by_country": {
      "United States": 17000,
      "Australia": 2200,
      "India": 1700
    },
    "related_keywords": [
      {"keyword": "pet grooming near me", "search_volume": 44000},
      {"keyword": "dog grooming services", "search_volume": 2800}
    ],
    "questions": [
      {"keyword": "how to start a pet grooming business", "search_volume": 150},
      {"keyword": "does pet insurance cover grooming", "search_volume": 100}
    ],
    "topics": [
      {"keyword": "tractor supply", "search_volume": 1600000},
      {"keyword": "dog", "search_volume": 1400000}
    ]
  }
}
```

---

## Testing Plan

### Test Case 1: Single Keyword
```bash
curl -X POST "https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/keywords/enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["pet grooming"],
    "location": "United States",
    "language": "en"
  }'
```

**Expected:** Search volume > 0, CPC > 0, related keywords present

### Test Case 2: Multiple Keywords
```bash
curl -X POST "https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/keywords/enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["pet grooming", "dog care", "pet health"],
    "location": "United States",
    "language": "en",
    "max_suggestions_per_keyword": 20
  }'
```

**Expected:** All keywords have metrics, suggestions returned

---

## Priority Actions

1. **Immediate:** Fix `_get_dataforseo_metrics()` to use `keyword_overview` endpoint
2. **Immediate:** Add fallback to `search_volume` endpoint if overview fails
3. **Short-term:** Add related keywords to response
4. **Short-term:** Add keyword ideas (questions, topics) to response
5. **Medium-term:** Add global search volume breakdown
6. **Medium-term:** Add Google Trends integration

---

## Cost Considerations

- **Keyword Overview:** ~1 credit per keyword
- **Search Volume:** ~0.5 credits per keyword
- **Related Keywords:** ~2 credits per keyword (depth 1)
- **Keyword Ideas:** ~1 credit per keyword

**Total per keyword:** ~4-5 credits for comprehensive analysis

**Recommendation:** Cache results aggressively (current: 1 hour TTL) to reduce costs.

---

## Next Steps

1. ✅ Review current implementation
2. ⏳ Update `_get_dataforseo_metrics()` to use multiple endpoints
3. ⏳ Add related keywords to enhanced endpoint response
4. ⏳ Add keyword ideas to enhanced endpoint response
5. ⏳ Test with "pet grooming" keyword
6. ⏳ Deploy and verify results match Ahrefs-level data

