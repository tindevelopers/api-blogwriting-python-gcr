# Frontend Framework Examples - Image Generation Integration

**Version:** 2.0.0  
**Date:** 2025-01-15

---

## 📚 Table of Contents

1. [Next.js (React) with TypeScript](#nextjs-react-with-typescript)
2. [Vue.js 3 with Composition API](#vuejs-3-with-composition-api)
3. [Angular with TypeScript](#angular-with-typescript)
4. [SvelteKit](#sveltekit)
5. [React with Tailwind CSS](#react-with-tailwind-css)
6. [React with Material-UI](#react-with-material-ui)

---

## Next.js (React) with TypeScript

### Complete Implementation

#### 1. API Service Layer

```typescript
// lib/api/imageGeneration.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://your-api-url.com';

export interface ImageSuggestion {
  image_type: 'featured' | 'section_header' | 'infographic';
  style: string;
  aspect_ratio: string;
  prompt: string;
  prompt_variations: string[];
  alt_text: string;
  placement: {
    position: number;
    section: string;
    priority: number;
  };
}

export interface ImageSuggestionsResponse {
  suggestions: ImageSuggestion[];
  total_suggestions: number;
  recommended_count: number;
}

export class ImageGenerationService {
  static async getSuggestions(
    content: string,
    topic: string,
    keywords: string[],
    tone: string = 'professional'
  ): Promise<ImageSuggestionsResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/images/suggestions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, topic, keywords, tone }),
    });

    if (!response.ok) {
      throw new Error(`Failed to get suggestions: ${response.statusText}`);
    }

    return response.json();
  }

  static async generateFromContent(
    content: string,
    topic: string,
    keywords: string[],
    imageType: 'featured' | 'section_header' | 'infographic',
    tone: string = 'professional',
    sectionTitle?: string
  ): Promise<{ job_id: string; status: string }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/images/generate-from-content`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content,
        topic,
        keywords,
        image_type: imageType,
        tone,
        section_title: sectionTitle,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to generate image: ${response.statusText}`);
    }

    return response.json();
  }

  static async checkJobStatus(jobId: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/v1/images/jobs/${jobId}`);
    if (!response.ok) {
      throw new Error(`Failed to check job status: ${response.statusText}`);
    }
    return response.json();
  }
}
```

#### 2. Custom Hook

```typescript
// hooks/useImageSuggestions.ts
import { useState, useCallback, useEffect } from 'react';
import { ImageGenerationService, ImageSuggestion } from '@/lib/api/imageGeneration';

export const useImageSuggestions = (
  content: string,
  topic: string,
  keywords: string[],
  tone: string = 'professional'
) => {
  const [suggestions, setSuggestions] = useState<ImageSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSuggestions = useCallback(async () => {
    if (!content || !topic) return;

    setLoading(true);
    setError(null);

    try {
      const data = await ImageGenerationService.getSuggestions(content, topic, keywords, tone);
      setSuggestions(data.suggestions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [content, topic, keywords, tone]);

  useEffect(() => {
    fetchSuggestions();
  }, [fetchSuggestions]);

  return { suggestions, loading, error, refetch: fetchSuggestions };
};
```

#### 3. Image Generation Hook with Job Polling

```typescript
// hooks/useImageGeneration.ts
import { useState, useCallback, useRef } from 'react';
import { ImageGenerationService } from '@/lib/api/imageGeneration';

export const useImageGeneration = () => {
  const [generating, setGenerating] = useState(false);
  const [jobStatus, setJobStatus] = useState<Map<string, any>>(new Map());
  const pollingIntervals = useRef<Map<string, NodeJS.Timeout>>(new Map());

  const generateImage = useCallback(async (
    content: string,
    topic: string,
    keywords: string[],
    imageType: 'featured' | 'section_header' | 'infographic',
    tone: string = 'professional',
    sectionTitle?: string
  ): Promise<string> => {
    setGenerating(true);

    try {
      const { job_id } = await ImageGenerationService.generateFromContent(
        content,
        topic,
        keywords,
        imageType,
        tone,
        sectionTitle
      );

      // Start polling
      startPolling(job_id);

      return job_id;
    } catch (err) {
      throw err;
    } finally {
      setGenerating(false);
    }
  }, []);

  const startPolling = useCallback((jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const status = await ImageGenerationService.checkJobStatus(jobId);
        setJobStatus(prev => new Map(prev).set(jobId, status));

        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(interval);
          pollingIntervals.current.delete(jobId);
        }
      } catch (err) {
        console.error('Polling error:', err);
        clearInterval(interval);
        pollingIntervals.current.delete(jobId);
      }
    }, 2000);

    pollingIntervals.current.set(jobId, interval);
  }, []);

  const stopPolling = useCallback((jobId: string) => {
    const interval = pollingIntervals.current.get(jobId);
    if (interval) {
      clearInterval(interval);
      pollingIntervals.current.delete(jobId);
    }
  }, []);

  return {
    generating,
    jobStatus,
    generateImage,
    stopPolling,
  };
};
```

#### 4. Component with Tailwind CSS

```typescript
// components/ImageSuggestionsPanel.tsx
'use client';

import React from 'react';
import { useImageSuggestions } from '@/hooks/useImageSuggestions';
import { useImageGeneration } from '@/hooks/useImageGeneration';
import { ImageSuggestion } from '@/lib/api/imageGeneration';

interface ImageSuggestionsPanelProps {
  content: string;
  topic: string;
  keywords: string[];
  tone?: string;
  onImageGenerated?: (image: any, suggestion: ImageSuggestion) => void;
}

export const ImageSuggestionsPanel: React.FC<ImageSuggestionsPanelProps> = ({
  content,
  topic,
  keywords,
  tone = 'professional',
  onImageGenerated,
}) => {
  const { suggestions, loading, error } = useImageSuggestions(content, topic, keywords, tone);
  const { generating, jobStatus, generateImage } = useImageGeneration();
  const [generatingJobs, setGeneratingJobs] = useState<Set<string>>(new Set());

  const handleGenerate = async (suggestion: ImageSuggestion) => {
    try {
      const jobId = await generateImage(
        content,
        topic,
        keywords,
        suggestion.image_type,
        tone,
        suggestion.placement.section
      );
      setGeneratingJobs(prev => new Set(prev).add(jobId));

      // Check for completion
      const checkCompletion = setInterval(async () => {
        const status = jobStatus.get(jobId);
        if (status?.status === 'completed' && status.result) {
          clearInterval(checkCompletion);
          setGeneratingJobs(prev => {
            const next = new Set(prev);
            next.delete(jobId);
            return next;
          });
          if (onImageGenerated) {
            onImageGenerated(status.result.images[0], suggestion);
          }
        }
      }, 2000);
    } catch (err) {
      console.error('Generation failed:', err);
    }
  };

  if (loading) {
    return (
      <div className="p-6 bg-gray-50 rounded-lg">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-800">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="p-6 bg-white border border-gray-200 rounded-lg shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Image Suggestions</h3>
        <span className="text-sm text-gray-500">
          {suggestions.length} suggestions
        </span>
      </div>

      <div className="space-y-4">
        {suggestions.map((suggestion, index) => {
          const isGenerating = Array.from(generatingJobs).some(jobId => {
            const status = jobStatus.get(jobId);
            return status?.status === 'processing';
          });

          return (
            <div
              key={index}
              className={`p-4 border rounded-lg transition-all ${
                suggestion.placement.priority >= 4
                  ? 'border-green-300 bg-green-50'
                  : 'border-gray-200 bg-white'
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900 capitalize">
                      {suggestion.image_type.replace('_', ' ')}
                    </span>
                    {suggestion.placement.priority >= 4 && (
                      <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded">
                        Recommended
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    {suggestion.placement.section} • Priority: {suggestion.placement.priority}/5
                  </p>
                </div>
              </div>

              <p className="text-sm text-gray-700 mb-2">{suggestion.prompt}</p>
              <p className="text-xs text-gray-500 mb-3">
                <strong>Alt Text:</strong> {suggestion.alt_text}
              </p>

              <div className="flex items-center gap-4 text-xs text-gray-500 mb-3">
                <span>Style: {suggestion.style}</span>
                <span>Aspect: {suggestion.aspect_ratio}</span>
              </div>

              <button
                onClick={() => handleGenerate(suggestion)}
                disabled={isGenerating}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {isGenerating ? 'Generating...' : 'Generate Image'}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};
```

#### 5. Server Action (Next.js App Router)

```typescript
// app/actions/imageActions.ts
'use server';

import { ImageGenerationService } from '@/lib/api/imageGeneration';

export async function getImageSuggestionsAction(
  content: string,
  topic: string,
  keywords: string[],
  tone: string = 'professional'
) {
  try {
    return await ImageGenerationService.getSuggestions(content, topic, keywords, tone);
  } catch (error) {
    throw new Error('Failed to get image suggestions');
  }
}

export async function generateImageAction(
  content: string,
  topic: string,
  keywords: string[],
  imageType: 'featured' | 'section_header' | 'infographic',
  tone: string = 'professional',
  sectionTitle?: string
) {
  try {
    return await ImageGenerationService.generateFromContent(
      content,
      topic,
      keywords,
      imageType,
      tone,
      sectionTitle
    );
  } catch (error) {
    throw new Error('Failed to generate image');
  }
}
```

---

## Vue.js 3 with Composition API

### Complete Implementation

#### 1. Composable Hook

```typescript
// composables/useImageGeneration.ts
import { ref, computed } from 'vue';
import type { Ref } from 'vue';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://your-api-url.com';

export interface ImageSuggestion {
  image_type: 'featured' | 'section_header' | 'infographic';
  style: string;
  aspect_ratio: string;
  prompt: string;
  prompt_variations: string[];
  alt_text: string;
  placement: {
    position: number;
    section: string;
    priority: number;
  };
}

export function useImageGeneration() {
  const generating = ref(false);
  const suggestions = ref<ImageSuggestion[]>([]);
  const error = ref<string | null>(null);
  const jobStatus = ref<Map<string, any>>(new Map());
  const pollingIntervals = ref<Map<string, number>>(new Map());

  const getSuggestions = async (
    content: string,
    topic: string,
    keywords: string[],
    tone: string = 'professional'
  ) => {
    generating.value = true;
    error.value = null;

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/images/suggestions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, topic, keywords, tone }),
      });

      if (!response.ok) {
        throw new Error(`Failed to get suggestions: ${response.statusText}`);
      }

      const data = await response.json();
      suggestions.value = data.suggestions;
      return data;
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error';
      throw err;
    } finally {
      generating.value = false;
    }
  };

  const generateFromContent = async (
    content: string,
    topic: string,
    keywords: string[],
    imageType: 'featured' | 'section_header' | 'infographic',
    tone: string = 'professional',
    sectionTitle?: string
  ): Promise<string> => {
    generating.value = true;
    error.value = null;

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/images/generate-from-content`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content,
          topic,
          keywords,
          image_type: imageType,
          tone,
          section_title: sectionTitle,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to generate image: ${response.statusText}`);
      }

      const data = await response.json();
      startPolling(data.job_id);
      return data.job_id;
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unknown error';
      throw err;
    } finally {
      generating.value = false;
    }
  };

  const startPolling = (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/images/jobs/${jobId}`);
        const status = await response.json();
        
        jobStatus.value.set(jobId, status);

        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(interval);
          pollingIntervals.value.delete(jobId);
        }
      } catch (err) {
        console.error('Polling error:', err);
        clearInterval(interval);
        pollingIntervals.value.delete(jobId);
      }
    }, 2000);

    pollingIntervals.value.set(jobId, interval as unknown as number);
  };

  const recommendedSuggestions = computed(() =>
    suggestions.value.filter(s => s.placement.priority >= 4)
  );

  return {
    generating,
    suggestions,
    error,
    jobStatus,
    recommendedSuggestions,
    getSuggestions,
    generateFromContent,
  };
}
```

#### 2. Vue Component

```vue
<!-- components/ImageSuggestionsPanel.vue -->
<template>
  <div class="image-suggestions-panel">
    <div v-if="loading" class="loading-state">
      <div class="animate-pulse space-y-4">
        <div class="h-4 bg-gray-200 rounded w-1/4"></div>
        <div class="h-32 bg-gray-200 rounded"></div>
      </div>
    </div>

    <div v-else-if="error" class="error-state">
      <p class="text-red-800">Error: {{ error }}</p>
    </div>

    <div v-else>
      <div class="panel-header">
        <h3>Image Suggestions</h3>
        <span class="count">{{ suggestions.length }} suggestions</span>
      </div>

      <div class="suggestions-list">
        <div
          v-for="(suggestion, index) in suggestions"
          :key="index"
          :class="[
            'suggestion-card',
            {
              'recommended': suggestion.placement.priority >= 4,
              'generating': generatingJobs.has(suggestion.image_type)
            }
          ]"
        >
          <div class="card-header">
            <div>
              <h4 class="type">{{ suggestion.image_type.replace('_', ' ') }}</h4>
              <p class="section">
                {{ suggestion.placement.section }} • Priority: {{ suggestion.placement.priority }}/5
              </p>
            </div>
            <span v-if="suggestion.placement.priority >= 4" class="badge">
              Recommended
            </span>
          </div>

          <p class="prompt">{{ suggestion.prompt }}</p>
          <p class="alt-text">
            <strong>Alt Text:</strong> {{ suggestion.alt_text }}
          </p>

          <div class="meta">
            <span>Style: {{ suggestion.style }}</span>
            <span>Aspect: {{ suggestion.aspect_ratio }}</span>
          </div>

          <button
            @click="handleGenerate(suggestion)"
            :disabled="generating || generatingJobs.has(suggestion.image_type)"
            class="generate-btn"
          >
            {{ generatingJobs.has(suggestion.image_type) ? 'Generating...' : 'Generate Image' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useImageGeneration, type ImageSuggestion } from '@/composables/useImageGeneration';

interface Props {
  content: string;
  topic: string;
  keywords: string[];
  tone?: string;
}

const props = withDefaults(defineProps<Props>(), {
  tone: 'professional',
});

const emit = defineEmits<{
  imageGenerated: [image: any, suggestion: ImageSuggestion];
}>();

const {
  generating,
  suggestions,
  error,
  jobStatus,
  getSuggestions,
  generateFromContent,
} = useImageGeneration();

const loading = ref(false);
const generatingJobs = ref<Set<string>>(new Set());

onMounted(async () => {
  if (props.content && props.topic) {
    loading.value = true;
    try {
      await getSuggestions(props.content, props.topic, props.keywords, props.tone);
    } finally {
      loading.value = false;
    }
  }
});

const handleGenerate = async (suggestion: ImageSuggestion) => {
  try {
    generatingJobs.value.add(suggestion.image_type);
    const jobId = await generateFromContent(
      props.content,
      props.topic,
      props.keywords,
      suggestion.image_type,
      props.tone,
      suggestion.placement.section
    );

    // Watch for completion
    const checkCompletion = setInterval(() => {
      const status = jobStatus.value.get(jobId);
      if (status?.status === 'completed' && status.result) {
        clearInterval(checkCompletion);
        generatingJobs.value.delete(suggestion.image_type);
        emit('imageGenerated', status.result.images[0], suggestion);
      }
    }, 2000);
  } catch (err) {
    generatingJobs.value.delete(suggestion.image_type);
    console.error('Generation failed:', err);
  }
};
</script>

<style scoped>
.image-suggestions-panel {
  @apply p-6 bg-white border border-gray-200 rounded-lg shadow-sm;
}

.panel-header {
  @apply flex items-center justify-between mb-4;
}

.panel-header h3 {
  @apply text-lg font-semibold text-gray-900;
}

.count {
  @apply text-sm text-gray-500;
}

.suggestions-list {
  @apply space-y-4;
}

.suggestion-card {
  @apply p-4 border rounded-lg transition-all;
  @apply border-gray-200 bg-white;
}

.suggestion-card.recommended {
  @apply border-green-300 bg-green-50;
}

.suggestion-card.generating {
  @apply opacity-75;
}

.card-header {
  @apply flex items-start justify-between mb-3;
}

.type {
  @apply font-medium text-gray-900 capitalize;
}

.section {
  @apply text-sm text-gray-600 mt-1;
}

.badge {
  @apply px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded;
}

.prompt {
  @apply text-sm text-gray-700 mb-2;
}

.alt-text {
  @apply text-xs text-gray-500 mb-3;
}

.meta {
  @apply flex items-center gap-4 text-xs text-gray-500 mb-3;
}

.generate-btn {
  @apply w-full px-4 py-2 bg-blue-600 text-white rounded-md;
  @apply hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed;
  @apply transition-colors;
}
</style>
```

---

## Angular with TypeScript

### Complete Implementation

#### 1. Service

```typescript
// services/image-generation.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { map, switchMap, interval } from 'rxjs';

export interface ImageSuggestion {
  image_type: 'featured' | 'section_header' | 'infographic';
  style: string;
  aspect_ratio: string;
  prompt: string;
  prompt_variations: string[];
  alt_text: string;
  placement: {
    position: number;
    section: string;
    priority: number;
  };
}

export interface ImageSuggestionsResponse {
  suggestions: ImageSuggestion[];
  total_suggestions: number;
  recommended_count: number;
}

@Injectable({
  providedIn: 'root',
})
export class ImageGenerationService {
  private apiUrl = environment.apiUrl || 'https://your-api-url.com';
  private jobStatuses$ = new BehaviorSubject<Map<string, any>>(new Map());

  constructor(private http: HttpClient) {}

  getSuggestions(
    content: string,
    topic: string,
    keywords: string[],
    tone: string = 'professional'
  ): Observable<ImageSuggestionsResponse> {
    return this.http.post<ImageSuggestionsResponse>(
      `${this.apiUrl}/api/v1/images/suggestions`,
      { content, topic, keywords, tone }
    );
  }

  generateFromContent(
    content: string,
    topic: string,
    keywords: string[],
    imageType: 'featured' | 'section_header' | 'infographic',
    tone: string = 'professional',
    sectionTitle?: string
  ): Observable<{ job_id: string; status: string }> {
    return this.http.post<{ job_id: string; status: string }>(
      `${this.apiUrl}/api/v1/images/generate-from-content`,
      {
        content,
        topic,
        keywords,
        image_type: imageType,
        tone,
        section_title: sectionTitle,
      }
    );
  }

  checkJobStatus(jobId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/api/v1/images/jobs/${jobId}`);
  }

  pollJobStatus(jobId: string): Observable<any> {
    return interval(2000).pipe(
      switchMap(() => this.checkJobStatus(jobId)),
      map((status) => {
        const currentStatuses = this.jobStatuses$.value;
        currentStatuses.set(jobId, status);
        this.jobStatuses$.next(currentStatuses);
        return status;
      })
    );
  }

  getJobStatuses(): Observable<Map<string, any>> {
    return this.jobStatuses$.asObservable();
  }
}
```

#### 2. Component

```typescript
// components/image-suggestions-panel.component.ts
import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { ImageGenerationService, ImageSuggestion } from '../services/image-generation.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-image-suggestions-panel',
  templateUrl: './image-suggestions-panel.component.html',
  styleUrls: ['./image-suggestions-panel.component.css'],
})
export class ImageSuggestionsPanelComponent implements OnInit, OnDestroy {
  @Input() content: string = '';
  @Input() topic: string = '';
  @Input() keywords: string[] = [];
  @Input() tone: string = 'professional';

  suggestions: ImageSuggestion[] = [];
  loading = false;
  error: string | null = null;
  generatingJobs = new Set<string>();
  private subscriptions = new Subscription();

  constructor(private imageService: ImageGenerationService) {}

  ngOnInit() {
    if (this.content && this.topic) {
      this.loadSuggestions();
    }

    // Subscribe to job status updates
    this.subscriptions.add(
      this.imageService.getJobStatuses().subscribe((statuses) => {
        statuses.forEach((status, jobId) => {
          if (status.status === 'completed' || status.status === 'failed') {
            this.generatingJobs.delete(jobId);
          }
        });
      })
    );
  }

  ngOnDestroy() {
    this.subscriptions.unsubscribe();
  }

  loadSuggestions() {
    this.loading = true;
    this.error = null;

    this.subscriptions.add(
      this.imageService
        .getSuggestions(this.content, this.topic, this.keywords, this.tone)
        .subscribe({
          next: (data) => {
            this.suggestions = data.suggestions;
            this.loading = false;
          },
          error: (err) => {
            this.error = err.message || 'Unknown error';
            this.loading = false;
          },
        })
    );
  }

  generateImage(suggestion: ImageSuggestion) {
    this.subscriptions.add(
      this.imageService
        .generateFromContent(
          this.content,
          this.topic,
          this.keywords,
          suggestion.image_type,
          this.tone,
          suggestion.placement.section
        )
        .subscribe({
          next: ({ job_id }) => {
            this.generatingJobs.add(job_id);
            this.startPolling(job_id, suggestion);
          },
          error: (err) => {
            console.error('Generation failed:', err);
          },
        })
    );
  }

  private startPolling(jobId: string, suggestion: ImageSuggestion) {
    this.subscriptions.add(
      this.imageService.pollJobStatus(jobId).subscribe((status) => {
        if (status.status === 'completed' && status.result) {
          this.generatingJobs.delete(jobId);
          // Emit event or call callback
          this.onImageGenerated(status.result.images[0], suggestion);
        }
      })
    );
  }

  onImageGenerated(image: any, suggestion: ImageSuggestion) {
    // Handle image generation completion
    console.log('Image generated:', image, suggestion);
  }

  isRecommended(suggestion: ImageSuggestion): boolean {
    return suggestion.placement.priority >= 4;
  }

  isGenerating(suggestion: ImageSuggestion): boolean {
    return Array.from(this.generatingJobs).some((jobId) => {
      // Check if this suggestion is being generated
      return true; // Implement your logic
    });
  }
}
```

```html
<!-- components/image-suggestions-panel.component.html -->
<div class="image-suggestions-panel">
  <div *ngIf="loading" class="loading-state">
    <div class="animate-pulse">
      <div class="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
      <div class="h-32 bg-gray-200 rounded"></div>
    </div>
  </div>

  <div *ngIf="error" class="error-state">
    <p class="text-red-800">Error: {{ error }}</p>
  </div>

  <div *ngIf="!loading && !error">
    <div class="panel-header">
      <h3>Image Suggestions</h3>
      <span class="count">{{ suggestions.length }} suggestions</span>
    </div>

    <div class="suggestions-list">
      <div
        *ngFor="let suggestion of suggestions; let i = index"
        [class]="[
          'suggestion-card',
          { 'recommended': isRecommended(suggestion), 'generating': isGenerating(suggestion) }
        ]"
      >
        <div class="card-header">
          <div>
            <h4 class="type">{{ suggestion.image_type | titlecase }}</h4>
            <p class="section">
              {{ suggestion.placement.section }} • Priority: {{ suggestion.placement.priority }}/5
            </p>
          </div>
          <span *ngIf="isRecommended(suggestion)" class="badge">Recommended</span>
        </div>

        <p class="prompt">{{ suggestion.prompt }}</p>
        <p class="alt-text">
          <strong>Alt Text:</strong> {{ suggestion.alt_text }}
        </p>

        <div class="meta">
          <span>Style: {{ suggestion.style }}</span>
          <span>Aspect: {{ suggestion.aspect_ratio }}</span>
        </div>

        <button
          (click)="generateImage(suggestion)"
          [disabled]="isGenerating(suggestion)"
          class="generate-btn"
        >
          {{ isGenerating(suggestion) ? 'Generating...' : 'Generate Image' }}
        </button>
      </div>
    </div>
  </div>
</div>
```

---

## SvelteKit

### Complete Implementation

#### 1. Store

```typescript
// stores/imageGeneration.ts
import { writable } from 'svelte/store';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://your-api-url.com';

export interface ImageSuggestion {
  image_type: 'featured' | 'section_header' | 'infographic';
  style: string;
  aspect_ratio: string;
  prompt: string;
  prompt_variations: string[];
  alt_text: string;
  placement: {
    position: number;
    section: string;
    priority: number;
  };
}

export const suggestions = writable<ImageSuggestion[]>([]);
export const loading = writable(false);
export const error = writable<string | null>(null);
export const generatingJobs = writable<Set<string>>(new Set());
export const jobStatuses = writable<Map<string, any>>(new Map());

export async function getSuggestions(
  content: string,
  topic: string,
  keywords: string[],
  tone: string = 'professional'
) {
  loading.set(true);
  error.set(null);

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/images/suggestions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, topic, keywords, tone }),
    });

    if (!response.ok) {
      throw new Error(`Failed to get suggestions: ${response.statusText}`);
    }

    const data = await response.json();
    suggestions.set(data.suggestions);
  } catch (err) {
    error.set(err instanceof Error ? err.message : 'Unknown error');
  } finally {
    loading.set(false);
  }
}

export async function generateFromContent(
  content: string,
  topic: string,
  keywords: string[],
  imageType: 'featured' | 'section_header' | 'infographic',
  tone: string = 'professional',
  sectionTitle?: string
): Promise<string> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/images/generate-from-content`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content,
        topic,
        keywords,
        image_type: imageType,
        tone,
        section_title: sectionTitle,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to generate image: ${response.statusText}`);
    }

    const data = await response.json();
    generatingJobs.update(jobs => new Set(jobs).add(data.job_id));
    startPolling(data.job_id);
    return data.job_id;
  } catch (err) {
    error.set(err instanceof Error ? err.message : 'Unknown error');
    throw err;
  }
}

function startPolling(jobId: string) {
  const interval = setInterval(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/images/jobs/${jobId}`);
      const status = await response.json();

      jobStatuses.update(statuses => {
        const newStatuses = new Map(statuses);
        newStatuses.set(jobId, status);
        return newStatuses;
      });

      if (status.status === 'completed' || status.status === 'failed') {
        clearInterval(interval);
        generatingJobs.update(jobs => {
          const newJobs = new Set(jobs);
          newJobs.delete(jobId);
          return newJobs;
        });
      }
    } catch (err) {
      console.error('Polling error:', err);
      clearInterval(interval);
    }
  }, 2000);
}
```

#### 2. Component

```svelte
<!-- components/ImageSuggestionsPanel.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import {
    suggestions,
    loading,
    error,
    generatingJobs,
    jobStatuses,
    getSuggestions,
    generateFromContent,
    type ImageSuggestion,
  } from '$stores/imageGeneration';

  export let content: string;
  export let topic: string;
  export let keywords: string[];
  export let tone: string = 'professional';

  let generating = $derived($generatingJobs.size > 0);

  onMount(() => {
    if (content && topic) {
      getSuggestions(content, topic, keywords, tone);
    }
  });

  async function handleGenerate(suggestion: ImageSuggestion) {
    try {
      await generateFromContent(
        content,
        topic,
        keywords,
        suggestion.image_type,
        tone,
        suggestion.placement.section
      );
    } catch (err) {
      console.error('Generation failed:', err);
    }
  }

  function isRecommended(suggestion: ImageSuggestion): boolean {
    return suggestion.placement.priority >= 4;
  }

  function isGenerating(suggestion: ImageSuggestion): boolean {
    return Array.from($generatingJobs).some(jobId => {
      const status = $jobStatuses.get(jobId);
      return status?.status === 'processing';
    });
  }
</script>

<div class="image-suggestions-panel">
  {#if $loading}
    <div class="loading-state">
      <div class="animate-pulse space-y-4">
        <div class="h-4 bg-gray-200 rounded w-1/4"></div>
        <div class="h-32 bg-gray-200 rounded"></div>
      </div>
    </div>
  {:else if $error}
    <div class="error-state">
      <p class="text-red-800">Error: {$error}</p>
    </div>
  {:else}
    <div class="panel-header">
      <h3>Image Suggestions</h3>
      <span class="count">{$suggestions.length} suggestions</span>
    </div>

    <div class="suggestions-list">
      {#each $suggestions as suggestion (suggestion.image_type)}
        <div
          class="suggestion-card {isRecommended(suggestion) ? 'recommended' : ''} {isGenerating(suggestion) ? 'generating' : ''}"
        >
          <div class="card-header">
            <div>
              <h4 class="type">{suggestion.image_type.replace('_', ' ')}</h4>
              <p class="section">
                {suggestion.placement.section} • Priority: {suggestion.placement.priority}/5
              </p>
            </div>
            {#if isRecommended(suggestion)}
              <span class="badge">Recommended</span>
            {/if}
          </div>

          <p class="prompt">{suggestion.prompt}</p>
          <p class="alt-text">
            <strong>Alt Text:</strong> {suggestion.alt_text}
          </p>

          <div class="meta">
            <span>Style: {suggestion.style}</span>
            <span>Aspect: {suggestion.aspect_ratio}</span>
          </div>

          <button
            on:click={() => handleGenerate(suggestion)}
            disabled={isGenerating(suggestion)}
            class="generate-btn"
          >
            {isGenerating(suggestion) ? 'Generating...' : 'Generate Image'}
          </button>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .image-suggestions-panel {
    @apply p-6 bg-white border border-gray-200 rounded-lg shadow-sm;
  }

  .panel-header {
    @apply flex items-center justify-between mb-4;
  }

  .panel-header h3 {
    @apply text-lg font-semibold text-gray-900;
  }

  .count {
    @apply text-sm text-gray-500;
  }

  .suggestions-list {
    @apply space-y-4;
  }

  .suggestion-card {
    @apply p-4 border rounded-lg transition-all border-gray-200 bg-white;
  }

  .suggestion-card.recommended {
    @apply border-green-300 bg-green-50;
  }

  .suggestion-card.generating {
    @apply opacity-75;
  }

  .card-header {
    @apply flex items-start justify-between mb-3;
  }

  .type {
    @apply font-medium text-gray-900 capitalize;
  }

  .section {
    @apply text-sm text-gray-600 mt-1;
  }

  .badge {
    @apply px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded;
  }

  .prompt {
    @apply text-sm text-gray-700 mb-2;
  }

  .alt-text {
    @apply text-xs text-gray-500 mb-3;
  }

  .meta {
    @apply flex items-center gap-4 text-xs text-gray-500 mb-3;
  }

  .generate-btn {
    @apply w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors;
  }
</style>
```

---

## React with Tailwind CSS

### Complete Styled Component

```typescript
// components/ImageSuggestionsPanel.tsx (with Tailwind)
import React from 'react';
import { useImageSuggestions } from '@/hooks/useImageSuggestions';
import { useImageGeneration } from '@/hooks/useImageGeneration';

export const ImageSuggestionsPanel: React.FC<Props> = ({ content, topic, keywords, tone }) => {
  const { suggestions, loading, error } = useImageSuggestions(content, topic, keywords, tone);
  const { generating, generateImage } = useImageGeneration();

  return (
    <div className="max-w-4xl mx-auto p-6 bg-gradient-to-br from-gray-50 to-white rounded-xl shadow-lg border border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Image Suggestions</h2>
          <p className="text-sm text-gray-600 mt-1">
            AI-powered image recommendations for your blog
          </p>
        </div>
        <div className="px-4 py-2 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
          {suggestions.length} suggestions
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-32 bg-gray-200 rounded-lg"></div>
            </div>
          ))}
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-red-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <p className="text-red-800">{error}</p>
          </div>
        </div>
      )}

      {/* Suggestions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {suggestions.map((suggestion, index) => (
          <div
            key={index}
            className={`group relative p-5 rounded-lg border-2 transition-all duration-200 hover:shadow-lg ${
              suggestion.placement.priority >= 4
                ? 'border-green-400 bg-green-50'
                : 'border-gray-200 bg-white hover:border-blue-300'
            }`}
          >
            {/* Priority Badge */}
            {suggestion.placement.priority >= 4 && (
              <div className="absolute top-3 right-3">
                <span className="px-2 py-1 bg-green-500 text-white text-xs font-bold rounded-full shadow-sm">
                  ⭐ Recommended
                </span>
              </div>
            )}

            {/* Type Badge */}
            <div className="mb-3">
              <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded-full uppercase">
                {suggestion.image_type.replace('_', ' ')}
              </span>
            </div>

            {/* Content */}
            <h4 className="font-semibold text-gray-900 mb-2">{suggestion.placement.section}</h4>
            <p className="text-sm text-gray-700 mb-3 line-clamp-2">{suggestion.prompt}</p>

            {/* Metadata */}
            <div className="flex items-center gap-3 text-xs text-gray-500 mb-4">
              <span className="flex items-center">
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                {suggestion.style}
              </span>
              <span className="flex items-center">
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                </svg>
                {suggestion.aspect_ratio}
              </span>
              <span className="flex items-center">
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Priority {suggestion.placement.priority}/5
              </span>
            </div>

            {/* Generate Button */}
            <button
              onClick={() => handleGenerate(suggestion)}
              disabled={generating}
              className="w-full px-4 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-medium rounded-lg shadow-md hover:from-blue-700 hover:to-blue-800 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98]"
            >
              {generating ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Generating...
                </span>
              ) : (
                'Generate Image'
              )}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
```

---

## React with Material-UI

### Complete Component

```typescript
// components/ImageSuggestionsPanel.tsx (with MUI)
import React from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  Box,
  CircularProgress,
  Alert,
  Grid,
  LinearProgress,
} from '@mui/material';
import { Star, Image, AspectRatio, Style } from '@mui/icons-material';
import { useImageSuggestions } from '@/hooks/useImageSuggestions';
import { useImageGeneration } from '@/hooks/useImageGeneration';

export const ImageSuggestionsPanel: React.FC<Props> = ({ content, topic, keywords, tone }) => {
  const { suggestions, loading, error } = useImageSuggestions(content, topic, keywords, tone);
  const { generating, generateImage } = useImageGeneration();

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Error: {error}
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" component="h2" fontWeight="bold">
          Image Suggestions
        </Typography>
        <Chip label={`${suggestions.length} suggestions`} color="primary" />
      </Box>

      <Grid container spacing={3}>
        {suggestions.map((suggestion, index) => (
          <Grid item xs={12} md={6} key={index}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                border: suggestion.placement.priority >= 4 ? '2px solid' : '1px solid',
                borderColor: suggestion.placement.priority >= 4 ? 'success.main' : 'divider',
                bgcolor: suggestion.placement.priority >= 4 ? 'success.50' : 'background.paper',
                transition: 'all 0.2s',
                '&:hover': {
                  boxShadow: 4,
                  transform: 'translateY(-2px)',
                },
              }}
            >
              <CardContent sx={{ flexGrow: 1 }}>
                <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                  <Box>
                    <Chip
                      label={suggestion.image_type.replace('_', ' ')}
                      size="small"
                      color="primary"
                      sx={{ mb: 1 }}
                    />
                    {suggestion.placement.priority >= 4 && (
                      <Chip
                        icon={<Star />}
                        label="Recommended"
                        size="small"
                        color="success"
                        sx={{ ml: 1 }}
                      />
                    )}
                  </Box>
                </Box>

                <Typography variant="h6" component="h3" gutterBottom>
                  {suggestion.placement.section}
                </Typography>

                <Typography variant="body2" color="text.secondary" paragraph>
                  {suggestion.prompt}
                </Typography>

                <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                  <strong>Alt Text:</strong> {suggestion.alt_text}
                </Typography>

                <Box display="flex" gap={2} mt={2} flexWrap="wrap">
                  <Chip
                    icon={<Style />}
                    label={suggestion.style}
                    size="small"
                    variant="outlined"
                  />
                  <Chip
                    icon={<AspectRatio />}
                    label={suggestion.aspect_ratio}
                    size="small"
                    variant="outlined"
                  />
                  <Chip
                    label={`Priority ${suggestion.placement.priority}/5`}
                    size="small"
                    variant="outlined"
                    color={suggestion.placement.priority >= 4 ? 'success' : 'default'}
                  />
                </Box>
              </CardContent>

              <CardActions sx={{ p: 2, pt: 0 }}>
                <Button
                  fullWidth
                  variant="contained"
                  color="primary"
                  onClick={() => handleGenerate(suggestion)}
                  disabled={generating}
                  startIcon={generating ? <CircularProgress size={20} /> : <Image />}
                >
                  {generating ? 'Generating...' : 'Generate Image'}
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};
```

---

## Summary

This guide provides complete implementations for:

1. ✅ **Next.js** - Server actions, hooks, components
2. ✅ **Vue.js 3** - Composables, components with Composition API
3. ✅ **Angular** - Services, components with RxJS
4. ✅ **SvelteKit** - Stores, components with reactive statements
5. ✅ **React + Tailwind** - Styled components with utility classes
6. ✅ **React + Material-UI** - Material Design components

All examples include:
- TypeScript types
- Error handling
- Loading states
- Job polling
- Progressive enhancement
- Responsive design

Choose the framework that matches your frontend stack!

