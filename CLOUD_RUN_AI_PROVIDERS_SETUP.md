# Cloud Run AI Provider Setup Guide

**Date:** 2025-11-13  
**Purpose:** Configure OpenAI and Anthropic API keys in Google Cloud Run  
**Critical:** Required for enhanced blog generation endpoint to work

---

## 🚨 Problem

The enhanced blog generation endpoint (`/api/v1/blog/generate-enhanced`) requires AI providers to be configured. Without them, the system falls back to template-based generation, producing identical, low-quality content.

**Error you might see:**
```json
{
  "error": "All AI providers failed. Last error: [openai] Error code: 401 - Incorrect API key provided"
}
```

---

## ✅ Solution: Setup AI Provider Secrets

### Option 1: Automated Setup (Recommended)

Run the setup script:

```bash
# Set your project and service details
export GOOGLE_CLOUD_PROJECT="api-ai-blog-writer"
export REGION="europe-west1"
export SERVICE_NAME="blog-writer-api-dev"

# Run the setup script
./scripts/setup-ai-provider-secrets.sh
```

The script will:
1. Prompt for OpenAI API key
2. Prompt for Anthropic API key
3. Create secrets in Secret Manager
4. Grant Cloud Run service account access
5. Update Cloud Run service to use secrets

### Option 2: Manual Setup

#### Step 1: Create Secrets in Secret Manager

**OpenAI API Key:**
```bash
# Get your API key from: https://platform.openai.com/account/api-keys
echo -n "your-openai-api-key-here" | gcloud secrets create OPENAI_API_KEY \
  --data-file=- \
  --replication-policy="automatic" \
  --project=api-ai-blog-writer
```

**Anthropic API Key:**
```bash
# Get your API key from: https://console.anthropic.com/settings/keys
echo -n "your-anthropic-api-key-here" | gcloud secrets create ANTHROPIC_API_KEY \
  --data-file=- \
  --replication-policy="automatic" \
  --project=api-ai-blog-writer
```

#### Step 2: Grant Cloud Run Access

```bash
# Get the service account
SERVICE_ACCOUNT=$(gcloud run services describe blog-writer-api-dev \
  --region=europe-west1 \
  --project=api-ai-blog-writer \
  --format="value(spec.template.spec.serviceAccountName)")

# Grant access to OpenAI secret
gcloud secrets add-iam-policy-binding OPENAI_API_KEY \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor" \
  --project=api-ai-blog-writer

# Grant access to Anthropic secret
gcloud secrets add-iam-policy-binding ANTHROPIC_API_KEY \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor" \
  --project=api-ai-blog-writer
```

#### Step 3: Update Cloud Run Service

```bash
gcloud run services update blog-writer-api-dev \
  --region=europe-west1 \
  --project=api-ai-blog-writer \
  --update-secrets=OPENAI_API_KEY=OPENAI_API_KEY:latest \
  --update-secrets=ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest
```

---

## 🔍 Verification

### Check Secrets Exist

```bash
gcloud secrets list --project=api-ai-blog-writer --filter="name:OPENAI_API_KEY OR name:ANTHROPIC_API_KEY"
```

Should show:
```
NAME                CREATED              REPLICATION_POLICY
ANTHROPIC_API_KEY   2025-11-13T...      automatic
OPENAI_API_KEY      2025-11-13T...      automatic
```

### Check Service Configuration

```bash
gcloud run services describe blog-writer-api-dev \
  --region=europe-west1 \
  --project=api-ai-blog-writer \
  --format="yaml(spec.template.spec.containers[0].env)"
```

Should show secrets referenced:
```yaml
env:
- name: OPENAI_API_KEY
  valueFrom:
    secretKeyRef:
      name: OPENAI_API_KEY
      key: latest
- name: ANTHROPIC_API_KEY
  valueFrom:
    secretKeyRef:
      name: ANTHROPIC_API_KEY
      key: latest
```

### Test Enhanced Endpoint

```bash
curl -X POST "https://blog-writer-api-dev-613248238610.europe-west1.run.app/api/v1/blog/generate-enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Best Notary Services in California",
    "keywords": ["notary services", "california notary"],
    "tone": "professional",
    "length": "medium",
    "use_google_search": true,
    "use_fact_checking": true,
    "use_citations": true,
    "use_serp_optimization": true,
    "use_knowledge_graph": true,
    "use_semantic_keywords": true,
    "use_quality_scoring": true
  }'
```

**Expected Success Response:**
```json
{
  "title": "...",
  "content": "# Proper H1\n\n## Proper H2 sections...",
  "quality_score": 85.5,
  "total_tokens": 5000,
  "stage_results": [...],
  "citations": [...],
  "success": true
}
```

**If Still Failing:**
- Check service logs: `gcloud run services logs read blog-writer-api-dev --region=europe-west1`
- Verify secrets are accessible: `gcloud secrets versions access latest --secret=OPENAI_API_KEY`

---

## 📋 Requirements

### Minimum Configuration

**At least ONE** of these must be configured:
- ✅ OpenAI API Key (for GPT-4o, GPT-4o-mini)
- ✅ Anthropic API Key (for Claude 3.5 Sonnet)

### Recommended Configuration

**Both** configured for best quality:
- ✅ OpenAI API Key (Stage 2: Draft, Stage 4: SEO)
- ✅ Anthropic API Key (Stage 1: Research, Stage 3: Enhancement)

---

## 🔧 Troubleshooting

### Issue: "All AI providers failed"

**Cause:** Secrets not configured or not accessible

**Fix:**
1. Verify secrets exist: `gcloud secrets list`
2. Check service account has access: `gcloud secrets get-iam-policy OPENAI_API_KEY`
3. Verify service is using secrets: `gcloud run services describe ...`

### Issue: "401 Unauthorized"

**Cause:** Invalid API key

**Fix:**
1. Verify API key is correct
2. Check API key hasn't expired
3. Regenerate API key if needed

### Issue: "Secret not found"

**Cause:** Secret name mismatch or wrong project

**Fix:**
1. Check secret name: `gcloud secrets list`
2. Verify project: `gcloud config get-value project`
3. Create secret if missing

---

## 🚀 Quick Commands Reference

```bash
# Setup (one-time)
./scripts/setup-ai-provider-secrets.sh

# Update existing secret
echo -n "new-api-key" | gcloud secrets versions add OPENAI_API_KEY --data-file=-

# Check service configuration
gcloud run services describe blog-writer-api-dev --region=europe-west1 --format="yaml(spec.template.spec.containers[0].env)"

# View logs
gcloud run services logs read blog-writer-api-dev --region=europe-west1 --limit=50

# Test endpoint
curl -X POST "https://blog-writer-api-dev-613248238610.europe-west1.run.app/api/v1/blog/generate-enhanced" \
  -H "Content-Type: application/json" \
  -d '{"topic":"Test","keywords":["test"],"use_google_search":true}'
```

---

## 📝 Notes

- Secrets are stored in Google Secret Manager (secure, encrypted)
- Secrets are automatically replicated across regions
- Service account must have `roles/secretmanager.secretAccessor` role
- Cloud Run service must reference secrets in environment variables
- Changes take effect immediately after service update

---

**Last Updated:** 2025-11-13  
**Status:** ✅ Ready to Execute

