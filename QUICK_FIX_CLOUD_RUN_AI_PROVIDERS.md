# Quick Fix: Cloud Run AI Provider Configuration

**Date:** 2025-11-13  
**Status:** 🔴 Critical - Required for Enhanced Blog Generation

---

## 🚨 Problem

The enhanced blog generation endpoint is failing with:
```
"All AI providers failed. Last error: [openai] Error code: 401 - Incorrect API key provided"
```

This causes the system to fall back to template-based generation, producing identical, low-quality content.

---

## ✅ Quick Fix (5 Minutes)

### Step 1: Run the Setup Script

```bash
# Set your project details
export GOOGLE_CLOUD_PROJECT="api-ai-blog-writer"
export REGION="europe-west1"
export SERVICE_NAME="blog-writer-api-dev"

# Run the automated setup script
./scripts/setup-ai-provider-secrets.sh
```

The script will:
1. Prompt for your OpenAI API key
2. Prompt for your Anthropic API key  
3. Create secrets in Secret Manager
4. Grant Cloud Run access
5. Update the service

### Step 2: Verify It Works

```bash
# Test the enhanced endpoint
curl -X POST "https://blog-writer-api-dev-613248238610.europe-west1.run.app/api/v1/blog/generate-enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Test Blog Post",
    "keywords": ["test"],
    "use_google_search": true,
    "use_citations": true
  }'
```

**Expected:** High-quality AI-generated content with proper structure  
**If still failing:** Check logs with `gcloud run services logs read blog-writer-api-dev --region=europe-west1`

---

## 📋 Manual Setup (If Script Doesn't Work)

### 1. Create Secrets

```bash
# OpenAI
echo -n "sk-your-openai-key-here" | gcloud secrets create OPENAI_API_KEY \
  --data-file=- \
  --replication-policy="automatic" \
  --project=api-ai-blog-writer

# Anthropic  
echo -n "sk-ant-your-anthropic-key-here" | gcloud secrets create ANTHROPIC_API_KEY \
  --data-file=- \
  --replication-policy="automatic" \
  --project=api-ai-blog-writer
```

### 2. Grant Access

```bash
# Get service account
SERVICE_ACCOUNT=$(gcloud run services describe blog-writer-api-dev \
  --region=europe-west1 \
  --project=api-ai-blog-writer \
  --format="value(spec.template.spec.serviceAccountName)")

# Grant access
gcloud secrets add-iam-policy-binding OPENAI_API_KEY \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor" \
  --project=api-ai-blog-writer

gcloud secrets add-iam-policy-binding ANTHROPIC_API_KEY \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor" \
  --project=api-ai-blog-writer
```

### 3. Update Cloud Run Service

```bash
gcloud run services update blog-writer-api-dev \
  --region=europe-west1 \
  --project=api-ai-blog-writer \
  --update-secrets=OPENAI_API_KEY=OPENAI_API_KEY:latest \
  --update-secrets=ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest
```

---

## 🔍 Verification Checklist

- [ ] Secrets created: `gcloud secrets list | grep -E "OPENAI|ANTHROPIC"`
- [ ] Service account has access: `gcloud secrets get-iam-policy OPENAI_API_KEY`
- [ ] Service updated: `gcloud run services describe blog-writer-api-dev --region=europe-west1`
- [ ] Test endpoint returns quality_score > 80
- [ ] Content has proper H1/H2 structure
- [ ] Citations are present

---

## 📝 Notes

- **At least ONE** provider (OpenAI OR Anthropic) is required
- **Both** providers recommended for best quality (4-stage pipeline uses both)
- Secrets are stored securely in Google Secret Manager
- Service will restart automatically after update
- Changes take effect immediately

---

**Last Updated:** 2025-11-13  
**Status:** ✅ Ready to Execute

