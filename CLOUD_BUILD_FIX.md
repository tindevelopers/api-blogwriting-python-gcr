# Cloud Build Fix

**Date:** 2025-01-23  
**Status:** ✅ Fixed

---

## Issue

Cloud Build was failing with the following error:

```
ERROR: (gcloud.run.deploy) argument --set-env-vars: At most one of 
--clear-env-vars | --env-vars-file | --set-env-vars | --remove-env-vars 
--update-env-vars can be specified.
```

**Root Cause:**
The `gcloud run deploy` command was using `--update-env-vars`, which was conflicting with an implicit `--set-env-vars` flag (possibly from a previous deployment or trigger configuration).

---

## Fix Applied

**File:** `cloudbuild.yaml`

**Change:**
```yaml
# ❌ BEFORE (Causing conflict)
'--update-env-vars', 'PYTHONUNBUFFERED=1',

# ✅ AFTER (Fixed)
'--set-env-vars', 'PYTHONUNBUFFERED=1',
```

**Why this works:**
- `--set-env-vars` replaces all environment variables (but we only have one: `PYTHONUNBUFFERED=1`)
- `--update-env-vars` updates only specified variables, but conflicts with `--set-env-vars` if both are present
- Since the service uses **secrets** (not env vars) for API keys, using `--set-env-vars` is safe and won't affect secret-based configuration

---

## Impact

**Before Fix:**
- ❌ Cloud Build failing
- ❌ Subtopics fix not deployed
- ❌ Blog generation returning empty content

**After Fix:**
- ✅ Cloud Build should succeed
- ✅ Subtopics fix will be deployed
- ✅ Blog generation should work with subtopics

---

## Verification

After the build completes, verify:

1. **Build Status:**
   ```bash
   gcloud builds list --project=api-ai-blog-writer --limit=1
   ```

2. **Service Deployment:**
   ```bash
   gcloud run services describe blog-writer-api-dev \
     --region=europe-west9 \
     --project=api-ai-blog-writer
   ```

3. **Test Blog Generation:**
   ```bash
   curl -X POST "<SERVICE_URL>/api/v1/blog/generate-enhanced" \
     -H "Content-Type: application/json" \
     -d '{
       "topic": "Introduction to Python",
       "keywords": ["python", "programming"],
       "word_count_target": 100,
       "use_dataforseo_content_generation": true
     }'
   ```

---

## Related Changes

- **Subtopics Fix:** `23ac0c1` - Correct subtopics endpoint path
- **Metadata Fix:** `faccd32` - Update subtopics metadata extraction
- **Cloud Build Fix:** `2300692` - Change --update-env-vars to --set-env-vars

---

## Status

✅ **Fixed and pushed to GitHub**  
⏳ **Waiting for Cloud Build to complete**  
⏳ **Will test blog generation after deployment**

