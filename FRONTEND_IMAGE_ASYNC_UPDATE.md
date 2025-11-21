# Frontend Update: Async Image Generation ⭐ NEW

**Date:** 2025-11-20  
**Version:** 1.3.4  
**Status:** ✅ Ready for Integration

---

## 🎯 What's New

### Async Image Generation Endpoints

Three new endpoints have been added for asynchronous image generation via Cloud Tasks:

1. **`POST /api/v1/images/generate-async`** - Create async image job
2. **`GET /api/v1/images/jobs/{job_id}`** - Poll job status
3. **`POST /api/v1/images/batch-generate`** - Batch image generation

### Benefits

✅ **Non-blocking** - API returns immediately with `job_id`  
✅ **Better UX** - No long waits, progress tracking available  
✅ **Batch operations** - Generate multiple images efficiently  
✅ **Draft workflow** - Fast previews before final generation  
✅ **Blog linking** - Track which images belong to which blog  

---

## 📝 Quick Integration Guide

### 1. Generate Image Async

```typescript
// Create async job
const job = await apiClient.post('/api/v1/images/generate-async', {
  prompt: 'Hero image for blog',
  quality: 'draft', // Fast preview
  aspect_ratio: '16:9'
});

// Poll for completion
const result = await pollJobStatus(job.data.job_id);
const imageUrl = result.images[0].url;
```

### 2. Batch Generation

```typescript
// Generate all images for a blog at once
const batch = await apiClient.post('/api/v1/images/batch-generate', {
  images: [
    { prompt: 'Hero', quality: 'draft' },
    { prompt: 'Featured', quality: 'draft' }
  ],
  blog_id: blogId,
  workflow: 'draft_then_final'
});

// Poll all jobs
const results = await Promise.all(
  batch.data.job_ids.map(id => pollJobStatus(id))
);
```

### 3. Polling Helper

```typescript
async function pollJobStatus(jobId: string, maxWait = 300000) {
  const startTime = Date.now();
  
  while (Date.now() - startTime < maxWait) {
    const status = await apiClient.get(`/api/v1/images/jobs/${jobId}`);
    
    if (status.data.status === 'completed') {
      return status.data.result;
    }
    
    if (status.data.status === 'failed') {
      throw new Error(status.data.error_message);
    }
    
    // Exponential backoff
    const waitTime = Math.min(1000 * Math.pow(1.5, attempts), 10000);
    await new Promise(resolve => setTimeout(resolve, waitTime));
  }
  
  throw new Error('Job timeout');
}
```

---

## 🔄 Migration from Synchronous

### Before (Synchronous)

```typescript
// Blocks for 15+ seconds
const response = await apiClient.post('/api/v1/images/generate', {
  prompt: '...',
  quality: 'standard'
});
const imageUrl = response.data.images[0].url;
```

### After (Async)

```typescript
// Returns immediately
const job = await apiClient.post('/api/v1/images/generate-async', {
  prompt: '...',
  quality: 'standard'
});

// Poll for result
const result = await pollJobStatus(job.data.job_id);
const imageUrl = result.images[0].url;
```

---

## 💡 Recommended Workflow

### Draft → Final Pattern

```typescript
// Step 1: Generate draft (fast, ~3 seconds)
const draftJob = await apiClient.post('/api/v1/images/generate-async', {
  prompt: 'Hero image',
  quality: 'draft'
});

const draftResult = await pollJobStatus(draftJob.data.job_id);
// Show draft to user for approval

// Step 2: Generate final (high quality, ~15 seconds)
if (userApproves) {
  const finalJob = await apiClient.post('/api/v1/images/generate-async', {
    prompt: 'Hero image',
    quality: 'high'
  });
  
  const finalResult = await pollJobStatus(finalJob.data.job_id);
  // Use final image
}
```

### Batch Generation Pattern

```typescript
// Generate all images for blog at once
const batch = await apiClient.post('/api/v1/images/batch-generate', {
  images: blogImagePrompts.map(prompt => ({
    prompt,
    quality: 'draft',
    aspect_ratio: '16:9'
  })),
  blog_id: blogId,
  workflow: 'draft_then_final'
});

// Show progress
const progress = await Promise.all(
  batch.data.job_ids.map(async (jobId) => {
    const status = await apiClient.get(`/api/v1/images/jobs/${jobId}`);
    return {
      jobId,
      progress: status.data.progress_percentage,
      status: status.data.status
    };
  })
);
```

---

## 📊 TypeScript Types

```typescript
interface ImageGenerationJobResponse {
  job_id: string;
  status: 'pending' | 'queued' | 'processing' | 'completed' | 'failed';
  message: string;
  estimated_completion_time?: number;
  is_draft: boolean;
}

interface ImageJobStatusResponse {
  job_id: string;
  status: 'pending' | 'queued' | 'processing' | 'completed' | 'failed';
  progress_percentage: number;
  current_stage?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  result?: {
    success: boolean;
    images: Array<{
      url: string;
      width: number;
      height: number;
    }>;
    generation_time_seconds: number;
    provider: string;
    model: string;
    cost: number;
  };
  error_message?: string;
  estimated_time_remaining?: number;
  is_draft: boolean;
  final_job_id?: string;
}

interface BatchImageGenerationResponse {
  batch_id: string;
  job_ids: string[];
  status: 'pending' | 'queued' | 'processing' | 'completed' | 'failed';
  total_images: number;
  estimated_completion_time?: number;
}
```

---

## ⚠️ Error Handling

```typescript
try {
  const job = await apiClient.post('/api/v1/images/generate-async', {...});
  const result = await pollJobStatus(job.data.job_id);
} catch (error) {
  if (error.response?.status === 500) {
    // Cloud Tasks not configured - fallback to synchronous
    const syncResult = await apiClient.post('/api/v1/images/generate', {...});
  } else {
    // Handle other errors
    console.error('Image generation failed:', error);
  }
}
```

---

## 📚 Full Documentation

See `FRONTEND_INTEGRATION_V1.3.4.md` for complete API documentation.

---

**Status:** ✅ Ready for Integration  
**Breaking Changes:** None (new endpoints, existing endpoints unchanged)

