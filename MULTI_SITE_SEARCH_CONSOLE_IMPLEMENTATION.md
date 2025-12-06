# Multi-Site Google Search Console Implementation

## Summary

✅ **Implemented:** Per-request site URL support for Google Search Console

**What Changed:**
- Added `gsc_site_url` field to `EnhancedBlogGenerationRequest` model
- Updated blog generation endpoints to support site-specific Search Console clients
- Updated `MultiStageGenerationPipeline` to accept Search Console client

---

## How It Works

### 1. **Request Model Update**

Added optional `gsc_site_url` field to `EnhancedBlogGenerationRequest`:

```python
gsc_site_url: Optional[str] = Field(
    None,
    description="Google Search Console site URL (optional). If not provided, uses default GSC_SITE_URL from environment. Format: 'https://example.com' or 'sc-domain:example.com'"
)
```

### 2. **Endpoint Logic**

**Synchronous Endpoint (`/api/v1/blog/generate-enhanced`):**
- If `request.gsc_site_url` is provided → Creates site-specific `GoogleSearchConsoleClient`
- If not provided → Uses default `google_search_console_client` (from `GSC_SITE_URL` env var)
- Passes client to `MultiStageGenerationPipeline`

**Asynchronous Endpoint (`/api/v1/blog/worker`):**
- Same logic as synchronous endpoint
- Supports site-specific clients in background jobs

### 3. **Pipeline Update**

`MultiStageGenerationPipeline` now accepts:
```python
search_console: Optional[GoogleSearchConsoleClient] = None
```

The pipeline can use this client for:
- Query performance analysis
- Content opportunity identification
- Content gap analysis

---

## Usage Examples

### Example 1: Site-Specific Request

```json
{
  "topic": "Blog topic",
  "keywords": ["keyword1", "keyword2"],
  "gsc_site_url": "https://site1.com",
  "mode": "multi_phase"
}
```

**Result:** Uses Search Console data from `https://site1.com`

### Example 2: Default Site (No gsc_site_url)

```json
{
  "topic": "Blog topic",
  "keywords": ["keyword1", "keyword2"],
  "mode": "multi_phase"
}
```

**Result:** Uses default `GSC_SITE_URL` from environment (if configured)

### Example 3: Multiple Sites

```typescript
// Frontend code
const sites = [
  "https://site1.com",
  "https://site2.com",
  "sc-domain:example.com"
];

for (const siteUrl of sites) {
  await generateBlog({
    topic: "Topic",
    keywords: ["keyword"],
    gsc_site_url: siteUrl,  // Different site per request
    mode: "multi_phase"
  });
}
```

---

## Setup Requirements

### 1. **Service Account Access**

For each site, grant your service account access:

1. Go to: https://search.google.com/search-console
2. Select your property (site URL)
3. Go to **Settings → Users and permissions**
4. Click **Add user**
5. Enter service account email: `blog-writer-gsc@api-ai-blog-writer.iam.gserviceaccount.com`
6. Grant **Full** access
7. Click **Add**

**Repeat for each site.**

### 2. **Default Site (Optional)**

If you want a default site, set `GSC_SITE_URL` in Secret Manager:

```bash
gcloud secrets versions add blog-writer-env-dev \
    --data-file=- <<EOF
GSC_SITE_URL=https://default-site.com
EOF
```

---

## Benefits

✅ **Flexible:** Each request can use a different site  
✅ **Backward Compatible:** Works with existing single-site setup  
✅ **No Configuration Changes:** No need to update secrets for new sites  
✅ **Frontend Control:** Frontend decides which site to use per request  

---

## Site URL Formats

Supported formats:
- **URL Prefix:** `https://example.com`, `https://www.example.com`
- **Domain Property:** `sc-domain:example.com` (includes all subdomains)

---

## Testing

### Test 1: Default Site

```bash
curl -X POST /api/v1/blog/generate-enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Test",
    "keywords": ["test"],
    "mode": "multi_phase"
  }'
```

**Expected:** Uses `GSC_SITE_URL` from environment

### Test 2: Site-Specific

```bash
curl -X POST /api/v1/blog/generate-enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Test",
    "keywords": ["test"],
    "gsc_site_url": "https://site1.com",
    "mode": "multi_phase"
  }'
```

**Expected:** Uses `https://site1.com` for Search Console queries

---

## Files Modified

1. ✅ `src/blog_writer_sdk/models/enhanced_blog_models.py`
   - Added `gsc_site_url` field

2. ✅ `main.py`
   - Updated `/api/v1/blog/generate-enhanced` endpoint
   - Updated `/api/v1/blog/worker` endpoint
   - Added site-specific client creation logic

3. ✅ `src/blog_writer_sdk/ai/multi_stage_pipeline.py`
   - Added `search_console` parameter to `__init__`

---

## Next Steps

1. ✅ **Code Changes:** Complete
2. ⏳ **Testing:** Test with multiple sites
3. ⏳ **Documentation:** Update API documentation
4. ⏳ **Frontend Integration:** Frontend can now pass `gsc_site_url` per request

---

## Questions?

**Q: What if I don't provide `gsc_site_url`?**  
A: Falls back to default `GSC_SITE_URL` from environment. If not set, Search Console features are disabled.

**Q: Can I use domain properties (`sc-domain:`)?**  
A: Yes, any valid Search Console site URL format works.

**Q: How many sites can I use?**  
A: Unlimited. Each request can use a different site.

**Q: Do I need to configure each site in Secret Manager?**  
A: No. Just grant service account access to each site in Search Console. The site URL is passed per request.

