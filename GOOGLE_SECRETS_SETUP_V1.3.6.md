# Google Secrets Manager Setup v1.3.6

**Date:** 2025-11-23  
**Status:** ✅ Complete Guide

---

## 🎯 Overview

This guide explains how to configure Google Secrets Manager with DataForSEO credentials so the backend can generate blog content.

---

## 📋 Required Secrets

The backend requires these secrets in Google Secret Manager:

### DataForSEO Credentials
- `DATAFORSEO_API_KEY` - DataForSEO API username/login
- `DATAFORSEO_API_SECRET` - DataForSEO API password/secret

### AI Provider Credentials (for fallback)
- `OPENAI_API_KEY` - OpenAI API key (optional, for pipeline fallback)
- `ANTHROPIC_API_KEY` - Anthropic API key (optional, for pipeline fallback)

---

## 🔧 Setup Steps

### Step 1: Identify Your Project and Secrets

```bash
# Set your project ID
PROJECT_ID="api-ai-blog-writer"  # Update with your actual project ID

# Secret names for each environment
DEV_SECRET="blog-writer-env-dev"
STAGING_SECRET="blog-writer-env-staging"
PROD_SECRET="blog-writer-env-prod"
```

### Step 2: Add DataForSEO Credentials to Secrets

#### Option A: Using the Automated Script

```bash
# Run the setup script
cd /Users/gene/Projects/api-blogwriting-python-gcr
./scripts/add-dataforseo-secrets.sh
```

The script will:
1. Prompt for DataForSEO API Key and Secret
2. Add them to all environment secrets (dev, staging, production)
3. Create new secret versions with the updated values

#### Option B: Manual Setup via gcloud CLI

**For Dev Environment:**

```bash
PROJECT_ID="api-ai-blog-writer"
SECRET_NAME="blog-writer-env-dev"

# Get current secret value (JSON format)
CURRENT_JSON=$(gcloud secrets versions access latest \
  --secret=$SECRET_NAME \
  --project=$PROJECT_ID)

# Update with DataForSEO credentials
UPDATED_JSON=$(echo "$CURRENT_JSON" | jq '. + {
  "DATAFORSEO_API_KEY": "your-api-key-here",
  "DATAFORSEO_API_SECRET": "your-api-secret-here"
}')

# Create new version
echo "$UPDATED_JSON" | gcloud secrets versions add $SECRET_NAME \
  --data-file=- \
  --project=$PROJECT_ID

echo "✅ Dev secrets updated"
```

**For Staging Environment:**

```bash
PROJECT_ID="api-ai-blog-writer"
SECRET_NAME="blog-writer-env-staging"

CURRENT_JSON=$(gcloud secrets versions access latest \
  --secret=$SECRET_NAME \
  --project=$PROJECT_ID)

UPDATED_JSON=$(echo "$CURRENT_JSON" | jq '. + {
  "DATAFORSEO_API_KEY": "your-api-key-here",
  "DATAFORSEO_API_SECRET": "your-api-secret-here"
}')

echo "$UPDATED_JSON" | gcloud secrets versions add $SECRET_NAME \
  --data-file=- \
  --project=$PROJECT_ID

echo "✅ Staging secrets updated"
```

**For Production Environment:**

```bash
PROJECT_ID="api-ai-blog-writer"
SECRET_NAME="blog-writer-env-prod"

CURRENT_JSON=$(gcloud secrets versions access latest \
  --secret=$SECRET_NAME \
  --project=$PROJECT_ID)

UPDATED_JSON=$(echo "$CURRENT_JSON" | jq '. + {
  "DATAFORSEO_API_KEY": "your-api-key-here",
  "DATAFORSEO_API_SECRET": "your-api-secret-here"
}')

echo "$UPDATED_JSON" | gcloud secrets versions add $SECRET_NAME \
  --data-file=- \
  --project=$PROJECT_ID

echo "✅ Production secrets updated"
```

---

## ✅ Verify Secrets

After adding secrets, verify they're accessible:

```bash
PROJECT_ID="api-ai-blog-writer"

# Check dev secrets
echo "Dev Environment:"
gcloud secrets versions access latest \
  --secret=blog-writer-env-dev \
  --project=$PROJECT_ID | jq '.DATAFORSEO_API_KEY, .DATAFORSEO_API_SECRET'

# Check staging secrets
echo "Staging Environment:"
gcloud secrets versions access latest \
  --secret=blog-writer-env-staging \
  --project=$PROJECT_ID | jq '.DATAFORSEO_API_KEY, .DATAFORSEO_API_SECRET'

# Check production secrets
echo "Production Environment:"
gcloud secrets versions access latest \
  --secret=blog-writer-env-prod \
  --project=$PROJECT_ID | jq '.DATAFORSEO_API_KEY, .DATAFORSEO_API_SECRET'
```

---

## 🔐 Grant Service Account Access

Ensure the Cloud Run service account has access to the secrets:

```bash
PROJECT_ID="api-ai-blog-writer"
SERVICE_ACCOUNT="blog-writer-service-account@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant access to dev secrets
gcloud secrets add-iam-policy-binding blog-writer-env-dev \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT_ID

# Grant access to staging secrets
gcloud secrets add-iam-policy-binding blog-writer-env-staging \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT_ID

# Grant access to production secrets
gcloud secrets add-iam-policy-binding blog-writer-env-prod \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT_ID
```

---

## 🚀 Deployment Configuration

The backend is configured to load secrets from Google Secret Manager:

### How Secrets Are Loaded

1. **Cloud Run mounts secrets** at `/secrets/env` (configured in `cloudbuild.yaml`)
2. **Backend loads secrets** in `load_env_from_secrets()` function (line 426-456 in `main.py`)
3. **DataForSEO client initialized** with credentials from environment (line 557-583 in `main.py`)

### Cloud Build Configuration

The `cloudbuild.yaml` file includes:

```yaml
--update-secrets: '/secrets/env=blog-writer-env-${_ENV}:latest'
```

This mounts the secret file at `/secrets/env` in the container.

### Backend Code Reference

The backend loads secrets in this order:

1. **From mounted secret file** (`/secrets/env`) - Line 426-456
2. **From environment variables** - Fallback if secret file not found
3. **Initialize DataForSEO client** - Line 557-583

```python
# Load secrets from mounted file
load_env_from_secrets()

# Get credentials from environment
dataforseo_api_key = os.getenv("DATAFORSEO_API_KEY")
dataforseo_api_secret = os.getenv("DATAFORSEO_API_SECRET")

# Initialize DataForSEO client
if dataforseo_api_key and dataforseo_api_secret:
    dataforseo_client_global = DataForSEOClient(
        api_key=dataforseo_api_key,
        api_secret=dataforseo_api_secret,
        ...
    )
```

---

## 🔄 Deploy After Adding Secrets

After adding secrets, redeploy the service:

### Option 1: Automatic Deployment (Recommended)

Push to the appropriate branch:
- **Dev**: Push to `develop` branch → Auto-deploys
- **Staging**: Push to `staging` branch → Auto-deploys  
- **Production**: Push to `main` branch → Auto-deploys

### Option 2: Manual Deployment

```bash
# Deploy dev environment
gcloud run deploy blog-writer-api-dev \
  --image gcr.io/$PROJECT_ID/blog-writer-sdk:latest \
  --region europe-west1 \
  --update-secrets /secrets/env=blog-writer-env-dev:latest \
  --project=$PROJECT_ID
```

---

## ✅ Verification

After deployment, verify the backend is loading secrets:

### 1. Check Cloud Run Logs

```bash
# View startup logs
gcloud logging read "resource.type=cloud_run_revision AND \
  resource.labels.service_name=blog-writer-api-dev" \
  --limit 50 \
  --format json | jq '.[] | select(.textPayload | contains("DataForSEO"))'
```

Look for:
- ✅ `✅ Environment variables loaded from secrets: X set`
- ✅ `✅ DataForSEO Labs client initialized.`
- ❌ `⚠️ DataForSEO Labs not configured` (indicates missing credentials)

### 2. Test the Endpoint

```bash
curl -X POST https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/generate-enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Introduction to Python",
    "keywords": ["python", "programming"],
    "blog_type": "tutorial",
    "length": "short"
  }'
```

**Expected Response:**
- HTTP 200 status
- `content` field with > 50 characters
- `total_tokens` > 0
- `generation_time` > 1 second

**If Empty Content:**
- Check logs for: `DataForSEO Content Generation not configured`
- Verify secrets are accessible
- Check service account permissions

---

## 🐛 Troubleshooting

### Issue: Secrets Not Loading

**Symptoms:**
- Log shows: `⚠️ No secrets file found at /secrets/env`
- DataForSEO client not initialized

**Solutions:**
1. Verify secret exists:
   ```bash
   gcloud secrets versions access latest --secret=blog-writer-env-dev --project=$PROJECT_ID
   ```

2. Check Cloud Run service configuration:
   ```bash
   gcloud run services describe blog-writer-api-dev \
     --region=europe-west1 \
     --project=$PROJECT_ID \
     --format="yaml(spec.template.spec.containers[0].volumeMounts)"
   ```

3. Verify service account has access:
   ```bash
   gcloud secrets get-iam-policy blog-writer-env-dev \
     --project=$PROJECT_ID
   ```

### Issue: Empty Content Generation

**Symptoms:**
- HTTP 200 but `content` field is empty
- `total_tokens: 0`

**Solutions:**
1. Check logs for DataForSEO errors:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND \
     textPayload=~'DataForSEO'" \
     --limit 20
   ```

2. Verify credentials are correct:
   ```bash
   # Test credentials directly
   gcloud secrets versions access latest \
     --secret=blog-writer-env-dev \
     --project=$PROJECT_ID | jq '.DATAFORSEO_API_KEY'
   ```

3. Check DataForSEO subscription status:
   - Ensure DataForSEO Content Generation API subscription is active
   - Verify API key has access to Content Generation endpoints

### Issue: Permission Denied

**Symptoms:**
- Error: `Permission denied on secret`

**Solutions:**
1. Grant service account access:
   ```bash
   SERVICE_ACCOUNT="blog-writer-service-account@${PROJECT_ID}.iam.gserviceaccount.com"
   gcloud secrets add-iam-policy-binding blog-writer-env-dev \
     --member="serviceAccount:${SERVICE_ACCOUNT}" \
     --role="roles/secretmanager.secretAccessor" \
     --project=$PROJECT_ID
   ```

2. Verify service account exists:
   ```bash
   gcloud iam service-accounts describe ${SERVICE_ACCOUNT} --project=$PROJECT_ID
   ```

---

## 📝 Secret Format

Secrets should be stored as **JSON** in Google Secret Manager:

```json
{
  "DATAFORSEO_API_KEY": "your-api-key",
  "DATAFORSEO_API_SECRET": "your-api-secret",
  "OPENAI_API_KEY": "your-openai-key",
  "ANTHROPIC_API_KEY": "your-anthropic-key"
}
```

The backend's `load_env_from_secrets()` function parses this JSON and loads it as environment variables.

---

## 🔒 Security Best Practices

1. **Never commit secrets to git**
2. **Use different credentials for dev/staging/prod** if possible
3. **Rotate secrets regularly**
4. **Monitor secret access** via Cloud Audit Logs
5. **Use least privilege** - Only grant `secretAccessor` role
6. **Enable secret versioning** - Keep history of secret changes

---

## 📚 Related Documentation

- `DATAFORSEO_SECRETS_SETUP.md` - Original setup guide
- `CREDENTIALS_LOCATION.md` - Where credentials are needed
- `CONTENT_GENERATION_FIX_V1.3.6.md` - Content generation fixes

---

## ✅ Checklist

- [ ] DataForSEO API credentials obtained
- [ ] Secrets added to Google Secret Manager for all environments
- [ ] Service account has `secretAccessor` role
- [ ] Secrets verified with `gcloud secrets versions access`
- [ ] Service redeployed after adding secrets
- [ ] Cloud Run logs show secrets loading successfully
- [ ] Endpoint tested and returns content (not empty)
- [ ] `total_tokens` > 0 in response

---

**Last Updated:** 2025-11-23

