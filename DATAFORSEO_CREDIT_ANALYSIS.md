# DataForSEO Credit Usage Analysis

## Current API Call Patterns

### 1. Enhanced Keyword Analysis Endpoint (`/api/v1/keywords/enhanced`)

**Per Request:**
- 5 parallel API calls per keyword batch:
  1. `get_search_volume_data` - Google Ads search volume
  2. `get_keyword_difficulty` - Keyword difficulty
  3. `get_ai_search_volume` - AI optimization search volume
  4. `get_keyword_overview` - Keyword overview (includes monthly searches, intent)
  5. `get_search_intent` - Search intent analysis

**Additional Calls:**
- `get_keyword_suggestions` - For each seed keyword (up to 5)
- `get_related_keywords` - For each primary keyword
- `get_keyword_ideas` - For each primary keyword
- `get_serp_analysis` - If `include_serp=true` (depth=10-20, PAA click depth=2)

**Credit Cost Estimate:**
- Base batch: 5 credits per keyword set
- Suggestions: ~1 credit per seed keyword
- Related keywords: ~1 credit per keyword
- Keyword ideas: ~1 credit per keyword
- SERP analysis: ~2-5 credits per keyword (depending on depth)

**Total per request:** 10-20+ credits for a single keyword analysis

### 2. Streaming Endpoint (`/api/v1/keywords/enhanced/stream`)

**Same API calls as enhanced endpoint**, but may be making duplicate calls if:
- Cache is not shared between requests
- Multiple stages trigger the same API calls
- Error retries cause duplicate calls

### 3. SERP Analysis

**High Credit Cost:**
- `depth=10-20` (default)
- `people_also_ask_click_depth=2` (expands PAA questions)
- Each SERP call: 2-5 credits depending on depth

### 4. Cache Issues

**Current Cache Implementation:**
- In-memory cache (`self._cache = {}`)
- Cache TTL: 1 hour (3600 seconds)
- Cache is per-instance (not shared across Cloud Run instances)
- Cache is lost on container restart

**Problems:**
1. **No persistent cache** - Every container restart loses cache
2. **No shared cache** - Multiple Cloud Run instances don't share cache
3. **Cache key collisions** - Hash-based keys might collide
4. **Cache invalidation** - No mechanism to invalidate stale cache

### 5. Duplicate API Calls

**Potential Issues:**
1. **Multiple endpoints calling same APIs** - Enhanced endpoint and streaming endpoint both call DataForSEO
2. **No request deduplication** - Same keyword requested multiple times in short period
3. **Error retries** - Failed requests might retry without checking cache
4. **Batch inefficiency** - Not batching keywords optimally

## Recommendations

### Immediate Fixes (High Impact)

1. **Increase Cache TTL**
   - Current: 1 hour
   - Recommended: 24 hours for keyword data (changes slowly)
   - SERP data: 6-12 hours (more dynamic)

2. **Implement Redis Cache**
   - Shared cache across all Cloud Run instances
   - Persistent cache survives restarts
   - Better cache hit rates

3. **Optimize SERP Analysis**
   - Reduce default depth from 10-20 to 5-10
   - Reduce PAA click depth from 2 to 1
   - Only fetch SERP when explicitly requested

4. **Batch Optimization**
   - Combine multiple keyword requests into single batch
   - Avoid calling same API multiple times for same keywords
   - Use request deduplication

5. **Conditional API Calls**
   - Only call `get_keyword_overview` if needed (it's expensive)
   - Only call `get_search_intent` if needed
   - Skip AI search volume if not needed

### Medium-Term Improvements

1. **Request Deduplication**
   - Track in-flight requests
   - Share results across concurrent requests for same keywords

2. **Smart Caching**
   - Cache by keyword + location + language
   - Cache partial results
   - Implement cache warming

3. **API Call Reduction**
   - Combine related API calls where possible
   - Use cheaper endpoints when available
   - Skip optional API calls

### Long-Term Solutions

1. **Persistent Cache Layer**
   - Redis or Cloud Memorystore
   - Cache with longer TTLs
   - Cache invalidation strategy

2. **API Usage Monitoring**
   - Track credit usage per endpoint
   - Alert on high usage
   - Rate limiting per user/tenant

3. **Optimization Dashboard**
   - Show cache hit rates
   - Show API call counts
   - Show credit usage trends

## Estimated Credit Savings

**Current Usage (estimated):**
- Enhanced endpoint: 10-20 credits per request
- Streaming endpoint: 10-20 credits per request
- SERP analysis: 2-5 credits per keyword

**With Optimizations:**
- Enhanced endpoint: 2-5 credits per request (with cache)
- Streaming endpoint: 2-5 credits per request (with cache)
- SERP analysis: 1-2 credits per keyword (reduced depth)

**Potential Savings:** 50-75% reduction in credit usage

## Action Items

1. ✅ Analyze current usage patterns
2. ⏳ Increase cache TTL to 24 hours
3. ⏳ Implement Redis cache
4. ⏳ Reduce SERP analysis depth
5. ⏳ Add request deduplication
6. ⏳ Add API usage monitoring
