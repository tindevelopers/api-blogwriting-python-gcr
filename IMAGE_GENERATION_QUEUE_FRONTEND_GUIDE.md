# Image Generation Queue - Frontend Implementation Guide

This guide explains how to integrate the image generation queue system with SSE streaming into your frontend application.

## Overview

The image generation API now **always** uses async queue processing and provides **SSE streaming** for real-time progress updates. This allows you to:

- Track image generation progress in real-time via Server-Sent Events (SSE)
- Handle long-running generation tasks without blocking
- Provide better user feedback with stage updates
- Retry failed generations automatically via Cloud Tasks
- Monitor generation history

## Backend Endpoints

### 1. Generate Image (Async Queue)
**Endpoint:** `POST /api/v1/images/generate`

**Request:**
```typescript
{
  prompt: string;
  provider?: 'stability_ai';
  style?: 'photographic' | 'digital-art' | 'anime' | '3d-model' | ...;
  aspect_ratio?: '16:9' | '1:1' | '9:16' | ...;
  quality?: 'draft' | 'standard' | 'high' | 'ultra';
  blog_id?: string;
  blog_job_id?: string;
}
```

**Response:**
```typescript
{
  job_id: string;              // Use this to track status
  status: "queued";
  message: "Image generation job queued successfully";
  estimated_completion_time: number;  // seconds
  is_draft: boolean;
}
```

### 2. SSE Streaming (Recommended) ⭐ NEW
**Endpoint:** `POST /api/v1/images/generate/stream`

Returns Server-Sent Events (SSE) stream with real-time stage updates.

**Stages:**
- `queued` - Job created and queued
- `processing` - Starting generation
- `generating` - AI generating image
- `uploading` - Uploading to storage
- `completed` - Image ready
- `error` - Generation failed

### 3. Get Job Status (Polling Alternative)
**Endpoint:** `GET /api/v1/images/jobs/{job_id}`

**Response:**
```typescript
{
  job_id: string;
  status: "queued" | "processing" | "completed" | "failed";
  progress_percentage: number;  // 0-100
  current_stage?: string;
  result?: {
    images: Array<{
      image_id: string;
      image_url: string;
      width: number;
      height: number;
      format: string;
      // ... other image data
    }>;
  };
  error_message?: string;
  estimated_time_remaining?: number;
  is_draft: boolean;
}
```

## Implementation Steps

### Step 1: Generate Image (Returns job_id)

```typescript
const generateImage = async (params: {
  prompt: string;
  style?: string;
  aspect_ratio?: string;
  quality?: 'draft' | 'standard' | 'high' | 'ultra';
  blog_id?: string;
  blog_job_id?: string;
}) => {
  try {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://your-api.run.app';
    
    const response = await fetch(`${API_BASE_URL}/api/v1/images/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Image generation failed');
    }

    const result = await response.json();
    
    // Always returns job_id (always async now)
    return {
      job_id: result.job_id,
      status: result.status,
      estimated_time: result.estimated_completion_time,
      is_draft: result.is_draft
    };
  } catch (error) {
    console.error('❌ Image generation error:', error);
    throw error;
  }
};
```

### Step 2: Track Queue Status

You have two options for tracking status:

#### Option A: SSE Streaming (Recommended) ⭐ NEW

Use the `/generate/stream` endpoint for real-time updates:

```typescript
const generateImageWithStream = async (
  params: ImageGenerationRequest,
  onProgress: (update: ImageStreamUpdate) => void
): Promise<ImageGenerationResult> => {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://your-api.run.app';
  
  const response = await fetch(`${API_BASE_URL}/api/v1/images/generate/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    throw new Error('Failed to start image generation stream');
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  let jobId: string | null = null;
  let finalResult: ImageGenerationResult | null = null;

  if (!reader) {
    throw new Error('Response body is not readable');
  }

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const update = JSON.parse(line.slice(6));
          
          if (update.job_id) {
            jobId = update.job_id;
          }

          // Call progress callback
          onProgress({
            stage: update.stage,
            progress: update.progress,
            message: update.message,
            job_id: update.job_id,
            status: update.status,
            data: update.data
          });

          // Check if completed
          if (update.stage === 'completed' && update.data?.result) {
            finalResult = {
              job_id: update.job_id,
              images: update.data.result.images || [],
              status: 'completed'
            };
          }

          // Check if failed
          if (update.stage === 'error') {
            throw new Error(update.data?.error || update.message || 'Image generation failed');
          }
        } catch (e) {
          console.error('Error parsing SSE update:', e);
        }
      }
    }
  }

  if (!finalResult) {
    throw new Error('Stream ended without completion');
  }

  return finalResult;
};
```

#### Option B: Polling (Alternative)

Create a React hook for SSE streaming:

```typescript
// hooks/useImageGenerationStream.ts
"use client";

import { useState, useCallback, useRef } from "react";

type ImageGenerationStage = 'queued' | 'processing' | 'generating' | 'uploading' | 'completed' | 'error';

interface ImageStreamUpdate {
  stage: ImageGenerationStage;
  progress: number;
  message?: string;
  job_id?: string;
  status?: string;
  data?: any;
}

interface ImageGenerationResult {
  job_id: string;
  images: Array<{
    image_id: string;
    image_url: string;
    width: number;
    height: number;
    format: string;
    [key: string]: any;
  }>;
  status: string;
}

export function useImageGenerationStream() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentStage, setCurrentStage] = useState<ImageGenerationStage | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ImageGenerationResult | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const generateWithStream = useCallback(async (
    params: {
      prompt: string;
      style?: string;
      aspect_ratio?: string;
      quality?: 'draft' | 'standard' | 'high' | 'ultra';
      blog_id?: string;
      blog_job_id?: string;
    },
    onProgress?: (update: ImageStreamUpdate) => void
  ): Promise<ImageGenerationResult> => {
    setIsGenerating(true);
    setError(null);
    setResult(null);
    setProgress(0);
    setCurrentStage(null);

    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://your-api.run.app';
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/images/generate/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error('Failed to start image generation stream');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let jobId: string | null = null;
      let finalResult: ImageGenerationResult | null = null;

      if (!reader) {
        throw new Error('Response body is not readable');
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const update = JSON.parse(line.slice(6));
              
              if (update.job_id) {
                jobId = update.job_id;
              }

              setCurrentStage(update.stage);
              setProgress(update.progress || 0);

              // Call progress callback
              if (onProgress) {
                onProgress(update);
              }

              // Check if completed
              if (update.stage === 'completed' && update.data?.result) {
                finalResult = {
                  job_id: update.job_id || jobId || '',
                  images: update.data.result.images || [],
                  status: 'completed'
                };
                setResult(finalResult);
              }

              // Check if failed
              if (update.stage === 'error') {
                const errorMsg = update.data?.error || update.message || 'Image generation failed';
                setError(errorMsg);
                throw new Error(errorMsg);
              }
            } catch (e) {
              if (e instanceof Error && e.message !== 'Image generation failed') {
                console.error('Error parsing SSE update:', e);
              } else {
                throw e;
              }
            }
          }
        }
      }

      if (!finalResult) {
        throw new Error('Stream ended without completion');
      }

      setIsGenerating(false);
      return finalResult;
    } catch (err) {
      setIsGenerating(false);
      const errorMsg = err instanceof Error ? err.message : 'Image generation failed';
      setError(errorMsg);
      throw err;
    }
  }, []);

  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsGenerating(false);
      setError('Generation cancelled');
    }
  }, []);

  return {
    generateWithStream,
    cancel,
    isGenerating,
    currentStage,
    progress,
    error,
    result,
  };
}
```

#### Option C: Polling (Alternative)

If you prefer polling instead of SSE:

```typescript
const pollImageJobStatus = async (jobId: string): Promise<any> => {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://your-api.run.app';
  const maxAttempts = 60; // 5 minutes max (5 second intervals)
  let attempts = 0;

  while (attempts < maxAttempts) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/images/jobs/${jobId}`);
      const data = await response.json();

      if (data.status === 'completed' && data.result?.images) {
        return data.result.images[0];
      }

      if (data.status === 'failed') {
        throw new Error(data.error_message || 'Image generation failed');
      }

      // Still processing - wait and retry
      await new Promise(resolve => setTimeout(resolve, 5000)); // 5 second intervals
      attempts++;
    } catch (error) {
      console.error('Error polling job status:', error);
      throw error;
    }
  }

  throw new Error('Image generation timeout');
};

// Usage
const jobResponse = await generateImage({ prompt: 'A sunset' });
const image = await pollImageJobStatus(jobResponse.job_id);
```

### Step 3: Complete Example Component (SSE Streaming)

```typescript
"use client";

import { useState, useEffect } from 'react';
import { useImageGenerationStream } from '@/hooks/useImageGenerationStream';

export function ImageGenerator() {
  const [generatedImage, setGeneratedImage] = useState<any>(null);
  
  const {
    generateWithStream,
    cancel,
    isGenerating,
    currentStage,
    progress,
    error,
    result
  } = useImageGenerationStream();

  const handleGenerateImage = async () => {
    try {
      const result = await generateWithStream(
        {
          prompt: 'A beautiful sunset over mountains',
          style: 'photographic',
          aspect_ratio: '16:9',
          quality: 'high',
        },
        (update) => {
          // Optional: Handle progress updates
          console.log(`Stage: ${update.stage}, Progress: ${update.progress}%`);
        }
      );

      if (result.images && result.images.length > 0) {
        setGeneratedImage(result.images[0]);
      }
    } catch (err) {
      console.error('Generation error:', err);
    }
  };

  // Update generated image when result is available
  useEffect(() => {
    if (result?.images && result.images.length > 0) {
      setGeneratedImage(result.images[0]);
    }
  }, [result]);

  return (
    <div>
      <button 
        onClick={handleGenerateImage}
        disabled={isGenerating}
      >
        {isGenerating ? 'Generating...' : 'Generate Image'}
      </button>

      {isGenerating && (
        <div className="mt-4">
          <p>Stage: {currentStage || 'queued'}</p>
          {progress > 0 && (
            <div>
              <p>Progress: {progress}%</p>
              <progress value={progress} max={100} />
            </div>
          )}
          <button onClick={cancel} className="mt-2 text-red-500">
            Cancel
          </button>
        </div>
      )}

      {error && (
        <p className="mt-4 text-red-500">Error: {error}</p>
      )}

      {generatedImage && (
        <div className="mt-4">
          <img 
            src={generatedImage.image_url} 
            alt={generatedImage.alt_text || 'Generated image'}
            className="max-w-full"
          />
        </div>
      )}
    </div>
  );
}
```

## Integration with Existing Image Insert Modal

If you're using the `ImageInsertModal` component, update it to use SSE streaming:

```typescript
// In ImageInsertModal.tsx or similar component

import { useEffect } from 'react';
import { useImageGenerationStream } from '@/hooks/useImageGenerationStream';

const ImageInsertModal = ({ onImageSelect, blogTopic, keywords }) => {
  const {
    generateWithStream,
    isGenerating,
    currentStage,
    progress,
    error,
    result
  } = useImageGenerationStream();

  const handleGenerateFromExcerpt = async (excerpt: string) => {
    try {
      const result = await generateWithStream({
        prompt: excerpt, // Use excerpt as prompt
        style: 'photographic',
        aspect_ratio: '16:9',
        quality: 'high',
        blog_topic: blogTopic,
      });

      if (result.images && result.images.length > 0) {
        onImageSelect(result.images[0]);
    }
  } catch (err) {
      console.error('Generation failed:', err);
  }
};

  // Auto-select image when generation completes
useEffect(() => {
    if (result?.images && result.images.length > 0) {
      onImageSelect(result.images[0]);
    }
  }, [result, onImageSelect]);

  return (
    <div>
      {/* Your UI here */}
      {isGenerating && (
        <div>
          <p>Stage: {currentStage}</p>
          <progress value={progress} max={100} />
        </div>
      )}
      {error && <p className="text-red-500">{error}</p>}
    </div>
  );
};
```

## Queue Status Endpoints

### Get Job Status (Polling)
```typescript
GET /api/v1/images/jobs/{job_id}

Response:
{
  job_id: string,
  status: 'pending' | 'queued' | 'processing' | 'completed' | 'failed',
  progress_percentage: number,
  current_stage?: string,
  result?: {
    images: Array<{
      image_id: string;
      image_url: string;
      width: number;
      height: number;
      format: string;
      // ... other image fields
    }>;
  },
  error_message?: string,
  estimated_time_remaining?: number,
  is_draft: boolean,
  created_at: string,
  started_at?: string,
  completed_at?: string
}
```

### Polling Example
```typescript
const pollImageJobStatus = async (jobId: string): Promise<any> => {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://your-api.run.app';
  const maxAttempts = 60; // 5 minutes max (5 second intervals)
  let attempts = 0;

  while (attempts < maxAttempts) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/images/jobs/${jobId}`);
      const data = await response.json();

      if (data.status === 'completed' && data.result?.images) {
        return data.result.images[0];
      }

      if (data.status === 'failed') {
        throw new Error(data.error_message || 'Image generation failed');
      }

      // Still processing - wait and retry
      await new Promise(resolve => setTimeout(resolve, 5000));
      attempts++;
    } catch (error) {
      console.error('Error polling job status:', error);
      throw error;
    }
  }

  throw new Error('Image generation timeout');
};
```

## Status Values

- `pending` - Job created, not yet queued
- `queued` - Request is in queue, waiting to start
- `processing` - Image generation in progress
- `completed` - Successfully generated (image available in `result`)
- `failed` - Generation failed (check `error_message`)
- `cancelled` - Generation was cancelled

## Best Practices

1. **Use SSE Streaming** - The `/generate/stream` endpoint provides real-time updates without polling overhead

2. **Always capture `job_id`** - The job_id is returned immediately and useful for tracking and history

3. **Show progress feedback** - Use the `progress` and `stage` from SSE updates to show users what's happening

4. **Handle errors gracefully** - Check for `error` in SSE updates and display user-friendly messages

5. **Store job_id** - Consider storing job_id in localStorage or state management for persistence across page refreshes

6. **Cancel support** - Use AbortController to allow users to cancel long-running generations

7. **Fallback to polling** - If SSE is not available, fallback to polling `/api/v1/images/jobs/{job_id}` every 2-5 seconds

## Migration from Old Implementation

If you have existing code that calls the image generation API:

**Before (Synchronous):**
```typescript
const result = await fetch('/api/v1/images/generate', {...});
const data = await result.json();
// Use data.images directly (synchronous)
```

**After (SSE Streaming - Recommended):**
```typescript
const { generateWithStream, result } = useImageGenerationStream();

await generateWithStream({
  prompt: 'A sunset',
  quality: 'high'
});

// result.images contains the generated images
```

**After (Polling Alternative):**
```typescript
// Step 1: Create job
const response = await fetch('/api/v1/images/generate', {...});
const { job_id } = await response.json();

// Step 2: Poll for status
const image = await pollImageJobStatus(job_id);
```

## Example: Full Integration with TipTap Editor

```typescript
// In TipTapEditor component or ImageInsertModal

import { useEffect } from 'react';
import { useImageGenerationStream } from '@/hooks/useImageGenerationStream';

const ImageInsertModal = ({ editor, onClose }) => {
  const {
    generateWithStream,
    isGenerating,
    currentStage,
    progress,
    error,
    result
  } = useImageGenerationStream();

  const handleGenerateImage = async (excerpt: string) => {
    try {
      await generateWithStream({
        prompt: excerpt,
        style: 'photographic',
        aspect_ratio: '16:9',
        quality: 'high',
      });
    } catch (error) {
      console.error('Generation failed:', error);
    }
  };

  // Auto-insert image when generation completes
  useEffect(() => {
    if (result?.images && result.images.length > 0 && editor) {
      const image = result.images[0];
      editor.chain().focus().setImage({
        src: image.image_url,
        alt: image.alt_text || '',
      }).run();
      onClose();
    }
  }, [result, editor, onClose]);

  return (
    <div>
      {/* Your UI here */}
      {isGenerating && (
        <div>
          <p>Stage: {currentStage}</p>
          <progress value={progress} max={100} />
        </div>
      )}
      {error && <p className="text-red-500">{error}</p>}
    </div>
  );
};
```

## Troubleshooting

### Job ID not returned
- Check that the API request was successful (status 200)
- Verify the response includes `job_id` field
- Check browser console for errors

### SSE stream not connecting
- Verify the endpoint URL is correct: `/api/v1/images/generate/stream`
- Check that your API base URL is configured correctly
- Ensure CORS is properly configured on the backend
- Check browser console for connection errors

### Status stuck on "processing"
- Check network connectivity
- Verify the job exists: `GET /api/v1/images/jobs/{job_id}`
- Check server logs for errors
- Try polling the status endpoint as fallback

### Image not appearing after "completed" stage
- Verify `result.images` array is present in SSE final update
- Check that `image_url` is accessible
- Verify Cloudinary/storage upload completed successfully
- Check browser network tab for image loading errors

### SSE stream disconnects early
- Check for network timeouts
- Verify backend supports long-running connections
- Implement reconnection logic if needed
- Fallback to polling if SSE is unreliable

## Next Steps

1. ✅ **SSE Streaming Endpoint** - Already implemented at `/api/v1/images/generate/stream`
2. ✅ **React Hook** - Use `useImageGenerationStream` hook provided above
3. Update your image generation UI to show progress with SSE updates
4. Add error handling and retry logic
5. Consider adding job history view using `/api/v1/images/jobs` endpoint

## Complete TypeScript Types

```typescript
// types/image-generation.ts

export interface ImageGenerationRequest {
  prompt: string;
  provider?: 'stability_ai';
  style?: 'photographic' | 'digital-art' | 'anime' | '3d-model' | 'cinematic' | 'comic-book' | 'fantasy-art' | 'line-art' | 'neon-punk' | 'origami' | 'pixel-art' | 'tile-texture';
  aspect_ratio?: '16:9' | '1:1' | '21:9' | '2:3' | '3:2' | '4:5' | '5:4' | '9:16' | '9:21';
  quality?: 'draft' | 'standard' | 'high' | 'ultra';
  negative_prompt?: string;
  seed?: number;
  blog_id?: string;
  blog_job_id?: string;
}

export interface ImageStreamUpdate {
  stage: 'queued' | 'processing' | 'generating' | 'uploading' | 'completed' | 'error';
  progress: number;
  message?: string;
  job_id?: string;
  status?: string;
  data?: {
    result?: {
      images: Array<{
        image_id: string;
        image_url: string;
        width: number;
        height: number;
        format: string;
        [key: string]: any;
      }>;
    };
    error?: string;
    is_draft?: boolean;
    blog_id?: string;
    blog_job_id?: string;
  };
}

export interface ImageGenerationResult {
  job_id: string;
  images: Array<{
    image_id: string;
    image_url: string;
    width: number;
    height: number;
    format: string;
    [key: string]: any;
  }>;
  status: string;
}
```

