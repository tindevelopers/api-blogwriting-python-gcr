# Frontend API Integration Guide

**Version**: 1.2.1  
**Date**: 2025-11-12  
**API Base URL**: `https://blog-writer-api-dev-613248238610.europe-west1.run.app`

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [API Base Configuration](#api-base-configuration)
3. [TypeScript Types](#typescript-types)
4. [Error Handling](#error-handling)
5. [Endpoint Reference](#endpoint-reference)
6. [Best Practices](#best-practices)
7. [Common Patterns](#common-patterns)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. API Client Setup

```typescript
// lib/api-client.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 
  'https://blog-writer-api-dev-613248238610.europe-west1.run.app';

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await this.handleError(response);
      throw error;
    }

    return response.json();
  }

  private async handleError(response: Response): Promise<ApiError> {
    let errorData: any;
    try {
      errorData = await response.json();
    } catch {
      errorData = { detail: response.statusText };
    }

    return new ApiError(
      response.status,
      errorData.detail || errorData.error || 'An error occurred',
      errorData
    );
  }

  // GET request
  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  // POST request
  async post<T>(endpoint: string, data: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}

export const apiClient = new ApiClient();
```

### 2. Error Handling Class

```typescript
// lib/api-error.ts
export class ApiError extends Error {
  constructor(
    public status: number,
    public message: string,
    public data?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }

  isValidationError(): boolean {
    return this.status === 422;
  }

  isServerError(): boolean {
    return this.status >= 500;
  }

  isNotFound(): boolean {
    return this.status === 404;
  }

  isUnauthorized(): boolean {
    return this.status === 401 || this.status === 403;
  }
}
```

---

## API Base Configuration

### Environment Variables

```env
# .env.local
NEXT_PUBLIC_API_URL=https://blog-writer-api-dev-613248238610.europe-west1.run.app
NEXT_PUBLIC_API_VERSION=v1
```

### API Configuration

```typescript
// lib/api-config.ts
export const API_CONFIG = {
  baseURL: process.env.NEXT_PUBLIC_API_URL || '',
  version: process.env.NEXT_PUBLIC_API_VERSION || 'v1',
  timeout: 30000, // 30 seconds
  retries: 3,
  retryDelay: 1000, // 1 second
} as const;

export const API_ENDPOINTS = {
  // Health & Status
  health: '/health',
  
  // Keyword Analysis
  keywords: {
    analyze: '/api/v1/keywords/analyze',
    enhanced: '/api/v1/keywords/enhanced',
    extract: '/api/v1/keywords/extract',
    suggest: '/api/v1/keywords/suggest',
  },
  
  // Topic Recommendations
  topics: {
    recommend: '/api/v1/topics/recommend',
  },
  
  // Blog Generation
  blog: {
    generate: '/api/v1/generate',
    generateEnhanced: '/api/v1/blog/generate-enhanced',
    analyze: '/api/v1/analyze',
    optimize: '/api/v1/optimize',
  },
  
  // Integrations
  integrations: {
    connectAndRecommend: '/api/v1/integrations/connect-and-recommend',
  },
} as const;
```

---

## TypeScript Types

### Core Types

```typescript
// types/api.ts

// Request Types
export interface KeywordAnalysisRequest {
  keywords: string[];
  location?: string;
  language?: string;
  text?: string; // Optional, ignored if keywords provided
  max_suggestions_per_keyword?: number; // Optional, routes to enhanced if provided
}

export interface EnhancedKeywordAnalysisRequest {
  keywords: string[];
  location?: string;
  language?: string;
  include_serp?: boolean;
  max_suggestions_per_keyword?: number; // 5-150, default: 20
}

export interface TopicRecommendationRequest {
  seed_keywords: string[]; // 1-10 keywords
  location?: string;
  language?: string;
  max_topics?: number; // 5-50, default: 20
  min_search_volume?: number; // default: 100
  max_difficulty?: number; // 0-100, default: 70
  include_ai_suggestions?: boolean; // default: true
}

export interface BlogGenerationRequest {
  topic: string;
  keywords: string[];
  tone?: 'professional' | 'casual' | 'friendly' | 'authoritative' | 'conversational' | 'technical' | 'creative';
  length?: 'short' | 'medium' | 'long' | 'extended';
  custom_instructions?: string;
}

export interface EnhancedBlogGenerationRequest extends BlogGenerationRequest {
  use_google_search?: boolean;
  use_citations?: boolean;
  use_serp_optimization?: boolean;
  use_consensus_generation?: boolean;
  use_knowledge_graph?: boolean;
  use_semantic_keywords?: boolean;
  use_quality_scoring?: boolean;
  template_type?: string;
  target_audience?: string;
}

// Response Types
export interface KeywordAnalysis {
  difficulty: string;
  search_volume?: number;
  competition?: number;
  cpc?: number;
  recommended?: boolean;
  reason?: string;
  related_keywords?: string[];
  long_tail_keywords?: string[];
  parent_topic?: string;
  category_type?: string;
  cluster_score?: number;
}

export interface KeywordAnalysisResponse {
  keyword_analysis: Record<string, KeywordAnalysis>;
}

export interface EnhancedKeywordAnalysisResponse {
  enhanced_analysis: Record<string, KeywordAnalysis>;
  total_keywords: number;
  original_keywords: string[];
  suggested_keywords: string[];
  clusters: Array<{
    parent_topic: string;
    keywords: string[];
    cluster_score: number;
    category_type: string;
    keyword_count: number;
  }>;
  cluster_summary: {
    total_keywords: number;
    cluster_count: number;
    unclustered_count: number;
  };
}

export interface RecommendedTopic {
  topic: string;
  primary_keyword: string;
  search_volume: number;
  difficulty: number;
  competition: number;
  cpc: number;
  ranking_score: number;
  opportunity_score: number;
  related_keywords: string[];
  content_gaps: string[];
  estimated_traffic: number;
  reason: string;
}

export interface TopicRecommendationResponse {
  recommended_topics: RecommendedTopic[];
  high_priority_topics: RecommendedTopic[];
  trending_topics: RecommendedTopic[];
  low_competition_topics: RecommendedTopic[];
  total_opportunities: number;
  analysis_date: string;
}

export interface BlogGenerationResponse {
  title: string;
  content: string;
  meta_title?: string;
  meta_description?: string;
  readability_score?: number;
  seo_score?: number;
  success: boolean;
  warnings?: string[];
}
```

---

## Error Handling

### Comprehensive Error Handler

```typescript
// lib/error-handler.ts
import { ApiError } from './api-error';

export async function handleApiError(error: unknown): Promise<string> {
  if (error instanceof ApiError) {
    // Handle specific error types
    if (error.isValidationError()) {
      return `Validation Error: ${error.message}. Please check your input.`;
    }
    
    if (error.isServerError()) {
      return `Server Error: ${error.message}. Please try again later.`;
    }
    
    if (error.isNotFound()) {
      return `Not Found: ${error.message}`;
    }
    
    if (error.isUnauthorized()) {
      return `Unauthorized: ${error.message}. Please check your credentials.`;
    }
    
    return error.message;
  }
  
  if (error instanceof Error) {
    return error.message;
  }
  
  return 'An unexpected error occurred';
}

// Usage in components
try {
  const result = await apiClient.post('/api/v1/keywords/analyze', data);
} catch (error) {
  const message = await handleApiError(error);
  toast.error(message);
}
```

### Retry Logic

```typescript
// lib/retry.ts
export async function withRetry<T>(
  fn: () => Promise<T>,
  retries: number = 3,
  delay: number = 1000
): Promise<T> {
  try {
    return await fn();
  } catch (error) {
    if (retries > 0 && error instanceof ApiError && error.isServerError()) {
      await new Promise(resolve => setTimeout(resolve, delay));
      return withRetry(fn, retries - 1, delay * 2);
    }
    throw error;
  }
}

// Usage
const result = await withRetry(() => 
  apiClient.post('/api/v1/keywords/analyze', data)
);
```

---

## Endpoint Reference

### 1. Keyword Analysis

#### Standard Analysis

```typescript
// ✅ RECOMMENDED: Use enhanced endpoint for better results
const analyzeKeywords = async (keywords: string[]) => {
  try {
    const response = await apiClient.post<EnhancedKeywordAnalysisResponse>(
      API_ENDPOINTS.keywords.enhanced,
      {
        keywords,
        location: 'United States',
        language: 'en',
        max_suggestions_per_keyword: 20, // Get up to 20 suggestions per keyword
      }
    );
    
    return response.enhanced_analysis;
  } catch (error) {
    throw error;
  }
};
```

#### Flexible Analysis (Auto-routes to Enhanced)

```typescript
// ✅ WORKS: Standard endpoint now auto-routes to enhanced if max_suggestions_per_keyword is provided
const analyzeKeywordsFlexible = async (keywords: string[]) => {
  try {
    const response = await apiClient.post<KeywordAnalysisResponse>(
      API_ENDPOINTS.keywords.analyze,
      {
        keywords,
        location: 'United States',
        language: 'en',
        max_suggestions_per_keyword: 0, // Even 0 routes to enhanced for better results
        text: 'optional text', // Ignored if keywords provided
      }
    );
    
    return response.keyword_analysis;
  } catch (error) {
    throw error;
  }
};
```

### 2. Topic Recommendations

```typescript
const getTopicRecommendations = async (seedKeywords: string[]) => {
  try {
    const response = await apiClient.post<TopicRecommendationResponse>(
      API_ENDPOINTS.topics.recommend,
      {
        seed_keywords: seedKeywords.slice(0, 10), // Max 10 seed keywords
        location: 'United States',
        language: 'en',
        max_topics: 20,
        min_search_volume: 100,
        max_difficulty: 70,
        include_ai_suggestions: true, // Use Claude AI for topic generation
      }
    );
    
    return {
      all: response.recommended_topics,
      highPriority: response.high_priority_topics,
      trending: response.trending_topics,
      lowCompetition: response.low_competition_topics,
    };
  } catch (error) {
    throw error;
  }
};
```

### 3. Blog Generation

```typescript
const generateBlog = async (request: EnhancedBlogGenerationRequest) => {
  try {
    const response = await apiClient.post<BlogGenerationResponse>(
      API_ENDPOINTS.blog.generateEnhanced,
      {
        ...request,
        use_google_search: true,
        use_citations: true,
        use_serp_optimization: true,
        use_consensus_generation: false, // Set to true for higher quality (slower, more expensive)
        use_knowledge_graph: true,
        use_semantic_keywords: true,
        use_quality_scoring: true,
      }
    );
    
    return response;
  } catch (error) {
    throw error;
  }
};
```

---

## Best Practices

### 1. Always Use Enhanced Endpoints When Available

```typescript
// ❌ DON'T: Use basic endpoint when enhanced is available
const basicAnalysis = await apiClient.post('/api/v1/keywords/analyze', {
  keywords: ['pet care'],
});

// ✅ DO: Use enhanced endpoint for better results
const enhancedAnalysis = await apiClient.post('/api/v1/keywords/enhanced', {
  keywords: ['pet care'],
  max_suggestions_per_keyword: 20,
});
```

### 2. Handle Large Keyword Lists

```typescript
// ✅ DO: Batch large keyword lists
const analyzeManyKeywords = async (keywords: string[]) => {
  const BATCH_SIZE = 30; // API limit
  const batches = [];
  
  for (let i = 0; i < keywords.length; i += BATCH_SIZE) {
    batches.push(keywords.slice(i, i + BATCH_SIZE));
  }
  
  const results = await Promise.all(
    batches.map(batch =>
      apiClient.post(API_ENDPOINTS.keywords.enhanced, {
        keywords: batch,
        max_suggestions_per_keyword: 0, // Don't get suggestions for batches
      })
    )
  );
  
  // Merge results
  return results.reduce((acc, result) => ({
    ...acc,
    ...result.enhanced_analysis,
  }), {});
};
```

### 3. Use TypeScript for Type Safety

```typescript
// ✅ DO: Use typed responses
interface MyKeywordData {
  keyword: string;
  search_volume: number;
  difficulty: number;
}

const getKeywordData = async (keyword: string): Promise<MyKeywordData> => {
  const response = await apiClient.post<EnhancedKeywordAnalysisResponse>(
    API_ENDPOINTS.keywords.enhanced,
    { keywords: [keyword] }
  );
  
  const analysis = response.enhanced_analysis[keyword];
  return {
    keyword,
    search_volume: analysis.search_volume || 0,
    difficulty: analysis.difficulty === 'easy' ? 20 : 
                analysis.difficulty === 'medium' ? 50 : 80,
  };
};
```

### 4. Implement Proper Loading States

```typescript
// ✅ DO: Show loading states for async operations
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);

const handleAnalyze = async () => {
  setLoading(true);
  setError(null);
  
  try {
    const result = await analyzeKeywords(keywords);
    // Handle success
  } catch (err) {
    setError(await handleApiError(err));
  } finally {
    setLoading(false);
  }
};
```

### 5. Cache Results When Appropriate

```typescript
// ✅ DO: Cache keyword analysis results
const keywordCache = new Map<string, KeywordAnalysis>();

const getCachedAnalysis = async (keyword: string): Promise<KeywordAnalysis> => {
  if (keywordCache.has(keyword)) {
    return keywordCache.get(keyword)!;
  }
  
  const response = await apiClient.post<EnhancedKeywordAnalysisResponse>(
    API_ENDPOINTS.keywords.enhanced,
    { keywords: [keyword] }
  );
  
  const analysis = response.enhanced_analysis[keyword];
  keywordCache.set(keyword, analysis);
  
  return analysis;
};
```

---

## Common Patterns

### React Hook for Keyword Analysis

```typescript
// hooks/useKeywordAnalysis.ts
import { useState, useCallback } from 'react';
import { apiClient } from '@/lib/api-client';
import { EnhancedKeywordAnalysisResponse } from '@/types/api';

export function useKeywordAnalysis() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<EnhancedKeywordAnalysisResponse | null>(null);

  const analyze = useCallback(async (keywords: string[]) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiClient.post<EnhancedKeywordAnalysisResponse>(
        '/api/v1/keywords/enhanced',
        {
          keywords,
          location: 'United States',
          language: 'en',
          max_suggestions_per_keyword: 20,
        }
      );
      
      setData(response);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Analysis failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { analyze, loading, error, data };
}
```

### React Hook for Topic Recommendations

```typescript
// hooks/useTopicRecommendations.ts
import { useState, useCallback } from 'react';
import { apiClient } from '@/lib/api-client';
import { TopicRecommendationResponse } from '@/types/api';

export function useTopicRecommendations() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recommendations, setRecommendations] = useState<TopicRecommendationResponse | null>(null);

  const getRecommendations = useCallback(async (
    seedKeywords: string[],
    options?: {
      maxTopics?: number;
      minSearchVolume?: number;
      maxDifficulty?: number;
    }
  ) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiClient.post<TopicRecommendationResponse>(
        '/api/v1/topics/recommend',
        {
          seed_keywords: seedKeywords.slice(0, 10),
          location: 'United States',
          language: 'en',
          max_topics: options?.maxTopics || 20,
          min_search_volume: options?.minSearchVolume || 100,
          max_difficulty: options?.maxDifficulty || 70,
          include_ai_suggestions: true,
        }
      );
      
      setRecommendations(response);
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get recommendations';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { getRecommendations, loading, error, recommendations };
}
```

### Component Example

```typescript
// components/KeywordAnalyzer.tsx
'use client';

import { useState } from 'react';
import { useKeywordAnalysis } from '@/hooks/useKeywordAnalysis';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export function KeywordAnalyzer() {
  const [keywords, setKeywords] = useState<string[]>([]);
  const { analyze, loading, error, data } = useKeywordAnalysis();

  const handleAnalyze = async () => {
    if (keywords.length === 0) return;
    
    try {
      await analyze(keywords);
    } catch (err) {
      console.error('Analysis failed:', err);
    }
  };

  return (
    <div className="space-y-4">
      <Input
        placeholder="Enter keywords (comma-separated)"
        onChange={(e) => {
          const values = e.target.value
            .split(',')
            .map(k => k.trim())
            .filter(k => k.length > 0);
          setKeywords(values);
        }}
      />
      
      <Button onClick={handleAnalyze} disabled={loading || keywords.length === 0}>
        {loading ? 'Analyzing...' : 'Analyze Keywords'}
      </Button>
      
      {error && (
        <div className="text-red-500">{error}</div>
      )}
      
      {data && (
        <div className="space-y-2">
          <h3>Analysis Results</h3>
          {Object.entries(data.enhanced_analysis).map(([keyword, analysis]) => (
            <div key={keyword} className="border p-4 rounded">
              <h4>{keyword}</h4>
              <p>Search Volume: {analysis.search_volume || 'N/A'}</p>
              <p>Difficulty: {analysis.difficulty}</p>
              <p>Parent Topic: {analysis.parent_topic}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## Troubleshooting

### Common Issues

#### 1. 422 Validation Error

**Problem**: Request body doesn't match expected schema.

**Solution**: 
- Check that all required fields are present
- Ensure field types match (arrays vs strings, etc.)
- Use the flexible endpoint which accepts extra fields

```typescript
// ✅ This works even with extra fields
await apiClient.post('/api/v1/keywords/analyze', {
  keywords: ['pet care'],
  text: 'optional text', // Extra field, ignored
  max_suggestions_per_keyword: 0, // Routes to enhanced
});
```

#### 2. CORS Errors

**Problem**: Browser blocks requests due to CORS policy.

**Solution**: 
- Ensure your frontend domain is whitelisted in the API
- Use the correct API base URL
- Check that credentials are not being sent unnecessarily

#### 3. Timeout Errors

**Problem**: Requests take too long and timeout.

**Solution**:
- Increase timeout for long-running operations
- Use background jobs for blog generation
- Implement retry logic with exponential backoff

```typescript
const apiClient = new ApiClient();
apiClient.timeout = 60000; // 60 seconds for blog generation
```

#### 4. Rate Limiting

**Problem**: Too many requests in a short time.

**Solution**:
- Implement request throttling
- Batch multiple keywords in single requests
- Cache results when possible

```typescript
// Throttle requests
import { throttle } from 'lodash';

const throttledAnalyze = throttle(
  (keywords: string[]) => analyzeKeywords(keywords),
  1000 // Max once per second
);
```

### Debugging Tips

```typescript
// Enable request/response logging
const apiClient = new ApiClient();
apiClient.onRequest = (url, options) => {
  console.log('Request:', url, options);
};
apiClient.onResponse = (response) => {
  console.log('Response:', response);
};
```

---

## Summary

### Key Takeaways

1. **Use Enhanced Endpoints**: Always prefer `/api/v1/keywords/enhanced` over `/api/v1/keywords/analyze` for better results
2. **Handle Errors Gracefully**: Implement proper error handling with user-friendly messages
3. **Type Safety**: Use TypeScript types for all API requests/responses
4. **Batch Operations**: Group multiple keywords in single requests when possible
5. **Cache Results**: Cache keyword analysis results to reduce API calls
6. **Loading States**: Always show loading indicators for async operations
7. **Flexible Requests**: The API accepts extra fields, so don't worry about minor mismatches

### Recommended Endpoints

| Use Case | Endpoint | Why |
|----------|----------|-----|
| Keyword Analysis | `/api/v1/keywords/enhanced` | Returns search volume, difficulty, competition, clustering |
| Topic Discovery | `/api/v1/topics/recommend` | AI-powered topic recommendations with ranking scores |
| Blog Generation | `/api/v1/blog/generate-enhanced` | Multi-stage pipeline with quality scoring |
| Keyword Extraction | `/api/v1/keywords/extract` | Extract keywords from content with clustering |

---

## Additional Resources

- [Search Volume Guide](./FRONTEND_SEARCH_VOLUME_GUIDE.md)
- [Keyword Clustering Guide](./FRONTEND_KEYWORD_CLUSTERING_GUIDE.md)
- [Image Integration Guide](./FRONTEND_IMAGE_INTEGRATION_GUIDE.md)
- [API Documentation](https://blog-writer-api-dev-613248238610.europe-west1.run.app/docs)

---

**Last Updated**: 2025-11-12  
**API Version**: 1.2.1

