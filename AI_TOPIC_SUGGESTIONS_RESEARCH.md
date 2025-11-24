# AI Topic Suggestions Research: DataForSEO AI Optimization API

## 🎯 Critical Finding: LLM Mentions API

Based on [DataForSEO AI Optimization API documentation](https://docs.dataforseo.com/v3/ai_optimization/overview/), there is a **critical missing component** for AI topic suggestions: **LLM Mentions API**.

---

## 📊 Current Implementation Status

### ✅ What's Already Implemented:

1. **AI Search Volume** (`keywords_data/ai_optimization/search_volume/live`)
   - ✅ Implemented: `get_ai_search_volume()`
   - **What it does:** Shows search volume for keywords in AI queries
   - **Limitation:** Only shows volume, not WHAT topics AI agents are actually citing

2. **LLM Responses API** (`ai_optimization/llm_responses/live`)
   - ✅ Implemented: `get_llm_responses()`
   - **What it does:** Gets responses from ChatGPT, Claude, Gemini, Perplexity
   - **Use case:** Multi-model fact-checking, content research
   - **Limitation:** Requires you to provide prompts - doesn't discover trending topics

3. **SERP AI Summary** (`serp/ai_summary/live`)
   - ✅ Implemented: `get_serp_ai_summary()`
   - **What it does:** AI-generated summary of SERP results
   - **Use case:** Content structure optimization
   - **Limitation:** Focuses on traditional search, not AI agent citations

---

## 🚨 Critical Missing Component: LLM Mentions API

### What It Does:

The **LLM Mentions API** tracks what topics, keywords, and URLs are being **cited by AI agents** (ChatGPT, Claude, Gemini, Perplexity) in their responses. This is the key to creating content that gets discovered and cited by AI agents.

### Available Endpoints:

According to DataForSEO documentation, the LLM Mentions API includes:

1. **`ai_optimization/llm_mentions/search`** ⭐⭐⭐
   - **Purpose:** Search for specific keywords/domains mentioned by LLMs
   - **Returns:** Aggregated metrics grouped by most frequently mentioned pages
   - **Use case:** Find what topics AI agents are citing for your keywords
   - **Critical for:** Discovering AI-optimized topic opportunities

2. **`ai_optimization/llm_mentions/top_pages`** ⭐⭐⭐
   - **Purpose:** Get top pages mentioned by LLMs for a target
   - **Returns:** Pages ranked by LLM mention frequency
   - **Use case:** See what content AI agents are citing most
   - **Critical for:** Understanding what content structure works for AI citations

3. **`ai_optimization/llm_mentions/top_domains`** ⭐⭐
   - **Purpose:** Get top domains mentioned by LLMs
   - **Returns:** Domains ranked by LLM mention frequency
   - **Use case:** Identify authoritative sources AI agents cite
   - **Critical for:** Competitive analysis in AI search space

4. **`ai_optimization/llm_mentions/aggregated_metrics`** ⭐⭐
   - **Purpose:** Get aggregated metrics for LLM mentions
   - **Returns:** Summary statistics on LLM citations
   - **Use case:** Track overall AI citation performance

---

## 💡 Why LLM Mentions API is Critical

### The Problem:

**Traditional SEO** focuses on ranking in Google search results.  
**AI-Optimized SEO** focuses on getting **cited by AI agents** (ChatGPT, Claude, Gemini, Perplexity).

### The Solution:

LLM Mentions API shows:
- **What topics** AI agents are searching for
- **What content** AI agents are citing
- **What keywords** trigger AI citations
- **What domains** AI agents trust most

### Real-World Impact:

1. **Content Discovery:** If your content gets cited by ChatGPT, users discover it through AI conversations
2. **Topic Opportunities:** Find topics that AI agents frequently discuss but have limited citations
3. **Content Structure:** Understand what content format AI agents prefer to cite
4. **Competitive Analysis:** See what competitors are getting cited by AI agents

---

## 🎯 Use Cases for AI Topic Suggestions

### 1. Topic Discovery for AI Agents

**Current Approach (Limited):**
- Use `get_ai_search_volume()` to find keywords with AI search volume
- Problem: Only shows volume, not what topics AI agents are actually citing

**With LLM Mentions API:**
```python
# Find topics AI agents are citing
llm_mentions = await df_client.get_llm_mentions_search(
    keyword="pet grooming",
    location="United States",
    language="en"
)

# Returns:
# - Top pages cited by AI agents for "pet grooming"
# - Topics frequently mentioned in AI responses
# - Content gaps (topics AI agents discuss but few citations exist)
```

### 2. Content Gap Analysis

**What AI agents discuss** vs **What content exists** = **Content opportunities**

```python
# Find content gaps
# 1. Get topics AI agents frequently mention
ai_topics = await get_llm_mentions_topics("pet grooming")

# 2. Check what content exists for those topics
existing_content = await check_content_exists(ai_topics)

# 3. Identify gaps
content_gaps = ai_topics - existing_content

# Result: Topics AI agents cite but have limited content = Opportunity
```

### 3. AI Citation Optimization

**Optimize content to get cited by AI agents:**

```python
# 1. Find top-cited pages for your topic
top_cited = await get_llm_mentions_top_pages("pet grooming")

# 2. Analyze what makes them get cited
citation_patterns = analyze_citation_patterns(top_cited)

# 3. Apply patterns to your content
optimize_content_for_ai_citations(citation_patterns)
```

---

## 📋 Integration Strategy

### Phase 1: LLM Mentions Search (Priority 1) ⭐⭐⭐

**Endpoint:** `ai_optimization/llm_mentions/search`

**Purpose:** Find what topics/keywords AI agents are citing

**Implementation:**
- Add `get_llm_mentions_search()` method to `DataForSEOClient`
- Create endpoint: `POST /api/v1/keywords/ai-mentions`
- Use in goal-based routing for all 4 content goals
- Especially critical for **Brand Awareness** goal

**Benefits:**
- Discover AI-optimized topics
- Find content gaps
- Identify citation opportunities

### Phase 2: Top Pages Analysis (Priority 2) ⭐⭐

**Endpoint:** `ai_optimization/llm_mentions/top_pages`

**Purpose:** See what content AI agents cite most

**Implementation:**
- Add `get_llm_mentions_top_pages()` method
- Use for content structure analysis
- Identify citation patterns

**Benefits:**
- Understand what content format AI agents prefer
- Competitive analysis
- Content optimization insights

### Phase 3: Top Domains Analysis (Priority 3) ⭐

**Endpoint:** `ai_optimization/llm_mentions/top_domains`

**Purpose:** Identify authoritative domains in AI search

**Benefits:**
- Competitive domain analysis
- Authority building insights

---

## 🔄 Integration with Goal-Based Routing

### How LLM Mentions Fits Each Goal:

1. **SEO & Rankings**
   - Use LLM Mentions to find topics with high AI citation potential
   - Optimize for both traditional search AND AI citations

2. **Engagement**
   - Find topics AI agents frequently discuss
   - Create content that answers AI agent queries

3. **Conversions**
   - Identify commercial topics AI agents cite
   - Optimize product/service content for AI citations

4. **Brand Awareness** ⭐⭐⭐ **MOST CRITICAL**
   - Track brand mentions in AI agent responses
   - Find topics where brand can get cited
   - Monitor brand visibility in AI search

---

## 📊 Data Structure Expected

Based on DataForSEO documentation, LLM Mentions API returns:

```json
{
  "tasks": [{
    "result": [{
      "target": "pet grooming",
      "ai_search_volume": 15000,
      "mentions_count": 250,
      "top_pages": [
        {
          "url": "https://example.com/pet-grooming-guide",
          "mentions": 45,
          "ai_search_volume": 3200,
          "platforms": ["chatgpt", "claude"]
        }
      ],
      "top_domains": [
        {
          "domain": "example.com",
          "mentions": 120,
          "ai_search_volume": 8500
        }
      ],
      "topics": [
        {
          "topic": "dog grooming tips",
          "mentions": 35,
          "ai_search_volume": 2100
        }
      ]
    }]
  }]
}
```

---

## 💰 Cost Considerations

**LLM Mentions API Pricing:**
- Estimated cost: Similar to other AI Optimization endpoints
- Check DataForSEO pricing page for exact costs
- Likely: ~$0.05-0.10 per request

**ROI:**
- High ROI if content gets cited by AI agents
- AI citations = New discovery channel
- Long-term value: Content stays discoverable through AI

---

## 🎯 Recommendations

### Immediate Action:

1. **Integrate LLM Mentions Search API** (Priority 1)
   - Most critical for AI topic suggestions
   - Enables discovery of AI-cited topics
   - Essential for Brand Awareness goal

2. **Add to Goal-Based Routing**
   - Include LLM Mentions data in all 4 content goals
   - Especially valuable for Brand Awareness

3. **Create AI Topic Suggestions Endpoint**
   - New endpoint: `POST /api/v1/keywords/ai-topic-suggestions`
   - Combines: AI Search Volume + LLM Mentions + LLM Responses
   - Returns: Topics optimized for AI agent discovery

### Long-Term Strategy:

1. **Monitor AI Citations**
   - Track which content gets cited by AI agents
   - Measure AI citation performance
   - Optimize content based on citation patterns

2. **Content Gap Analysis**
   - Compare AI agent discussions vs existing content
   - Identify high-opportunity topics
   - Prioritize content creation based on AI citation potential

---

## 📚 References

- [DataForSEO AI Optimization API Overview](https://docs.dataforseo.com/v3/ai_optimization/overview/)
- [LLM Mentions API Documentation](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/)
- [AI Keyword Data API](https://docs.dataforseo.com/v3/ai_optimization/ai_keyword_data/)

---

## ✅ Summary

**Current Status:**
- ✅ AI Search Volume: Implemented
- ✅ LLM Responses: Implemented  
- ✅ SERP AI Summary: Implemented
- ❌ **LLM Mentions API: NOT IMPLEMENTED** ⚠️ **CRITICAL GAP**

**Critical Need:**
LLM Mentions API is **essential** for:
- Discovering topics AI agents are citing
- Creating content optimized for AI agent discovery
- Tracking brand mentions in AI responses
- Finding content gaps in AI search space

**Recommendation:**
**Integrate LLM Mentions Search API immediately** - This is the missing piece for true AI-optimized content strategy.

