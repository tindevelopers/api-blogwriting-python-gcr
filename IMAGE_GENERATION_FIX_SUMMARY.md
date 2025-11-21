# Image Generation Fix Summary

## Changes Implemented

### 1. ✅ Updated `cloudbuild.yaml`
- **File**: `cloudbuild.yaml`
- **Change**: Added `STABILITY_AI_API_KEY=STABILITY_AI_API_KEY:latest` to the `--update-secrets` flag
- **Impact**: Cloud Run deployments will now include the Stability AI API key as a secret

**Before:**
```yaml
'--update-secrets', '/secrets/env=blog-writer-env-${_ENV}:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest'
```

**After:**
```yaml
'--update-secrets', '/secrets/env=blog-writer-env-${_ENV}:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest,STABILITY_AI_API_KEY=STABILITY_AI_API_KEY:latest'
```

### 2. ✅ Improved Error Handling in `main.py`
- **File**: `main.py` (lines 987-1070)
- **Changes**:
  - Added `image_generation_warnings` list to track all image generation issues
  - Enhanced error messages to be more descriptive
  - Added specific checks for:
    - Image provider manager initialization
    - Provider availability (with helpful message about missing STABILITY_AI_API_KEY)
    - Individual image generation failures
  - Changed log levels from `warning` to `error` for critical failures
  - Added `exc_info=True` for better stack traces
  - Included warnings in API response

**Key Improvements:**
- Clear error message when `STABILITY_AI_API_KEY` is missing: `"No image providers configured. STABILITY_AI_API_KEY may be missing."`
- Warnings are now returned in the API response `warnings` field
- Better logging with full exception details

### 3. ✅ Created Stability AI Setup Script
- **File**: `scripts/setup-stability-ai-secrets.sh`
- **Purpose**: Automated script to set up Stability AI API key in Google Secret Manager
- **Features**:
  - Creates/updates `STABILITY_AI_API_KEY` secret
  - Grants Cloud Run service account access
  - Updates Cloud Run service to use the secret
  - Provides verification commands
  - Interactive prompt for API key input

## How to Use

### Step 1: Run the Setup Script
```bash
cd scripts
./setup-stability-ai-secrets.sh
```

The script will:
1. Prompt for your Stability AI API key
2. Create/update the secret in Google Secret Manager
3. Grant Cloud Run service account access
4. Update the Cloud Run service configuration

### Step 2: Verify Secret is Created
```bash
gcloud secrets list --project=your-project-id
gcloud secrets versions access latest --secret=STABILITY_AI_API_KEY
```

### Step 3: Deploy Updated Code
The next Cloud Build deployment will automatically include the `STABILITY_AI_API_KEY` secret.

### Step 4: Test Image Generation
```bash
curl -X POST https://your-service.run.app/api/v1/blog/generate-enhanced \
  -H 'Content-Type: application/json' \
  -d '{
    "topic": "Best Products 2025",
    "keywords": ["products"],
    "use_google_search": true
  }'
```

Check the response for:
- `generated_images` array with image URLs
- `warnings` array (should be empty if working correctly)

## Expected Behavior

### Before Fix:
- ❌ Images not generated
- ❌ Silent failures (only in logs)
- ❌ No indication in API response

### After Fix:
- ✅ Images generated for product topics
- ✅ Clear error messages in `warnings` field
- ✅ Helpful messages when API key is missing
- ✅ Better logging for debugging

## Troubleshooting

### Issue: "No image providers configured"
**Solution**: Run `./scripts/setup-stability-ai-secrets.sh` to configure the API key

### Issue: Images still not generating
**Check**:
1. Verify secret exists: `gcloud secrets list`
2. Check service logs: `gcloud run services logs read blog-writer-api-dev --region=europe-west1`
3. Verify topic contains product indicators: "best", "top", "review", "compare", "guide"
4. Ensure `use_google_search: true` in request

### Issue: Secret not accessible
**Solution**: Grant service account access:
```bash
gcloud secrets add-iam-policy-binding STABILITY_AI_API_KEY \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"
```

## Files Modified

1. `cloudbuild.yaml` - Added STABILITY_AI_API_KEY to secrets
2. `main.py` - Improved error handling and warning messages
3. `scripts/setup-stability-ai-secrets.sh` - New setup script

## Next Steps

1. Run the setup script to configure the API key
2. Deploy the updated code
3. Test image generation
4. Monitor logs for any issues

