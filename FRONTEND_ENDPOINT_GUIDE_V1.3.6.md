# Frontend Endpoint Guide v1.3.6

**Version:** 1.3.6  
**Date:** 2025-11-23  
**Status:** ✅ Production Ready

---

## 🎯 Primary Endpoint for DataForSEO Content Generation

### **POST** `/api/v1/blog/generate-enhanced`

**This is the ONLY endpoint you need for blog generation with all 28 blog types.**

---

## ✅ Why This Endpoint?

1. **✅ Supports All 28 Blog Types** - Complete blog type support
2. **✅ DataForSEO Content Generation** - Uses DataForSEO API by default
3. **✅ SEO Optimization** - Automatic post-processing for traffic
4. **✅ Word Count Tolerance** - ±25% flexibility
5. **✅ Backlink Analysis** - Premium keyword extraction feature
6. **✅ Comprehensive Response** - Full SEO metrics and quality scores

---

## 📋 Endpoint Details

### URL
```
POST https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/generate-enhanced
```

### Request Body

```typescript
interface EnhancedBlogGenerationRequest {
  // Required
  topic: string;                    // Main topic (3-200 chars)
  keywords: string[];                // Target SEO keywords (min 1)
  
  // Blog Type (28 options available)
  blog_type?: BlogContentType;       // See Blog Types below (default: 'custom')
  
  // Content Settings
  tone?: ContentTone;                // 'professional' | 'casual' | 'friendly' | etc.
  length?: ContentLength;            // 'short' | 'medium' | 'long' | 'extended'
  word_count_target?: number;        // Specific word count (100-10000)
  
  // SEO & Optimization
  optimize_for_traffic?: boolean;    // Enable SEO post-processing (default: true)
  
  // Backlink Analysis (Premium)
  analyze_backlinks?: boolean;       // Analyze backlinks for keywords (default: false)
  backlink_url?: string;             // URL to analyze (required if analyze_backlinks=true)
  
  // DataForSEO (default: true)
  use_dataforseo_content_generation?: boolean; // Use DataForSEO API (default: true)
  
  // Additional Options
  target_audience?: string;          // Target audience description
  custom_instructions?: string;       // Additional instructions (max 2000 chars)
  
  // Blog Type-Specific Fields
  brand_name?: string;               // For 'brand' type
  category?: string;                 // For 'top_10' or 'listicle' type
  product_name?: string;             // For 'product_review' type
  comparison_items?: string[];       // For 'comparison' type
}
```

### Response

```typescript
interface EnhancedBlogGenerationResponse {
  title: string;
  content: string;
  meta_title: string;
  meta_description: string;
  readability_score: number;         // 0-100
  seo_score: number;                 // 0-100
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
  quality_dimensions: {
    readability: number;
    seo: number;
    structure: number;
    keyword_optimization: number;
  };
  total_tokens: number;
  total_cost: number;
  generation_time: number;
  success: boolean;
  warnings: string[];
}
```

---

## 📚 All 28 Blog Types

### Core Types (7)
- `custom` - Custom content with specific instructions
- `brand` - Brand overviews and histories
- `top_10` - Ranking lists with detailed entries
- `product_review` - Detailed product analysis
- `how_to` - Step-by-step guides
- `comparison` - Side-by-side comparisons
- `guide` - Comprehensive guides

### Popular Content Types (21)
- `tutorial` - Step-by-step learning content
- `listicle` - Numbered lists (Top 5, Top 20, etc.)
- `case_study` - Real-world examples and results
- `news` - Current events and updates
- `opinion` - Editorial and thought leadership
- `interview` - Q&A with experts
- `faq` - Frequently asked questions
- `checklist` - Actionable checklists
- `tips` - Tips and tricks
- `definition` - What is X? Explanatory content
- `benefits` - Benefits-focused content
- `problem_solution` - Problem-solving content
- `trend_analysis` - Industry trends
- `statistics` - Data-driven content
- `resource_list` - Curated resources
- `timeline` - Historical or process timelines
- `myth_busting` - Debunking myths
- `best_practices` - Industry best practices
- `getting_started` - Beginner guides
- `advanced` - Advanced topics
- `troubleshooting` - Problem-solving guides

---

## 💻 Complete Example

```typescript
const response = await fetch(
  'https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/generate-enhanced',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      topic: 'Introduction to Python Programming',
      keywords: ['python', 'programming', 'coding'],
      blog_type: 'tutorial',              // ✅ One of 28 blog types
      tone: 'professional',
      length: 'short',
      word_count_target: 300,
      optimize_for_traffic: true,         // ✅ SEO optimization
      use_dataforseo_content_generation: true  // ✅ DataForSEO API
    })
  }
);

const data = await response.json();

// Access generated content
console.log(data.content);
console.log(data.seo_score);              // SEO score (0-100)
console.log(data.seo_metadata.word_count_range); // Word count validation
```

---

## 🚫 Endpoints to Avoid (Deprecated/Redundant)

### ❌ Do NOT Use These Endpoints

1. **`POST /api/v1/generate`**
   - ❌ Only supports CUSTOM blog type
   - ❌ Limited blog type support
   - ❌ Use `/api/v1/blog/generate-enhanced` instead

2. **`POST /api/v1/blog/generate`**
   - ❌ Only supports CUSTOM blog type
   - ❌ Limited blog type support
   - ❌ Use `/api/v1/blog/generate-enhanced` instead

3. **`POST /api/v1/blog/generate-unified`**
   - ❌ Different abstraction layer
   - ❌ Not optimized for DataForSEO
   - ❌ Use `/api/v1/blog/generate-enhanced` instead

4. **`POST /api/v1/blog/generate-local-business`**
   - ❌ Specialized for local business only
   - ❌ Use `/api/v1/blog/generate-enhanced` with `blog_type: 'brand'` instead

5. **`POST /api/v1/abstraction/blog/generate`**
   - ❌ Different abstraction layer
   - ❌ Not optimized for DataForSEO
   - ❌ Use `/api/v1/blog/generate-enhanced` instead

---

## ✅ Summary

**Use ONLY this endpoint:**
```
POST /api/v1/blog/generate-enhanced
```

**Why?**
- ✅ Supports all 28 blog types
- ✅ Uses DataForSEO Content Generation API
- ✅ Includes SEO optimization
- ✅ Includes word count tolerance (±25%)
- ✅ Includes backlink analysis option
- ✅ Comprehensive response with all metrics

**All other blog generation endpoints are deprecated or have limited functionality.**

---

## 📖 Full Documentation

- **Frontend Integration Guide:** `FRONTEND_INTEGRATION_V1.3.6.md`
- **API Documentation:** `API_DOCUMENTATION_V1.3.6.md`
- **Blog Types Reference:** `BLOG_TYPES_REFERENCE.md`

