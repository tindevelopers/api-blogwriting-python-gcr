# Image Generation Cloud Tasks Setup - Complete ✅

**Date:** 2025-11-20  
**Status:** ✅ Configured and Ready

---

## What Was Configured

### 1. Cloud Tasks Queue Created ✅

**Queue Name:** `image-generation-queue`  
**Location:** `europe-west1`  
**Project:** `api-ai-blog-writer`

**Configuration:**
- Max dispatches per second: **200** (higher than blog queue for faster image processing)
- Max concurrent dispatches: **1000** (higher than blog queue for batch operations)
- Max retry duration: **30 minutes** (shorter than blog queue, images are faster)

**Created via:**
```bash
./scripts/setup-image-cloud-tasks-queue.sh
```

### 2. Environment Variables Added ✅

**Secret:** `blog-writer-env-dev` (and staging/prod as needed)

**Variables Added:**
- `CLOUD_TASKS_IMAGE_QUEUE_NAME=image-generation-queue` (new)
- `CLOUD_TASKS_QUEUE_LOCATION=europe-west1` (already exists for blog generation)
- `GOOGLE_CLOUD_PROJECT=api-ai-blog-writer` (already exists for blog generation)

**Added via:**
```bash
./scripts/add-image-cloud-tasks-secrets.sh dev
```

---

## Configuration Pattern

### Follows Blog Generation Pattern ✅

Image generation Cloud Tasks configuration follows the **exact same pattern** as blog generation:

| Configuration | Blog Generation | Image Generation |
|---------------|----------------|------------------|
| **Queue Location** | `europe-west1` | `europe-west1` ✅ |
| **Project ID** | `api-ai-blog-writer` | `api-ai-blog-writer` ✅ |
| **Worker URL Pattern** | `/api/v1/blog/worker` | `/api/v1/images/worker` ✅ |
| **Service** | `CloudTasksService` | `CloudTasksService` ✅ |
| **Method** | `create_blog_generation_task()` | `create_image_generation_task()` ✅ |

**Only Difference:**
- **Queue Name:** `blog-generation-queue` vs `image-generation-queue`
- **Queue Settings:** Image queue has higher throughput (200/sec vs 100/sec)

---

## Environment Variables

### Already Configured (from blog generation):
- ✅ `GOOGLE_CLOUD_PROJECT=api-ai-blog-writer`
- ✅ `CLOUD_TASKS_QUEUE_LOCATION=europe-west1`
- ✅ `CLOUD_RUN_SERVICE_URL` (or `CLOUD_RUN_WORKER_URL`)

### Newly Added:
- ✅ `CLOUD_TASKS_IMAGE_QUEUE_NAME=image-generation-queue`

---

## Code Implementation

### Service Method ✅

**File:** `src/blog_writer_sdk/services/cloud_tasks_service.py`

```python
def create_image_generation_task(
    self,
    request_data: Dict[str, Any],
    worker_url: str,
    schedule_time: Optional[int] = None,
    queue_name: Optional[str] = None
) -> str:
    """Create a Cloud Task for image generation."""
    # Uses same pattern as create_blog_generation_task()
    # Only difference: queue_name parameter
```

### Endpoint Implementation ✅

**File:** `src/blog_writer_sdk/api/image_generation.py`

```python
@router.post("/generate-async")
async def generate_image_async(...):
    # Gets Cloud Tasks service
    cloud_tasks_service = get_cloud_tasks_service()
    
    # Creates task with image queue name
    task_name = cloud_tasks_service.create_image_generation_task(
        request_data={...},
        worker_url=worker_url,
        queue_name=os.getenv("CLOUD_TASKS_IMAGE_QUEUE_NAME", "image-generation-queue")
    )
```

---

## Setup Scripts Created

### 1. Queue Setup Script ✅

**File:** `scripts/setup-image-cloud-tasks-queue.sh`

**Usage:**
```bash
export GOOGLE_CLOUD_PROJECT=api-ai-blog-writer
./scripts/setup-image-cloud-tasks-queue.sh
```

**What it does:**
- Creates `image-generation-queue` in `europe-west1`
- Sets optimal queue configuration for image processing
- Provides next steps

### 2. Secrets Setup Script ✅

**File:** `scripts/add-image-cloud-tasks-secrets.sh`

**Usage:**
```bash
export GOOGLE_CLOUD_PROJECT=api-ai-blog-writer
./scripts/add-image-cloud-tasks-secrets.sh dev    # for dev
./scripts/add-image-cloud-tasks-secrets.sh staging # for staging
./scripts/add-image-cloud-tasks-secrets.sh prod    # for prod
```

**What it does:**
- Adds `CLOUD_TASKS_IMAGE_QUEUE_NAME` to secret
- Preserves existing `GOOGLE_CLOUD_PROJECT` and `CLOUD_TASKS_QUEUE_LOCATION`
- Updates secret version

---

## Next Steps

### 1. Redeploy Service ✅

The service needs to be redeployed to pick up the new secret version:

```bash
# Via Cloud Build (automatic on push to develop)
git push origin develop

# Or manually
gcloud run deploy blog-writer-api-dev \
  --region=europe-west9 \
  --project=api-ai-blog-writer
```

### 2. Test Async Endpoints ✅

After deployment, test the async endpoints:

```bash
# Test async image generation
curl -X POST "https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/images/generate-async" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful sunset",
    "quality": "draft",
    "aspect_ratio": "16:9"
  }'

# Should return:
# {
#   "job_id": "uuid",
#   "status": "queued",
#   "message": "Image generation job queued successfully",
#   "estimated_completion_time": 5,
#   "is_draft": true
# }
```

### 3. Monitor Queue ✅

Monitor the Cloud Tasks queue in Cloud Console:
- **Queue:** `image-generation-queue`
- **Location:** `europe-west1`
- **Metrics:** Tasks created, executed, failed

---

## Verification Checklist

- ✅ Queue created: `image-generation-queue`
- ✅ Queue location: `europe-west1`
- ✅ Queue configuration: 200/sec, 1000 concurrent
- ✅ Environment variables added to secret
- ✅ Code implementation complete
- ✅ Setup scripts created
- ⏳ Service redeployed (pending)
- ⏳ Endpoints tested (pending)

---

## Summary

✅ **Cloud Tasks for image generation is now configured following the exact same pattern as blog generation.**

**Key Points:**
1. ✅ Uses same Cloud Tasks service (`CloudTasksService`)
2. ✅ Uses same queue location (`europe-west1`)
3. ✅ Uses same project (`api-ai-blog-writer`)
4. ✅ Uses same worker URL pattern (`/api/v1/images/worker`)
5. ✅ Only difference: Queue name (`image-generation-queue`)

**Status:** ✅ **Ready for deployment and testing**

---

**Last Updated:** 2025-11-20  
**Configuration Complete:** ✅

