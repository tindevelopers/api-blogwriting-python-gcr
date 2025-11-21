# Keyword Analysis Granularity Issue

## Problem Statement

The API response for keyword analysis lacks the granularity of Ahrefs, specifically:

1. **CPC Discrepancy**: API shows $10.05 vs Ahrefs $2.00
2. **Missing Global Search Volume**: Shows 0 instead of country breakdown
3. **Missing Historical Data**: `monthly_searches` is empty
4. **Missing Traffic Metrics**: `clicks`, `cps`, `traffic_potential` are null
5. **Missing Related Data**: `also_rank_for`, `also_talk_about` not populated

## Root Causes

### 1. CPC Source Issue

**Current Implementation**:
- Uses `keywords_data/google_ads/search_volume/live` which returns **Google Ads CPC** (advertising costs)
- This is typically 3-5x higher than organic search CPC
- Ahrefs shows **organic search CPC** which is more relevant for SEO

**Fix Required**:
- Prioritize CPC from `dataforseo_labs/google/keyword_overview/live` (organic CPC)
- Only fall back to Google Ads CPC if overview data unavailable
- The overview endpoint provides more accurate organic CPC

### 2. Overview Data Not Merging

**Current Flow**:
```python
# In _get_dataforseo_batch_metrics:
overview_task = asyncio.create_task(
    self._df_client.get_keyword_overview(...)
)
overview_map, _ = self._parse_keyword_overview_response(overview_raw)

# Then merges:
cpc = self._safe_float(m.get("cpc", overview_entry.get("cpc")))
```

**Issue**: 
- If `overview_raw` fails or returns empty, `overview_map` is empty
- The code falls back to Google Ads data (`m.get("cpc")`) which has higher CPC
- Overview data fields (`global_search_volume`, `clicks`, etc.) are not populated

**Fix Required**:
- Ensure overview endpoint is called and data is properly parsed
- Add error handling to log when overview fails
- Verify overview response structure matches expected format

### 3. Missing DataForSEO Endpoints

**Ahrefs Shows**:
- "Also rank for" keywords (keywords that pages ranking for this keyword also rank for)
- "Also talk about" topics (related topics/entities)
- Questions with search volumes
- Matching terms with volumes
- Related terms with volumes

**Current Implementation**:
- `also_rank_for` and `also_talk_about` are extracted from overview response
- But if overview fails, these are empty
- Need to verify these fields are in the overview response structure

**Additional Endpoints Needed**:
- `dataforseo_labs/google/ranked_keywords` - For "also rank for" data
- `dataforseo_labs/google/related_keywords` - For related keywords with volumes
- `serp/google/organic/live/advanced` - For questions and related searches

## Solutions

### Solution 1: Fix CPC Priority (Immediate)

**File**: `src/blog_writer_sdk/seo/enhanced_keyword_analyzer.py`

**Change**: Prioritize overview CPC over Google Ads CPC

```python
# Current (line ~360):
cpc = self._safe_float(m.get("cpc", overview_entry.get("cpc")))

# Fixed:
# Prioritize overview CPC (organic) over Google Ads CPC
cpc = self._safe_float(
    overview_entry.get("cpc") if overview_entry.get("cpc") else m.get("cpc", 0.0)
)
```

### Solution 2: Ensure Overview Data is Populated

**File**: `src/blog_writer_sdk/seo/enhanced_keyword_analyzer.py`

**Change**: Add logging and fallback handling

```python
# After parsing overview (line ~349):
overview_map, _ = self._parse_keyword_overview_response(overview_raw)

# Add logging:
if not overview_map:
    logger.warning(f"Keyword overview returned empty for {len(keywords)} keywords")
    logger.debug(f"Overview raw response: {overview_raw}")

# Ensure overview data is used even if search volume data is missing
for kw in keywords:
    overview_entry = overview_map.get(kw, {})
    if overview_entry:
        # Use overview data as primary source
        search_volume = self._safe_int(overview_entry.get("search_volume", m.get("search_volume", 0)))
        cpc = self._safe_float(overview_entry.get("cpc", 0.0))  # Prioritize overview CPC
        # ... rest of fields from overview
```

### Solution 3: Add Missing Endpoints for Related Data

**File**: `src/blog_writer_sdk/integrations/dataforseo_integration.py`

**Add**: Call additional endpoints for "also rank for" and related keywords

```python
# In _get_dataforseo_batch_metrics, add:
ranked_keywords_task = asyncio.create_task(
    self._df_client.get_ranked_keywords_for_keyword(
        keyword=kw,
        location_name=self.location,
        language_code=self.language_code,
        tenant_id=tenant_id
    )
)
```

### Solution 4: Verify Overview Response Structure

**Action**: Test the actual DataForSEO API response to ensure fields are being extracted correctly.

**Expected Overview Response Structure**:
```json
{
  "tasks": [{
    "result": [{
      "keyword_data": {
        "keyword_info": {
          "search_volume": 22000,
          "global_search_volume": 57000,
          "search_volume_by_country": [...],
          "monthly_searches": [...],
          "cpc": 2.00,  // Organic CPC
          "currency": "USD"
        },
        "impressions_info": {
          "clicks": 25000,
          "cps": 1.19,
          "value": 86800  // Traffic potential
        }
      }
    }]
  }]
}
```

## Testing

### Test Case 1: Verify CPC Source

```bash
curl -X POST "https://blog-writer-api-dev-kq42l26tuq-ew.a.run.app/api/v1/keywords/enhanced" \
  -H "Content-Type: application/json" \
  -d '{"keywords":["schedule maker"],"max_suggestions_per_keyword":5}'
```

**Expected**: CPC should be ~$2.00 (organic) not $10.05 (Google Ads)

### Test Case 2: Verify Global Search Volume

**Expected**: Should show country breakdown like Ahrefs:
- United States: 22K (38%)
- Philippines: 14K (24%)
- etc.

### Test Case 3: Verify Historical Data

**Expected**: `monthly_searches` should have 12+ months of data

## Implementation Priority

1. **Fix CPC priority** (Immediate - 30 min)
2. **Add overview data logging** (Immediate - 15 min)
3. **Verify overview response parsing** (High - 1 hour)
4. **Add related keywords endpoints** (Medium - 2 hours)

## Expected Outcome

After fixes:
- CPC: ~$2.00 (matches Ahrefs organic CPC)
- Global Search Volume: 57K with country breakdown
- Monthly Searches: 12+ months of historical data
- Clicks: ~25K
- Traffic Potential: ~$86.8K
- Also Rank For: List of related keywords
- Also Talk About: List of related topics

