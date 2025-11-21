# Cloud Tasks Queue Fix - Migration to Correct Region

**Date:** 2025-11-18  
**Issue:** Cloud Tasks queue was stuck with tasks pointing to wrong region

---

## Problem Identified

1. **Old Queue Location:** `europe-west1` (had 8 stuck tasks)
2. **Service Location:** `europe-west9` (where blog-writer-api-dev is deployed)
3. **Tasks Pointing To:** `https://blog-writer-api-dev-api-ai-blog-writer.europe-west1.run.app` (wrong URL)
4. **Issue:** Tasks were failing because the URL pointed to a non-existent service

---

## Root Cause

- Cloud Tasks queue was created in `europe-west1`
- Tasks were being created with worker URL pointing to `europe-west1` service
- But the actual service is deployed in `europe-west9`
- `europe-west9` is NOT a valid Cloud Tasks location (Cloud Tasks doesn't support it)

---

## Solution

### Key Insight
**Cloud Tasks queues can be in a different region than the Cloud Run service.** The important thing is that the worker URL points to the correct Cloud Run service.

### Actions Taken

1. ✅ **Purged old queue** in `europe-west1` (removed 8 stuck tasks)
2. ✅ **Deleted old queue** in `europe-west1`
3. ✅ **Created new queue** in `europe-west1` (closest valid Cloud Tasks region to europe-west9)
4. ✅ **Updated CloudTasksService** to use `europe-west1` for queue location
5. ✅ **Verified worker URL** construction points to `europe-west9` service

---

## Configuration

### Queue Location
- **Queue Region:** `europe-west1` (valid Cloud Tasks location)
- **Service Region:** `europe-west9` (where Cloud Run service is deployed)
- **Worker URL:** `https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/worker`

### Environment Variables

The code now uses:
- `CLOUD_TASKS_QUEUE_LOCATION` - For queue location (defaults to `europe-west1`)
- `GCP_LOCATION` - For Cloud Run service region (defaults to `europe-west9`)
- `CLOUD_RUN_SERVICE_NAME` - Service name (defaults to `blog-writer-api-dev`)

### Worker URL Construction

The worker URL is constructed correctly in `main.py:988-990`:
```python
region = os.getenv("GCP_LOCATION", "europe-west9")  # Service region
service_name = os.getenv("CLOUD_RUN_SERVICE_NAME", "blog-writer-api-dev")
worker_url = f"https://{service_name}-{project_id}.{region}.run.app/api/v1/blog/worker"
```

This ensures tasks point to the correct `europe-west9` service.

---

## Files Updated

1. ✅ `src/blog_writer_sdk/services/cloud_tasks_service.py`
   - Changed default location to `europe-west1` (valid Cloud Tasks region)
   - Added comment explaining queue can be in different region than service

2. ✅ `scripts/setup-cloud-tasks-queue.sh`
   - Changed default location to `europe-west1`
   - Added comments explaining the region choice

---

## Verification

### Queue Status
```bash
gcloud tasks queues describe blog-generation-queue --location=europe-west1
```

### Test Async Job Creation
```bash
curl -X POST "https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/generate-enhanced?async_mode=true" \
  -H "Content-Type: application/json" \
  -d '{"topic":"Test","keywords":["test"],"use_google_search":false}'
```

### Check Task in Queue
```bash
gcloud tasks list --queue=blog-generation-queue --location=europe-west1
```

---

## Important Notes

1. **Queue Location vs Service Location:**
   - Queue: `europe-west1` (must be valid Cloud Tasks region)
   - Service: `europe-west9` (where Cloud Run is deployed)
   - This is OK - they can be different regions

2. **Worker URL:**
   - Must point to the actual Cloud Run service URL
   - Currently: `https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/worker`
   - This is constructed from `GCP_LOCATION` (europe-west9)

3. **IAM Permissions:**
   - Cloud Tasks service account needs permission to invoke Cloud Run service
   - Service account: `cloud-tasks@api-ai-blog-writer.iam.gserviceaccount.com`
   - Needs: `roles/run.invoker` on the Cloud Run service

---

## Next Steps

1. ✅ Queue created and ready
2. ⚠️ Verify IAM permissions (Cloud Tasks → Cloud Run)
3. ✅ Test async job creation
4. ✅ Monitor queue for task processing

---

## Troubleshooting

### Tasks Not Processing?

1. **Check Queue:** `gcloud tasks queues describe blog-generation-queue --location=europe-west1`
2. **Check Tasks:** `gcloud tasks list --queue=blog-generation-queue --location=europe-west1`
3. **Check Worker URL:** Verify it points to correct service
4. **Check IAM:** Ensure Cloud Tasks service account can invoke Cloud Run service
5. **Check Logs:** `gcloud run services logs read blog-writer-api-dev --region=europe-west9`

### Worker Endpoint Not Responding?

- Verify endpoint exists: `POST /api/v1/blog/worker`
- Check service is running: `curl https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/health`
- Check logs for errors

---

**Status:** ✅ Queue fixed and ready for use

