# AI API Endpoints Your Project Connects To

## 🤖 **Yes, your project connects to AI generation systems via API!**

Your Blog Writer SDK is designed to make API calls to multiple AI providers for content generation.

## 🔗 **Supported AI API Endpoints**

### **1. OpenAI API**
- **Base URL**: `https://api.openai.com/v1`
- **Endpoint**: `/chat/completions`
- **Models**: GPT-4o-mini, GPT-4, GPT-3.5-turbo
- **Authentication**: API Key via `Authorization: Bearer {api_key}`
- **Usage**: `await client.chat.completions.create()`

### **2. Anthropic Claude API**
- **Base URL**: `https://api.anthropic.com`
- **Endpoint**: `/v1/messages`
- **Models**: Claude-3.5-Haiku, Claude-3.5-Sonnet
- **Authentication**: API Key via `x-api-key` header
- **Usage**: `await client.messages.create()`

### **3. Azure OpenAI API**
- **Base URL**: `https://{your-resource}.openai.azure.com/openai/deployments/{deployment}/chat/completions`
- **Endpoint**: `/chat/completions`
- **Models**: Same as OpenAI but through Azure
- **Authentication**: API Key via `api-key` header
- **Usage**: `await client.chat.completions.create()`

### **4. DeepSeek API**
- **Base URL**: `https://api.deepseek.com`
- **Endpoint**: `/v1/chat/completions`
- **Models**: DeepSeek Chat
- **Authentication**: API Key via `Authorization: Bearer {api_key}`
- **Usage**: `await client.chat.completions.create()`

## 🔧 **How API Calls Are Made**

### **OpenAI Example:**
```python
response = await self._client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a blog writing assistant"},
        {"role": "user", "content": "Write a blog about AI"}
    ],
    max_tokens=1000,
    temperature=0.7
)
```

### **Anthropic Example:**
```python
response = await self._client.messages.create(
    model="claude-3-5-haiku-20241022",
    max_tokens=1000,
    system="You are a blog writing assistant",
    messages=[
        {"role": "user", "content": "Write a blog about AI"}
    ]
)
```

## 🛡️ **API Security & Configuration**

### **Environment Variables Required:**
```bash
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_ORGANIZATION=org-... (optional)

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Azure OpenAI
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# DeepSeek
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_API_BASE=https://api.deepseek.com
```

## 🔄 **API Fallback System**

Your project implements intelligent fallback:
1. **Primary Provider**: Tries the preferred AI provider first
2. **Fallback**: If primary fails, automatically tries other providers
3. **Error Handling**: Graceful degradation with detailed error messages
4. **Rate Limiting**: Built-in rate limit handling and retry logic

## 📊 **API Usage Tracking**

The system tracks:
- API calls per provider
- Response times
- Token usage
- Cost estimation
- Success/failure rates

## 🚀 **Current Status**

- ✅ **API Integration Code**: Fully implemented
- ✅ **Multi-provider Support**: Ready for all 4 providers
- ✅ **Error Handling**: Comprehensive error management
- ❌ **API Keys**: Not configured (need real API keys)
- ✅ **Fallback System**: Ready to use

## 💡 **To Enable AI API Calls**

1. **Get API Keys** from your preferred AI provider(s)
2. **Set Environment Variables** with real API keys
3. **Deploy** - The system will automatically start making API calls
4. **Monitor** - Track usage and costs through the built-in metrics

Your project is ready to make AI API calls as soon as you provide the API keys!

---

## 🔗 Target-Agnostic Integrations Endpoint (Backlinks/Interlinks)

### Endpoint
- `POST /api/v1/integrations/connect-and-recommend`

### Purpose
- Compute recommended backlinks and interlinks based on selected keywords.
- Accepts any frontend integration (Webflow, WordPress, Medium, Shopify, custom, etc.) without backend code changes.
- Best‑effort persistence to Supabase:
  - `integrations_{ENV}` for integration metadata
  - `recommendations_{ENV}` for computed recommendations

### Request (summary)
```json
{
  "provider": "custom",
  "tenant_id": "example-tenant",
  "connection": { "any": "opaque-config" },
  "keywords": ["example keyword", "another term"]
}
```

### Response (summary)
```json
{
  "provider": "custom",
  "tenant_id": "example-tenant",
  "saved_integration": true,
  "recommended_backlinks": 4,
  "recommended_interlinks": 6,
  "per_keyword": [
    { "keyword": "example keyword", "difficulty": 0.5, "suggested_backlinks": 3, "suggested_interlinks": 5 },
    { "keyword": "another term", "difficulty": 0.4, "suggested_backlinks": 3, "suggested_interlinks": 5 }
  ],
  "notes": null
}
```

### Supabase Schema
- See `supabase_schema.sql` for `integrations_{env}` and `recommendations_{env}` tables.

### Version
- Added in API version `1.1.0`.

---

## 🚀 Enhanced Blog Generation Endpoint

### Endpoint
- `POST /api/v1/blog/generate-enhanced`

### Purpose
- Generate high-quality blog content using a sophisticated 4-stage pipeline with advanced optimizations
- Implements all recommendations from `BLOG_QUALITY_IMPROVEMENTS.md`
- Produces significantly higher-quality, ranking-optimized content

### Features
- **4-Stage Pipeline**: Research → Draft → Enhancement → SEO Polish
- **Intent-Based Generation**: Automatically detects and optimizes for search intent
- **Few-Shot Learning**: Learns from top-ranking content examples
- **Content Length Optimization**: Dynamically adjusts based on SERP competition
- **Multi-Model Consensus** (optional): Combines GPT-4o and Claude for higher quality
- **Google Knowledge Graph**: Entity recognition and structured data
- **Semantic Keywords**: Natural integration of related keywords
- **Quality Scoring**: 6-dimensional quality assessment
- **Content Freshness**: Current dates and "last updated" signals

### Request
```json
{
  "topic": "AI Content Generation",
  "keywords": ["ai content", "blog writing"],
  "tone": "professional",
  "length": "medium",
  "use_google_search": true,
  "use_citations": true,
  "use_consensus_generation": false,
  "use_knowledge_graph": true,
  "use_semantic_keywords": true,
  "use_quality_scoring": true
}
```

### Response
```json
{
  "title": "Generated Blog Title",
  "content": "Full blog content...",
  "meta_title": "SEO-optimized meta title",
  "meta_description": "SEO-optimized meta description",
  "readability_score": 72.5,
  "seo_score": 85.0,
  "quality_score": 88.5,
  "quality_dimensions": {
    "readability": 75.0,
    "seo": 90.0,
    "structure": 85.0,
    "factual": 95.0,
    "uniqueness": 90.0,
    "engagement": 85.0
  },
  "structured_data": {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    ...
  },
  "semantic_keywords": ["related keyword 1", "related keyword 2"],
  "stage_results": [
    {"stage": "research_outline", "provider": "anthropic", "tokens": 500, "cost": 0.002},
    {"stage": "draft", "provider": "openai", "tokens": 2000, "cost": 0.010},
    {"stage": "enhancement", "provider": "anthropic", "tokens": 1500, "cost": 0.006},
    {"stage": "seo_polish", "provider": "openai", "tokens": 800, "cost": 0.001}
  ],
  "citations": [
    {"text": "...", "url": "https://source.com", "title": "Source Title"}
  ],
  "total_tokens": 4800,
  "total_cost": 0.019,
  "generation_time": 12.5,
  "seo_metadata": {
    "search_intent": {
      "primary_intent": "informational",
      "confidence": 0.92
    }
  },
  "success": true,
  "warnings": []
}
```

### Configuration
- **Required**: `GOOGLE_CUSTOM_SEARCH_API_KEY`, `GOOGLE_CUSTOM_SEARCH_ENGINE_ID`
- **Recommended**: `DATAFORSEO_API_KEY`, `DATAFORSEO_API_SECRET`
- **Optional**: `GOOGLE_KNOWLEDGE_GRAPH_API_KEY`

### Cost
- **Standard**: ~$0.015-$0.030 per article (10-15 seconds)
- **With Consensus**: ~$0.040-$0.080 per article (15-20 seconds)

### Version
- Added in API version `1.2.0`.
- See [Enhanced Blog Generation Guide](ENHANCED_BLOG_GENERATION_GUIDE.md) for detailed documentation.

---

## 🔍 Enhanced Keyword Analysis Endpoint

### Endpoint
- `POST /api/v1/keywords/enhanced`

### Purpose
- Returns richer keyword metrics (when DataForSEO is configured): search volume, difficulty, CPC, intent signals, trend proxy, related and long-tail suggestions, with graceful fallback.

### Request (summary)
```json
{
  "keywords": ["ai in business","cloud run seo"],
  "location": "United States",
  "language": "en"
}
```

### Response (summary)
```json
{
  "enhanced_analysis": {
    "ai in business": {
      "search_volume": 1200,
      "difficulty": "medium",
      "competition": 0.45,
      "cpc": 2.1,
      "trend_score": 0.3,
      "recommended": true,
      "reason": "High search volume with manageable difficulty",
      "related_keywords": ["best ai in business", "..."],
      "long_tail_keywords": ["how to use ai in business", "..."]
    }
  }
}
```

### Credentials
- Set `DATAFORSEO_API_KEY` and `DATAFORSEO_API_SECRET` in your environment (legacy `LOGIN/PASSWORD` also supported as fallback).

### Version
- Added in API version `1.1.0`.
