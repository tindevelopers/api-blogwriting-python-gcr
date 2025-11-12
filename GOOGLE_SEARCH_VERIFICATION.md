# Google Search Services Verification Guide

## Overview

The Blog Writer API integrates with three Google Search services:

1. **Google Custom Search API** - For research, fact-checking, and source discovery
2. **Google Knowledge Graph API** - For entity recognition and structured data
3. **Google Search Console API** - For query performance and content opportunities

## How to Verify Access

### 1. Check Startup Logs

The application logs initialization status at startup. Check Cloud Run logs:

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=blog-writer-api-dev AND textPayload=~'Google.*Search'" --limit=10 --format="value(timestamp,textPayload)" --project=api-ai-blog-writer
```

**Expected Output:**
- ✅ `Google Custom Search client initialized.` - Credentials configured
- ⚠️ `Google Custom Search not configured (GOOGLE_CUSTOM_SEARCH_API_KEY and GOOGLE_CUSTOM_SEARCH_ENGINE_ID)` - Missing credentials

### 2. Check Environment Variables

Verify credentials are set in Secret Manager:

```bash
# Check dev environment
gcloud secrets versions access latest --secret=blog-writer-env-dev --project=api-ai-blog-writer | grep GOOGLE

# Expected variables:
# GOOGLE_CUSTOM_SEARCH_API_KEY=your-api-key
# GOOGLE_CUSTOM_SEARCH_ENGINE_ID=your-engine-id
# GOOGLE_KNOWLEDGE_GRAPH_API_KEY=your-kg-api-key
```

### 3. Test via API Endpoint

The `/api/v1/blog/generate-enhanced` endpoint will use Google Search if:
- Credentials are configured
- `use_google_search: true` is set in the request

**Test Request:**
```bash
curl -X POST https://blog-writer-api-dev-613248238610.europe-west1.run.app/api/v1/blog/generate-enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Python programming",
    "keywords": ["python", "programming"],
    "use_google_search": true,
    "use_citations": true
  }'
```

**If Google Search is working:**
- Response will include `citations` array with sources
- Content will reference real sources
- Few-shot learning will extract examples from top results

**If Google Search is NOT configured:**
- Endpoint will still work but without research/citations
- `citations` array will be empty
- Warning messages in logs

### 4. Check Service Status Endpoint

Create a health check endpoint that reports Google Search status:

```python
@app.get("/api/v1/health/services")
async def check_services():
    return {
        "google_custom_search": google_custom_search_client is not None,
        "google_knowledge_graph": google_knowledge_graph_client is not None,
        "google_search_console": google_search_console_client is not None,
        "dataforseo": dataforseo_client_global is not None
    }
```

## Required Credentials

### Google Custom Search API

1. **Get API Key:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Create API key or use existing
   - Enable "Custom Search API"

2. **Create Search Engine:**
   - Go to [Google Custom Search](https://programmablesearchengine.google.com/)
   - Create a new search engine
   - Copy the Search Engine ID (CX)

3. **Set Environment Variables:**
   ```bash
   GOOGLE_CUSTOM_SEARCH_API_KEY=your-api-key
   GOOGLE_CUSTOM_SEARCH_ENGINE_ID=your-engine-id
   ```

### Google Knowledge Graph API

1. **Get API Key:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Create API key
   - Enable "Knowledge Graph Search API"

2. **Set Environment Variable:**
   ```bash
   GOOGLE_KNOWLEDGE_GRAPH_API_KEY=your-api-key
   ```

### Google Search Console API

1. **Create Service Account:**
   - Go to [Google Cloud Console IAM](https://console.cloud.google.com/iam-admin/serviceaccounts)
   - Create service account
   - Download JSON credentials

2. **Grant Access:**
   - Go to [Google Search Console](https://search.google.com/search-console)
   - Add service account email as user
   - Grant "Full" access

3. **Set Environment Variables:**
   ```bash
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
   GSC_SITE_URL=https://your-domain.com
   ```

## Adding Credentials to Cloud Run

Use the secret management script:

```bash
# Add Google Custom Search credentials
echo "GOOGLE_CUSTOM_SEARCH_API_KEY=your-key" | gcloud secrets versions add blog-writer-env-dev --data-file=-
echo "GOOGLE_CUSTOM_SEARCH_ENGINE_ID=your-id" | gcloud secrets versions add blog-writer-env-dev --data-file=-

# Add Knowledge Graph credentials
echo "GOOGLE_KNOWLEDGE_GRAPH_API_KEY=your-key" | gcloud secrets versions add blog-writer-env-dev --data-file=-
```

Or update the secret file directly:

```bash
# Get current secret
gcloud secrets versions access latest --secret=blog-writer-env-dev > /tmp/secrets.env

# Add Google Search credentials
echo "GOOGLE_CUSTOM_SEARCH_API_KEY=your-key" >> /tmp/secrets.env
echo "GOOGLE_CUSTOM_SEARCH_ENGINE_ID=your-id" >> /tmp/secrets.env
echo "GOOGLE_KNOWLEDGE_GRAPH_API_KEY=your-kg-key" >> /tmp/secrets.env

# Update secret
gcloud secrets versions add blog-writer-env-dev --data-file=/tmp/secrets.env
```

## Current Status

Based on the code implementation:

- ✅ **Code is implemented** - All three Google Search services have client implementations
- ✅ **Graceful degradation** - Services work without Google Search (fallback to basic generation)
- ⚠️ **Credentials needed** - Google Search features require API keys to be configured
- ✅ **Startup detection** - Application logs initialization status

## Verification Checklist

- [ ] Check Cloud Run startup logs for Google Search initialization messages
- [ ] Verify credentials exist in Secret Manager
- [ ] Test API endpoint with `use_google_search: true`
- [ ] Check response includes citations (if Google Search is working)
- [ ] Review Cloud Run logs for any Google Search API errors

## Troubleshooting

### "Google Custom Search not configured" Warning

**Cause:** Missing `GOOGLE_CUSTOM_SEARCH_API_KEY` or `GOOGLE_CUSTOM_SEARCH_ENGINE_ID`

**Solution:** Add credentials to Secret Manager and redeploy

### API Quota Exceeded

**Cause:** Google Custom Search has a free tier limit (100 queries/day)

**Solution:** 
- Upgrade to paid tier
- Implement caching to reduce API calls
- Use DataForSEO as alternative for some features

### Search Returns Empty Results

**Cause:** Search Engine ID may be misconfigured or restricted

**Solution:** Verify Search Engine ID in Google Custom Search console

## Next Steps

1. **Add credentials to Secret Manager** for dev environment
2. **Redeploy** Cloud Run service to load new credentials
3. **Test** with a real blog generation request
4. **Monitor** logs for Google Search API usage
5. **Verify** citations appear in generated content

