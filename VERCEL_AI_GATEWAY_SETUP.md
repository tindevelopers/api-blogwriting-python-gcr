# Vercel AI Gateway Integration Guide

## Overview

This guide shows you how to configure your LiteLLM proxy to route AI requests through Vercel AI Gateway for centralized management, caching, and cost tracking.

---

## 🎯 Architecture

```
Your Backend (Cloud Run)
        ↓
LiteLLM Proxy (Cloud Run)
        ↓
Vercel AI Gateway (Vercel Edge)
        ↓
OpenAI / Anthropic / Other Providers
```

**Benefits:**
- ✅ Centralized rate limiting
- ✅ Request/response caching at edge
- ✅ Built-in analytics dashboard
- ✅ DDoS protection
- ✅ Multi-provider fallbacks
- ✅ Cost optimization

---

## Step 1: Set Up Vercel AI Gateway

### 1.1 Get Your Vercel AI Gateway URL

1. **Go to Vercel Dashboard**
   - Navigate to https://vercel.com/dashboard
   - Select your project (or create a new one)

2. **Enable AI Gateway**
   - Go to **Settings** → **AI**
   - Click **Enable AI Gateway**
   - Copy your AI Gateway URL (e.g., `https://your-app.vercel.app/api/ai`)

3. **Generate Gateway Token**
   - In the AI settings, generate an access token
   - Save this token securely

### 1.2 Configure Provider Keys in Vercel

Add your AI provider keys to Vercel:

```bash
# Using Vercel CLI
vercel env add OPENAI_API_KEY
# Paste your OpenAI API key

vercel env add ANTHROPIC_API_KEY
# Paste your Anthropic API key
```

Or add them in the Vercel Dashboard:
- Go to **Settings** → **Environment Variables**
- Add: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`

---

## Step 2: Configure LiteLLM to Use Vercel Gateway

### 2.1 Update Environment Variables

Add these to your Cloud Run service:

```bash
gcloud run services update litellm-proxy \
  --region europe-west9 \
  --set-env-vars VERCEL_AI_GATEWAY_URL=https://your-app.vercel.app/api/ai \
  --set-env-vars VERCEL_AI_GATEWAY_KEY=your-vercel-gateway-token
```

### 2.2 Use the Vercel-Enabled Config

Deploy LiteLLM with the Vercel configuration:

```bash
# Option A: Update deployment script
cd /Users/gene/Projects/api-blogwriting-python-gcr

# Modify scripts/deploy-litellm.sh to use litellm-config-vercel.yaml
# Then deploy:
./scripts/deploy-litellm.sh

# Option B: Manual deployment
gcloud run deploy litellm-proxy \
  --image ghcr.io/berriai/litellm:main-latest \
  --region europe-west9 \
  --platform managed \
  --set-env-vars VERCEL_AI_GATEWAY_URL=https://your-app.vercel.app/api/ai \
  --set-env-vars VERCEL_AI_GATEWAY_KEY=your-gateway-token \
  --set-secrets LITELLM_CONFIG=/app/config.yaml:LITELLM_CONFIG_VERCEL:latest
```

---

## Step 3: Verify the Connection

### 3.1 Test LiteLLM → Vercel Connection

Create a test script:

```bash
# File: test_vercel_connection.sh
#!/bin/bash

LITELLM_URL="https://litellm-proxy-613248238610.europe-west9.run.app"
LITELLM_KEY="your-litellm-master-key"

echo "Testing LiteLLM → Vercel AI Gateway connection..."

# Test 1: Health check
echo -e "\n1. Health Check"
curl -s "$LITELLM_URL/health" | jq

# Test 2: Simple generation request
echo -e "\n2. Test Generation (gpt-4o-mini via Vercel)"
curl -s -X POST "$LITELLM_URL/v1/chat/completions" \
  -H "Authorization: Bearer $LITELLM_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Say hello"}],
    "max_tokens": 10
  }' | jq

echo -e "\n✅ If you see a response, LiteLLM is working!"
echo "Now check Vercel logs to confirm requests are passing through..."
```

### 3.2 Check Vercel Logs

1. **Go to Vercel Dashboard**
   - Select your project
   - Click **Deployments** → **Functions**
   - View logs for `/api/ai`

2. **Look for Request Logs**
   You should see:
   ```
   [AI Gateway] Incoming request: POST /api/ai/v1/chat/completions
   [AI Gateway] Provider: openai, Model: gpt-4o-mini
   [AI Gateway] Response: 200 OK
   ```

3. **Check Analytics**
   - Go to **Analytics** → **AI**
   - You should see request counts, latency, and costs

---

## Step 4: Monitor Both Systems

### 4.1 Backend Logs (Cloud Run)

Check that your backend is sending to LiteLLM:

```bash
gcloud logging read "resource.type=cloud_run_revision AND \
  resource.labels.service_name=blog-writer-api-dev AND \
  textPayload=~'AI Gateway'" \
  --project=api-ai-blog-writer \
  --limit=20 \
  --format=json
```

Look for:
```json
{
  "textPayload": "AIGateway initialized with base_url: https://litellm-proxy-xxx.run.app",
  "textPayload": "Generated content: 1234 chars, model: gpt-4o-mini, org: test-org"
}
```

### 4.2 LiteLLM Logs (Cloud Run)

Check LiteLLM proxy logs:

```bash
gcloud logging read "resource.type=cloud_run_revision AND \
  resource.labels.service_name=litellm-proxy" \
  --project=api-ai-blog-writer \
  --limit=20 \
  --format=json
```

Look for Vercel Gateway URL in requests:
```json
{
  "textPayload": "Making request to: https://your-app.vercel.app/api/ai/v1/chat/completions"
}
```

### 4.3 Vercel Logs (Dashboard)

In Vercel Dashboard → Functions → Logs, you should see:
```
[AI Gateway] Request received
[AI Gateway] Forwarding to provider: openai
[AI Gateway] Response: 200 OK, tokens: 123
```

---

## Step 5: Verify End-to-End Flow

### Test Script: Complete Flow

```bash
#!/bin/bash
# File: test_complete_flow.sh

BACKEND_URL="https://blog-writer-api-dev-613248238610.europe-west9.run.app"

echo "Testing Complete Flow: Backend → LiteLLM → Vercel → OpenAI"
echo "================================================================"

# Test blog generation
curl -X POST "$BACKEND_URL/api/v1/blog/generate-gateway" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Testing Vercel AI Gateway",
    "keywords": ["test", "vercel", "gateway"],
    "org_id": "test-org",
    "user_id": "test-user",
    "word_count": 300,
    "model": "gpt-4o-mini"
  }' | jq '.content | length'

echo ""
echo "If you see a number (content length), the complete flow works!"
echo ""
echo "Now verify in:"
echo "1. Backend logs (Cloud Run): blog-writer-api-dev"
echo "2. LiteLLM logs (Cloud Run): litellm-proxy"
echo "3. Vercel logs (Dashboard): AI Gateway function"
```

---

## Step 6: Confirmation Checklist

### ✅ How to Confirm Vercel AI Gateway is Active

Use this checklist to verify the connection:

- [ ] **Environment Variables Set**
  ```bash
  # Check LiteLLM has Vercel vars
  gcloud run services describe litellm-proxy \
    --region=europe-west9 \
    --format="value(spec.template.spec.containers[0].env)" | grep VERCEL
  ```

- [ ] **LiteLLM Config Uses Vercel**
  ```bash
  # Check config has api_base pointing to Vercel
  cat litellm/litellm-config-vercel.yaml | grep -A2 "api_base"
  ```

- [ ] **Backend Points to LiteLLM**
  ```bash
  # Check backend env vars
  gcloud run services describe blog-writer-api-dev \
    --region=europe-west9 \
    --format="value(spec.template.spec.containers[0].env)" | grep LITELLM_PROXY_URL
  ```

- [ ] **Test Request Succeeds**
  ```bash
  # Run test script from Step 3.1
  ./test_vercel_connection.sh
  ```

- [ ] **Vercel Dashboard Shows Traffic**
  - Go to Vercel Dashboard → Analytics → AI
  - Should see request counts increasing

- [ ] **LiteLLM Logs Show Vercel URL**
  ```bash
  gcloud logging read "resource.labels.service_name=litellm-proxy AND \
    textPayload=~'vercel'" --limit=5
  ```

---

## Troubleshooting

### Issue: "Connection Refused" Error

**Problem:** LiteLLM can't reach Vercel AI Gateway

**Solution:**
```bash
# 1. Verify Vercel URL is correct
curl https://your-app.vercel.app/api/ai/health

# 2. Check environment variable
gcloud run services describe litellm-proxy --format=json | jq '.spec.template.spec.containers[0].env'

# 3. Redeploy with correct URL
gcloud run services update litellm-proxy \
  --set-env-vars VERCEL_AI_GATEWAY_URL=https://your-correct-app.vercel.app/api/ai
```

### Issue: "401 Unauthorized" Error

**Problem:** Invalid Vercel gateway token

**Solution:**
```bash
# Regenerate token in Vercel Dashboard
# Then update:
gcloud run services update litellm-proxy \
  --set-env-vars VERCEL_AI_GATEWAY_KEY=your-new-token
```

### Issue: Requests Go Direct to OpenAI (Bypass Vercel)

**Problem:** LiteLLM config not using Vercel

**Solution:**
```bash
# 1. Check which config is loaded
gcloud secrets versions list LITELLM_CONFIG

# 2. Update to use Vercel config
gcloud secrets versions add LITELLM_CONFIG \
  --data-file=litellm/litellm-config-vercel.yaml

# 3. Redeploy
./scripts/deploy-litellm.sh
```

### Issue: Can't See Requests in Vercel Dashboard

**Problem:** Requests not reaching Vercel or logging not enabled

**Solution:**
1. Enable verbose logging in `litellm-config-vercel.yaml`:
   ```yaml
   litellm_settings:
     set_verbose: true
     log_requests: true
   ```

2. Check Vercel function logs:
   - Dashboard → Deployments → Functions → `/api/ai` → Logs

3. Verify Vercel AI Gateway is deployed:
   ```bash
   curl https://your-app.vercel.app/api/ai/health
   ```

---

## Performance Comparison

### Direct Connection (Current)
```
Backend → OpenAI API
Latency: ~2-5 seconds
Cost: Full API cost
Caching: Backend only
```

### Via Vercel AI Gateway (Recommended)
```
Backend → LiteLLM → Vercel Edge → OpenAI API
Latency: ~2-5 seconds (edge caching can reduce to <100ms on cache hits)
Cost: Same API cost + edge caching savings (20-40% reduction)
Caching: Multi-layer (LiteLLM + Vercel Edge + Backend)
```

**Estimated Savings:**
- Cache hit rate: 30-50%
- Cost reduction: 20-40%
- Latency improvement: 80-95% on cached requests

---

## Alternative: Direct Backend → Vercel (Skip LiteLLM)

If you want to skip LiteLLM entirely:

### Update Backend to Point to Vercel

```bash
# Set backend to use Vercel AI Gateway directly
gcloud run services update blog-writer-api-dev \
  --region=europe-west9 \
  --set-env-vars LITELLM_PROXY_URL=https://your-app.vercel.app/api/ai \
  --set-env-vars LITELLM_API_KEY=your-vercel-gateway-token
```

**Pros:**
- Simpler architecture (one less hop)
- Direct edge caching
- Vercel's analytics dashboard

**Cons:**
- Lose LiteLLM's features (load balancing, fallbacks, custom routing)
- No Redis caching layer
- Less flexibility for complex routing

---

## Summary

### Current State (Direct)
```
Backend → OpenAI/Anthropic (Direct)
Status: ✅ Working
Cache: Backend only
Analytics: Backend logs only
```

### Recommended State (via Vercel)
```
Backend → LiteLLM → Vercel AI Gateway → Providers
Status: 🔧 Needs configuration
Cache: Multi-layer
Analytics: Backend + LiteLLM + Vercel Dashboard
```

### Next Steps

1. **Get Vercel AI Gateway URL** from Vercel Dashboard
2. **Add environment variables** to LiteLLM service
3. **Deploy LiteLLM** with Vercel config
4. **Run test scripts** to verify connection
5. **Monitor Vercel Dashboard** to confirm traffic flow

**Ready to configure? Start with Step 1!** 🚀

---

## Quick Reference

### Environment Variables Needed

**LiteLLM Service:**
```bash
VERCEL_AI_GATEWAY_URL=https://your-app.vercel.app/api/ai
VERCEL_AI_GATEWAY_KEY=your-vercel-token
LITELLM_MASTER_KEY=your-litellm-key
REDIS_HOST=your-redis-host
REDIS_PASSWORD=your-redis-password
```

**Backend Service:**
```bash
LITELLM_PROXY_URL=https://litellm-proxy-xxx.run.app
LITELLM_API_KEY=your-litellm-master-key
```

### Test Commands

```bash
# Test backend
curl https://blog-writer-api-dev-613248238610.europe-west9.run.app/health

# Test LiteLLM
curl https://litellm-proxy-xxx.run.app/health

# Test Vercel
curl https://your-app.vercel.app/api/ai/health

# Test complete flow
./test_complete_flow.sh
```

---

**Questions?** Check the troubleshooting section or review logs at each layer!

