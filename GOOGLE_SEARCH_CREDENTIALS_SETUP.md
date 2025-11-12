# Google Search Credentials Setup Guide

## Quick Setup

Run the automated script:

```bash
./scripts/add-google-search-secrets.sh
```

The script will prompt you for each credential and add them to Secret Manager.

## Manual Setup

### Step 1: Get Google Custom Search API Credentials

1. **Get API Key:**
   - Go to [Google Cloud Console - APIs & Services - Credentials](https://console.cloud.google.com/apis/credentials)
   - Click "Create Credentials" → "API Key"
   - Copy the API key
   - (Optional) Restrict the API key to "Custom Search API" for security

2. **Enable Custom Search API:**
   - Go to [Custom Search API Library](https://console.cloud.google.com/apis/library/customsearch.googleapis.com)
   - Click "Enable"

3. **Create Custom Search Engine:**
   - Go to [Google Custom Search Engine](https://programmablesearchengine.google.com/)
   - Click "Add" to create a new search engine
   - Enter a name and description
   - Choose "Search the entire web" or specify sites
   - Click "Create"
   - Copy the **Search Engine ID (CX)** from the "Overview" page

### Step 2: Get Google Knowledge Graph API Credentials (Optional)

1. **Get API Key:**
   - Go to [Google Cloud Console - APIs & Services - Credentials](https://console.cloud.google.com/apis/credentials)
   - Create a new API key or use existing
   - Copy the API key

2. **Enable Knowledge Graph API:**
   - Go to [Knowledge Graph Search API Library](https://console.cloud.google.com/apis/library/kgsearch.googleapis.com)
   - Click "Enable"

### Step 3: Add Credentials to Secret Manager

#### Option A: Using the Script (Recommended)

```bash
./scripts/add-google-search-secrets.sh
```

#### Option B: Manual Addition

**For JSON format secret:**

```bash
# Get current secret
gcloud secrets versions access latest --secret=blog-writer-env-dev --project=api-ai-blog-writer > /tmp/secrets.json

# Add Google Search credentials
jq '. + {
  "GOOGLE_CUSTOM_SEARCH_API_KEY": "your-api-key-here",
  "GOOGLE_CUSTOM_SEARCH_ENGINE_ID": "your-engine-id-here",
  "GOOGLE_KNOWLEDGE_GRAPH_API_KEY": "your-kg-api-key-here"
}' /tmp/secrets.json > /tmp/secrets-updated.json

# Update secret
gcloud secrets versions add blog-writer-env-dev \
  --data-file=/tmp/secrets-updated.json \
  --project=api-ai-blog-writer
```

**For plain text format (env file):**

```bash
# Get current secret
gcloud secrets versions access latest --secret=blog-writer-env-dev --project=api-ai-blog-writer > /tmp/secrets.env

# Add Google Search credentials
cat >> /tmp/secrets.env << EOF
GOOGLE_CUSTOM_SEARCH_API_KEY=your-api-key-here
GOOGLE_CUSTOM_SEARCH_ENGINE_ID=your-engine-id-here
GOOGLE_KNOWLEDGE_GRAPH_API_KEY=your-kg-api-key-here
EOF

# Update secret
gcloud secrets versions add blog-writer-env-dev \
  --data-file=/tmp/secrets.env \
  --project=api-ai-blog-writer
```

### Step 4: Verify Credentials

Check that credentials were added:

```bash
gcloud secrets versions access latest --secret=blog-writer-env-dev --project=api-ai-blog-writer | grep GOOGLE
```

You should see:
```
GOOGLE_CUSTOM_SEARCH_API_KEY=...
GOOGLE_CUSTOM_SEARCH_ENGINE_ID=...
GOOGLE_KNOWLEDGE_GRAPH_API_KEY=...
```

### Step 5: Redeploy Cloud Run

The credentials will be loaded on the next deployment. Trigger a deployment:

```bash
# Push a change to trigger deployment
git commit --allow-empty -m "trigger: reload Google Search credentials"
git push origin develop
```

Or manually redeploy:

```bash
gcloud run deploy blog-writer-api-dev \
  --region=europe-west1 \
  --source . \
  --project=api-ai-blog-writer
```

### Step 6: Verify Initialization

Check Cloud Run logs for initialization messages:

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=blog-writer-api-dev AND textPayload=~'Google'" --limit=10 --format="value(textPayload)" --project=api-ai-blog-writer
```

**Expected output:**
```
✅ Google Custom Search client initialized.
✅ Google Knowledge Graph client initialized.
```

If you see warnings instead:
```
⚠️ Google Custom Search not configured (GOOGLE_CUSTOM_SEARCH_API_KEY and GOOGLE_CUSTOM_SEARCH_ENGINE_ID)
```

This means the credentials weren't loaded. Check:
1. Credentials are in Secret Manager
2. Secret is mounted correctly in Cloud Run
3. Environment variable names match exactly

## Testing

Test the API endpoint with Google Search enabled:

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

**If working correctly:**
- Response includes `citations` array with sources
- Content references real sources
- Few-shot learning extracts examples from top results

## API Quotas & Limits

### Google Custom Search API
- **Free tier:** 100 queries per day
- **Paid tier:** $5 per 1,000 queries (after free tier)
- **Rate limit:** 10 queries per second

### Google Knowledge Graph API
- **Free tier:** 100,000 queries per day
- **No paid tier** (completely free)

## Troubleshooting

### "API key not valid" Error

1. Verify API key is correct
2. Check API is enabled in Google Cloud Console
3. Verify API key restrictions (if any) allow the API

### "Search Engine ID not found" Error

1. Verify Search Engine ID (CX) is correct
2. Check Custom Search Engine exists and is active
3. Ensure Search Engine is set to "Search the entire web" if needed

### Credentials Not Loading

1. Check Secret Manager has the credentials:
   ```bash
   gcloud secrets versions access latest --secret=blog-writer-env-dev --project=api-ai-blog-writer | grep GOOGLE
   ```

2. Verify Cloud Run service mounts the secret:
   ```bash
   gcloud run services describe blog-writer-api-dev --region=europe-west1 --format="get(spec.template.spec.containers[0].env)" --project=api-ai-blog-writer
   ```

3. Check startup logs for errors:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=blog-writer-api-dev" --limit=50 --format="value(textPayload)" --project=api-ai-blog-writer | grep -i "google\|error"
   ```

## Security Best Practices

1. **Restrict API Keys:**
   - Restrict API keys to specific APIs (Custom Search API, Knowledge Graph API)
   - Restrict by IP address or HTTP referrer if possible

2. **Use Service Accounts:**
   - For production, consider using service accounts instead of API keys
   - Service accounts provide better security and auditability

3. **Rotate Credentials:**
   - Regularly rotate API keys
   - Update Secret Manager when rotating

4. **Monitor Usage:**
   - Set up billing alerts in Google Cloud Console
   - Monitor API usage to detect anomalies

## Support

For issues with:
- **Google Cloud Console:** [Google Cloud Support](https://cloud.google.com/support)
- **Custom Search API:** [Custom Search API Documentation](https://developers.google.com/custom-search/v1/overview)
- **Knowledge Graph API:** [Knowledge Graph API Documentation](https://developers.google.com/knowledge-graph)

