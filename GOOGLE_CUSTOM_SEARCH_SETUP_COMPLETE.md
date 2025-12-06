# Google Custom Search API Setup - Complete

## ✅ Configuration Complete

Google Custom Search API credentials have been configured in the codebase to enable Multi-Phase mode with citations.

## Changes Made

### 1. Updated `cloudbuild.yaml`

Added Google Custom Search secrets to the `--update-secrets` flag:

```yaml
'--update-secrets', '/secrets/env=blog-writer-env-${_ENV}:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest,STABILITY_AI_API_KEY=STABILITY_AI_API_KEY:latest,GOOGLE_CUSTOM_SEARCH_API_KEY=GOOGLE_CUSTOM_SEARCH_API_KEY:latest,GOOGLE_CUSTOM_SEARCH_ENGINE_ID=GOOGLE_CUSTOM_SEARCH_ENGINE_ID:latest'
```

**What this does:**
- Mounts `GOOGLE_CUSTOM_SEARCH_API_KEY` secret as environment variable `GOOGLE_CUSTOM_SEARCH_API_KEY`
- Mounts `GOOGLE_CUSTOM_SEARCH_ENGINE_ID` secret as environment variable `GOOGLE_CUSTOM_SEARCH_ENGINE_ID`

### 2. Updated `service.yaml`

Added environment variable references for Google Custom Search:

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

**What this does:**
- Reads `GOOGLE_CUSTOM_SEARCH_API_KEY` from `blog-writer-env` secret
- Reads `GOOGLE_CUSTOM_SEARCH_ENGINE_ID` from `blog-writer-env` secret
- Sets them as environment variables in the Cloud Run container

### 3. Created Setup Scripts

#### `scripts/setup-google-custom-search-secrets.sh`
- Adds Google Custom Search credentials to existing `blog-writer-env-{ENV}` secrets
- Preserves existing secret values
- Interactive script with prompts

#### `scripts/create-google-custom-search-secrets.sh`
- Creates separate secrets: `GOOGLE_CUSTOM_SEARCH_API_KEY` and `GOOGLE_CUSTOM_SEARCH_ENGINE_ID`
- Grants Cloud Run service account access
- Alternative approach if you prefer individual secrets

#### `scripts/verify-google-custom-search-setup.sh`
- Verifies secrets exist
- Checks service account permissions
- Validates configuration

### 4. Code Already Configured ✅

The code in `main.py` already reads from environment variables:

```python
google_api_key = os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY")
google_engine_id = os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")
if google_api_key and google_engine_id:
    google_custom_search_client = GoogleCustomSearchClient(
        api_key=google_api_key,
        search_engine_id=google_engine_id
    )
    print("✅ Google Custom Search client initialized.")
```

**No code changes needed** - the environment variables will be automatically available after deployment.

## Next Steps

### Step 1: Create Secrets in Google Secret Manager

**Option A: Add to existing blog-writer-env secret (Recommended)**

```bash
./scripts/setup-google-custom-search-secrets.sh
```

This will:
1. Prompt for API key and Engine ID
2. Add them to `blog-writer-env-dev`, `blog-writer-env-staging`, or `blog-writer-env-prod`
3. Preserve existing secret values

**Option B: Create separate secrets**

```bash
./scripts/create-google-custom-search-secrets.sh
```

This will:
1. Create `GOOGLE_CUSTOM_SEARCH_API_KEY` secret
2. Create `GOOGLE_CUSTOM_SEARCH_ENGINE_ID` secret
3. Grant Cloud Run service account access

### Step 2: Grant Service Account Access

If using Option B (separate secrets), ensure the service account has access:

```bash
PROJECT_ID=$(gcloud config get-value project)
SERVICE_ACCOUNT="blog-writer-service-account@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud secrets add-iam-policy-binding "GOOGLE_CUSTOM_SEARCH_API_KEY" \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding "GOOGLE_CUSTOM_SEARCH_ENGINE_ID" \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"
```

### Step 3: Verify Setup

```bash
./scripts/verify-google-custom-search-setup.sh
```

### Step 4: Deploy

```bash
# Commit changes
git add cloudbuild.yaml service.yaml scripts/ GOOGLE_CUSTOM_SEARCH_SETUP*.md
git commit -m "feat: Configure Google Custom Search API secrets for Multi-Phase mode"
git push origin develop  # Triggers dev deployment
```

### Step 5: Test Multi-Phase Mode

After deployment, test the Multi-Phase mode:

```bash
curl -X POST https://your-api-url/api/v1/blog/generate-enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Using Euras Technology to Fix Leaks",
    "keywords": ["Euras Technology", "leak repair"],
    "mode": "multi_phase",
    "use_citations": true
  }'
```

**Expected:** Should succeed without the "Google Custom Search API is required" error.

## Verification

### Check Cloud Run Logs

```bash
gcloud logging read "resource.type=cloud_run_revision AND textPayload=~'Google Custom Search'" \
    --limit=10 \
    --format="value(timestamp,textPayload)"
```

**Expected output:**
```
✅ Google Custom Search client initialized.
```

### Check Environment Variables

```bash
gcloud run services describe SERVICE_NAME \
    --region=REGION \
    --format="value(spec.template.spec.containers[0].env)"
```

Should show `GOOGLE_CUSTOM_SEARCH_API_KEY` and `GOOGLE_CUSTOM_SEARCH_ENGINE_ID`.

## Troubleshooting

### Secret Not Found

**Error:** `Secret 'GOOGLE_CUSTOM_SEARCH_API_KEY' not found`

**Solution:**
1. Create the secret using one of the setup scripts
2. Verify secret name matches cloudbuild.yaml
3. Check project: `gcloud config get-value project`

### Permission Denied

**Error:** `Permission denied on secret`

**Solution:**
1. Grant service account access (see Step 2)
2. Verify service account: `gcloud run services describe SERVICE_NAME --format="value(spec.template.spec.serviceAccountName)"`
3. Check IAM: `gcloud secrets get-iam-policy SECRET_NAME`

### Still Getting "Not Configured" Error

**Error:** `⚠️ Google Custom Search not configured`

**Solution:**
1. Verify secrets are mounted: Check Cloud Run service configuration
2. Check logs for startup messages
3. Verify environment variables are set: `gcloud run services describe SERVICE_NAME --format="yaml(spec.template.spec.containers[0].env)"`
4. Redeploy after adding secrets

## Files Modified

- ✅ `cloudbuild.yaml` - Added secret mounting
- ✅ `service.yaml` - Added environment variable references
- ✅ `scripts/setup-google-custom-search-secrets.sh` - Setup script (Option A)
- ✅ `scripts/create-google-custom-search-secrets.sh` - Setup script (Option B)
- ✅ `scripts/verify-google-custom-search-setup.sh` - Verification script
- ✅ `GOOGLE_CUSTOM_SEARCH_SETUP.md` - Detailed setup guide
- ✅ `GOOGLE_CUSTOM_SEARCH_SETUP_COMPLETE.md` - This summary

## Summary

✅ **Code Configuration:** Complete - No code changes needed  
✅ **Deployment Configuration:** Complete - cloudbuild.yaml and service.yaml updated  
⏳ **Secret Creation:** Pending - Run setup script to create secrets  
⏳ **Deployment:** Pending - Push to trigger deployment  

Once secrets are created and deployed, Multi-Phase mode will work with citations enabled!

