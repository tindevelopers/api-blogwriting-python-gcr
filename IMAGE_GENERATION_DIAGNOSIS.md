# Image Generation Diagnosis

## Problem
Images are not being generated for blog posts, even when conditions appear to be met.

## Current Implementation Analysis

### Image Generation Conditions (main.py:987-1044)

Images are generated only when **ALL** of the following conditions are met:

1. ✅ **`request.use_google_search == True`**
   - Status: **MET** (test request has `"use_google_search": true`)

2. ✅ **Topic contains product indicators**
   - Code: `product_indicators = ["best", "top", "review", "compare", "guide"]`
   - Status: **MET** (topic "Best Presents for Christmas 2025 for Teenagers" contains "best")

3. ❌ **`image_provider_manager.providers` is not empty**
   - Code: `if is_product_topic and image_provider_manager and image_provider_manager.providers:`
   - Status: **LIKELY FAILING** - This is the most probable issue

### Root Cause Analysis

The `image_provider_manager.providers` dictionary is populated by `initialize_image_providers_from_env()` which:

1. Checks for `STABILITY_AI_API_KEY` environment variable
2. If found, calls `configure_image_provider()` to add Stability AI provider
3. If not found or initialization fails, `providers` dictionary remains empty

**Most Likely Issue**: `STABILITY_AI_API_KEY` is not configured in Cloud Run secrets.

## Verification Steps

### 1. Check if STABILITY_AI_API_KEY is set in Cloud Run

```bash
# Check Cloud Run service secrets
gcloud run services describe blog-writer-api-dev \
  --region=europe-west1 \
  --format="value(spec.template.spec.containers[0].env)"

# Or check Secret Manager
gcloud secrets versions access latest --secret="STABILITY_AI_API_KEY"
```

### 2. Check Image Provider Initialization Logs

Look for these log messages during startup:
- ✅ `"✅ Image providers initialized from environment"`
- ⚠️ `"⚠️ Failed to initialize image providers from environment: {e}"`

### 3. Check Runtime Provider Status

The API has an endpoint to check provider status:
```bash
curl https://blog-writer-api-dev-kq42l26tuq-ew.a.run.app/api/v1/images/providers/status
```

## Solution Plan

### Option 1: Configure Stability AI API Key (Recommended)

1. **Get Stability AI API Key**
   - Sign up at https://platform.stability.ai/
   - Get API key from account settings

2. **Add to Secret Manager**
   ```bash
   # Add to blog-writer-env-dev secret
   gcloud secrets versions add blog-writer-env-dev \
     --data-file=- <<< "STABILITY_AI_API_KEY=sk-..."
   ```

3. **Update Cloud Run Service**
   - Ensure the secret is mounted/accessible
   - Redeploy the service

### Option 2: Make Image Generation Optional with Better Error Handling

If Stability AI is not available, the code should:
- Log a clear warning (not just silently fail)
- Optionally fall back to placeholder images
- Return a clear error message in the response

### Option 3: Add Image Generation Toggle

Add a request parameter to explicitly enable/disable image generation:
```json
{
  "generate_images": true,  // New parameter
  "use_google_search": true
}
```

## Code Locations

1. **Image Generation Logic**: `main.py:987-1044`
2. **Provider Initialization**: `main.py:307-312`
3. **Provider Manager**: `src/blog_writer_sdk/api/image_generation.py:532-549`
4. **Provider Configuration**: `src/blog_writer_sdk/api/image_generation.py:448-476`

## Expected Behavior After Fix

When properly configured:
1. ✅ `initialize_image_providers_from_env()` adds Stability AI provider
2. ✅ `image_provider_manager.providers` contains at least one provider
3. ✅ Image generation executes for product topics
4. ✅ Generated images appear in `generated_images` array
5. ✅ Images are auto-inserted into markdown content

## Testing

After fixing, test with:
```json
{
  "topic": "Best Presents for Christmas 2025 for Teenagers",
  "keywords": ["christmas gifts for teenagers 2025"],
  "use_google_search": true
}
```

Expected response should include:
```json
{
  "generated_images": [
    {
      "type": "featured",
      "image_url": "https://...",
      "alt_text": "Featured image for Best Presents for Christmas 2025 for Teenagers"
    }
  ]
}
```

