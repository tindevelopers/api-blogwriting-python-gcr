# Secrets Verification Guide v1.3.6

**Date:** 2025-11-23  
**Status:** ✅ Complete Verification Guide

---

## 🎯 Quick Verification

Run these commands to verify secrets are configured correctly:

```bash
PROJECT_ID="api-ai-blog-writer"

# 1. Check if secrets exist
echo "Checking secrets..."
gcloud secrets list --project=$PROJECT_ID | grep blog-writer-env

# 2. Verify DataForSEO credentials are in secrets
echo ""
echo "Dev Environment:"
gcloud secrets versions access latest \
  --secret=blog-writer-env-dev \
  --project=$PROJECT_ID | jq '.DATAFORSEO_API_KEY, .DATAFORSEO_API_SECRET' | head -2

echo ""
echo "Staging Environment:"
gcloud secrets versions access latest \
  --secret=blog-writer-env-staging \
  --project=$PROJECT_ID | jq '.DATAFORSEO_API_KEY, .DATAFORSEO_API_SECRET' | head -2

echo ""
echo "Production Environment:"
gcloud secrets versions access latest \
  --secret=blog-writer-env-prod \
  --project=$PROJECT_ID | jq '.DATAFORSEO_API_KEY, .DATAFORSEO_API_SECRET' | head -2
```

---

## ✅ Expected Results

### Secrets Should Exist:
- ✅ `blog-writer-env-dev`
- ✅ `blog-writer-env-staging`
- ✅ `blog-writer-env-prod`

### Secrets Should Contain:
- ✅ `DATAFORSEO_API_KEY` - Non-empty value
- ✅ `DATAFORSEO_API_SECRET` - Non-empty value
- ✅ `OPENAI_API_KEY` - Optional (for fallback)
- ✅ `ANTHROPIC_API_KEY` - Optional (for fallback)

---

## 🔍 Backend Verification

### Check Cloud Run Logs

```bash
# View startup logs
gcloud logging read "resource.type=cloud_run_revision AND \
  resource.labels.service_name=blog-writer-api-dev AND \
  textPayload=~'secrets|DataForSEO'" \
  --limit 50 \
  --format json | jq -r '.[] | .textPayload'
```

**Look for:**
- ✅ `✅ Environment variables loaded from secrets: X set`
- ✅ `✅ DataForSEO Labs client initialized.`
- ❌ `⚠️ DataForSEO Labs not configured` (indicates missing credentials)

---

## 🧪 Test Endpoint

```bash
curl -X POST https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/generate-enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Introduction to Python Programming",
    "keywords": ["python", "programming"],
    "blog_type": "tutorial",
    "length": "short",
    "word_count_target": 300
  }' | jq '.content | length, .total_tokens, .generation_time'
```

**Expected:**
- `content` length > 50 characters
- `total_tokens` > 0
- `generation_time` > 1 second

---

## 📋 Complete Setup Checklist

- [ ] DataForSEO API credentials obtained
- [ ] Secrets added to Google Secret Manager using script
- [ ] Secrets verified with `gcloud secrets versions access`
- [ ] Service account has `secretAccessor` role
- [ ] Service redeployed after adding secrets
- [ ] Cloud Run logs show secrets loading
- [ ] Cloud Run logs show DataForSEO client initialized
- [ ] Endpoint tested and returns content (not empty)
- [ ] `total_tokens` > 0 in response

---

**See `GOOGLE_SECRETS_SETUP_V1.3.6.md` for detailed setup instructions.**

