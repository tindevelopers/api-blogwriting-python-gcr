# Google Search Console - Multi-Site Setup Guide

## Overview

Google Search Console requires a **site URL** to access search performance data. If you have **multiple websites**, you have several options for configuration.

## Current Implementation

**Current Status:** Single site URL via `GSC_SITE_URL` environment variable

**Limitation:** Only one site can be configured globally

---

## Options for Multiple Sites

### Option 1: Per-Request Site URL (Recommended) ✅

**Best for:** Different sites per blog generation request

**How it works:**
- Add optional `gsc_site_url` field to blog generation request
- If provided, uses that site URL for Search Console queries
- If not provided, falls back to default `GSC_SITE_URL`
- Each request can use a different site

**Benefits:**
- ✅ Flexible - different sites per request
- ✅ No code changes needed for new sites
- ✅ Frontend controls which site to use
- ✅ Works with existing single-site setup

**Implementation:**
```json
{
  "topic": "Blog topic",
  "keywords": ["keyword1", "keyword2"],
  "gsc_site_url": "https://example.com",  // Optional: site-specific
  "mode": "multi_phase"
}
```

---

### Option 2: Site URL Mapping (For Many Sites)

**Best for:** Many sites with identifiers (e.g., tenant IDs, site IDs)

**How it works:**
- Store site URLs in a mapping (database, config file, or environment)
- Use an identifier (e.g., `site_id`, `tenant_id`) to look up site URL
- Automatically select the correct site URL based on identifier

**Benefits:**
- ✅ Centralized site management
- ✅ Easy to add/remove sites
- ✅ Works well with tenant systems

**Implementation:**
```json
{
  "topic": "Blog topic",
  "keywords": ["keyword1", "keyword2"],
  "site_id": "site-123",  // Maps to site URL
  "mode": "multi_phase"
}
```

**Configuration Example:**
```python
SITE_URL_MAPPING = {
    "site-123": "https://example.com",
    "site-456": "https://another-site.com",
    "site-789": "sc-domain:example.com"
}
```

---

### Option 3: Environment-Based Configuration

**Best for:** Different sites per environment (dev/staging/prod)

**How it works:**
- Set different `GSC_SITE_URL` per environment
- Dev environment → dev site
- Staging environment → staging site
- Prod environment → prod site

**Benefits:**
- ✅ Simple setup
- ✅ Environment isolation
- ✅ One site per environment

**Limitation:** Only one site per environment

---

### Option 4: Multiple Service Accounts (Advanced)

**Best for:** Sites requiring different service accounts

**How it works:**
- Create separate service accounts per site
- Store service account keys in Secret Manager
- Select service account based on site URL

**Benefits:**
- ✅ Complete isolation per site
- ✅ Different permissions per site
- ✅ Security best practice

**Complexity:** Higher setup and maintenance

---

## Recommended Approach: Option 1 (Per-Request Site URL)

### Why Option 1?

1. **Flexibility:** Each blog generation can use a different site
2. **Simplicity:** No complex configuration needed
3. **Backward Compatible:** Works with existing single-site setup
4. **Frontend Control:** Frontend decides which site to use

### Implementation Details

**Request Model:**
```python
class EnhancedBlogGenerationRequest(BaseModel):
    topic: str
    keywords: List[str]
    gsc_site_url: Optional[str] = Field(
        None,
        description="Google Search Console site URL (optional). If not provided, uses default GSC_SITE_URL"
    )
    # ... other fields
```

**Usage:**
```python
# In blog generation endpoint
if request.gsc_site_url:
    # Create site-specific Search Console client
    gsc_client = GoogleSearchConsoleClient(site_url=request.gsc_site_url)
else:
    # Use default global client
    gsc_client = google_search_console_client
```

---

## Setup Instructions

### Step 1: Configure Default Site (Optional)

If you want a default site for all requests:

```bash
# Add to Secret Manager
gcloud secrets versions add blog-writer-env-dev \
    --data-file=- <<EOF
GSC_SITE_URL=https://default-site.com
EOF
```

### Step 2: Grant Service Account Access

For each site, grant your service account access:

1. Go to: https://search.google.com/search-console
2. Select your property (site URL)
3. Go to **Settings → Users and permissions**
4. Click **Add user**
5. Enter your service account email: `blog-writer-gsc@api-ai-blog-writer.iam.gserviceaccount.com`
6. Grant **Full** access
7. Click **Add**

**Repeat for each site.**

### Step 3: Use Per-Request Site URLs

**Frontend Example:**
```typescript
const generateBlog = async (siteUrl: string) => {
  const response = await fetch('/api/v1/blog/generate-enhanced', {
    method: 'POST',
    body: JSON.stringify({
      topic: "Blog topic",
      keywords: ["keyword1", "keyword2"],
      gsc_site_url: siteUrl,  // Site-specific URL
      mode: "multi_phase"
    })
  });
  return response.json();
};

// Use different sites
await generateBlog("https://site1.com");
await generateBlog("https://site2.com");
await generateBlog("sc-domain:example.com");
```

---

## Site URL Formats

Google Search Console supports these formats:

1. **URL Prefix Property:**
   - `https://example.com`
   - `https://www.example.com`
   - `https://blog.example.com`

2. **Domain Property:**
   - `sc-domain:example.com` (includes all subdomains)

**Recommendation:** Use **URL Prefix** format for specific sites, **Domain** format for multi-subdomain sites.

---

## Multi-Site Setup Script

Use the setup script for each site:

```bash
# Setup Site 1
./scripts/setup-google-search-console.sh dev
# Enter: https://site1.com

# Setup Site 2
./scripts/setup-google-search-console.sh dev
# Enter: https://site2.com

# Setup Site 3 (Domain property)
./scripts/setup-google-search-console.sh dev
# Enter: sc-domain:example.com
```

**Note:** The script currently stores one `GSC_SITE_URL` in Secret Manager. For multiple sites, use **Option 1** (per-request site URLs) instead.

---

## Code Changes Needed

### 1. Update Request Model

Add `gsc_site_url` field to `EnhancedBlogGenerationRequest`:

```python
gsc_site_url: Optional[str] = Field(
    None,
    description="Google Search Console site URL (optional). If not provided, uses default GSC_SITE_URL"
)
```

### 2. Update Blog Generation Endpoint

Create site-specific client when `gsc_site_url` is provided:

```python
# In generate_blog_enhanced endpoint
gsc_client = None
if request.gsc_site_url:
    gsc_client = GoogleSearchConsoleClient(site_url=request.gsc_site_url)
elif google_search_console_client:
    gsc_client = google_search_console_client
```

### 3. Pass Client to Pipeline

Pass the site-specific client to the pipeline:

```python
pipeline = MultiStageGenerationPipeline(
    # ... other params
    search_console=gsc_client
)
```

---

## Testing Multi-Site Setup

### Test 1: Default Site (No gsc_site_url)

```bash
curl -X POST /api/v1/blog/generate-enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Test topic",
    "keywords": ["test"],
    "mode": "multi_phase"
  }'
```

**Expected:** Uses `GSC_SITE_URL` from environment

### Test 2: Site-Specific URL

```bash
curl -X POST /api/v1/blog/generate-enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Test topic",
    "keywords": ["test"],
    "gsc_site_url": "https://site1.com",
    "mode": "multi_phase"
  }'
```

**Expected:** Uses `https://site1.com` for Search Console queries

---

## Summary

**Recommended:** **Option 1 (Per-Request Site URL)**

- ✅ Flexible and simple
- ✅ Works with existing setup
- ✅ Frontend controls site selection
- ✅ No complex configuration needed

**Next Steps:**
1. Implement `gsc_site_url` field in request model
2. Update blog generation endpoint to use site-specific client
3. Grant service account access to all sites
4. Test with multiple sites

---

## Questions?

- **Q: Can I use different service accounts per site?**
  - A: Yes, but requires Option 4 (Multiple Service Accounts). Option 1 uses one service account for all sites.

- **Q: What if I don't provide gsc_site_url?**
  - A: Falls back to default `GSC_SITE_URL` from environment. If not set, Search Console features are disabled.

- **Q: Can I use domain properties (sc-domain:)?**
  - A: Yes, any valid Search Console site URL format works.

- **Q: How many sites can I configure?**
  - A: Unlimited with Option 1. Each request can use a different site.

