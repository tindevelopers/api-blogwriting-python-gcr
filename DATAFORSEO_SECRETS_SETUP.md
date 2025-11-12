# DataForSEO Secrets Setup Guide

This guide explains how to add DataForSEO API credentials to Google Secret Manager for all environments.

## Prerequisites

- Google Cloud SDK (`gcloud`) installed and authenticated
- Access to the `api-ai-blog-writer` project
- DataForSEO API credentials (API Key and API Secret)

## Quick Setup

### Option 1: Using the Automated Script

```bash
# Run the setup script
./scripts/add-dataforseo-secrets.sh
```

The script will:
1. Prompt you for your DataForSEO API Key and Secret
2. Add them to all environment secrets (dev, staging, production)
3. Create new secret versions with the updated values

### Option 2: Manual Setup via gcloud CLI

#### For Dev Environment

```bash
# Get current secret value
CURRENT_JSON=$(gcloud secrets versions access latest --secret=blog-writer-env-dev --project=api-ai-blog-writer)

# Update with DataForSEO credentials
UPDATED_JSON=$(echo "$CURRENT_JSON" | jq '. + {
  "DATAFORSEO_API_KEY": "your-api-key-here",
  "DATAFORSEO_API_SECRET": "your-api-secret-here"
}')

# Create new version
echo "$UPDATED_JSON" | gcloud secrets versions add blog-writer-env-dev \
  --data-file=- \
  --project=api-ai-blog-writer
```

#### For Staging Environment

```bash
CURRENT_JSON=$(gcloud secrets versions access latest --secret=blog-writer-env-staging --project=api-ai-blog-writer)
UPDATED_JSON=$(echo "$CURRENT_JSON" | jq '. + {
  "DATAFORSEO_API_KEY": "your-api-key-here",
  "DATAFORSEO_API_SECRET": "your-api-secret-here"
}')
echo "$UPDATED_JSON" | gcloud secrets versions add blog-writer-env-staging \
  --data-file=- \
  --project=api-ai-blog-writer
```

#### For Production Environment

```bash
CURRENT_JSON=$(gcloud secrets versions access latest --secret=blog-writer-env-prod --project=api-ai-blog-writer)
UPDATED_JSON=$(echo "$CURRENT_JSON" | jq '. + {
  "DATAFORSEO_API_KEY": "your-api-key-here",
  "DATAFORSEO_API_SECRET": "your-api-secret-here"
}')
echo "$UPDATED_JSON" | gcloud secrets versions add blog-writer-env-prod \
  --data-file=- \
  --project=api-ai-blog-writer
```

## Verify Secrets

After adding the secrets, verify they're accessible:

```bash
# Check dev secrets
gcloud secrets versions access latest --secret=blog-writer-env-dev --project=api-ai-blog-writer | jq '.DATAFORSEO_API_KEY'

# Check staging secrets
gcloud secrets versions access latest --secret=blog-writer-env-staging --project=api-ai-blog-writer | jq '.DATAFORSEO_API_KEY'

# Check production secrets
gcloud secrets versions access latest --secret=blog-writer-env-prod --project=api-ai-blog-writer | jq '.DATAFORSEO_API_KEY'
```

## Deployment

After adding secrets, redeploy each environment to pick up the new credentials:

1. **Dev**: Push to `develop` branch (auto-deploys)
2. **Staging**: Push to `staging` branch (auto-deploys)
3. **Production**: Push to `main` branch (auto-deploys)

Or trigger manual deployments via GitHub Actions workflow_dispatch.

## Verify DataForSEO is Working

After deployment, test the enhanced keywords endpoint:

```bash
# Dev
curl -X POST https://blog-writer-api-dev-613248238610.europe-west1.run.app/api/v1/keywords/enhanced \
  -H "Content-Type: application/json" \
  -d '{"keywords":["ai content generation"],"location":"United States","language":"en"}'

# Staging
curl -X POST https://blog-writer-api-staging-613248238610.europe-west1.run.app/api/v1/keywords/enhanced \
  -H "Content-Type: application/json" \
  -d '{"keywords":["ai content generation"],"location":"United States","language":"en"}'

# Production
curl -X POST https://blog-writer-api-prod-613248238610.us-east1.run.app/api/v1/keywords/enhanced \
  -H "Content-Type: application/json" \
  -d '{"keywords":["ai content generation"],"location":"United States","language":"en"}'
```

You should see real DataForSEO data (search volume, difficulty, CPC, etc.) instead of a 503 error.

## Troubleshooting

### Secret Not Found Error

If you get "secret not found", create the secret first:

```bash
# Create empty JSON secret
echo '{}' | gcloud secrets create blog-writer-env-dev --data-file=- --project=api-ai-blog-writer
```

### Secrets Not Loading in Container

- Verify the secret file exists: Check Cloud Run logs for "Loading secrets from /secrets/env"
- Ensure `jq` is installed in the Docker image (it's included in the Dockerfile)
- Check that the secret mount path matches: `/secrets/env`

### Still Getting 503 Errors

- Verify secrets were added correctly: `gcloud secrets versions access latest --secret=blog-writer-env-dev --project=api-ai-blog-writer | jq`
- Check Cloud Run logs for initialization errors
- Ensure the service account has `secretAccessor` role on the secrets

## Security Notes

- Never commit API keys to git
- Use Google Secret Manager for all sensitive credentials
- Rotate secrets regularly
- Use different credentials for dev/staging/prod if possible
- Monitor secret access via Cloud Audit Logs

