# Google Search Console Service Account Status

## Current Status

### Cloud Run Service Account
**Service Account:** `613248238610-compute@developer.gserviceaccount.com`  
**Type:** Default Compute Service Account  
**Used By:** Cloud Run service (`blog-writer-api-dev`)

### Google Search Console Configuration

**Status:** ⚠️ **Not Fully Configured**

**What's Needed:**
1. **Service Account for GSC** - Either:
   - Use existing service account, OR
   - Create new dedicated service account for GSC

2. **Service Account Key** - JSON key file stored in Secret Manager

3. **Grant GSC Access** - Add service account email to Google Search Console

---

## Available Service Accounts

Based on the project, you have these service accounts available:

1. **`blog-writer-dev@api-ai-blog-writer.iam.gserviceaccount.com`**
   - Display Name: Blog Writer Dev Service Account
   - **Recommended:** Use this for dev environment

2. **`blog-writer-staging@api-ai-blog-writer.iam.gserviceaccount.com`**
   - Display Name: Blog Writer Staging Service Account
   - Use for staging environment

3. **`blog-writer-prod@api-ai-blog-writer.iam.gserviceaccount.com`**
   - Display Name: Blog Writer Prod Service Account
   - Use for production environment

4. **`613248238610-compute@developer.gserviceaccount.com`**
   - Display Name: Default compute service account
   - Currently used by Cloud Run
   - **Can be used** but not recommended (less secure)

---

## Recommended Approach

### Option 1: Use Existing Blog Writer Service Account (Recommended) ✅

**For Dev Environment:**
- **Service Account:** `blog-writer-dev@api-ai-blog-writer.iam.gserviceaccount.com`
- **Benefits:**
  - Already exists
  - Environment-specific
  - Better security isolation

**Steps:**
1. Create service account key:
   ```bash
   gcloud iam service-accounts keys create /tmp/blog-writer-dev-key.json \
     --iam-account=blog-writer-dev@api-ai-blog-writer.iam.gserviceaccount.com \
     --project=api-ai-blog-writer
   ```

2. Store key in Secret Manager:
   ```bash
   cat /tmp/blog-writer-dev-key.json | gcloud secrets create GSC_SERVICE_ACCOUNT_KEY \
     --project=api-ai-blog-writer \
     --data-file=-
   ```

3. Grant Cloud Run access:
   ```bash
   gcloud secrets add-iam-policy-binding GSC_SERVICE_ACCOUNT_KEY \
     --project=api-ai-blog-writer \
     --member="serviceAccount:613248238610-compute@developer.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   ```

4. Grant GSC access (for each site):
   - Go to: https://search.google.com/search-console
   - Select property (site URL)
   - Settings → Users and permissions
   - Add user: `blog-writer-dev@api-ai-blog-writer.iam.gserviceaccount.com`
   - Grant "Full" access

### Option 2: Create New Dedicated GSC Service Account

**Service Account Name:** `blog-writer-gsc@api-ai-blog-writer.iam.gserviceaccount.com`

**Steps:**
1. Run setup script:
   ```bash
   ./scripts/setup-google-search-console.sh dev
   ```
   - Choose option 2 (Create new service account)
   - Enter name: `blog-writer-gsc`
   - Script will create account and key automatically

2. Grant GSC access (same as Option 1, step 4)

---

## Current Code Configuration

### How GSC Client Works

The `GoogleSearchConsoleClient` looks for credentials in this order:

1. **`credentials_path` parameter** (if provided)
2. **`GOOGLE_APPLICATION_CREDENTIALS` environment variable** (points to JSON key file)
3. **Falls back** to warning if neither is available

### Required Configuration

**In Cloud Run:**
1. Mount `GSC_SERVICE_ACCOUNT_KEY` secret as file
2. Set `GOOGLE_APPLICATION_CREDENTIALS=/secrets/gsc-service-account-key`
3. Or mount secret and set path accordingly

**In `cloudbuild.yaml`:**
```yaml
'--update-secrets', '...,GSC_SERVICE_ACCOUNT_KEY=GSC_SERVICE_ACCOUNT_KEY:latest'
```

**In Cloud Run Environment:**
```bash
GOOGLE_APPLICATION_CREDENTIALS=/secrets/gsc-service-account-key
```

---

## Setup Checklist

### ✅ Step 1: Choose Service Account
- [ ] Use existing `blog-writer-dev@...` (recommended)
- [ ] OR create new `blog-writer-gsc@...`

### ✅ Step 2: Create Service Account Key
- [ ] Generate JSON key file
- [ ] Store in Secret Manager as `GSC_SERVICE_ACCOUNT_KEY`

### ✅ Step 3: Grant Cloud Run Access
- [ ] Grant `roles/secretmanager.secretAccessor` to Cloud Run service account
- [ ] Verify secret is accessible

### ✅ Step 4: Grant Google Search Console Access
- [ ] For each site, add service account email to GSC
- [ ] Grant "Full" access
- [ ] Verify access works

### ✅ Step 5: Update Deployment Configuration
- [ ] Update `cloudbuild.yaml` to mount `GSC_SERVICE_ACCOUNT_KEY`
- [ ] Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable
- [ ] Deploy and test

---

## Quick Setup Command

**For Dev Environment (using existing service account):**

```bash
# 1. Create key
gcloud iam service-accounts keys create /tmp/blog-writer-dev-gsc-key.json \
  --iam-account=blog-writer-dev@api-ai-blog-writer.iam.gserviceaccount.com \
  --project=api-ai-blog-writer

# 2. Store in Secret Manager
cat /tmp/blog-writer-dev-gsc-key.json | gcloud secrets create GSC_SERVICE_ACCOUNT_KEY \
  --project=api-ai-blog-writer \
  --data-file=-

# 3. Grant Cloud Run access
gcloud secrets add-iam-policy-binding GSC_SERVICE_ACCOUNT_KEY \
  --project=api-ai-blog-writer \
  --member="serviceAccount:613248238610-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# 4. Clean up temporary file
rm /tmp/blog-writer-dev-gsc-key.json

# 5. Grant GSC access (manual step)
echo "Now go to https://search.google.com/search-console"
echo "Add user: blog-writer-dev@api-ai-blog-writer.iam.gserviceaccount.com"
echo "Grant 'Full' access for each site"
```

---

## Service Account Email for GSC Access

**For Dev Environment:**
```
blog-writer-dev@api-ai-blog-writer.iam.gserviceaccount.com
```

**For Staging Environment:**
```
blog-writer-staging@api-ai-blog-writer.iam.gserviceaccount.com
```

**For Production Environment:**
```
blog-writer-prod@api-ai-blog-writer.iam.gserviceaccount.com
```

---

## Next Steps

1. **Choose service account** (recommend `blog-writer-dev@...` for dev)
2. **Create and store key** using commands above
3. **Grant GSC access** to service account email for each site
4. **Update deployment** to mount secret and set environment variable
5. **Test** GSC integration

---

## Verification

After setup, verify:

```bash
# Check secret exists
gcloud secrets describe GSC_SERVICE_ACCOUNT_KEY --project=api-ai-blog-writer

# Check Cloud Run has access
gcloud secrets get-iam-policy GSC_SERVICE_ACCOUNT_KEY \
  --project=api-ai-blog-writer \
  --format="table(bindings.members)"
```

---

## Summary

**Current Status:** ⚠️ Service account key not yet created/stored

**Recommended Service Account:** `blog-writer-dev@api-ai-blog-writer.iam.gserviceaccount.com`

**Next Action:** Create service account key and store in Secret Manager, then grant GSC access

