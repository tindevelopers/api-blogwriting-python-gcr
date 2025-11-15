# Update STABILITY_AI_API_KEY for Image Generation

**Status:** ⚠️ **ACTION REQUIRED**

---

## Current Status

The `STABILITY_AI_API_KEY` secret exists in Google Secret Manager but is currently set to `"placeholder-key"`, which prevents image generation from working.

---

## Steps to Update

### Option 1: Using the Setup Script (Recommended)

```bash
cd scripts
./setup-stability-ai-secrets.sh
```

The script will:
1. Prompt you for your Stability AI API key
2. Create/update the secret in Google Secret Manager
3. Grant Cloud Run service account access
4. Update the Cloud Run service

### Option 2: Manual Update

#### Step 1: Get Your Stability AI API Key
1. Sign up at https://platform.stability.ai/
2. Navigate to Account → API Keys
3. Copy your API key (starts with `sk-`)

#### Step 2: Update the Secret
```bash
# Update the secret with your real API key
echo "sk-YOUR-REAL-API-KEY-HERE" | gcloud secrets versions add STABILITY_AI_API_KEY \
  --data-file=- \
  --project=api-ai-blog-writer
```

#### Step 3: Verify the Secret
```bash
# Check that the secret was updated (will show first few characters)
gcloud secrets versions access latest --secret=STABILITY_AI_API_KEY \
  --project=api-ai-blog-writer | head -c 20
```

#### Step 4: Redeploy Service
The service will automatically redeploy on the next push to `develop`, or you can manually trigger:

```bash
# Trigger deployment by pushing to develop (already done)
# Or manually deploy:
gcloud builds submit --config cloudbuild.yaml \
  --substitutions _REGION=europe-west1,_ENV=dev,_SERVICE_NAME=blog-writer-api-dev \
  --project=api-ai-blog-writer
```

---

## Verification

After updating the secret and redeploying:

1. **Check Service Logs:**
   ```bash
   gcloud run services logs read blog-writer-api-dev \
     --region=europe-west1 \
     --project=api-ai-blog-writer \
     --limit=50 | grep -i "image\|stability"
   ```

2. **Look for:**
   - ✅ `"✅ Stability AI image provider initialized successfully"`
   - ✅ `"✅ 1 image provider(s) available"`
   - ❌ `"⚠️ STABILITY_AI_API_KEY not found or invalid"` (if still not working)

3. **Test Image Generation:**
   ```bash
   curl -X POST "https://blog-writer-api-dev-kq42l26tuq-ew.a.run.app/api/v1/blog/generate-enhanced" \
     -H "Content-Type: application/json" \
     -d '{
       "topic": "Best Products for 2025",
       "keywords": ["best", "products"],
       "use_google_search": true
     }'
   ```

   **Expected:** Response should include `generated_images` array with image URLs.

---

## Important Notes

- The secret is already configured in `cloudbuild.yaml` to be mounted at runtime
- The service will automatically pick up the new secret on next deployment
- Image generation only works for product-related topics (contains "best", "top", "review", "compare", "guide")
- Images are automatically inserted into markdown content

---

**Last Updated:** 2025-11-15

