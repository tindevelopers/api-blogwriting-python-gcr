# DataForSEO Secrets Setup - Complete ✅

**Date**: 2025-01-20  
**Status**: Secrets added to Google Secret Manager

## What Was Done

### 1. Secrets Added to Secret Manager ✅

**Development Environment:**
- Secret: `blog-writer-env-dev`
- Added: `DATAFORSEO_API_KEY=developer@tin.info`
- Added: `DATAFORSEO_API_SECRET=725ec88e0af0c905`

**Staging Environment:**
- Secret: `blog-writer-env-staging`
- Added: `DATAFORSEO_API_KEY=developer@tin.info`
- Added: `DATAFORSEO_API_SECRET=725ec88e0af0c905`

### 2. Service Account Permissions ✅

Granted `roles/secretmanager.secretAccessor` to:
- `613248238610-compute@developer.gserviceaccount.com` (default compute service account)
- For secrets: `blog-writer-env-dev` and `blog-writer-env-staging`

### 3. Cloud Run Configuration ✅

Cloud Run services are already configured to:
- Mount secrets at `/secrets/env`
- Use secret versions tagged as `latest` (auto-updates)

## Next Steps: Redeploy Services

The secrets are now in Secret Manager, but Cloud Run needs to be redeployed to pick them up:

### Option 1: Trigger via Git Push (Recommended)
```bash
# For dev environment
git push origin develop

# For staging environment  
git push origin staging
```

### Option 2: Manual Redeploy
```bash
# Redeploy dev environment
gcloud run deploy blog-writer-api-dev \
  --region europe-west1 \
  --project api-ai-blog-writer \
  --source .

# Redeploy staging environment
gcloud run deploy blog-writer-api-staging \
  --region europe-west1 \
  --project api-ai-blog-writer \
  --source .
```

### Option 3: Force New Revision (Quick Test)
```bash
# Force Cloud Run to create a new revision (picks up latest secrets)
gcloud run services update blog-writer-api-dev \
  --region europe-west1 \
  --project api-ai-blog-writer \
  --update-env-vars DUMMY=$(date +%s)
```

## Verification

After redeploy, verify the secrets are accessible:

```bash
# Test the enhanced endpoint
curl -X POST https://blog-writer-api-dev-613248238610.europe-west1.run.app/api/v1/keywords/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["pet grooming"],
    "location": "United States",
    "language": "en",
    "max_suggestions_per_keyword": 20
  }'

# Should return 200 OK with search_volume and cpc data (not null)
```

## Expected Results

After redeploy, the API should:
- ✅ Return `200 OK` from `/api/v1/keywords/enhanced` (no more 503)
- ✅ Return real `search_volume` values (not null or 0)
- ✅ Return real `cpc` values (not null or 0)
- ✅ Return `difficulty`, `competition`, and other metrics from DataForSEO

## Troubleshooting

If secrets still don't work after redeploy:

1. **Check secret access:**
   ```bash
   gcloud secrets versions access latest --secret=blog-writer-env-dev --project=api-ai-blog-writer | grep DATAFORSEO
   ```

2. **Check service account permissions:**
   ```bash
   gcloud secrets get-iam-policy blog-writer-env-dev --project=api-ai-blog-writer
   ```

3. **Check Cloud Run logs:**
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=blog-writer-api-dev" \
     --project=api-ai-blog-writer \
     --limit 50
   ```

4. **Verify environment variables are loaded:**
   ```bash
   # Check if the service is reading from /secrets/env
   gcloud run services describe blog-writer-api-dev \
     --region europe-west1 \
     --project api-ai-blog-writer \
     --format="value(spec.template.spec.containers[0].volumeMounts)"
   ```

## Summary

✅ Secrets added to Secret Manager  
✅ Service account has access  
✅ Cloud Run configured to mount secrets  
⏳ **Action Required**: Redeploy Cloud Run services to pick up new secrets

