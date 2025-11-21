# AI Enhancement Plan: Search Customization & LLM Integration

**Date**: 2025-11-19  
**Status**: 📋 Planning Phase

---

## 🎯 Objectives

1. **Ensure all variables available** for customizing search queries based on search type
2. **Add new endpoint** for DataForSEO LLM Responses API
3. **Integrate AI search results** into current keyword analysis endpoint

---

## 📊 Current State Analysis

### Current Request Model (`EnhancedKeywordAnalysisRequest`)

```python
class EnhancedKeywordAnalysisRequest(BaseModel):
    keywords: List[str]                    # ✅ Available
    location: Optional[str]                 # ✅ Available
    language: Optional[str]                 # ✅ Available
    search_type: Optional[str]             # ✅ Available (but not fully utilized)
    include_serp: bool                      # ✅ Available
    max_suggestions_per_keyword: int       # ✅ Available
```

### Missing Variables for Customization

**SERP Analysis Customization:**
- ❌ `serp_depth` - Number of results to analyze (currently hardcoded to 20)
- ❌ `serp_prompt` - Custom prompt for SERP AI summary
- ❌ `include_serp_features` - Control which SERP features to analyze
- ❌ `serp_analysis_type` - Type of SERP analysis (basic, ai_summary, both)

**Related Keywords Customization:**
- ❌ `related_keywords_depth` - Graph traversal depth (currently hardcoded to 1-2)
- ❌ `related_keywords_limit` - Max related keywords (currently hardcoded to 20)

**Keyword Ideas Customization:**
- ❌ `keyword_ideas_limit` - Max ideas per keyword (currently hardcoded to 50)
- ❌ `keyword_ideas_type` - Filter by type (questions, topics, all)

**AI Search Volume Customization:**
- ❌ `include_ai_volume` - Toggle AI search volume (currently always included)
- ❌ `ai_volume_timeframe` - Historical timeframe (currently 12 months)

**LLM Responses (Not Available):**
- ❌ `include_llm_responses` - Toggle LLM research queries
- ❌ `llm_prompts` - Custom prompts for LLM queries
- ❌ `llm_models` - Which LLMs to query (chatgpt, claude, gemini, perplexity)
- ❌ `llm_max_tokens` - Response length limit

---

## 🚀 Implementation Plan

### Phase 1: Enhance Request Model with All Customization Variables

#### 1.1 Update `EnhancedKeywordAnalysisRequest`

**Add SERP Customization:**
```python
# SERP Analysis Options
serp_depth: Optional[int] = Field(default=20, ge=5, le=100, description="Number of SERP results to analyze")
serp_prompt: Optional[str] = Field(default=None, description="Custom prompt for SERP AI summary analysis")
include_serp_features: Optional[List[str]] = Field(
    default=["featured_snippet", "people_also_ask", "videos", "images"],
    description="SERP features to analyze"
)
serp_analysis_type: Optional[str] = Field(
    default="both",
    enum=["basic", "ai_summary", "both"],
    description="Type of SERP analysis to perform"
)
```

**Add Related Keywords Customization:**
```python
# Related Keywords Options
related_keywords_depth: Optional[int] = Field(default=1, ge=1, le=4, description="Graph traversal depth for related keywords")
related_keywords_limit: Optional[int] = Field(default=20, ge=5, le=100, description="Maximum related keywords per seed keyword")
```

**Add Keyword Ideas Customization:**
```python
# Keyword Ideas Options
keyword_ideas_limit: Optional[int] = Field(default=50, ge=10, le=200, description="Maximum keyword ideas per seed keyword")
keyword_ideas_type: Optional[str] = Field(
    default="all",
    enum=["all", "questions", "topics"],
    description="Filter keyword ideas by type"
)
```

**Add AI Search Volume Customization:**
```python
# AI Search Volume Options
include_ai_volume: Optional[bool] = Field(default=True, description="Include AI search volume metrics")
ai_volume_timeframe: Optional[int] = Field(default=12, ge=1, le=24, description="Historical timeframe in months for AI volume")
```

**Add LLM Responses Options:**
```python
# LLM Responses Options (NEW)
include_llm_responses: Optional[bool] = Field(default=False, description="Include LLM research responses for keywords")
llm_prompts: Optional[List[str]] = Field(
    default=None,
    description="Custom prompts for LLM queries (one per keyword or shared)"
)
llm_models: Optional[List[str]] = Field(
    default=["chatgpt", "claude", "gemini"],
    enum=["chatgpt", "claude", "gemini", "perplexity"],
    description="Which LLMs to query"
)
llm_max_tokens: Optional[int] = Field(default=500, ge=100, le=2000, description="Maximum tokens per LLM response")
```

#### 1.2 Search Type-Based Defaults

**Implement search type presets:**

```python
def _apply_search_type_defaults(request: EnhancedKeywordAnalysisRequest) -> EnhancedKeywordAnalysisRequest:
    """
    Apply default configurations based on search_type.
    """
    search_type_presets = {
        "competitor_analysis": {
            "include_serp": True,
            "serp_depth": 30,
            "serp_analysis_type": "both",
            "include_llm_responses": True,
            "llm_prompts": [
                "What are the main topics covered in top-ranking content?",
                "What content gaps exist in current top results?"
            ]
        },
        "content_research": {
            "include_llm_responses": True,
            "llm_models": ["chatgpt", "claude", "gemini"],
            "keyword_ideas_limit": 100,
            "related_keywords_depth": 2
        },
        "quick_analysis": {
            "max_suggestions_per_keyword": 10,
            "include_serp": False,
            "include_ai_volume": False,
            "include_llm_responses": False
        },
        "comprehensive_analysis": {
            "max_suggestions_per_keyword": 150,
            "include_serp": True,
            "serp_depth": 50,
            "include_llm_responses": True,
            "related_keywords_depth": 3,
            "keyword_ideas_limit": 200
        }
    }
    
    if request.search_type in search_type_presets:
        preset = search_type_presets[request.search_type]
        for key, value in preset.items():
            if getattr(request, key, None) is None:
                setattr(request, key, value)
    
    return request
```

---

### Phase 2: Create New LLM Responses Endpoint

#### 2.1 New Endpoint: `/api/v1/keywords/llm-research`

**Purpose:** Dedicated endpoint for LLM-powered keyword research

**Request Model:**
```python
class LLMResearchRequest(BaseModel):
    keywords: List[str] = Field(..., max_length=10, description="Keywords to research (max 10 for cost control)")
    prompts: Optional[List[str]] = Field(
        default=None,
        description="Custom prompts (one per keyword or shared prompt for all)"
    )
    llm_models: Optional[List[str]] = Field(
        default=["chatgpt", "claude", "gemini"],
        description="Which LLMs to query"
    )
    max_tokens: Optional[int] = Field(default=500, ge=100, le=2000)
    location: Optional[str] = Field("United States")
    language: Optional[str] = Field("en")
    include_consensus: Optional[bool] = Field(default=True, description="Calculate consensus across LLMs")
    include_sources: Optional[bool] = Field(default=True, description="Extract citation sources")
```

**Response Structure:**
```json
{
  "llm_research": {
    "pet grooming": {
      "prompts_used": [
        "What are the key topics people ask about pet grooming?",
        "What are common misconceptions about pet grooming?"
      ],
      "responses": {
        "chatgpt": {
          "text": "...",
          "tokens": 450,
          "model": "gpt-4",
          "timestamp": "2025-11-19T10:00:00Z"
        },
        "claude": {...},
        "gemini": {...}
      },
      "consensus": [
        "Regular grooming is essential for pet health",
        "Professional grooming recommended every 4-6 weeks"
      ],
      "differences": [
        "ChatGPT emphasizes cost, Claude emphasizes health benefits"
      ],
      "sources": [
        {"url": "...", "title": "..."},
        ...
      ],
      "confidence": {
        "chatgpt": 0.85,
        "claude": 0.90,
        "gemini": 0.82
      }
    }
  },
  "summary": {
    "total_keywords": 1,
    "total_responses": 3,
    "average_confidence": 0.86,
    "consensus_rate": 0.75
  }
}
```

**Implementation:**
- Use existing `DataForSEOClient.get_llm_responses()` method
- Support multiple prompts per keyword
- Calculate consensus and differences
- Extract sources/citations
- Return structured response

---

### Phase 3: Integrate AI Search Results into Current Endpoint

#### 3.1 Add LLM Responses to `/api/v1/keywords/enhanced`

**Integration Points:**

1. **Stage 6.5: LLM Research (Optional)** - After AI Optimization Data
   - Only if `include_llm_responses: true`
   - Generate prompts based on keywords
   - Query multiple LLMs
   - Extract insights

2. **Response Enhancement:**
   - Add `llm_research` field to each keyword analysis
   - Include consensus points
   - Include citation sources
   - Include confidence scores

**Prompt Generation Strategy:**

```python
def _generate_llm_prompts(keyword: str, search_type: str) -> List[str]:
    """
    Generate LLM research prompts based on keyword and search type.
    """
    base_prompts = {
        "competitor_analysis": [
            f"What are the main topics covered in top-ranking content about '{keyword}'?",
            f"What content gaps exist in current top results for '{keyword}'?",
            f"What questions do people ask about '{keyword}'?"
        ],
        "content_research": [
            f"What are the key points to cover when writing about '{keyword}'?",
            f"What are common misconceptions about '{keyword}'?",
            f"What are the latest developments related to '{keyword}'?"
        ],
        "enhanced_keyword_analysis": [
            f"What are the most important aspects of '{keyword}'?",
            f"What related topics should be covered alongside '{keyword}'?"
        ]
    }
    
    return base_prompts.get(search_type, base_prompts["enhanced_keyword_analysis"])
```

**Response Structure Addition:**

```json
{
  "enhanced_analysis": {
    "pet grooming": {
      // ... existing fields ...
      "llm_research": {  // NEW FIELD
        "enabled": true,
        "prompts_used": [...],
        "responses": {
          "chatgpt": {...},
          "claude": {...},
          "gemini": {...}
        },
        "consensus": [...],
        "key_insights": [...],
        "sources": [...],
        "confidence": {...}
      }
    }
  }
}
```

#### 3.2 Progress Tracking for LLM Research

**Add new stage:**
- Stage 6.5: "LLM Research" (87%) - Between AI Optimization and Related Keywords
- Progress updates per LLM query
- Show which models are being queried

---

## 📋 Detailed Implementation Steps

### Step 1: Update Request Model (Priority: High)

**File**: `main.py`

**Changes:**
1. Add all customization fields to `EnhancedKeywordAnalysisRequest`
2. Add `LLMResearchRequest` model
3. Implement `_apply_search_type_defaults()` function
4. Update request validation

**Estimated Time**: 2-3 hours

---

### Step 2: Update Analysis Function (Priority: High)

**File**: `main.py` - `_analyze_keywords_with_progress()`

**Changes:**
1. Apply search type defaults at start
2. Use customizable parameters throughout:
   - `serp_depth` instead of hardcoded 20
   - `related_keywords_depth` instead of hardcoded 1
   - `related_keywords_limit` instead of hardcoded 20
   - `keyword_ideas_limit` instead of hardcoded 50
3. Add conditional LLM research stage
4. Generate prompts based on search type
5. Integrate LLM responses into keyword analysis

**Estimated Time**: 4-6 hours

---

### Step 3: Create LLM Research Endpoint (Priority: Medium)

**File**: `main.py`

**Changes:**
1. Create `POST /api/v1/keywords/llm-research` endpoint
2. Implement request handling
3. Call `DataForSEOClient.get_llm_responses()`
4. Process and format responses
5. Calculate consensus and differences
6. Extract sources

**Estimated Time**: 3-4 hours

---

### Step 4: Update Streaming Endpoint (Priority: Medium)

**File**: `main.py` - `analyze_keywords_enhanced_stream()`

**Changes:**
1. Add progress update for LLM research stage
2. Stream LLM responses as they arrive
3. Update final result to include LLM data

**Estimated Time**: 2-3 hours

---

### Step 5: Update Documentation (Priority: Low)

**Files**: 
- `FRONTEND_KEYWORD_ENDPOINT_UPDATE.md`
- `MAX_SEARCH_PARAMETERS.json`
- `SSE_STREAMING_IMPLEMENTATION.md`

**Changes:**
1. Document new request parameters
2. Document LLM research endpoint
3. Update examples
4. Add search type presets documentation

**Estimated Time**: 2-3 hours

---

## 🎯 Search Type Presets

### 1. `competitor_analysis`
**Use Case**: Analyze competitor content and identify gaps

**Defaults:**
- `include_serp: true`
- `serp_depth: 30`
- `serp_analysis_type: "both"`
- `include_llm_responses: true`
- `llm_prompts`: ["What topics do top results cover?", "What's missing?"]
- `related_keywords_depth: 2`

### 2. `content_research`
**Use Case**: Deep research for comprehensive content

**Defaults:**
- `include_llm_responses: true`
- `llm_models: ["chatgpt", "claude", "gemini"]`
- `keyword_ideas_limit: 100`
- `related_keywords_depth: 2`
- `max_suggestions_per_keyword: 100`

### 3. `quick_analysis`
**Use Case**: Fast keyword metrics without deep analysis

**Defaults:**
- `max_suggestions_per_keyword: 10`
- `include_serp: false`
- `include_ai_volume: false`
- `include_llm_responses: false`
- `related_keywords_limit: 10`

### 4. `comprehensive_analysis`
**Use Case**: Full analysis with all features

**Defaults:**
- `max_suggestions_per_keyword: 150`
- `include_serp: true`
- `serp_depth: 50`
- `include_llm_responses: true`
- `related_keywords_depth: 3`
- `keyword_ideas_limit: 200`

### 5. `enhanced_keyword_analysis` (default)
**Use Case**: Balanced analysis with good coverage

**Defaults:**
- Current behavior (no changes)
- All features enabled with moderate limits

---

## 💰 Cost Considerations

### LLM Responses API Costs

**Per Request:**
- ChatGPT: ~$0.02-0.03 per query
- Claude: ~$0.02-0.03 per query
- Gemini: ~$0.01-0.02 per query
- Perplexity: ~$0.02-0.03 per query

**Per Keyword Analysis (3 LLMs, 2 prompts):**
- ~$0.12-0.18 per keyword
- For 3 keywords: ~$0.36-0.54 per request

**Monthly Estimate (1000 requests, 3 keywords avg):**
- ~$360-540/month additional cost

**Cost Optimization:**
- Make LLM research optional (`include_llm_responses: false` by default)
- Limit to primary keyword only (not all suggestions)
- Cache LLM responses (already implemented)
- Use fewer LLMs for quick analysis

---

## 🔄 Integration Flow

### Current Flow:
```
1. Initialization
2. Primary Keyword Analysis
3. Getting Suggestions
4. Analyzing Suggestions
5. Clustering
6. AI Optimization Data
7. Related Keywords
8. Keyword Ideas
9. SERP Analysis
10. Finalization
```

### Enhanced Flow with LLM:
```
1. Initialization
2. Primary Keyword Analysis
3. Getting Suggestions
4. Analyzing Suggestions
5. Clustering
6. AI Optimization Data
6.5. LLM Research (NEW - Optional) ← Insert here
7. Related Keywords
8. Keyword Ideas
9. SERP Analysis
10. Finalization
```

---

## 📊 Response Structure Changes

### Enhanced Keyword Analysis Response

**New Fields Added:**

```json
{
  "enhanced_analysis": {
    "keyword": {
      // Existing fields...
      
      // NEW: LLM Research (if include_llm_responses: true)
      "llm_research": {
        "enabled": true,
        "prompts_used": [
          "What are the key topics about 'keyword'?",
          "What questions do people ask?"
        ],
        "responses": {
          "chatgpt": {
            "text": "Full response text...",
            "tokens": 450,
            "model": "gpt-4",
            "timestamp": "2025-11-19T10:00:00Z"
          },
          "claude": {...},
          "gemini": {...}
        },
        "consensus": [
          "Point 1 agreed by all models",
          "Point 2 agreed by all models"
        ],
        "differences": [
          "ChatGPT emphasizes X, Claude emphasizes Y"
        ],
        "key_insights": [
          "Insight 1",
          "Insight 2"
        ],
        "sources": [
          {"url": "...", "title": "..."}
        ],
        "confidence": {
          "chatgpt": 0.85,
          "claude": 0.90,
          "gemini": 0.82,
          "average": 0.86
        }
      }
    }
  },
  
  // NEW: LLM Research Summary (if enabled)
  "llm_research_summary": {
    "total_keywords_researched": 3,
    "total_llm_queries": 9,
    "average_confidence": 0.86,
    "consensus_rate": 0.75,
    "sources_found": 15
  }
}
```

---

## ✅ Benefits

### For Blog Writers:
1. **Better Content Research** - Multi-model insights from LLMs
2. **Fact Verification** - Consensus across multiple AI models
3. **Content Gaps** - Identify what competitors miss
4. **Citation Sources** - Automatic source extraction
5. **Customizable Analysis** - Tailor to specific needs

### For Developers:
1. **Flexible Configuration** - All parameters customizable
2. **Search Type Presets** - Quick setup for common use cases
3. **Cost Control** - Optional LLM research (off by default)
4. **Backward Compatible** - Existing requests still work

---

## 🚨 Considerations

### Performance:
- LLM queries add ~2-5 seconds per keyword
- Use async/parallel queries to minimize impact
- Cache responses aggressively

### Cost:
- LLM research is expensive (~$0.12-0.18 per keyword)
- Make it optional and off by default
- Limit to primary keywords only

### Rate Limits:
- DataForSEO may have rate limits on LLM endpoints
- Implement retry logic with exponential backoff
- Monitor usage and costs

---

## 📝 Summary

### What Will Be Added:

1. **Enhanced Request Model** ✅
   - All customization variables
   - Search type presets
   - LLM research options

2. **New LLM Research Endpoint** ✅
   - `/api/v1/keywords/llm-research`
   - Dedicated endpoint for LLM queries
   - Multi-model responses

3. **Integrated LLM Research** ✅
   - Optional stage in enhanced endpoint
   - Progress tracking
   - Results included in response

### Implementation Order:

1. **Phase 1**: Update request model with all variables (2-3 hours)
2. **Phase 2**: Create LLM research endpoint (3-4 hours)
3. **Phase 3**: Integrate into enhanced endpoint (4-6 hours)
4. **Phase 4**: Update streaming endpoint (2-3 hours)
5. **Phase 5**: Documentation (2-3 hours)

**Total Estimated Time**: 13-19 hours

---

## 🎯 Next Steps

1. **Review and approve plan**
2. **Prioritize features** (which search types are most important?)
3. **Set cost limits** (max LLM queries per request?)
4. **Begin implementation** (start with Phase 1)

---

**This plan ensures full customization while adding powerful AI research capabilities!** 🚀

