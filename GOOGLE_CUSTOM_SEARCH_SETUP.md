# Google Custom Search API Setup Guide

## Overview

This guide explains how to set up Google Custom Search API credentials using Google Secret Manager and configure them in the codebase.

## Prerequisites

1. **Google Cloud Project** with Secret Manager API enabled
2. **Google Custom Search API Key** - Get from [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
3. **Google Custom Search Engine ID (CX)** - Create at [Google Custom Search](https://programmablesearchengine.google.com/)

## Step 1: Get Google Custom Search Credentials

### Get API Key

1. Go to [Google Cloud Console - APIs & Services - Credentials](https://console.cloud.google.com/apis/credentials)
2. Click "Create Credentials" → "API Key"
3. Copy the API key
4. Enable "Custom Search API" for this key (if not already enabled)

### Create Search Engine

1. Go to [Google Custom Search](https://programmablesearchengine.google.com/)
2. Click "Add" to create a new search engine
3. Configure:
   - **Sites to search:** `*` (search entire web) or specific domains
   - **Name:** Your search engine name
4. Click "Create"
5. Copy the **Search Engine ID (CX)** from the control panel

## Step 2: Store Credentials in Secret Manager

### Option A: Add to Existing Secret (Recommended)

Use the provided script to add credentials to the existing `blog-writer-env-{ENV}` secret:

```bash
./scripts/setup-google-custom-search-secrets.sh
```

This script will:
- Prompt for API key and Engine ID
- Add them to the appropriate `blog-writer-env-{dev|staging|prod}` secret
- Preserve existing secret values

### Option B: Create Separate Secrets

Alternatively, create individual secrets (matching cloudbuild.yaml format):

```bash
./scripts/create-google-custom-search-secrets.sh
```

This creates:
- `GOOGLE_CUSTOM_SEARCH_API_KEY` secret
- `GOOGLE_CUSTOM_SEARCH_ENGINE_ID` secret

## Step 3: Update Deployment Configuration

### cloudbuild.yaml

The `cloudbuild.yaml` has been updated to mount these secrets:

```yaml
'--update-secrets', '/secrets/env=blog-writer-env-${_ENV}:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest,STABILITY_AI_API_KEY=STABILITY_AI_API_KEY:latest,GOOGLE_CUSTOM_SEARCH_API_KEY=GOOGLE_CUSTOM_SEARCH_API_KEY:latest,GOOGLE_CUSTOM_SEARCH_ENGINE_ID=GOOGLE_CUSTOM_SEARCH_ENGINE_ID:latest'
```

**Note:** If using Option A (adding to blog-writer-env), you may need to adjust the cloudbuild.yaml to read from `/secrets/env` instead of separate secrets.

### service.yaml

The `service.yaml` has been updated to reference these secrets:

```yaml
- name: GOOGLE_CUSTOM_SEARCH_API_KEY
  valueFrom:
    secretKeyRef:
      name: blog-writer-env
      key: GOOGLE_CUSTOM_SEARCH_API_KEY
- name: GOOGLE_CUSTOM_SEARCH_ENGINE_ID
  valueFrom:
    secretKeyRef:
      name: blog-writer-env
      key: GOOGLE_CUSTOM_SEARCH_ENGINE_ID
```

## Step 4: Grant Service Account Access

Ensure the Cloud Run service account has access to the secrets:

```bash
PROJECT_ID=$(gcloud config get-value project)
SERVICE_ACCOUNT="blog-writer-service-account@${PROJECT_ID}.iam.gserviceaccount.com"

# If using Option A (blog-writer-env secret)
gcloud secrets add-iam-policy-binding "blog-writer-env-dev" \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"

# If using Option B (separate secrets)
gcloud secrets add-iam-policy-binding "GOOGLE_CUSTOM_SEARCH_API_KEY" \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding "GOOGLE_CUSTOM_SEARCH_ENGINE_ID" \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"
```

## Step 5: Code Configuration

The code already reads from environment variables:

**File:** `main.py` (lines 640-650)
```python
google_api_key = os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY")
google_engine_id = os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")
if google_api_key and google_engine_id:
    google_custom_search_client = GoogleCustomSearchClient(
        api_key=google_api_key,
        search_engine_id=google_engine_id
    )
    print("✅ Google Custom Search client initialized.")
else:
    google_custom_search_client = None
    print("⚠️ Google Custom Search not configured")
```

No code changes are needed - the environment variables will be automatically available after deployment.

## Step 6: Deploy and Verify

### Deploy

```bash
# Push to develop branch (triggers dev deployment)
git add cloudbuild.yaml service.yaml scripts/
git commit -m "feat: Add Google Custom Search API secrets configuration"
git push origin develop
```

### Verify

1. **Check Cloud Run logs:**
```bash
gcloud logging read "resource.type=cloud_run_revision AND textPayload=~'Google Custom Search'" \
    --limit=10 \
    --format="value(timestamp,textPayload)"
```

**Expected output:**
```
✅ Google Custom Search client initialized.
```

2. **Test Multi-Phase Mode:**
```bash
curl -X POST https://your-api-url/api/v1/blog/generate-enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Test topic",
    "keywords": ["test"],
    "mode": "multi_phase",
    "use_citations": true
  }'
```

**Expected:** Should succeed without the "Google Custom Search API is required" error.

## Troubleshooting

### Secret Not Found

**Error:** `Secret 'GOOGLE_CUSTOM_SEARCH_API_KEY' not found`

**Solution:**
- Verify secret exists: `gcloud secrets list --project=YOUR_PROJECT`
- Check secret name matches cloudbuild.yaml
- Ensure you're using the correct project

### Permission Denied

**Error:** `Permission denied on secret`

**Solution:**
- Grant service account access (see Step 4)
- Verify service account name matches Cloud Run configuration
- Check IAM policies: `gcloud secrets get-iam-policy SECRET_NAME`

### Environment Variable Not Set

**Error:** `⚠️ Google Custom Search not configured`

**Solution:**
- Verify secrets are mounted in Cloud Run service
- Check Cloud Run service configuration: `gcloud run services describe SERVICE_NAME --region=REGION`
- Verify environment variables are set: Check Cloud Run logs for startup messages

### API Quota Exceeded

**Error:** `403 Quota exceeded`

**Solution:**
- Google Custom Search API has a free tier of 100 queries/day
- Check quota in [Google Cloud Console](https://console.cloud.google.com/apis/api/customsearch.googleapis.com/quotas)
- Consider upgrading to paid tier for higher limits

## Files Modified

- ✅ `cloudbuild.yaml` - Added secret mounting for Google Custom Search credentials
- ✅ `service.yaml` - Added environment variable references
- ✅ `scripts/setup-google-custom-search-secrets.sh` - Script to add to blog-writer-env
- ✅ `scripts/create-google-custom-search-secrets.sh` - Script to create separate secrets
- ✅ `GOOGLE_CUSTOM_SEARCH_SETUP.md` - This documentation

## Next Steps

After setup:
1. ✅ Test Multi-Phase mode with citations
2. ✅ Verify citations are generated correctly
3. ✅ Monitor API usage and costs
4. ✅ Update documentation with any environment-specific notes

