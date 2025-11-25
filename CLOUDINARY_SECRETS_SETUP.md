# Cloudinary Credentials Setup in Google Secret Manager

**Date:** 2025-11-25  
**Status:** ✅ Ready to configure

---

## Overview

Yes, **Cloudinary credentials should be stored in Google Secret Manager** for secure credential management in Cloud Run deployments. The application is already configured to load these credentials automatically.

---

## How It Works

### 1. **Secret Storage**
- Cloudinary credentials are stored in Google Secret Manager as part of the environment secret
- Secret name: `blog-writer-env-{env}` (e.g., `blog-writer-env-dev`, `blog-writer-env-staging`, `blog-writer-env-prod`)
- Format: JSON object with all environment variables

### 2. **Automatic Loading**
- Cloud Run mounts the secret file at `/secrets/env` during deployment
- Backend automatically loads secrets in `load_env_from_secrets()` function (line 426 in `main.py`)
- Cloudinary credentials are read from environment variables:
  - `CLOUDINARY_CLOUD_NAME`
  - `CLOUDINARY_API_KEY`
  - `CLOUDINARY_API_SECRET`
  - `CLOUDINARY_FOLDER` (optional, default: `blog-content`)

### 3. **Code Reference**
The `CloudinaryStorage` class automatically reads from environment:

```python
# src/blog_writer_sdk/integrations/media_storage.py (line 70-73)
self.cloud_name = cloud_name or os.getenv("CLOUDINARY_CLOUD_NAME")
self.api_key = api_key or os.getenv("CLOUDINARY_API_KEY")
self.api_secret = api_secret or os.getenv("CLOUDINARY_API_SECRET")
self.default_folder = default_folder or os.getenv("CLOUDINARY_FOLDER", "blog-content")
```

---

## Adding Cloudinary Credentials

### Option 1: Using the Script (Recommended)

```bash
# Add to dev environment
./scripts/add-cloudinary-secrets.sh dev

# Add to staging environment
./scripts/add-cloudinary-secrets.sh staging

# Add to production environment
./scripts/add-cloudinary-secrets.sh prod
```

The script will:
1. Fetch current secret
2. Prompt for Cloudinary credentials
3. Update the secret in Google Secret Manager
4. Preserve existing values if you press Enter

### Option 2: Manual Update via gcloud

```bash
# 1. Get current secret
gcloud secrets versions access latest \
  --secret=blog-writer-env-dev \
  --project=api-ai-blog-writer > current-secret.json

# 2. Edit JSON file to add Cloudinary credentials
# Add these fields:
# {
#   "CLOUDINARY_CLOUD_NAME": "your_cloud_name",
#   "CLOUDINARY_API_KEY": "your_api_key",
#   "CLOUDINARY_API_SECRET": "your_api_secret",
#   "CLOUDINARY_FOLDER": "blog-content"
# }

# 3. Update secret
gcloud secrets versions add blog-writer-env-dev \
  --data-file=current-secret.json \
  --project=api-ai-blog-writer

# 4. Clean up
rm current-secret.json
```

### Option 3: Using Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to **Secret Manager**
3. Select secret: `blog-writer-env-dev` (or staging/prod)
4. Click **Add New Version**
5. Paste JSON with Cloudinary credentials:
   ```json
   {
     "CLOUDINARY_CLOUD_NAME": "your_cloud_name",
     "CLOUDINARY_API_KEY": "your_api_key",
     "CLOUDINARY_API_SECRET": "your_api_secret",
     "CLOUDINARY_FOLDER": "blog-content"
   }
   ```
6. Click **Add Version**

---

## Secret JSON Structure

The secret should include Cloudinary credentials along with other environment variables:

```json
{
  "DATAFORSEO_API_KEY": "...",
  "DATAFORSEO_API_SECRET": "...",
  "CLOUDINARY_CLOUD_NAME": "your_cloud_name",
  "CLOUDINARY_API_KEY": "123456789012345",
  "CLOUDINARY_API_SECRET": "abcdefghijklmnopqrstuvwxyz",
  "CLOUDINARY_FOLDER": "blog-content",
  "OPENAI_API_KEY": "...",
  "ANTHROPIC_API_KEY": "...",
  ...
}
```

---

## Verification

### Check if Credentials Are Loaded

After deployment, check Cloud Run logs:

```bash
gcloud run services logs read blog-writer-api-dev \
  --region=europe-west9 \
  --project=api-ai-blog-writer \
  --limit=50 | grep -i cloudinary
```

**Expected:** No errors about missing Cloudinary credentials

### Test Image Upload

```bash
# Run the test script
./test_image_generation_cloudinary.sh
```

**Expected:** Image uploads successfully to Cloudinary

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CLOUDINARY_CLOUD_NAME` | ✅ Yes | - | Your Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | ✅ Yes | - | Your Cloudinary API key |
| `CLOUDINARY_API_SECRET` | ✅ Yes | - | Your Cloudinary API secret |
| `CLOUDINARY_FOLDER` | ❌ No | `blog-content` | Default folder for uploads |

---

## Security Best Practices

1. ✅ **Use Secret Manager** - Never commit credentials to code
2. ✅ **Separate Environments** - Use different secrets for dev/staging/prod
3. ✅ **Least Privilege** - Only grant secret access to service accounts that need it
4. ✅ **Rotation** - Rotate credentials periodically
5. ✅ **Audit** - Monitor secret access via Cloud Audit Logs

---

## Service Account Permissions

Ensure the Cloud Run service account has access to secrets:

```bash
PROJECT_ID="api-ai-blog-writer"
SERVICE_ACCOUNT="blog-writer-service-account@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant access to dev secrets
gcloud secrets add-iam-policy-binding blog-writer-env-dev \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT_ID

# Repeat for staging and prod
gcloud secrets add-iam-policy-binding blog-writer-env-staging \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT_ID

gcloud secrets add-iam-policy-binding blog-writer-env-prod \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT_ID
```

---

## Deployment

After adding credentials to Secret Manager:

1. **Automatic:** Next deployment will automatically load the new credentials
2. **Manual Restart:** To apply immediately without redeploying:
   ```bash
   gcloud run services update blog-writer-api-dev \
     --region=europe-west9 \
     --project=api-ai-blog-writer
   ```

---

## Troubleshooting

### Issue: "Cloudinary cloud_name, api_key, and api_secret are required"

**Cause:** Credentials not loaded from Secret Manager

**Solutions:**
1. Verify credentials are in Secret Manager
2. Check service account has `secretmanager.secretAccessor` role
3. Verify secret is mounted at `/secrets/env` in Cloud Build config
4. Check logs for secret loading errors

### Issue: Credentials not updating

**Cause:** Individual environment variables may override secret values

**Solution:** The code now prioritizes volume-mounted secrets for Cloudinary (same as DataForSEO)

---

## Related Files

- `scripts/add-cloudinary-secrets.sh` - Script to add credentials
- `src/blog_writer_sdk/integrations/media_storage.py` - Cloudinary integration
- `main.py` (line 426-496) - Secret loading function
- `cloudbuild.yaml` - Cloud Build secret mounting config

---

## Next Steps

1. ✅ Add Cloudinary credentials to Secret Manager using the script
2. ✅ Verify credentials are loaded (check logs)
3. ✅ Test image upload endpoint
4. ✅ Deploy to staging/production

---

**Status:** Ready to configure Cloudinary credentials in Secret Manager!

