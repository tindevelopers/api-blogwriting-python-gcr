# DataForSEO Endpoint Recommendations for Content Goals

## Overview

Based on the frontend interface showing 4 content goal categories, here are the optimal DataForSEO API endpoints for each:

---

## 1. SEO & Rankings

**Goal**: Rank high in search results

### Recommended Endpoints:

#### Primary:
- **`keywords_data/google_ads/search_volume/live`** ✅ (Already integrated)
  - Purpose: Get search volume, CPC, competition
  - Use for: Identifying high-value keywords with ranking potential

- **`dataforseo_labs/google/keyword_difficulty/live`** ✅ (Already integrated)
  - Purpose: Keyword difficulty scoring
  - Use for: Finding keywords with ranking potential

- **`serp/google/organic/live/advanced`** ✅ (Already integrated)
  - Purpose: Analyze current SERP rankings
  - Use for: Understanding competition and ranking opportunities

#### Additional Recommendations:
- **`dataforseo_labs/google/keyword_overview/live`** ✅ (Already integrated)
  - Purpose: Comprehensive keyword metrics (intent, monthly searches, SERP features)
  - Use for: Complete SEO analysis

- **`dataforseo_labs/google/keyword_ideas/live`** ✅ (Already integrated)
  - Purpose: Get keyword ideas based on seed keywords
  - Use for: Expanding keyword opportunities

- **`on_page/instant_pages`** ❌ (Not integrated)
  - Purpose: On-page SEO analysis
  - Use for: Understanding what makes top-ranking pages successful

- **`dataforseo_labs/google/ranked_keywords/live`** ❌ (Not integrated)
  - Purpose: See what keywords competitors rank for
  - Use for: Competitive keyword research

---

## 2. Engagement

**Goal**: Increase shares and comments

### Recommended Endpoints:

#### Primary:
- **`dataforseo_labs/google/search_intent/live`** ✅ (Already integrated)
  - Purpose: Identify informational and question-based keywords
  - Use for: Finding topics that drive engagement (questions, discussions)

- **`serp/google/organic/live/advanced`** ✅ (Already integrated)
  - Purpose: Extract People Also Ask, related searches
  - Use for: Finding engaging question-based content

- **`content_analysis/search/live`** ❌ (Not integrated)
  - Purpose: Analyze content sentiment and engagement signals
  - Use for: Understanding what content gets shared/commented

#### Additional Recommendations:
- **`dataforseo_labs/google/related_keywords/live`** ✅ (Already integrated)
  - Purpose: Find related keywords from "searches related to"
  - Use for: Expanding topic coverage for engagement

- **`social_media/pinterest/posts/live`** ❌ (Not integrated)
  - Purpose: See what's trending on Pinterest
  - Use for: Finding shareable content ideas

- **`social_media/reddit/posts/live`** ❌ (Not integrated)
  - Purpose: See trending Reddit discussions
  - Use for: Finding engaging discussion topics

- **`dataforseo_labs/google/keyword_ideas/live`** ✅ (Already integrated)
  - Purpose: Find question-based keywords ("how to", "what is", etc.)
  - Use for: Creating engaging Q&A content

---

## 3. Conversions

**Goal**: Drive sales and sign-ups

### Recommended Endpoints:

#### Primary:
- **`keywords_data/google_ads/search_volume/live`** ✅ (Already integrated)
  - Purpose: Get CPC, competition, search volume
  - Use for: Identifying commercial intent keywords

- **`dataforseo_labs/google/search_intent/live`** ✅ (Already integrated)
  - Purpose: Identify transactional and commercial intent keywords
  - Use for: Finding keywords with purchase intent

- **`serp/google/organic/live/advanced`** ✅ (Already integrated)
  - Purpose: Analyze shopping results, local packs, featured snippets
  - Use for: Understanding conversion-focused SERP features

#### Additional Recommendations:
- **`business_data/google/my_business/live`** ❌ (Not integrated)
  - Purpose: Local business data and reviews
  - Use for: Local conversion optimization

- **`merchant/google/shopping/products/live`** ❌ (Not integrated)
  - Purpose: Google Shopping product data
  - Use for: E-commerce conversion optimization

- **`dataforseo_labs/google/keyword_overview/live`** ✅ (Already integrated)
  - Purpose: Get keyword intent classification
  - Use for: Filtering for commercial/transactional keywords

- **`keywords_data/google_ads/search_volume/live`** ✅ (Already integrated)
  - Purpose: High CPC keywords indicate commercial value
  - Use for: Prioritizing conversion-focused keywords

---

## 4. Brand Awareness

**Goal**: Build brand recognition

### Recommended Endpoints:

#### Primary:
- **`content_analysis/search/live`** ❌ (Not integrated)
  - Purpose: Analyze brand mentions and sentiment
  - Use for: Understanding brand visibility and perception

- **`dataforseo_labs/google/keyword_overview/live`** ✅ (Already integrated)
  - Purpose: Brand-related keyword analysis
  - Use for: Finding brand-building keyword opportunities

- **`serp/google/organic/live/advanced`** ✅ (Already integrated)
  - Purpose: See what brands rank for
  - Use for: Competitive brand analysis

#### Additional Recommendations:
- **`backlinks/backlinks/live`** ❌ (Not integrated)
  - Purpose: Analyze backlink profiles
  - Use for: Understanding brand authority and visibility

- **`dataforseo_labs/google/competitors_domain/live`** ❌ (Not integrated)
  - Purpose: Competitor domain analysis
  - Use for: Brand positioning and competitive analysis

- **`social_media/facebook/posts/live`** ❌ (Not integrated)
  - Purpose: Social media brand mentions
  - Use for: Brand awareness tracking

- **`content_analysis/summary/live`** ❌ (Not integrated)
  - Purpose: Content sentiment and brand perception
  - Use for: Understanding brand sentiment

- **`dataforseo_labs/google/keyword_ideas/live`** ✅ (Already integrated)
  - Purpose: Brand + industry keyword combinations
  - Use for: Branded keyword opportunities

---

## Content Generation Integration

Since you're switching from OpenAI/Anthropic to DataForSEO for content generation:

### Recommended Endpoint:
- **`content_generation/generate_text/live`** ❌ (Not integrated)
  - Purpose: Generate blog articles and content
  - Use for: All content generation needs
  - Pricing: $0.00005 per new token ($50 for 1M tokens)

### Additional Content Features:
- **`content_generation/paraphrase/live`** ❌ (Not integrated)
  - Purpose: Rephrase existing content
  - Use for: Content variation and optimization

- **`content_generation/check_grammar/live`** ❌ (Not integrated)
  - Purpose: Grammar and spelling check
  - Use for: Content quality assurance

- **`content_generation/generate_meta_tags/live`** ❌ (Not integrated)
  - Purpose: Generate meta descriptions and titles
  - Use for: SEO optimization

---

## Implementation Priority

### Phase 1: High Priority (Immediate Value)
1. **Content Generation API** - Core functionality
   - `content_generation/generate_text/live`
   - `content_generation/generate_meta_tags/live`

2. **Content Analysis API** - Engagement & Brand Awareness
   - `content_analysis/search/live`
   - `content_analysis/summary/live`

### Phase 2: Medium Priority (Enhanced Features)
1. **On-Page API** - SEO & Rankings
   - `on_page/instant_pages`

2. **Backlinks API** - Brand Awareness
   - `backlinks/backlinks/live`

3. **Competitor Analysis** - All Categories
   - `dataforseo_labs/google/competitors_domain/live`
   - `dataforseo_labs/google/ranked_keywords/live`

### Phase 3: Nice to Have (Specialized Features)
1. **Social Media APIs** - Engagement
   - `social_media/pinterest/posts/live`
   - `social_media/reddit/posts/live`
   - `social_media/facebook/posts/live`

2. **Business Data APIs** - Conversions
   - `business_data/google/my_business/live`
   - `merchant/google/shopping/products/live`

---

## Endpoint Mapping Summary

| Content Goal | Primary Endpoints | Secondary Endpoints | Content Generation |
|-------------|------------------|-------------------|-------------------|
| **SEO & Rankings** | search_volume, keyword_difficulty, serp_analysis | keyword_overview, keyword_ideas, on_page | generate_text |
| **Engagement** | search_intent, serp_analysis (PAA), content_analysis | related_keywords, social_media | generate_text (Q&A format) |
| **Conversions** | search_volume (CPC), search_intent (commercial), serp_analysis | keyword_overview, business_data | generate_text (conversion-focused) |
| **Brand Awareness** | content_analysis, keyword_overview, serp_analysis | backlinks, competitors_domain, social_media | generate_text (brand-focused) |

---

## Next Steps

1. **Integrate Content Generation API** (Priority 1)
2. **Integrate Content Analysis API** (Priority 1)
3. **Add missing SEO endpoints** (Priority 2)
4. **Create endpoint routing logic** based on content goal
5. **Update frontend integration** to use goal-specific endpoints

