# Frontend Blog Generation Integration Guide

**Date**: 2025-11-16  
**Version**: 1.3.2  
**Status**: Current Implementation + Recommended Unified Approach

---

## 📋 Table of Contents

1. [Current Implementation](#current-implementation)
2. [Recommended Unified Approach](#recommended-unified-approach)
3. [Frontend Integration Examples](#frontend-integration-examples)
4. [TypeScript Types](#typescript-types)
5. [Migration Path](#migration-path)

---

## Current Implementation

### Available Blog Generation Endpoints

Currently, we have **4 different blog generation endpoints**:

#### 1. Standard Blog Generation
```
POST /api/v1/blog/generate
```
**Use Case**: Basic blog posts with SEO optimization  
**Best For**: Simple, straightforward blog content

#### 2. Enhanced Blog Generation
```
POST /api/v1/blog/generate-enhanced
```
**Use Case**: High-quality multi-stage blog generation  
**Best For**: Premium content with research, fact-checking, citations

#### 3. Local Business Blog Generation
```
POST /api/v1/blog/generate-local-business
```
**Use Case**: Comprehensive blogs about local businesses  
**Best For**: "Best X in [Location]" type content with reviews

#### 4. Abstraction Layer Blog Generation
```
POST /api/v1/abstraction/blog/generate
```
**Use Case**: Advanced blog generation with content strategies  
**Best For**: Strategy-based content (SEO, Engagement, Conversion)

---

## ⚠️ Recommendation: Unified Endpoint Approach

**Current Problem**: Multiple endpoints create:
- ❌ Code duplication
- ❌ Inconsistent API design
- ❌ Harder frontend integration
- ❌ Maintenance overhead

**Recommended Solution**: **Single unified endpoint with `blog_type` parameter**

### Proposed Unified Endpoint

```
POST /api/v1/blog/generate
```

**Request Model:**
```typescript
interface UnifiedBlogRequest {
  // Required
  blog_type: "standard" | "enhanced" | "local_business" | "comparison" | "review";
  topic: string;
  
  // Common fields (all blog types)
  keywords?: string[];
  tone?: "professional" | "casual" | "academic" | "conversational" | "instructional";
  length?: "short" | "medium" | "long";
  format?: "markdown" | "html" | "json";
  target_audience?: string;
  custom_instructions?: string;
  
  // Type-specific fields (conditional based on blog_type)
  // Standard & Enhanced
  include_introduction?: boolean;
  include_conclusion?: boolean;
  include_faq?: boolean;
  include_toc?: boolean;
  
  // Enhanced only
  use_google_search?: boolean;
  use_fact_checking?: boolean;
  use_citations?: boolean;
  use_serp_optimization?: boolean;
  use_consensus_generation?: boolean;
  use_knowledge_graph?: boolean;
  use_semantic_keywords?: boolean;
  use_quality_scoring?: boolean;
  
  // Local Business only
  location?: string;
  max_businesses?: number;
  max_reviews_per_business?: number;
  include_business_details?: boolean;
  include_review_sentiment?: boolean;
  use_google?: boolean;
  
  // Comparison (future)
  comparison_items?: string[];
  
  // Review (future)
  product_name?: string;
  product_category?: string;
}
```

**Benefits:**
- ✅ Single endpoint for all blog types
- ✅ Consistent API design
- ✅ Easier frontend integration
- ✅ Type-safe with conditional fields
- ✅ Backward compatible (can route to existing handlers)

---

## Frontend Integration Examples

### Option 1: Current Implementation (Multiple Endpoints)

#### TypeScript Service Class

```typescript
// blogGenerationService.ts

export enum BlogType {
  STANDARD = 'standard',
  ENHANCED = 'enhanced',
  LOCAL_BUSINESS = 'local_business',
  ABSTRACTION = 'abstraction'
}

export interface BlogGenerationOptions {
  topic: string;
  keywords?: string[];
  tone?: 'professional' | 'casual' | 'academic' | 'conversational' | 'instructional';
  length?: 'short' | 'medium' | 'long';
  format?: 'markdown' | 'html' | 'json';
  target_audience?: string;
  custom_instructions?: string;
}

export interface LocalBusinessOptions extends BlogGenerationOptions {
  location: string;
  max_businesses?: number;
  max_reviews_per_business?: number;
  include_business_details?: boolean;
  include_review_sentiment?: boolean;
  use_google?: boolean;
}

export interface EnhancedOptions extends BlogGenerationOptions {
  use_google_search?: boolean;
  use_fact_checking?: boolean;
  use_citations?: boolean;
  use_serp_optimization?: boolean;
  use_consensus_generation?: boolean;
  use_knowledge_graph?: boolean;
  use_semantic_keywords?: boolean;
  use_quality_scoring?: boolean;
  async_mode?: boolean;
}

class BlogGenerationService {
  private baseUrl: string;

  constructor(baseUrl: string = process.env.NEXT_PUBLIC_API_URL || '') {
    this.baseUrl = baseUrl;
  }

  /**
   * Generate standard blog post
   */
  async generateStandard(options: BlogGenerationOptions) {
    const response = await fetch(`${this.baseUrl}/api/v1/blog/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        topic: options.topic,
        keywords: options.keywords || [],
        tone: options.tone || 'professional',
        length: options.length || 'medium',
        format: options.format || 'markdown',
        target_audience: options.target_audience,
        custom_instructions: options.custom_instructions,
      }),
    });

    if (!response.ok) {
      throw new Error(`Blog generation failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Generate enhanced blog post (multi-stage pipeline)
   */
  async generateEnhanced(options: EnhancedOptions) {
    const params = new URLSearchParams();
    if (options.async_mode) {
      params.append('async_mode', 'true');
    }

    const response = await fetch(
      `${this.baseUrl}/api/v1/blog/generate-enhanced?${params.toString()}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          topic: options.topic,
          keywords: options.keywords || [],
          tone: options.tone || 'professional',
          length: options.length || 'medium',
          use_google_search: options.use_google_search ?? true,
          use_fact_checking: options.use_fact_checking ?? true,
          use_citations: options.use_citations ?? true,
          use_serp_optimization: options.use_serp_optimization ?? true,
          use_consensus_generation: options.use_consensus_generation ?? false,
          use_knowledge_graph: options.use_knowledge_graph ?? true,
          use_semantic_keywords: options.use_semantic_keywords ?? true,
          use_quality_scoring: options.use_quality_scoring ?? true,
          target_audience: options.target_audience,
          custom_instructions: options.custom_instructions,
        }),
      }
    );

    if (!response.ok) {
      throw new Error(`Enhanced blog generation failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Generate local business blog post
   */
  async generateLocalBusiness(options: LocalBusinessOptions) {
    const response = await fetch(
      `${this.baseUrl}/api/v1/blog/generate-local-business`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          topic: options.topic,
          location: options.location,
          max_businesses: options.max_businesses || 10,
          max_reviews_per_business: options.max_reviews_per_business || 20,
          tone: options.tone || 'professional',
          length: options.length || 'long',
          format: options.format || 'markdown',
          include_business_details: options.include_business_details ?? true,
          include_review_sentiment: options.include_review_sentiment ?? true,
          use_google: options.use_google ?? true,
          custom_instructions: options.custom_instructions,
        }),
      }
    );

    if (!response.ok) {
      throw new Error(`Local business blog generation failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Unified method that routes to appropriate endpoint
   */
  async generate(
    type: BlogType,
    options: BlogGenerationOptions | EnhancedOptions | LocalBusinessOptions
  ) {
    switch (type) {
      case BlogType.STANDARD:
        return this.generateStandard(options as BlogGenerationOptions);
      
      case BlogType.ENHANCED:
        return this.generateEnhanced(options as EnhancedOptions);
      
      case BlogType.LOCAL_BUSINESS:
        return this.generateLocalBusiness(options as LocalBusinessOptions);
      
      default:
        throw new Error(`Unsupported blog type: ${type}`);
    }
  }
}

export default new BlogGenerationService();
```

#### React Component Example

```typescript
// BlogGenerationForm.tsx

import React, { useState } from 'react';
import BlogGenerationService, { BlogType } from './blogGenerationService';

interface BlogGenerationFormProps {
  onSuccess?: (result: any) => void;
  onError?: (error: Error) => void;
}

export const BlogGenerationForm: React.FC<BlogGenerationFormProps> = ({
  onSuccess,
  onError,
}) => {
  const [blogType, setBlogType] = useState<BlogType>(BlogType.STANDARD);
  const [topic, setTopic] = useState('');
  const [location, setLocation] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      let response;

      switch (blogType) {
        case BlogType.STANDARD:
          response = await BlogGenerationService.generateStandard({
            topic,
            keywords: [],
            tone: 'professional',
            length: 'medium',
          });
          break;

        case BlogType.ENHANCED:
          response = await BlogGenerationService.generateEnhanced({
            topic,
            keywords: [],
            tone: 'professional',
            length: 'long',
            use_google_search: true,
            use_fact_checking: true,
            use_citations: true,
          });
          break;

        case BlogType.LOCAL_BUSINESS:
          if (!location) {
            throw new Error('Location is required for local business blogs');
          }
          response = await BlogGenerationService.generateLocalBusiness({
            topic,
            location,
            max_businesses: 10,
            max_reviews_per_business: 20,
            tone: 'professional',
            length: 'long',
          });
          break;

        default:
          throw new Error(`Unsupported blog type: ${blogType}`);
      }

      setResult(response);
      onSuccess?.(response);
    } catch (error) {
      console.error('Blog generation error:', error);
      onError?.(error as Error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="blog-generation-form">
      <div className="form-group">
        <label htmlFor="blog-type">Blog Type</label>
        <select
          id="blog-type"
          value={blogType}
          onChange={(e) => setBlogType(e.target.value as BlogType)}
        >
          <option value={BlogType.STANDARD}>Standard Blog</option>
          <option value={BlogType.ENHANCED}>Enhanced Blog (Premium)</option>
          <option value={BlogType.LOCAL_BUSINESS}>Local Business Blog</option>
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="topic">Topic</label>
        <input
          id="topic"
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="e.g., 'Best plumbers in Miami'"
          required
        />
      </div>

      {blogType === BlogType.LOCAL_BUSINESS && (
        <div className="form-group">
          <label htmlFor="location">Location</label>
          <input
            id="location"
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="e.g., 'Miami, FL'"
            required
          />
        </div>
      )}

      <button type="submit" disabled={loading}>
        {loading ? 'Generating...' : 'Generate Blog'}
      </button>

      {result && (
        <div className="result-preview">
          <h3>{result.title || result.blog_post?.title}</h3>
          <div dangerouslySetInnerHTML={{ __html: result.content || result.blog_post?.content }} />
        </div>
      )}
    </form>
  );
};
```

---

### Option 2: Recommended Unified Endpoint (Future)

If we implement the unified endpoint, the frontend becomes much simpler:

```typescript
// Unified blog generation service

interface UnifiedBlogRequest {
  blog_type: 'standard' | 'enhanced' | 'local_business';
  topic: string;
  keywords?: string[];
  tone?: string;
  length?: string;
  // ... other common fields
  
  // Type-specific fields (only used when relevant)
  location?: string; // Only for local_business
  use_google_search?: boolean; // Only for enhanced
  // ... etc
}

class UnifiedBlogService {
  async generate(request: UnifiedBlogRequest) {
    const response = await fetch(`${this.baseUrl}/api/v1/blog/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Blog generation failed: ${response.statusText}`);
    }

    return response.json();
  }
}
```

**Much simpler!** Single method, single endpoint, type-safe with conditional fields.

---

## TypeScript Types

### Complete Type Definitions

```typescript
// types/blog.ts

export type BlogType = 'standard' | 'enhanced' | 'local_business' | 'comparison' | 'review';

export type ContentTone = 
  | 'professional' 
  | 'casual' 
  | 'academic' 
  | 'conversational' 
  | 'instructional';

export type ContentLength = 'short' | 'medium' | 'long';

export type ContentFormat = 'markdown' | 'html' | 'json';

export interface BaseBlogRequest {
  topic: string;
  keywords?: string[];
  tone?: ContentTone;
  length?: ContentLength;
  format?: ContentFormat;
  target_audience?: string;
  custom_instructions?: string;
}

export interface StandardBlogRequest extends BaseBlogRequest {
  blog_type: 'standard';
  include_introduction?: boolean;
  include_conclusion?: boolean;
  include_faq?: boolean;
  include_toc?: boolean;
  focus_keyword?: string;
  word_count_target?: number;
}

export interface EnhancedBlogRequest extends BaseBlogRequest {
  blog_type: 'enhanced';
  use_google_search?: boolean;
  use_fact_checking?: boolean;
  use_citations?: boolean;
  use_serp_optimization?: boolean;
  use_consensus_generation?: boolean;
  use_knowledge_graph?: boolean;
  use_semantic_keywords?: boolean;
  use_quality_scoring?: boolean;
  async_mode?: boolean;
}

export interface LocalBusinessBlogRequest extends BaseBlogRequest {
  blog_type: 'local_business';
  location: string;
  max_businesses?: number;
  max_reviews_per_business?: number;
  include_business_details?: boolean;
  include_review_sentiment?: boolean;
  use_yelp?: boolean;
  use_google?: boolean;
}

export type BlogRequest = 
  | StandardBlogRequest 
  | EnhancedBlogRequest 
  | LocalBusinessBlogRequest;

export interface BlogGenerationResponse {
  title: string;
  content: string;
  meta_description?: string;
  seo_score?: number;
  word_count?: number;
  generation_time_seconds?: number;
  // ... other common fields
}

export interface LocalBusinessBlogResponse extends BlogGenerationResponse {
  businesses: Array<{
    name: string;
    google_place_id?: string;
    address?: string;
    phone?: string;
    website?: string;
    rating?: number;
    review_count?: number;
    categories?: string[];
  }>;
  total_reviews_aggregated: number;
}
```

---

## Migration Path

### Phase 1: Current State (Now)
- ✅ Use multiple endpoints
- ✅ Frontend routes to appropriate endpoint based on blog type
- ✅ Service class handles routing logic

### Phase 2: Unified Endpoint Implementation (Recommended)
1. **Backend**: Create unified endpoint that routes internally
2. **Backend**: Keep existing endpoints for backward compatibility
3. **Frontend**: Migrate to unified endpoint gradually
4. **Frontend**: Update TypeScript types

### Phase 3: Deprecation (Future)
1. Mark old endpoints as deprecated
2. Provide migration guide
3. Remove old endpoints after deprecation period

---

## Recommendation Summary

**✅ Recommended Approach: Unified Endpoint with `blog_type`**

**Benefits:**
- Single endpoint = simpler frontend code
- Consistent API design
- Easier to maintain and extend
- Type-safe with conditional fields
- Backward compatible (can route internally)

**Implementation:**
- Add `blog_type` parameter to unified endpoint
- Route internally to existing handlers
- Keep old endpoints for backward compatibility
- Frontend can migrate gradually

**Frontend Impact:**
- **Current**: 4 different methods, 4 different endpoints
- **Unified**: 1 method, 1 endpoint, conditional fields

Would you like me to implement the unified endpoint approach?

