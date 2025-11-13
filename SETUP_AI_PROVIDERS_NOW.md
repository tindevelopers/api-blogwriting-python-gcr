# Setup AI Providers - Action Required

**Status:** 🔴 Critical - API keys are placeholders

---

## 🚨 Current Issue

The secrets contain placeholder values:
- `OPENAI_API_KEY=placeholder-openai-key` ❌
- `ANTHROPIC_API_KEY=placeholder-anthropic-key` ❌

This causes 401 errors and fallback to template-based generation.

---

## ✅ Quick Fix (Choose One Method)

### Method 1: Interactive Setup (Easiest)

```bash
# Run the interactive script
./scripts/setup-ai-provider-secrets.sh
```

The script will:
1. Prompt you to enter your OpenAI API key (securely, won't show on screen)
2. Prompt you to enter your Anthropic API key
3. Create individual secrets in Secret Manager
4. Grant Cloud Run access
5. Update the service automatically

### Method 2: Non-Interactive Setup

```bash
# Provide your real API keys
export OPENAI_API_KEY="sk-your-real-openai-key-here"
export ANTHROPIC_API_KEY="sk-ant-your-real-anthropic-key-here"

# Run the non-interactive script
./scripts/setup-ai-provider-secrets-noninteractive.sh
```

### Method 3: Manual Setup

```bash
# 1. Create OpenAI secret
echo -n "sk-your-real-openai-key" | gcloud secrets create OPENAI_API_KEY \
  --data-file=- \
  --replication-policy="automatic" \
  --project=api-ai-blog-writer

# 2. Create Anthropic secret
echo -n "sk-ant-your-real-anthropic-key" | gcloud secrets create ANTHROPIC_API_KEY \
  --data-file=- \
  --replication-policy="automatic" \
  --project=api-ai-blog-writer

# 3. Grant access
SERVICE_ACCOUNT="613248238610-compute@developer.gserviceaccount.com"

gcloud secrets add-iam-policy-binding OPENAI_API_KEY \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor" \
  --project=api-ai-blog-writer

gcloud secrets add-iam-policy-binding ANTHROPIC_API_KEY \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor" \
  --project=api-ai-blog-writer

# 4. Update Cloud Run service
gcloud run services update blog-writer-api-dev \
  --region=europe-west1 \
  --project=api-ai-blog-writer \
  --update-secrets=OPENAI_API_KEY=OPENAI_API_KEY:latest \
  --update-secrets=ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest
```

---

## 🔑 Get Your API Keys

**OpenAI:**
1. Go to: https://platform.openai.com/account/api-keys
2. Click "Create new secret key"
3. Copy the key (starts with `sk-`)

**Anthropic:**
1. Go to: https://console.anthropic.com/settings/keys
2. Click "Create Key"
3. Copy the key (starts with `sk-ant-`)

---

## ✅ Verification

After setup, verify it works:

```bash
# Check secrets exist
gcloud secrets list --project=api-ai-blog-writer | grep -E "OPENAI|ANTHROPIC"

# Test the endpoint
curl -X POST "https://blog-writer-api-dev-613248238610.europe-west1.run.app/api/v1/blog/generate-enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Test",
    "keywords": ["test"],
    "use_google_search": true
  }'
```

**Expected:** `quality_score` > 80, proper H1/H2 structure, citations present

---

## 📝 Notes

- **At least ONE** provider is required (OpenAI OR Anthropic)
- **Both** recommended for best quality (4-stage pipeline uses both)
- Secrets are stored securely in Google Secret Manager
- Service restarts automatically after update
- Changes take effect immediately

---

**Ready to proceed?** Run the interactive script: `./scripts/setup-ai-provider-secrets.sh`

