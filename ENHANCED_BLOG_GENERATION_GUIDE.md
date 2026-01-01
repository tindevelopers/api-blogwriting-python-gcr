# Enhanced Blog Generation API Guide

**Version**: 1.2.0  
**Date**: 2025-01-10

---

## Overview

The Enhanced Blog Generation endpoint (`POST /api/v1/blog/generate-enhanced`) uses a sophisticated multi-stage pipeline to produce significantly higher-quality, ranking-optimized blog content. This endpoint implements all recommendations from `BLOG_QUALITY_IMPROVEMENTS.md`.

---

## Endpoint

```
POST /api/v1/blog/generate-enhanced
```

---

## Request Body

```typescript
{
  // Required
  topic: string;                    // Main topic (3-200 characters)
  keywords: string[];               // Target SEO keywords (min 1)
  
  // Mode (Phase)
  // Phase 1: "quick_generate" (DataForSEO-only, cost-efficient)
  // Phase 2: "enhanced_dataforseo" (DataForSEO-only + research payload)
  // Phase 3: "multi_phase" (AI-first pipeline + LiteLLM polish)
  mode?: "quick_generate" | "enhanced_dataforseo" | "multi_phase";
  
  // Optional - Content Settings
  tone?: "professional" | "casual" | "academic" | "conversational" | "instructional";
  length?: "short" | "medium" | "long";
  template_type?: string;           // "expert_authority" | "how_to_guide" | "comparison" | etc.
  
  // Optional - Enhanced Features (Phase 1 & 2)
  use_google_search?: boolean;      // Default: true - Research and fact-checking
  use_fact_checking?: boolean;       // Default: true - Verify factual claims
  use_citations?: boolean;           // Default: true - Include citations
  use_serp_optimization?: boolean;  // Default: true - Optimize for SERP features
  
  // Optional - Phase 3 Features
  use_consensus_generation?: boolean;  // Default: false - Multi-model consensus (higher cost)
  use_knowledge_graph?: boolean;       // Default: true - Entity recognition & structured data
  use_semantic_keywords?: boolean;     // Default: true - Semantic keyword integration
  use_quality_scoring?: boolean;      // Default: true - Comprehensive quality scoring
  
  // Optional - Additional Context
  target_audience?: string;         // Target audience description
  custom_instructions?: string;      // Additional instructions (max 5000 chars)
}
```

---

## Response Body

```typescript
{
  // Content
  title: string;                    // Blog post title
  content: string;                   // Full blog content
  meta_title: string;                // SEO-optimized meta title
  meta_description: string;          // SEO-optimized meta description
  
  // Quality Metrics
  readability_score: number;         // Flesch Reading Ease (0-100)
  seo_score: number;                 // Overall SEO score (0-100)
  quality_score?: number;            // Overall quality score (0-100) - Phase 3
  quality_dimensions?: {             // Phase 3
    readability: number;
    seo: number;
    structure: number;
    factual: number;
    uniqueness: number;
    engagement: number;
  };
  
  // Pipeline Information
  stage_results: Array<{
    stage: string;                   // "research_outline" | "draft" | "enhancement" | "seo_polish"
    provider: string;                // "anthropic" | "openai" | "multi-model"
    tokens: number;
    cost: number;
  }>;
  
  // Citations & Sources
  citations: Array<{
    text: string;                    // Citation text snippet
    url: string;                     // Source URL
    title: string;                   // Source title
  }>;
  
  // Phase 3 Features
  structured_data?: object;          // Schema.org JSON-LD (Knowledge Graph)
  semantic_keywords?: string[];      // Semantically integrated keywords
  
  // SEO Metadata
  seo_metadata: {
    research?: {
      traditionalSeo?: object;       // SERP, competition, top domains (Phase 2/3)
      aiOptimization?: object;       // AI search volume / mentions (Phase 2/3)
      contentAnalysis?: object;      // Content Analysis summary (Phase 2/3)
      backlinks?: object;            // Backlink summary (Phase 2/3)
    };
    search_intent?: {                 // Intent analysis results
      primary_intent: "informational" | "commercial" | "transactional" | "navigational";
      confidence: number;             // 0-1
      probabilities: object;
    };
    semantic_keywords?: string[];
    keyword_clusters?: number;
    quality_report?: {
      overall_score: number;
      dimension_scores: object;
      passed_threshold: boolean;
      critical_issues: string[];
    };
  };
  internal_links: Array<{
    anchor_text: string;
    target_url: string;
  }>;
  
  // Performance Metrics
  total_tokens: number;
  total_cost: number;                // USD
  generation_time: number;           // Seconds
  cost_breakdown: {
    dataforseo: Record<string, number>;
    llm: Record<string, number>;
    total: number;
  };
  
  // Status
  success: boolean;
  warnings: string[];
}
```

---

## Example Usage

### Basic Request

```bash
curl -X POST "https://your-api.com/api/v1/blog/generate-enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "How to Optimize Python APIs for Production",
    "keywords": ["python api", "api optimization", "production deployment"],
    "tone": "professional",
    "length": "medium"
  }'
```

### Advanced Request with All Features

```bash
curl -X POST "https://your-api.com/api/v1/blog/generate-enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AI-Powered Content Generation Best Practices",
    "keywords": ["ai content", "content automation", "blog writing ai"],
    "tone": "professional",
    "length": "long",
    "template_type": "expert_authority",
    "use_google_search": true,
    "use_fact_checking": true,
    "use_citations": true,
    "use_serp_optimization": true,
    "use_consensus_generation": true,
    "use_knowledge_graph": true,
    "use_semantic_keywords": true,
    "use_quality_scoring": true,
    "target_audience": "Content marketers and SEO professionals",
    "custom_instructions": "Focus on practical, actionable insights with real-world examples"
  }'
```

### Python Example

```python
import httpx

async def generate_enhanced_blog():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://your-api.com/api/v1/blog/generate-enhanced",
            json={
                "topic": "Modern Web Development Practices",
                "keywords": ["web development", "best practices", "modern frameworks"],
                "tone": "professional",
                "length": "medium",
                "use_google_search": True,
                "use_citations": True,
                "use_quality_scoring": True
            }
        )
        
        result = response.json()
        
        print(f"Title: {result['title']}")
        print(f"Quality Score: {result['quality_score']}/100")
        print(f"Readability: {result['readability_score']}")
        print(f"Total Cost: ${result['total_cost']:.4f}")
        print(f"Generation Time: {result['generation_time']:.2f}s")
        
        if result['quality_dimensions']:
            print("\nQuality Breakdown:")
            for dimension, score in result['quality_dimensions'].items():
                print(f"  {dimension}: {score}/100")
        
        return result
```

### JavaScript/TypeScript Example

```typescript
async function generateEnhancedBlog() {
  const response = await fetch('https://your-api.com/api/v1/blog/generate-enhanced', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      topic: 'Cloud-Native Application Architecture',
      keywords: ['cloud native', 'microservices', 'containerization'],
      tone: 'professional',
      length: 'long',
      use_google_search: true,
      use_citations: true,
      use_quality_scoring: true,
    }),
  });
  
  const result = await response.json();
  
  console.log('Generated Blog:', result.title);
  console.log('Quality Score:', result.quality_score);
  console.log('Citations:', result.citations.length);
  
  return result;
}
```

---

## Pipeline Stages

### Stage 1: Research & Outline (Claude 3.5 Sonnet)
- Comprehensive topic research
- Competitor analysis
- Content gap identification
- Detailed outline generation
- **Duration**: ~2-3 seconds

### Stage 2: Draft Generation (GPT-4o or Consensus)
- Full content creation based on outline
- Source integration
- Recent information inclusion
- Few-shot learning from top-ranking content
- **Duration**: ~4-6 seconds (8-12s with consensus)

### Stage 3: Enhancement & Fact-Checking (Claude 3.5 Sonnet)
- Content refinement and flow improvement
- Fact-checking with Google Search
- Readability optimization
- Natural transitions
- **Duration**: ~3-4 seconds

### Stage 4: SEO & Polish (GPT-4o-mini)
- Meta title and description generation
- SEO optimization
- Internal linking suggestions
- Final polish
- **Duration**: ~1-2 seconds

### Post-Processing (Phase 3)
- Semantic keyword integration
- Knowledge Graph entity extraction
- Structured data generation
- Quality scoring
- **Duration**: ~1-2 seconds

**Total Generation Time**: ~10-15 seconds (standard), ~15-20 seconds (with consensus)

---

## Feature Details

### Intent-Based Generation

Automatically detects search intent and optimizes content:

- **Informational**: How-to guides, explanations, tutorials
- **Commercial**: Comparisons, reviews, best-of lists
- **Transactional**: Purchase intent, pricing information
- **Navigational**: Brand or site-specific queries

**Example**: For "best python frameworks", intent is detected as "commercial", so content includes comparison tables and recommendations.

### Few-Shot Learning

Extracts top-ranking content examples and includes them in prompts:

- Fetches top 3 ranking pages from SERP
- Extracts structure, tone, and key points
- Includes examples in prompt context
- Guides LLM to match successful patterns

**Benefit**: Content structure aligns with what ranks well.

### Content Length Optimization

Analyzes top-ranking content length and adjusts target:

- Fetches SERP results for target keyword
- Analyzes average content length
- Sets target to exceed average by 20-30%
- Ensures competitive depth

**Example**: If top results average 1,500 words, target is set to ~1,875 words.

### Multi-Model Consensus (Optional)

Generates content with multiple LLMs and synthesizes:

1. Generate draft with GPT-4o (comprehensive coverage)
2. Generate alternative with Claude 3.5 Sonnet (clarity & insights)
3. Synthesize best sections using GPT-4o-mini
4. Final coherence check with Claude

**Cost**: ~2-3x standard generation  
**Quality**: Significantly higher, especially for complex topics

### Knowledge Graph Integration

Extracts entities and generates structured data:

- Entity recognition from content
- Schema.org JSON-LD generation
- Rich snippet optimization
- Entity relationship mapping

**Requires**: `GOOGLE_KNOWLEDGE_GRAPH_API_KEY` (free tier: 100k queries/day)

### Semantic Keyword Integration

Naturally integrates related keywords:

- Fetches related keywords from DataForSEO
- Creates keyword clusters
- Identifies natural integration points
- Integrates without keyword stuffing

**Benefit**: Better topical authority and semantic relevance.

### Quality Scoring

6-dimensional quality assessment:

1. **Readability** (20%): Flesch Reading Ease, sentence/paragraph length
2. **SEO** (25%): Title, meta description, keyword optimization, headings
3. **Structure** (20%): Paragraph length, list usage, heading hierarchy
4. **Factual** (15%): Citation count, factual claim verification
5. **Uniqueness** (10%): Generic phrase detection, repetition analysis
6. **Engagement** (10%): Questions, CTAs, examples

**Threshold**: Default 70/100 (configurable)

---

## Cost Estimation

### Standard Generation (without consensus)
- **Tokens**: ~4,000-6,000 tokens
- **Cost**: $0.015-$0.030 per article
- **Time**: 10-15 seconds

### With Consensus Generation
- **Tokens**: ~8,000-12,000 tokens
- **Cost**: $0.040-$0.080 per article
- **Time**: 15-20 seconds

### Cost Breakdown (Standard)
- Stage 1 (Claude): ~500 tokens ($0.002)
- Stage 2 (GPT-4o): ~2,000 tokens ($0.010)
- Stage 3 (Claude): ~1,500 tokens ($0.006)
- Stage 4 (GPT-4o-mini): ~800 tokens ($0.001)
- **Total**: ~$0.019 per article

---

## Best Practices

### 1. Keyword Selection
- Use 3-5 primary keywords
- Include long-tail variations
- Ensure keywords are semantically related

### 2. Template Selection
- **Expert Authority**: For thought leadership content
- **How-To Guide**: For instructional content
- **Comparison**: For product/service comparisons
- **Case Study**: For data-driven insights

### 3. Feature Toggles
- **Always enable**: `use_google_search`, `use_citations`, `use_quality_scoring`
- **Enable for premium**: `use_consensus_generation` (higher cost, better quality)
- **Enable for SEO**: `use_knowledge_graph`, `use_semantic_keywords`

### 4. Quality Thresholds
- Aim for `quality_score` > 80
- Ensure `readability_score` > 60
- Check `seo_score` > 75
- Review `critical_issues` in response

### 5. Cost Optimization
- Use consensus generation selectively (premium content only)
- Cache SERP analysis results
- Batch similar requests when possible

---

## Error Handling

### Common Errors

**503 Service Unavailable**
- **Cause**: Missing Google Custom Search credentials
- **Solution**: Set `GOOGLE_CUSTOM_SEARCH_API_KEY` and `GOOGLE_CUSTOM_SEARCH_ENGINE_ID`

**422 Validation Error**
- **Cause**: Invalid request parameters
- **Solution**: Check request body matches schema

**500 Internal Server Error**
- **Cause**: AI provider failure or rate limit
- **Solution**: Check provider credentials and retry with exponential backoff

### Graceful Degradation

The endpoint gracefully degrades when optional services are unavailable:

- **No Google Search**: Falls back to AI-only research
- **No DataForSEO**: Uses keyword-based intent detection
- **No Knowledge Graph**: Skips entity extraction (content still generated)
- **No Citations**: Content generated without citations

---

## Performance Tips

1. **Use Appropriate Length**: Match length to content type (short for news, long for guides)
2. **Enable Caching**: Cache SERP analysis and keyword data
3. **Batch Requests**: Group similar topics for efficiency
4. **Monitor Costs**: Track `total_cost` in responses
5. **Quality First**: Use consensus generation for high-value content

---

## Response Examples

### Successful Response

```json
{
  "title": "Complete Guide to AI-Powered Content Generation",
  "content": "Full blog content with citations and structured data...",
  "meta_title": "AI Content Generation: Complete Guide 2025",
  "meta_description": "Learn how AI-powered content generation works...",
  "readability_score": 72.5,
  "seo_score": 88.0,
  "quality_score": 85.5,
  "quality_dimensions": {
    "readability": 75.0,
    "seo": 90.0,
    "structure": 85.0,
    "factual": 95.0,
    "uniqueness": 90.0,
    "engagement": 85.0
  },
  "stage_results": [
    {"stage": "research_outline", "provider": "anthropic", "tokens": 500, "cost": 0.002},
    {"stage": "draft", "provider": "openai", "tokens": 2000, "cost": 0.010},
    {"stage": "enhancement", "provider": "anthropic", "tokens": 1500, "cost": 0.006},
    {"stage": "seo_polish", "provider": "openai", "tokens": 800, "cost": 0.001}
  ],
  "citations": [
    {"text": "According to recent research...", "url": "https://source.com", "title": "Research Study"}
  ],
  "structured_data": {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    "headline": "Complete Guide to AI-Powered Content Generation",
    "about": {
      "@type": "Thing",
      "name": "AI Content Generation"
    }
  },
  "semantic_keywords": ["ai writing", "automated content", "content ai tools"],
  "total_tokens": 4800,
  "total_cost": 0.019,
  "generation_time": 12.5,
  "seo_metadata": {
    "search_intent": {
      "primary_intent": "informational",
      "confidence": 0.92
    },
    "semantic_keywords": ["ai writing", "automated content"],
    "keyword_clusters": 3,
    "quality_report": {
      "overall_score": 85.5,
      "passed_threshold": true,
      "critical_issues": []
    }
  },
  "success": true,
  "warnings": []
}
```

---

## Troubleshooting

### Low Quality Scores

**Issue**: Quality score below threshold

**Solutions**:
- Enable `use_google_search` for better research
- Enable `use_citations` for factual accuracy
- Use `use_consensus_generation` for complex topics
- Review `quality_dimensions` to identify weak areas

### High Costs

**Issue**: Cost per article too high

**Solutions**:
- Disable `use_consensus_generation` (saves ~60% cost)
- Use shorter `length` for simpler topics
- Cache SERP analysis results
- Monitor `total_cost` in responses

### Slow Generation

**Issue**: Generation time > 20 seconds

**Solutions**:
- Disable `use_consensus_generation` (saves ~5-8 seconds)
- Check Google Custom Search API quota
- Verify network connectivity
- Consider async processing for batch requests

---

## Related Documentation

- [Phase 1 & 2 Implementation](PHASE1_PHASE2_IMPLEMENTATION.md)
- [Phase 3 Implementation](PHASE3_IMPLEMENTATION.md)
- [Blog Quality Improvements](BLOG_QUALITY_IMPROVEMENTS.md)
- [Implementation Complete](IMPLEMENTATION_COMPLETE.md)

---

**Last Updated**: 2025-01-10  
**API Version**: 1.2.0

