# Cloud Tasks Queue Fix Summary

**Date:** 2025-11-18  
**Issue:** Blog generation queue stuck with 8 tasks pointing to wrong region

---

## ✅ Problem Fixed

### Root Cause
1. **Queue Location:** `europe-west1` (correct - valid Cloud Tasks region)
2. **Service Location:** `europe-west9` (where Cloud Run service is deployed)
3. **Worker URL Issue:** Tasks were pointing to wrong URL pattern
4. **Stuck Tasks:** 8 tasks with 60+ retries each, pointing to non-existent service

### Solution Applied

1. ✅ **Purged old queue** - Removed all 8 stuck tasks
2. ✅ **Deleted old queue** - Cleaned up the problematic queue
3. ✅ **Fixed worker URL** - Updated to use actual service URL instead of constructed pattern
4. ✅ **Updated code** - Fixed CloudTasksService to use correct queue location
5. ✅ **Updated scripts** - Fixed setup script to use correct region

---

## 🔧 Changes Made

### 1. Worker URL Fix (`main.py`)
**Before:**
```python
worker_url = f"https://{service_name}-{project_id}.{region}.run.app/api/v1/blog/worker"
```

**After:**
```python
service_base_url = os.getenv("CLOUD_RUN_SERVICE_URL", "https://blog-writer-api-dev-kq42l26tuq-od.a.run.app")
worker_url = f"{service_base_url}/api/v1/blog/worker"
```

**Why:** Cloud Run URLs have unique hashes, not predictable patterns.

### 2. CloudTasksService Location (`cloud_tasks_service.py`)
**Before:**
```python
self.location = location or os.getenv("GCP_LOCATION", "europe-west9")
```

**After:**
```python
# Cloud Tasks queue location (must be a valid Cloud Tasks region)
# Note: Queue can be in different region than Cloud Run service
# Using europe-west1 as it's closest to europe-west9 and is a valid Cloud Tasks location
self.location = location or os.getenv("CLOUD_TASKS_QUEUE_LOCATION", "europe-west1")
```

**Why:** `europe-west9` is NOT a valid Cloud Tasks location. Queue must be in `europe-west1` (or another valid region).

### 3. Setup Script (`scripts/setup-cloud-tasks-queue.sh`)
**Before:**
```bash
LOCATION="${GCP_LOCATION:-europe-west9}"
```

**After:**
```bash
# Cloud Tasks queue location (must be a valid Cloud Tasks region)
# Note: Queue can be in different region than Cloud Run service
LOCATION="${CLOUD_TASKS_QUEUE_LOCATION:-europe-west1}"
```

---

## 📋 Configuration

### Queue Setup
- **Queue Name:** `blog-generation-queue`
- **Queue Location:** `europe-west1` (valid Cloud Tasks region)
- **Service Location:** `europe-west9` (where Cloud Run is deployed)
- **Worker URL:** `https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/worker`

### Environment Variables
- `CLOUD_TASKS_QUEUE_LOCATION` - Queue location (defaults to `europe-west1`)
- `CLOUD_RUN_SERVICE_URL` - Service base URL (defaults to dev service URL)
- `GCP_LOCATION` - Cloud Run service region (defaults to `europe-west9`)

---

## ⚠️ Important Notes

### Queue Recreation
Google Cloud has a cooldown period after deleting a queue. If you need to recreate it immediately:

1. **Wait 5-10 minutes** after deletion, OR
2. **Use a different queue name** temporarily

### Queue Location vs Service Location
- ✅ **OK:** Queue in `europe-west1`, Service in `europe-west9`
- ✅ **OK:** Queue and Service can be in different regions
- ❌ **NOT OK:** Queue in `europe-west9` (not a valid Cloud Tasks location)

### Worker URL
- Must point to the **actual** Cloud Run service URL
- Cannot be constructed from service name + project + region
- Use `CLOUD_RUN_SERVICE_URL` environment variable or hardcode the actual URL

---

## 🚀 Next Steps

1. **Wait for queue cooldown** (if needed) - 5-10 minutes after deletion
2. **Recreate queue** (if needed):
   ```bash
   gcloud tasks queues create blog-generation-queue \
     --location=europe-west1 \
     --max-dispatches-per-second=100 \
     --max-concurrent-dispatches=500 \
     --max-retry-duration=3600s
   ```

3. **Verify IAM permissions:**
   ```bash
   # Cloud Tasks service account needs to invoke Cloud Run service
   gcloud run services add-iam-policy-binding blog-writer-api-dev \
     --region=europe-west9 \
     --member="serviceAccount:cloud-tasks@api-ai-blog-writer.iam.gserviceaccount.com" \
     --role="roles/run.invoker"
   ```

4. **Test async job creation:**
   ```bash
   curl -X POST "https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/generate-enhanced?async_mode=true" \
     -H "Content-Type: application/json" \
     -d '{"topic":"Test","keywords":["test"],"use_google_search":false}'
   ```

5. **Monitor queue:**
   ```bash
   gcloud tasks queues describe blog-generation-queue --location=europe-west1
   gcloud tasks list --queue=blog-generation-queue --location=europe-west1
   ```

---

## ✅ Verification Checklist

- [x] Old queue purged and deleted
- [x] Worker URL fixed to use actual service URL
- [x] CloudTasksService updated to use correct queue location
- [x] Setup script updated
- [ ] Queue recreated (wait for cooldown if needed)
- [ ] IAM permissions verified
- [ ] Test async job creation
- [ ] Monitor queue for task processing

---

## 📝 Files Modified

1. ✅ `main.py` - Fixed worker URL construction
2. ✅ `src/blog_writer_sdk/services/cloud_tasks_service.py` - Fixed queue location
3. ✅ `scripts/setup-cloud-tasks-queue.sh` - Fixed default location

---

**Status:** ✅ Code fixes complete. Queue needs to be recreated after cooldown period.

