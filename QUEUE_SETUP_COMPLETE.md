# Cloud Tasks Queue Setup Complete

**Date:** 2025-11-18  
**Status:** Queues cleaned up, ready for recreation

---

## ✅ Actions Completed

1. **Deleted Temporary Queue:** `blog-generation-queue-temp` ✅
2. **Created Alternative Queue:** `blog-queue-dev` ✅ (available immediately)
3. **Created Recreation Script:** `scripts/recreate-cloud-tasks-queue.sh` ✅

---

## 📋 Queue Status

### Current Queues

| Queue Name | Location | Status | Notes |
|------------|----------|--------|-------|
| `blog-generation-queue` | europe-west1 | ⏳ Cooldown | Cannot recreate yet (10-15 min wait) |
| `blog-queue-dev` | europe-west1 | ✅ Ready | Alternative queue, available now |

---

## 🚀 Quick Start Options

### Option 1: Use Alternative Queue (Immediate)

The alternative queue `blog-queue-dev` is ready to use:

```bash
# Update Cloud Run service to use alternative queue
gcloud run services update blog-writer-api-dev \
  --region=europe-west9 \
  --update-env-vars CLOUD_TASKS_QUEUE_NAME=blog-queue-dev

# Test async blog generation
curl -X POST "https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/generate-enhanced?async_mode=true" \
  -H "Content-Type: application/json" \
  -d '{"topic":"Test","keywords":["test"],"use_google_search":false}'
```

### Option 2: Wait for Cooldown (Use Original Name)

Wait 10-15 minutes, then run:

```bash
./scripts/recreate-cloud-tasks-queue.sh
```

This will recreate `blog-generation-queue` with the original name.

---

## 📝 Queue Configuration

Both queues use the same configuration:
- **Location:** `europe-west1` (valid Cloud Tasks region)
- **Max Dispatches:** 100 per second
- **Max Concurrent:** 500 dispatches
- **Max Retry Duration:** 3600 seconds (1 hour)
- **Worker URL:** `https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/worker`

---

## 🔍 Verification

### Check Queue Status
```bash
# Check alternative queue
gcloud tasks queues describe blog-queue-dev --location=europe-west1

# Check original queue (after cooldown)
gcloud tasks queues describe blog-generation-queue --location=europe-west1
```

### List All Queues
```bash
gcloud tasks queues list --location=europe-west1
```

### Check Tasks in Queue
```bash
gcloud tasks list --queue=blog-queue-dev --location=europe-west1
```

---

## ⚠️ Important Notes

1. **Cooldown Period:** Google Cloud prevents immediate recreation of deleted queues
2. **Queue Location:** Must be `europe-west1` (or another valid Cloud Tasks region)
3. **Service Location:** Cloud Run service is in `europe-west9` (different region is OK)
4. **Worker URL:** Points to `europe-west9` service (correct)

---

## ✅ Next Steps

1. **Choose a queue:**
   - Use `blog-queue-dev` immediately, OR
   - Wait for `blog-generation-queue` cooldown

2. **Update Cloud Run** (if using alternative queue):
   ```bash
   gcloud run services update blog-writer-api-dev \
     --region=europe-west9 \
     --update-env-vars CLOUD_TASKS_QUEUE_NAME=blog-queue-dev
   ```

3. **Test async blog generation:**
   ```bash
   curl -X POST "https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/generate-enhanced?async_mode=true" \
     -H "Content-Type: application/json" \
     -d '{"topic":"Best Coffee Makers","keywords":["coffee"],"use_google_search":true}'
   ```

4. **Monitor job progress:**
   ```bash
   # Get job_id from response, then:
   curl "https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/jobs/{job_id}"
   ```

---

**Status:** ✅ Ready for testing (alternative queue available)


