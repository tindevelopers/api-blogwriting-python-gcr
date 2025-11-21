# Image Generation Cloud Tasks Implementation

**Version:** 1.3.4  
**Date:** 2025-11-20  
**Status:** ✅ Complete

---

## Overview

Cloud Tasks integration for image generation has been successfully implemented, enabling asynchronous processing of image generation requests with support for draft/final workflows and batch operations.

---

## What Was Implemented

### 1. Cloud Tasks Service Extension

**File:** `src/blog_writer_sdk/services/cloud_tasks_service.py`

Added `create_image_generation_task()` method:
- Creates Cloud Tasks for image generation jobs
- Supports separate image generation queue
- Configurable queue name via `CLOUD_TASKS_IMAGE_QUEUE_NAME` env var

### 2. Draft/Final Model Selection

**File:** `src/blog_writer_sdk/image/stability_ai_provider.py`

**Model Mapping:**
- **Draft:** `stable-diffusion-xl-turbo` (~3 seconds, lower cost)
- **Standard:** `stable-diffusion-xl-1024-v1-0` (~15 seconds)
- **High:** `stable-diffusion-xl-1024-v1-0` with more steps (~20 seconds)
- **Ultra:** `stable-diffusion-3.5-large` (~30 seconds, highest quality)

**Quality-Based Parameters:**
- Draft: 20 steps, cfg_scale 5.0
- Standard: 30 steps, cfg_scale 7.0
- High: 50 steps, cfg_scale 7.0
- Ultra: 60 steps, cfg_scale 7.0

### 3. Image Job Models

**File:** `src/blog_writer_sdk/models/image_job_models.py`

New models:
- `ImageJobStatus` - Job status enumeration
- `ImageGenerationJobStatus` - Job tracking with Cloud Tasks metadata
- `ImageJobStatusResponse` - API response for job status
- `CreateImageJobResponse` - Response when creating async job
- `BatchImageGenerationRequest` - Batch image generation request
- `BatchImageGenerationResponse` - Batch job response

**Features:**
- Blog linking (`blog_id`, `blog_job_id`)
- Draft/final workflow tracking (`is_draft`, `final_job_id`, `draft_job_id`)
- Progress tracking and error handling

### 4. Async Image Generation Endpoint

**Endpoint:** `POST /api/v1/images/generate-async`

**Request:**
```json
{
  "prompt": "A futuristic cityscape at sunset",
  "quality": "draft",  // or "standard", "high", "ultra"
  "provider": "stability_ai",
  "style": "photographic",
  "aspect_ratio": "16:9",
  "blog_id": "optional-blog-id",
  "blog_job_id": "optional-blog-job-id"
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "queued",
  "message": "Image generation job queued successfully",
  "estimated_completion_time": 5,  // seconds
  "is_draft": true
}
```

### 5. Image Worker Endpoint

**Endpoint:** `POST /api/v1/images/worker`

Internal endpoint called by Cloud Tasks to process image generation jobs.

**Features:**
- Updates job status throughout processing
- Handles errors and retries
- Stores results in job record
- Supports draft and final workflows

### 6. Job Status Endpoint

**Endpoint:** `GET /api/v1/images/jobs/{job_id}`

**Response:**
```json
{
  "job_id": "uuid",
  "status": "completed",
  "progress_percentage": 100.0,
  "current_stage": "processing_result",
  "created_at": "2025-11-20T10:00:00Z",
  "started_at": "2025-11-20T10:00:01Z",
  "completed_at": "2025-11-20T10:00:06Z",
  "result": {
    "success": true,
    "images": [
      {
        "url": "https://...",
        "width": 1024,
        "height": 1024
      }
    ],
    "generation_time_seconds": 5.2,
    "provider": "stability_ai",
    "model": "stable-diffusion-xl-turbo",
    "cost": 0.002
  },
  "is_draft": true,
  "final_job_id": null
}
```

### 7. Batch Image Generation Endpoint

**Endpoint:** `POST /api/v1/images/batch-generate`

**Request:**
```json
{
  "images": [
    {
      "prompt": "Hero image for blog",
      "quality": "draft",
      "aspect_ratio": "16:9"
    },
    {
      "prompt": "Featured image",
      "quality": "draft",
      "aspect_ratio": "1:1"
    }
  ],
  "blog_id": "blog-uuid",
  "blog_job_id": "blog-job-uuid",
  "workflow": "draft_then_final"  // or "final_only"
}
```

**Response:**
```json
{
  "batch_id": "uuid",
  "job_ids": ["job-1", "job-2"],
  "status": "queued",
  "total_images": 2,
  "estimated_completion_time": 10
}
```

---

## Workflow Patterns

### Pattern 1: Draft Then Final

```typescript
// Step 1: Generate draft images (fast)
const draftResponse = await apiClient.post('/api/v1/images/generate-async', {
  prompt: 'Hero image',
  quality: 'draft',
  blog_id: blogId
});

// Step 2: Poll for draft completion
const draftStatus = await pollJobStatus(draftResponse.job_id);

// Step 3: User approves draft, generate final
const finalResponse = await apiClient.post('/api/v1/images/generate-async', {
  prompt: 'Hero image',
  quality: 'high',
  blog_id: blogId
});
```

### Pattern 2: Batch Generation

```typescript
// Generate all images for a blog at once
const batchResponse = await apiClient.post('/api/v1/images/batch-generate', {
  images: [
    { prompt: 'Hero', quality: 'draft' },
    { prompt: 'Featured', quality: 'draft' },
    { prompt: 'Inline 1', quality: 'draft' }
  ],
  blog_id: blogId,
  workflow: 'draft_then_final'
});

// Poll all jobs
const statuses = await Promise.all(
  batchResponse.job_ids.map(id => pollJobStatus(id))
);
```

### Pattern 3: Upscale Draft to Final

```typescript
// Generate draft
const draft = await generateImageAsync({ prompt: '...', quality: 'draft' });

// After approval, upscale draft
const upscaled = await apiClient.post('/api/v1/images/upscale', {
  image_url: draft.result.images[0].url,
  scale: 2
});
```

---

## Environment Variables

### Required

```bash
# Cloud Tasks Configuration
GOOGLE_CLOUD_PROJECT=api-ai-blog-writer
CLOUD_TASKS_QUEUE_LOCATION=europe-west1
CLOUD_TASKS_IMAGE_QUEUE_NAME=image-generation-queue  # New

# Cloud Run Configuration
CLOUD_RUN_SERVICE_URL=https://blog-writer-api-dev-kq42l26tuq-od.a.run.app
CLOUD_RUN_WORKER_URL=https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/images/worker

# Stability AI
STABILITY_AI_API_KEY=your-api-key
```

### Queue Setup

Create Cloud Tasks queue for images:

```bash
gcloud tasks queues create image-generation-queue \
  --location=europe-west1 \
  --project=api-ai-blog-writer \
  --max-dispatches-per-second=100 \
  --max-concurrent-dispatches=500
```

---

## API Endpoints Summary

### New Endpoints

1. **POST** `/api/v1/images/generate-async` - Create async image job
2. **GET** `/api/v1/images/jobs/{job_id}` - Get job status
3. **POST** `/api/v1/images/batch-generate` - Batch image generation
4. **POST** `/api/v1/images/worker` - Internal worker (Cloud Tasks)

### Existing Endpoints (Still Available)

1. **POST** `/api/v1/images/generate` - Synchronous generation
2. **POST** `/api/v1/images/variations` - Image variations
3. **POST** `/api/v1/images/upscale` - Image upscaling
4. **POST** `/api/v1/images/edit` - Image editing

---

## Cost Optimization

### Draft vs Final Costs

| Quality | Model | Time | Cost | Use Case |
|---------|-------|------|------|----------|
| Draft | turbo | ~3s | $0.002 | Quick previews |
| Standard | xl-1024 | ~15s | $0.004 | Standard quality |
| High | xl-1024 | ~20s | $0.006 | High quality |
| Ultra | 3.5-large | ~30s | $0.008 | Publication ready |

**Savings:** Using draft workflow saves ~60% cost and ~80% time for initial previews.

---

## Benefits

✅ **Non-blocking requests** - API returns immediately with job_id  
✅ **Better scalability** - Handle 100+ concurrent image generations  
✅ **Automatic retries** - Cloud Tasks handles failures  
✅ **Progress tracking** - Real-time status updates  
✅ **Draft workflow** - Fast previews before final generation  
✅ **Batch operations** - Generate multiple images efficiently  
✅ **Blog linking** - Track which images belong to which blog  
✅ **Cost optimization** - Use draft images for iteration  

---

## Next Steps

1. **Create Cloud Tasks Queue:**
   ```bash
   gcloud tasks queues create image-generation-queue --location=europe-west1
   ```

2. **Set Environment Variables:**
   - `CLOUD_TASKS_IMAGE_QUEUE_NAME=image-generation-queue`
   - `CLOUD_RUN_WORKER_URL` (if different from service URL)

3. **Deploy:**
   ```bash
   git push origin develop
   ```

4. **Test:**
   ```bash
   curl -X POST "https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/images/generate-async" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "test image", "quality": "draft"}'
   ```

---

## Migration Guide

### From Synchronous to Async

**Before:**
```typescript
const response = await apiClient.post('/api/v1/images/generate', {
  prompt: '...',
  quality: 'standard'
});
// Waits 15 seconds
const imageUrl = response.data.images[0].url;
```

**After:**
```typescript
// Create async job
const job = await apiClient.post('/api/v1/images/generate-async', {
  prompt: '...',
  quality: 'standard'
});

// Poll for completion
const status = await pollJobStatus(job.data.job_id);
const imageUrl = status.result.images[0].url;
```

---

**Version:** 1.3.4  
**Last Updated:** 2025-11-20  
**Status:** ✅ Ready for Deployment

