# Implement Next Steps - DataForSEO Secrets Setup

**Date:** 2025-11-23  
**Status:** Ready to Execute

---

## 🎯 What Needs to Be Done

To enable content generation, you need to add DataForSEO credentials to Google Secret Manager.

---

## ✅ Step 1: Add Secrets to Google Secret Manager

### Option A: Using Automated Script (Recommended)

```bash
cd /Users/gene/Projects/api-blogwriting-python-gcr

# Run the setup script
./scripts/add-dataforseo-secrets.sh
```

The script will:
1. Prompt you for DataForSEO API Key and Secret
2. Add them to all environment secrets (dev, staging, production)
3. Create new secret versions automatically

**You'll need:**
- DataForSEO API Key (username/login)
- DataForSEO API Secret (password/secret)

### Option B: Manual Setup

If you prefer manual setup, see `GOOGLE_SECRETS_SETUP_V1.3.6.md` for detailed instructions.

---

## ✅ Step 2: Verify Secrets Are Configured

After adding secrets, verify they're set correctly:

```bash
# Verify dev environment
./scripts/verify-secrets-setup.sh dev

# Verify staging environment
./scripts/verify-secrets-setup.sh staging

# Verify production environment
./scripts/verify-secrets-setup.sh prod
```

**Expected output:**
```
✅ Secret 'blog-writer-env-dev' exists
✅ Secret is in JSON format
✅ DATAFORSEO_API_KEY is set (length: XX chars)
✅ DATAFORSEO_API_SECRET is set (length: XX chars)
✅ Service account has access to secret
✅ Setup complete: All required secrets are configured
```

---

## ✅ Step 3: Redeploy the Service

After adding secrets, redeploy to pick up the new credentials:

### For Dev Environment:
```bash
# Push to develop branch (auto-deploys)
git push origin develop
```

### For Staging Environment:
```bash
# Push to staging branch (auto-deploys)
git push origin staging
```

### For Production Environment:
```bash
# Push to main branch (auto-deploys)
git push origin main
```

**Note:** The deployment will automatically mount secrets from Google Secret Manager at `/secrets/env`.

---

## ✅ Step 4: Verify Deployment

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
- ✅ `✅ Environment variables loaded from secrets (JSON format): X set`
- ✅ `✅ DataForSEO Labs client initialized.`
- ❌ `⚠️ DataForSEO Labs not configured` (indicates missing credentials)`

### Test the Endpoint

```bash
curl -X POST https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/generate-enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Introduction to Python Programming",
    "keywords": ["python", "programming"],
    "blog_type": "tutorial",
    "length": "short",
    "word_count_target": 300
  }' | jq '{content_length: (.content | length), total_tokens, generation_time, success}'
```

**Expected response:**
```json
{
  "content_length": 1234,
  "total_tokens": 567,
  "generation_time": 2.5,
  "success": true
}
```

**If content_length is 0:**
- Check Cloud Run logs for errors
- Verify secrets are accessible
- Check service account permissions

---

## 🔍 Troubleshooting

### Issue: Script Fails with "Secret does not exist"

**Solution:**
```bash
# Create the secret first
echo '{}' | gcloud secrets create blog-writer-env-dev \
  --data-file=- \
  --project=api-ai-blog-writer
```

### Issue: Service Account Permission Denied

**Solution:**
```bash
SERVICE_ACCOUNT="blog-writer-service-account@api-ai-blog-writer.iam.gserviceaccount.com"

gcloud secrets add-iam-policy-binding blog-writer-env-dev \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor" \
  --project=api-ai-blog-writer
```

### Issue: Secrets Not Loading in Container

**Check:**
1. Verify secret exists: `gcloud secrets describe blog-writer-env-dev --project=api-ai-blog-writer`
2. Check Cloud Run service configuration includes secret mount
3. Verify service account has `secretAccessor` role

### Issue: Empty Content Still Returned

**Check:**
1. Cloud Run logs for DataForSEO errors
2. Verify credentials are correct (not placeholders)
3. Check DataForSEO subscription status
4. Verify API key has access to Content Generation endpoints

---

## 📋 Complete Checklist

- [ ] DataForSEO API credentials obtained
- [ ] Secrets added to Google Secret Manager using script
- [ ] Secrets verified with `./scripts/verify-secrets-setup.sh`
- [ ] Service account has `secretAccessor` role (verified by script)
- [ ] Service redeployed (push to appropriate branch)
- [ ] Cloud Run logs show secrets loading successfully
- [ ] Cloud Run logs show DataForSEO client initialized
- [ ] Endpoint tested and returns content (not empty)
- [ ] `total_tokens` > 0 in response
- [ ] `generation_time` > 1 second

---

## 📚 Related Documentation

- `GOOGLE_SECRETS_SETUP_V1.3.6.md` - Detailed setup guide
- `SECRETS_VERIFICATION_GUIDE_V1.3.6.md` - Verification steps
- `CONTENT_GENERATION_FIX_V1.3.6.md` - Content generation fixes
- `CREDENTIALS_LOCATION.md` - Where credentials are needed

---

## 🚀 Quick Start Commands

```bash
# 1. Add secrets
./scripts/add-dataforseo-secrets.sh

# 2. Verify setup
./scripts/verify-secrets-setup.sh dev

# 3. Redeploy (if needed)
git push origin develop

# 4. Test endpoint
curl -X POST https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/generate-enhanced \
  -H "Content-Type: application/json" \
  -d '{"topic":"Test","keywords":["test"],"blog_type":"tutorial","length":"short"}' | jq '.content | length'
```

---

**Status:** Ready to execute - Run `./scripts/add-dataforseo-secrets.sh` to begin

