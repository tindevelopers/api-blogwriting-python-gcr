# Credential Fix - Version 1.3.6

**Issue:** HTTP 500 errors due to 401 Unauthorized from DataForSEO API

**Root Cause:** The stored secret contained the base64-encoded value instead of the decoded API key.

---

## 🔍 Problem Identified

### Stored Value (WRONG):
```
DATAFORSEO_API_SECRET: "ZGV2ZWxvcGVyQHRpbi5pbmZvOjcyNWVjODhlMGFmMGM5MDU="
```

### Correct Value (FIXED):
```
DATAFORSEO_API_SECRET: "725ec88e0af0c905"
```

---

## ✅ Fix Applied

Updated the DEV environment secret with the correct decoded API key:

```bash
echo '{"DATAFORSEO_API_KEY":"developer@tin.info","DATAFORSEO_API_SECRET":"725ec88e0af0c905"}' | \
  gcloud secrets versions add blog-writer-env-dev --data-file=- --project=api-ai-blog-writer
```

---

## 📋 Next Steps

1. **Redeploy Service:** The service needs to be restarted to pick up the new secret
   ```bash
   # Option 1: Trigger a new deployment (recommended)
   git commit --allow-empty -m "Trigger redeploy to pick up fixed credentials"
   git push origin develop
   
   # Option 2: Force restart the service
   gcloud run services update blog-writer-api-dev \
     --region=europe-west9 \
     --project=api-ai-blog-writer \
     --update-env-vars="FORCE_RESTART=$(date +%s)"
   ```

2. **Verify Fix:** After redeploy, test the endpoint again
   ```bash
   curl -X POST https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/generate-enhanced \
     -H 'Content-Type: application/json' \
     -d '{"topic":"Test Blog","keywords":["test"],"blog_type":"tutorial","length":"short","use_dataforseo_content_generation":true}'
   ```

3. **Check Logs:** Verify no more 401 errors
   ```bash
   gcloud run services logs read blog-writer-api-dev \
     --region=europe-west9 \
     --project=api-ai-blog-writer \
     --limit=50 | grep -i "401\|unauthorized"
   ```

---

## ⚠️ Important Notes

- The service needs to be restarted to load the new secret value
- Secrets are loaded at startup, so a restart is required
- The fix has been applied to DEV environment
- Staging and Production may need the same fix if they have the same issue

---

## 🔧 Verification

After redeploy, check logs for:
- ✅ No more "401 Unauthorized" errors
- ✅ "DataForSEO generation completed" with content_length > 0
- ✅ Successful content generation

