# Frontend Blog Generation Guidance

**Date:** 2025-11-23  
**Status:** ✅ Flow Working Correctly

---

## 🎯 Quick Answer

**The frontend should use synchronous mode** (`async_mode=false` or omit the parameter) and **wait for the response**. The endpoint handles everything internally:

1. ✅ Accepts keywords array
2. ✅ Performs keyword analysis internally (via SDK)
3. ✅ Generates content with semantic keywords
4. ✅ Returns complete response with semantic keywords

**No separate API calls needed. No polling required for synchronous mode.**

---

## 📋 What Frontend Needs to Know

### 1. Endpoint to Use

```typescript
POST /api/v1/blog/generate-enhanced
```

### 2. Request Format

```typescript
interface BlogGenerationRequest {
  topic: string;
  keywords: string[];                    // ✅ Array of keywords
  tone?: "professional" | "casual" | "friendly" | "formal";
  length?: "short" | "medium" | "long";
  use_semantic_keywords?: boolean;        // ✅ Set to true (default: true)
  use_quality_scoring?: boolean;          // Optional
  use_knowledge_graph?: boolean;          // Optional
  // ... other optional fields
}
```

### 3. Response Structure

```typescript
interface BlogGenerationResponse {
  // Content
  title: string;
  content: string;
  meta_title: string;
  meta_description: string;
  
  // ✅ Semantic Keywords (as requested)
  semantic_keywords: string[];  // ["programming", "coding", "python"]
  
  // ✅ SEO Metadata with keyword analysis
  seo_metadata: {
    semantic_keywords: string[];
    keyword_clusters: number;
    keyword_analysis: {
      difficulty: number;
      overview: {...};
    };
    search_intent: {
      primary_intent: string;
      confidence: number;
    };
  };
  
  // Quality metrics
  quality_score: number;
  seo_score: number;
  readability_score: number;
  
  // Additional data
  structured_data: {...};
  citations: Array<{...}>;
  internal_links: Array<{...}>;
}
```

---

## ✅ Recommended Implementation

### Synchronous Mode (Recommended)

**Use synchronous mode** - the endpoint handles everything and returns the complete response:

```typescript
async function generateBlogWithKeywords(
  topic: string,
  keywords: string[]
) {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/blog/generate-enhanced`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic,
          keywords,  // ✅ Array of keywords
          tone: 'professional',
          length: 'short',
          use_semantic_keywords: true  // ✅ Enable semantic keywords
        })
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ 
        detail: `HTTP ${response.status}` 
      }));
      throw new Error(error.detail || 'Blog generation failed');
    }

    const data = await response.json();
    
    // ✅ Access semantic keywords
    const semanticKeywords = data.semantic_keywords;
    // OR
    const semanticKeywords = data.seo_metadata.semantic_keywords;
    
    // ✅ Access keyword analysis
    const keywordAnalysis = data.seo_metadata.keyword_analysis;
    
    return {
      success: true,
      content: data.content,
      semanticKeywords,
      keywordAnalysis,
      qualityScore: data.quality_score
    };
    
  } catch (error) {
    console.error('Blog generation error:', error);
    throw error;
  }
}
```

### Timeout Configuration

```typescript
// Blog generation can take 2-5 minutes
const BLOG_GENERATION_TIMEOUT = 300000; // 5 minutes

const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), BLOG_GENERATION_TIMEOUT);

try {
  const response = await fetch(`${API_BASE_URL}/api/v1/blog/generate-enhanced`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    signal: controller.signal
  });
  // ... handle response
} catch (error) {
  if (error.name === 'AbortError') {
    throw new Error('Blog generation timeout - request took too long');
  }
  throw error;
} finally {
  clearTimeout(timeoutId);
}
```

---

## ⚠️ Error Handling

### Common Errors and Actions

| Error | Status Code | Action |
|-------|-------------|--------|
| Invalid request | 400 | Check request format, don't retry |
| Unauthorized | 401 | Check API credentials, don't retry |
| Service unavailable | 503 | Retry with exponential backoff |
| Internal server error | 500 | Retry with exponential backoff (up to 3 times) |
| Timeout | N/A | Retry once, then show error |

### Retry Logic

```typescript
async function generateBlogWithRetry(
  request: BlogGenerationRequest,
  maxRetries: number = 3
) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/blog/generate-enhanced`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(request)
        }
      );

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        
        // Don't retry client errors (4xx)
        if (response.status >= 400 && response.status < 500) {
          throw new Error(error.detail || `HTTP ${response.status}`);
        }
        
        // Retry server errors (5xx)
        if (response.status >= 500 && attempt < maxRetries - 1) {
          const delay = Math.pow(2, attempt) * 1000; // Exponential backoff
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }
        
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
      
    } catch (error) {
      // Network errors - retry
      if (error instanceof TypeError && attempt < maxRetries - 1) {
        const delay = Math.pow(2, attempt) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }
      
      // Last attempt or non-retryable error
      throw error;
    }
  }
  
  throw new Error('Max retries exceeded');
}
```

---

## 🔄 Should Frontend Poll or Wait?

### Recommendation: **Wait for Response** (Synchronous Mode)

**Use synchronous mode** (`async_mode=false` or omit parameter):

- ✅ Simpler implementation
- ✅ Single request/response cycle
- ✅ No polling needed
- ✅ Complete response includes everything
- ✅ Timeout handling sufficient

### When to Use Async Mode

Only use async mode (`async_mode=true`) if:
- You need to show a job queue UI
- You want to allow users to navigate away
- You're generating very long content (>5000 words)

**Note:** Async mode currently has Cloud Tasks queue setup issues. Use synchronous mode for now.

---

## 📊 What Happens Internally

The blog generation endpoint:

1. **Accepts keywords** → `keywords: ["python", "programming"]`
2. **Calls SDK methods** → Uses `SemanticKeywordIntegrator` (not HTTP endpoint)
3. **Gets DataForSEO insights** → Calls DataForSEO API through SDK client
4. **Generates content** → Integrates keywords naturally
5. **Returns response** → Includes semantic keywords and analysis

**No separate `/api/v1/keywords/analyze` call needed!**

---

## ✅ Frontend Checklist

- [ ] Use `/api/v1/blog/generate-enhanced` endpoint
- [ ] Set `use_semantic_keywords: true` in request
- [ ] Use synchronous mode (don't set `async_mode: true`)
- [ ] Set timeout to 5 minutes (300000ms)
- [ ] Handle errors with retry logic (for 5xx errors)
- [ ] Access `response.semantic_keywords` for semantic keywords
- [ ] Access `response.seo_metadata.keyword_analysis` for keyword insights
- [ ] Show loading state while waiting (can take 2-5 minutes)
- [ ] Display semantic keywords in UI after generation

---

## 🎯 Complete Example

```typescript
async function generateBlog(
  topic: string,
  keywords: string[]
): Promise<BlogGenerationResult> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 min

  try {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/blog/generate-enhanced`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic,
          keywords,
          tone: 'professional',
          length: 'medium',
          use_semantic_keywords: true,
          use_quality_scoring: true
        }),
        signal: controller.signal
      }
    );

    clearTimeout(timeoutId);

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: `HTTP ${response.status}`
      }));
      throw new Error(error.detail || 'Blog generation failed');
    }

    const data = await response.json();

    return {
      success: true,
      content: data.content,
      title: data.title,
      semanticKeywords: data.semantic_keywords || [],
      keywordAnalysis: data.seo_metadata?.keyword_analysis || {},
      qualityScore: data.quality_score || 0,
      seoScore: data.seo_score || 0
    };

  } catch (error) {
    clearTimeout(timeoutId);
    
    if (error.name === 'AbortError') {
      throw new Error('Blog generation timeout - please try again');
    }
    
    throw error;
  }
}

// Usage
try {
  const result = await generateBlog('Python Basics', ['python', 'programming']);
  console.log('Semantic keywords:', result.semanticKeywords);
  console.log('Content:', result.content);
} catch (error) {
  console.error('Generation failed:', error.message);
  // Show error to user, allow retry
}
```

---

## 🚫 What NOT to Do

### ❌ Don't Call Keywords Endpoint Separately

```typescript
// ❌ NOT NEEDED - Blog generation already includes this
const keywordResponse = await fetch('/api/v1/keywords/analyze', {
  method: 'POST',
  body: JSON.stringify({ keywords: ['python'] })
});

// ✅ INSTEAD: Just use blog generation endpoint
const blogResponse = await fetch('/api/v1/blog/generate-enhanced', {
  method: 'POST',
  body: JSON.stringify({
    topic: 'Python',
    keywords: ['python'],
    use_semantic_keywords: true
  })
});
// Response includes semantic_keywords automatically
```

### ❌ Don't Use Async Mode (For Now)

```typescript
// ❌ NOT RECOMMENDED: Async mode has Cloud Tasks queue issues
const response = await fetch(
  '/api/v1/blog/generate-enhanced?async_mode=true',
  { ... }
);

// ✅ RECOMMENDED: Use synchronous mode
const response = await fetch(
  '/api/v1/blog/generate-enhanced',
  { ... }
);
```

---

## 📝 Summary

### What Frontend Should Do

1. ✅ **Call `/api/v1/blog/generate-enhanced`** with keywords array
2. ✅ **Set `use_semantic_keywords: true`** to enable semantic keyword integration
3. ✅ **Wait for response** (synchronous mode, timeout: 5 minutes)
4. ✅ **Access `response.semantic_keywords`** for semantic keywords
5. ✅ **Handle errors** with retry logic for 5xx errors
6. ✅ **Show loading state** while waiting (2-5 minutes typical)

### What Frontend Should NOT Do

1. ❌ **Don't call `/api/v1/keywords/analyze` separately** - it's integrated
2. ❌ **Don't use async mode** (Cloud Tasks queue issues)
3. ❌ **Don't poll** - synchronous mode returns complete response
4. ❌ **Don't retry on 4xx errors** - these are client errors

---

## ✅ Conclusion

**The flow works correctly!** The frontend should:

- Use synchronous blog generation endpoint
- Wait for the complete response (with timeout)
- Access semantic keywords from response
- Handle errors with appropriate retry logic
- **No polling needed** - everything is in one response

**No changes needed to backend. Frontend just needs to use the correct endpoint and wait for response.**

