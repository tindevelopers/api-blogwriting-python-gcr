# Frontend Method Guide v1.3.6

**Version:** 1.3.6  
**Date:** 2025-11-23  
**Status:** ✅ Production Ready

---

## 🎯 Endpoint Verification

✅ **Endpoint:** `POST /api/v1/blog/generate-enhanced`  
✅ **Status:** Fully functional  
✅ **Content Generation:** Uses DataForSEO Content Generation API  
✅ **Blog Types:** All 28 types supported  

---

## 📋 Frontend Integration Method

### TypeScript/JavaScript Method

```typescript
/**
 * Generate blog content using DataForSEO Content Generation API
 * 
 * @param params - Blog generation parameters
 * @returns Promise with generated blog content and SEO metrics
 */
async function generateBlogEnhanced(params: {
  topic: string;
  keywords: string[];
  blog_type?: string;  // One of 28 blog types (default: 'custom')
  tone?: string;        // 'professional' | 'casual' | 'friendly' | etc.
  length?: string;      // 'short' | 'medium' | 'long' | 'extended'
  word_count_target?: number;  // Specific word count (100-10000)
  optimize_for_traffic?: boolean;  // Enable SEO optimization (default: true)
  analyze_backlinks?: boolean;  // Analyze backlinks for keywords (default: false)
  backlink_url?: string;  // URL to analyze (required if analyze_backlinks=true)
  brand_name?: string;  // For 'brand' type
  category?: string;  // For 'top_10' or 'listicle' type
  product_name?: string;  // For 'product_review' type
  comparison_items?: string[];  // For 'comparison' type
  target_audience?: string;
  custom_instructions?: string;
}): Promise<EnhancedBlogGenerationResponse> {
  const API_BASE_URL = 'https://blog-writer-api-dev-kq42l26tuq-od.a.run.app';
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/blog/generate-enhanced`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        topic: params.topic,
        keywords: params.keywords,
        blog_type: params.blog_type || 'custom',
        tone: params.tone || 'professional',
        length: params.length || 'medium',
        word_count_target: params.word_count_target,
        optimize_for_traffic: params.optimize_for_traffic !== false,  // Default: true
        analyze_backlinks: params.analyze_backlinks || false,
        backlink_url: params.backlink_url,
        brand_name: params.brand_name,
        category: params.category,
        product_name: params.product_name,
        comparison_items: params.comparison_items,
        target_audience: params.target_audience,
        custom_instructions: params.custom_instructions,
        use_dataforseo_content_generation: true,  // Always use DataForSEO
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: response.statusText }));
      throw new Error(errorData.error || `Blog generation failed: ${response.statusText}`);
    }

    const data: EnhancedBlogGenerationResponse = await response.json();
    return data;
    
  } catch (error) {
    console.error('Blog generation error:', error);
    throw error;
  }
}
```

---

## 📝 TypeScript Types

```typescript
interface EnhancedBlogGenerationResponse {
  // Generated Content
  title: string;
  content: string;
  meta_title: string;
  meta_description: string;
  
  // Quality Scores
  readability_score: number;  // 0-100
  seo_score: number;  // 0-100
  quality_score: number;  // 0-100
  
  // Quality Dimensions
  quality_dimensions: {
    readability: number;
    seo: number;
    structure: number;
    keyword_optimization: number;
  };
  
  // SEO Metadata
  seo_metadata: {
    semantic_keywords: string[];
    subtopics: string[];
    blog_type: string;
    keyword_density: Record<string, { count: number; density: number }>;
    headings_count: number;
    avg_sentence_length: number;
    seo_factors: string[];
    word_count_range: {
      min: number;
      max: number;
      actual: number;
    };
    backlink_keywords?: string[];
  };
  
  // Semantic Keywords
  semantic_keywords: string[];
  
  // Generation Info
  total_tokens: number;
  total_cost: number;
  generation_time: number;
  success: boolean;
  warnings: string[];
}
```

---

## 💻 Complete Usage Examples

### Example 1: Basic Blog Generation

```typescript
const result = await generateBlogEnhanced({
  topic: 'Introduction to Python Programming',
  keywords: ['python', 'programming', 'coding'],
  blog_type: 'tutorial',
  tone: 'professional',
  length: 'medium',
});

console.log('Title:', result.title);
console.log('Content:', result.content);
console.log('SEO Score:', result.seo_score);
console.log('Word Count:', result.seo_metadata.word_count_range.actual);
```

### Example 2: Brand Blog

```typescript
const result = await generateBlogEnhanced({
  topic: 'Why Choose Our Brand',
  keywords: ['brand', 'quality', 'reliability'],
  blog_type: 'brand',
  brand_name: 'TechCorp',
  tone: 'professional',
  length: 'long',
  optimize_for_traffic: true,
});
```

### Example 3: Top 10 List

```typescript
const result = await generateBlogEnhanced({
  topic: 'Top 10 Best Laptops for Developers',
  keywords: ['laptops', 'developers', 'programming'],
  blog_type: 'top_10',
  category: 'Technology',
  tone: 'professional',
  length: 'long',
  word_count_target: 2000,
});
```

### Example 4: Product Review

```typescript
const result = await generateBlogEnhanced({
  topic: 'iPhone 15 Pro Review',
  keywords: ['iphone', 'apple', 'smartphone'],
  blog_type: 'product_review',
  product_name: 'iPhone 15 Pro',
  tone: 'professional',
  length: 'medium',
});
```

### Example 5: Premium Blog with Backlink Analysis

```typescript
const result = await generateBlogEnhanced({
  topic: 'Advanced SEO Strategies',
  keywords: ['seo', 'marketing', 'optimization'],
  blog_type: 'guide',
  tone: 'professional',
  length: 'long',
  optimize_for_traffic: true,
  analyze_backlinks: true,
  backlink_url: 'https://example.com/premium-seo-blog',
});
```

---

## 🔍 Response Structure Verification

The endpoint returns content in this structure:

```json
{
  "title": "Generated Blog Title",
  "content": "Full blog content with HTML formatting...",
  "meta_title": "SEO-optimized meta title",
  "meta_description": "SEO-optimized meta description",
  "readability_score": 85.5,
  "seo_score": 92.3,
  "quality_score": 88.9,
  "quality_dimensions": {
    "readability": 85.5,
    "seo": 92.3,
    "structure": 90.0,
    "keyword_optimization": 88.2
  },
  "seo_metadata": {
    "semantic_keywords": ["keyword1", "keyword2"],
    "subtopics": ["subtopic1", "subtopic2"],
    "blog_type": "tutorial",
    "keyword_density": {
      "python": { "count": 15, "density": 2.5 }
    },
    "headings_count": 5,
    "avg_sentence_length": 18.5,
    "seo_factors": ["good keyword density", "proper headings"],
    "word_count_range": {
      "min": 375,
      "max": 625,
      "actual": 487
    }
  },
  "semantic_keywords": ["python", "programming", "coding"],
  "total_tokens": 1250,
  "total_cost": 0.0625,
  "generation_time": 3.45,
  "success": true,
  "warnings": []
}
```

---

## ✅ Content Generation Verification

The endpoint **guarantees content generation** because:

1. **DataForSEO API Integration**: Uses `DataForSEOContentGenerationService.generate_blog_content()`
2. **Fallback Mechanism**: Falls back to multi-stage pipeline if DataForSEO is unavailable
3. **Error Handling**: Returns clear error messages if generation fails
4. **Response Validation**: Always returns `EnhancedBlogGenerationResponse` with content fields

### Content Generation Flow:

```
Request → DataForSEO Service → Generate Subtopics → Generate Content → Generate Meta Tags → SEO Post-processing → Response
```

---

## 🚨 Error Handling

```typescript
try {
  const result = await generateBlogEnhanced({
    topic: 'Test Topic',
    keywords: ['test'],
  });
  
  if (!result.success) {
    console.error('Generation failed:', result.warnings);
  }
  
} catch (error) {
  if (error instanceof Error) {
    console.error('API Error:', error.message);
  } else {
    console.error('Unknown error:', error);
  }
}
```

---

## 📊 All 28 Blog Types

```typescript
type BlogType = 
  | 'custom'
  | 'brand'
  | 'top_10'
  | 'product_review'
  | 'how_to'
  | 'comparison'
  | 'guide'
  | 'tutorial'
  | 'listicle'
  | 'case_study'
  | 'news'
  | 'opinion'
  | 'interview'
  | 'faq'
  | 'checklist'
  | 'tips'
  | 'definition'
  | 'benefits'
  | 'problem_solution'
  | 'trend_analysis'
  | 'statistics'
  | 'resource_list'
  | 'timeline'
  | 'myth_busting'
  | 'best_practices'
  | 'getting_started'
  | 'advanced'
  | 'troubleshooting';
```

---

## 🎯 Quick Start

**Copy and paste this method into your frontend code:**

```typescript
const API_BASE_URL = 'https://blog-writer-api-dev-kq42l26tuq-od.a.run.app';

async function generateBlog(params: {
  topic: string;
  keywords: string[];
  blog_type?: string;
  tone?: string;
  length?: string;
}) {
  const response = await fetch(`${API_BASE_URL}/api/v1/blog/generate-enhanced`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      topic: params.topic,
      keywords: params.keywords,
      blog_type: params.blog_type || 'custom',
      tone: params.tone || 'professional',
      length: params.length || 'medium',
      use_dataforseo_content_generation: true,
    }),
  });
  
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return await response.json();
}
```

---

## ✅ Verification Checklist

- [x] Endpoint exists: `/api/v1/blog/generate-enhanced`
- [x] Content generation: Uses DataForSEO API
- [x] All 28 blog types: Supported
- [x] SEO optimization: Enabled by default
- [x] Word count tolerance: ±25%
- [x] Response structure: Complete with all metrics
- [x] Error handling: Proper error messages
- [x] TypeScript types: Provided above

---

**Ready to use!** Copy the method above and start generating blog content. 🚀

