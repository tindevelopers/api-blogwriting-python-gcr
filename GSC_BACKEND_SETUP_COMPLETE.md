# Google Search Console Backend Setup - Complete ✅

## Summary

Successfully configured Google Search Console backend support:

1. ✅ **Service Account Key Created**
2. ✅ **Stored in Secret Manager**
3. ✅ **Cloud Run Access Granted**
4. ✅ **Deployment Configuration Updated**

---

## What Was Done

### 1. ✅ Created Service Account Key

**Service Account:** `blog-writer-dev@api-ai-blog-writer.iam.gserviceaccount.com`

**Key Created:** JSON key file generated and stored securely

### 2. ✅ Stored in Secret Manager

**Secret Name:** `GSC_SERVICE_ACCOUNT_KEY`

**Location:** Google Secret Manager (encrypted)

**Access:** Only Cloud Run service account can read

### 3. ✅ Granted Cloud Run Access

**Service Account:** `613248238610-compute@developer.gserviceaccount.com`

**Permission:** `roles/secretmanager.secretAccessor`

**Result:** Cloud Run can now read the GSC service account key

### 4. ✅ Updated Deployment Configuration

**File:** `cloudbuild.yaml`

**Changes:**
- Added `GSC_SERVICE_ACCOUNT_KEY=GSC_SERVICE_ACCOUNT_KEY:latest` to `--update-secrets`
- Added `GOOGLE_APPLICATION_CREDENTIALS=/secrets/gsc-service-account-key` to `--set-env-vars`

**Result:** Next deployment will mount the secret and set the environment variable

---

## Configuration Details

### Secret Manager

**Secret:** `GSC_SERVICE_ACCOUNT_KEY`  
**Type:** Service Account JSON Key  
**Access:** Cloud Run service account only

### Cloud Run Environment Variable

**Variable:** `GOOGLE_APPLICATION_CREDENTIALS`  
**Value:** `/secrets/gsc-service-account-key`  
**Purpose:** Points to mounted service account key file

### Service Account

**Email:** `blog-writer-dev@api-ai-blog-writer.iam.gserviceaccount.com`  
**Use:** Google Search Console API authentication

---

## Next Steps

### 1. Grant Google Search Console Access (Per Site)

For each site you want to use with GSC:

1. Go to: https://search.google.com/search-console
2. Select your property (site URL)
3. Go to **Settings → Users and permissions**
4. Click **Add user**
5. Enter: `blog-writer-dev@api-ai-blog-writer.iam.gserviceaccount.com`
6. Grant **Full** access
7. Click **Add**

**Repeat for each site.**

### 2. Deploy Changes

The next deployment will automatically:
- Mount `GSC_SERVICE_ACCOUNT_KEY` secret
- Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable
- Enable Google Search Console integration

**To Deploy:**
```bash
# Push to develop branch (auto-deploys)
git add cloudbuild.yaml
git commit -m "feat: Add GSC service account key mounting"
git push origin develop
```

### 3. Test GSC Integration

After deployment, test with:

```bash
# Test with site URL
curl -X POST https://your-api-url/api/v1/blog/generate-enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Test topic",
    "keywords": ["test"],
    "gsc_site_url": "https://yoursite.com",
    "mode": "multi_phase"
  }'
```

---

## Verification

### Check Secret Exists
```bash
gcloud secrets describe GSC_SERVICE_ACCOUNT_KEY \
  --project=api-ai-blog-writer
```

### Check Cloud Run Access
```bash
gcloud secrets get-iam-policy GSC_SERVICE_ACCOUNT_KEY \
  --project=api-ai-blog-writer \
  --format="table(bindings.members,bindings.role)"
```

### Check Deployment Config
```bash
grep -A 2 "GSC_SERVICE_ACCOUNT_KEY" cloudbuild.yaml
grep "GOOGLE_APPLICATION_CREDENTIALS" cloudbuild.yaml
```

---

## Service Account Email for GSC Access

**Add this email to Google Search Console for each site:**

```
blog-writer-dev@api-ai-blog-writer.iam.gserviceaccount.com
```

**Permissions:** Full access

---

## Summary

✅ **Backend Setup Complete**

- Service account key: Created and stored
- Secret Manager: Configured
- Cloud Run access: Granted
- Deployment config: Updated

⏳ **Remaining Steps**

- Grant GSC access to service account email (per site)
- Deploy changes (next push to develop)
- Test GSC integration

---

## Files Modified

- ✅ `cloudbuild.yaml` - Added GSC secret mounting and environment variable

## Secrets Created

- ✅ `GSC_SERVICE_ACCOUNT_KEY` - Service account JSON key

## Permissions Granted

- ✅ `613248238610-compute@developer.gserviceaccount.com` → `roles/secretmanager.secretAccessor` on `GSC_SERVICE_ACCOUNT_KEY`

---

## Status

**Backend Configuration:** ✅ Complete  
**GSC Access Grants:** ⏳ Pending (per site)  
**Deployment:** ⏳ Pending (next push)

**Ready for:** Frontend can now use `gsc_site_url` parameter, backend will authenticate with GSC API using stored credentials.

