# DataForSEO Endpoint Strategy by Content Goal

## Overview

This document provides specific DataForSEO API endpoint recommendations for each of the 4 content goal categories shown in the frontend interface.

---

## 🎯 1. SEO & Rankings

**Goal**: Rank high in search results  
**Focus**: High search volume, low difficulty, ranking opportunities

### Primary Endpoint Combination:

```python
# Endpoint Strategy for SEO & Rankings
{
    "primary_endpoints": [
        "keywords_data/google_ads/search_volume/live",      # ✅ Integrated
        "dataforseo_labs/google/keyword_difficulty/live",  # ✅ Integrated
        "serp/google/organic/live/advanced",               # ✅ Integrated
        "dataforseo_labs/google/keyword_overview/live"     # ✅ Integrated
    ],
    "secondary_endpoints": [
        "dataforseo_labs/google/keyword_ideas/live",      # ✅ Integrated
        "dataforseo_labs/google/ranked_keywords/live",     # ❌ Not integrated
        "on_page/instant_pages"                            # ❌ Not integrated
    ],
    "content_generation": "content_generation/generate_text/live"  # ❌ Not integrated
}
```

### Recommended Query Flow:

1. **Get Keyword Ideas** → `keyword_ideas/live`
   - Find high-volume keywords in your niche
   
2. **Analyze Search Volume & Difficulty** → `search_volume/live` + `keyword_difficulty/live`
   - Filter: High volume (1000+), Low-Medium difficulty (<60)
   
3. **SERP Analysis** → `serp/organic/live/advanced`
   - Analyze top-ranking pages
   - Extract content structure, headings, featured snippets
   
4. **Keyword Overview** → `keyword_overview/live`
   - Get comprehensive metrics (intent, monthly trends, SERP features)
   
5. **Generate Content** → `content_generation/generate_text/live`
   - Use SERP insights to create ranking-optimized content

### Key Metrics to Prioritize:
- **Search Volume**: 1000+ monthly searches
- **Difficulty**: <60 (Medium or lower)
- **CPC**: Higher CPC = more valuable keyword
- **SERP Features**: Featured snippets, PAA opportunities

---

## 💬 2. Engagement

**Goal**: Increase shares and comments  
**Focus**: Question-based keywords, trending topics, discussion-worthy content

### Primary Endpoint Combination:

```python
# Endpoint Strategy for Engagement
{
    "primary_endpoints": [
        "dataforseo_labs/google/search_intent/live",       # ✅ Integrated
        "serp/google/organic/live/advanced",                # ✅ Integrated (PAA extraction)
        "content_analysis/search/live",                     # ❌ Not integrated
        "dataforseo_labs/google/related_keywords/live"    # ✅ Integrated
    ],
    "secondary_endpoints": [
        "social_media/pinterest/posts/live",                # ❌ Not integrated
        "social_media/reddit/posts/live",                  # ❌ Not integrated
        "dataforseo_labs/google/keyword_ideas/live"        # ✅ Integrated
    ],
    "content_generation": "content_generation/generate_text/live"  # ❌ Not integrated
}
```

### Recommended Query Flow:

1. **Search Intent Analysis** → `search_intent/live`
   - Filter: **Informational** intent keywords
   - Focus: Question-based queries ("how to", "what is", "why does")
   
2. **SERP Analysis (PAA Focus)** → `serp/organic/live/advanced`
   - Extract **People Also Ask** questions
   - Get related searches
   - Identify discussion-worthy topics
   
3. **Content Analysis** → `content_analysis/search/live` (if integrated)
   - Analyze sentiment of top-performing content
   - Identify engagement signals (shares, comments patterns)
   
4. **Related Keywords** → `related_keywords/live`
   - Expand topic coverage for comprehensive content
   
5. **Generate Content** → `content_generation/generate_text/live`
   - Create Q&A format content
   - Include discussion prompts
   - Use engaging, conversational tone

### Key Metrics to Prioritize:
- **Intent Type**: Informational (not transactional)
- **PAA Questions**: High number of related questions
- **Social Signals**: Trending on social platforms
- **Question Format**: "How", "What", "Why", "When", "Where"

---

## 💰 3. Conversions

**Goal**: Drive sales and sign-ups  
**Focus**: Commercial intent keywords, high CPC, transactional queries

### Primary Endpoint Combination:

```python
# Endpoint Strategy for Conversions
{
    "primary_endpoints": [
        "keywords_data/google_ads/search_volume/live",     # ✅ Integrated (CPC data)
        "dataforseo_labs/google/search_intent/live",       # ✅ Integrated
        "serp/google/organic/live/advanced",                # ✅ Integrated (Shopping results)
        "dataforseo_labs/google/keyword_overview/live"     # ✅ Integrated
    ],
    "secondary_endpoints": [
        "business_data/google/my_business/live",            # ❌ Not integrated
        "merchant/google/shopping/products/live",           # ❌ Not integrated
        "keywords_data/google_ads/search_volume/live"       # ✅ Integrated (for CPC analysis)
    ],
    "content_generation": "content_generation/generate_text/live"  # ❌ Not integrated
}
```

### Recommended Query Flow:

1. **Search Volume with CPC** → `search_volume/live`
   - Filter: **High CPC** keywords ($5+)
   - Focus: Commercial keywords ("buy", "best", "review", "price")
   
2. **Search Intent Analysis** → `search_intent/live`
   - Filter: **Transactional** or **Commercial** intent
   - Prioritize purchase-intent keywords
   
3. **SERP Analysis** → `serp/organic/live/advanced`
   - Analyze shopping results
   - Check for local packs (local businesses)
   - Review product comparison pages
   
4. **Keyword Overview** → `keyword_overview/live`
   - Get intent classification
   - Analyze commercial SERP features
   
5. **Generate Content** → `content_generation/generate_text/live`
   - Create conversion-focused content
   - Include CTAs, product comparisons, reviews
   - Optimize for purchase intent

### Key Metrics to Prioritize:
- **CPC**: High CPC = commercial value
- **Intent**: Transactional or Commercial
- **SERP Features**: Shopping results, local packs
- **Keywords**: "buy", "best", "review", "price", "compare"

---

## 🏢 4. Brand Awareness

**Goal**: Build brand recognition  
**Focus**: Brand mentions, industry keywords, thought leadership topics

### Primary Endpoint Combination:

```python
# Endpoint Strategy for Brand Awareness
{
    "primary_endpoints": [
        "content_analysis/search/live",                     # ❌ Not integrated
        "dataforseo_labs/google/keyword_overview/live",    # ✅ Integrated
        "serp/google/organic/live/advanced",               # ✅ Integrated
        "backlinks/backlinks/live"                         # ❌ Not integrated
    ],
    "secondary_endpoints": [
        "dataforseo_labs/google/competitors_domain/live",  # ✅ Integrated (get_competitor_keywords)
        "content_analysis/summary/live",                    # ❌ Not integrated
        "social_media/facebook/posts/live",                 # ❌ Not integrated
        "dataforseo_labs/google/keyword_ideas/live"         # ✅ Integrated
    ],
    "content_generation": "content_generation/generate_text/live"  # ❌ Not integrated
}
```

### Recommended Query Flow:

1. **Content Analysis** → `content_analysis/search/live` (if integrated)
   - Analyze brand mentions and sentiment
   - Identify brand visibility opportunities
   
2. **Keyword Overview** → `keyword_overview/live`
   - Find industry + brand keyword combinations
   - Identify thought leadership topics
   
3. **Competitor Analysis** → `competitors_domain/live`
   - See what competitors rank for
   - Identify brand positioning opportunities
   
4. **SERP Analysis** → `serp/organic/live/advanced`
   - Analyze brand presence in search results
   - Check for brand-related SERP features
   
5. **Backlink Analysis** → `backlinks/backlinks/live` (if integrated)
   - Understand brand authority
   - Identify content gaps
   
6. **Generate Content** → `content_generation/generate_text/live`
   - Create brand-building content
   - Thought leadership pieces
   - Industry insights and trends

### Key Metrics to Prioritize:
- **Brand Mentions**: Current brand visibility
- **Industry Keywords**: Brand + industry combinations
- **Competitor Gaps**: Opportunities competitors miss
- **Authority**: Backlink profile strength

---

## 🚀 Implementation Recommendations

### Phase 1: Core Integration (Immediate)

1. **Content Generation API** (Required for all goals)
   ```python
   # Priority 1: Must integrate
   - content_generation/generate_text/live
   - content_generation/generate_meta_tags/live
   ```

2. **Content Analysis API** (Engagement & Brand Awareness)
   ```python
   # Priority 1: High value for Engagement and Brand Awareness
   - content_analysis/search/live
   - content_analysis/summary/live
   ```

### Phase 2: Enhanced Features (High Value)

1. **On-Page API** (SEO & Rankings)
   ```python
   - on_page/instant_pages
   ```

2. **Backlinks API** (Brand Awareness)
   ```python
   - backlinks/backlinks/live
   ```

3. **Competitor Analysis** (All categories)
   ```python
   - dataforseo_labs/google/competitors_domain/live  # ✅ Already integrated
   - dataforseo_labs/google/ranked_keywords/live    # ❌ Not integrated
   ```

### Phase 3: Specialized Features (Nice to Have)

1. **Social Media APIs** (Engagement)
   ```python
   - social_media/pinterest/posts/live
   - social_media/reddit/posts/live
   - social_media/facebook/posts/live
   ```

2. **Business Data APIs** (Conversions)
   ```python
   - business_data/google/my_business/live
   - merchant/google/shopping/products/live
   ```

---

## 📊 Endpoint Priority Matrix

| Endpoint | SEO & Rankings | Engagement | Conversions | Brand Awareness | Priority |
|----------|---------------|------------|-------------|-----------------|----------|
| `content_generation/generate_text/live` | ✅ | ✅ | ✅ | ✅ | **P1** |
| `keywords_data/google_ads/search_volume/live` | ✅✅ | ⚠️ | ✅✅ | ⚠️ | P1 |
| `dataforseo_labs/google/search_intent/live` | ⚠️ | ✅✅ | ✅✅ | ⚠️ | P1 |
| `serp/google/organic/live/advanced` | ✅✅ | ✅✅ | ✅✅ | ✅✅ | P1 |
| `content_analysis/search/live` | ⚠️ | ✅✅ | ⚠️ | ✅✅ | **P1** |
| `dataforseo_labs/google/keyword_overview/live` | ✅✅ | ✅ | ✅✅ | ✅✅ | P1 |
| `dataforseo_labs/google/keyword_difficulty/live` | ✅✅ | ⚠️ | ⚠️ | ⚠️ | P1 |
| `on_page/instant_pages` | ✅✅ | ⚠️ | ⚠️ | ⚠️ | P2 |
| `backlinks/backlinks/live` | ⚠️ | ⚠️ | ⚠️ | ✅✅ | P2 |
| `dataforseo_labs/google/ranked_keywords/live` | ✅✅ | ⚠️ | ⚠️ | ✅✅ | P2 |
| `social_media/*/posts/live` | ⚠️ | ✅✅ | ⚠️ | ✅ | P3 |

**Legend:**
- ✅✅ = Critical for this goal
- ✅ = Important for this goal
- ⚠️ = Optional/supplementary

---

## 🎯 Goal-Specific Endpoint Routing

### Recommended API Endpoint Structure:

```python
POST /api/v1/keywords/goal-based-analysis
{
    "keywords": ["pet grooming", "dog grooming"],
    "content_goal": "SEO & Rankings" | "Engagement" | "Conversions" | "Brand Awareness",
    "location": "United States",
    "language": "en"
}
```

### Endpoint Selection Logic:

```python
def get_endpoints_for_goal(content_goal: str) -> List[str]:
    """Return optimal endpoints for content goal."""
    
    if content_goal == "SEO & Rankings":
        return [
            "keywords_data/google_ads/search_volume/live",
            "dataforseo_labs/google/keyword_difficulty/live",
            "serp/google/organic/live/advanced",
            "dataforseo_labs/google/keyword_overview/live",
            "dataforseo_labs/google/keyword_ideas/live"
        ]
    
    elif content_goal == "Engagement":
        return [
            "dataforseo_labs/google/search_intent/live",
            "serp/google/organic/live/advanced",  # Focus on PAA
            "content_analysis/search/live",
            "dataforseo_labs/google/related_keywords/live"
        ]
    
    elif content_goal == "Conversions":
        return [
            "keywords_data/google_ads/search_volume/live",  # Focus on CPC
            "dataforseo_labs/google/search_intent/live",   # Focus on commercial intent
            "serp/google/organic/live/advanced",             # Focus on shopping results
            "dataforseo_labs/google/keyword_overview/live"
        ]
    
    elif content_goal == "Brand Awareness":
        return [
            "content_analysis/search/live",
            "dataforseo_labs/google/keyword_overview/live",
            "serp/google/organic/live/advanced",
            "backlinks/backlinks/live",
            "dataforseo_labs/google/competitors_domain/live"
        ]
```

---

## 💡 Content Generation Strategy

Since switching from OpenAI/Anthropic to DataForSEO:

### For Each Goal:

1. **SEO & Rankings**
   - Use SERP analysis to structure content
   - Match top-ranking page structure
   - Optimize for featured snippets
   - Include target keywords naturally

2. **Engagement**
   - Q&A format based on PAA questions
   - Conversational, discussion-worthy tone
   - Include prompts for comments/shares
   - Address common questions

3. **Conversions**
   - Include product comparisons
   - Add clear CTAs
   - Focus on benefits and value
   - Include reviews/testimonials structure

4. **Brand Awareness**
   - Thought leadership content
   - Industry insights
   - Brand storytelling
   - Authority-building topics

---

## 📋 Next Steps

1. **Integrate Content Generation API** (Critical)
2. **Integrate Content Analysis API** (High value)
3. **Create goal-based endpoint routing** in backend
4. **Update frontend** to pass `content_goal` parameter
5. **Add missing endpoints** (on_page, backlinks, ranked_keywords)
6. **Test each goal category** with appropriate endpoints
7. **Monitor performance** and optimize endpoint selection

