# DataForSEO Credit Usage Optimization Summary

## Problem Identified

You're consuming DataForSEO credits too quickly due to:

1. **Short Cache TTL (1 hour)** - Keyword data cached for only 1 hour, causing frequent API calls
2. **High SERP Analysis Depth** - Using depth=20 with PAA click depth=2, very expensive
3. **In-Memory Cache** - Cache lost on container restart, not shared across instances
4. **Multiple API Calls Per Request** - 5+ parallel API calls per keyword batch
5. **No Request Deduplication** - Same keywords requested multiple times

## Optimizations Applied

### 1. Increased Cache TTL ✅
- **Keyword data cache**: 1 hour → **24 hours**
- **SERP data cache**: New separate cache with **6 hours TTL**
- **Expected savings**: ~70% reduction in repeated API calls

### 2. Reduced SERP Analysis Depth ✅
- **Default depth**: 20 → **10** (saves ~50% credits per SERP call)
- **PAA click depth**: 2 → **1** (saves ~30-40% credits)
- **Expected savings**: ~50% reduction in SERP credit usage

### 3. Optimized Cache Strategy ✅
- Separate TTLs for keyword vs SERP data
- Better cache hit logging for monitoring

## Estimated Impact

### Before Optimizations:
- Enhanced endpoint: **10-20 credits per request**
- Streaming endpoint: **10-20 credits per request**
- SERP analysis: **2-5 credits per keyword**

### After Optimizations:
- Enhanced endpoint: **2-5 credits per request** (with cache hits)
- Streaming endpoint: **2-5 credits per request** (with cache hits)
- SERP analysis: **1-2 credits per keyword** (reduced depth)

### Total Savings: **50-75% reduction in credit usage**

## Additional Recommendations

### High Priority (Next Steps):
1. **Implement Redis Cache** - Shared cache across Cloud Run instances
2. **Request Deduplication** - Track in-flight requests to avoid duplicates
3. **Conditional API Calls** - Skip expensive calls when not needed

### Medium Priority:
1. **API Usage Monitoring** - Track credits per endpoint/user
2. **Rate Limiting** - Prevent abuse
3. **Cache Warming** - Pre-populate cache for common keywords

### Long-Term:
1. **Persistent Cache Layer** - Redis/Memorystore
2. **Optimization Dashboard** - Monitor cache hit rates
3. **Smart Batching** - Combine requests more efficiently

## Files Modified

1. `src/blog_writer_sdk/integrations/dataforseo_integration.py`
   - Increased cache TTL from 1 hour to 24 hours
   - Added separate SERP cache TTL (6 hours)
   - Reduced PAA click depth from 2 to 1

2. `src/blog_writer_sdk/seo/enhanced_keyword_analyzer.py`
   - Increased cache TTL from 1 hour to 24 hours

3. `main.py`
   - Reduced SERP depth from 20 to 10 in local business endpoint
   - Reduced SERP depth from 20 to 10 in enhanced endpoint

## Monitoring

After deployment, monitor:
- Cache hit rates (check logs for "cache hit" messages)
- API call frequency (should decrease significantly)
- Credit usage trends (should see 50-75% reduction)

## Next Steps

1. Deploy these changes
2. Monitor credit usage for 24-48 hours
3. If still high, implement Redis cache
4. Add API usage monitoring dashboard
