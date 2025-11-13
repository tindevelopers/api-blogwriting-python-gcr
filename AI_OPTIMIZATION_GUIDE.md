# AI Optimization Integration Guide

## Overview

AI optimization is now integrated into the Blog Writer SDK API, providing critical data on how keywords appear in AI LLM queries/responses (ChatGPT, Claude, Gemini, etc.). This is essential for creating content that gets cited by AI systems.

## What Was Implemented

### 1. DataForSEO AI Optimization Integration

**New Method**: `DataForSEOClient.get_ai_search_volume()`
- Fetches AI search volume data from DataForSEO API
- Endpoint: `keywords_data/ai_optimization/search_volume/live`
- Returns:
  - `ai_search_volume`: Current month's estimated volume in AI queries
  - `ai_monthly_searches`: Historical trend over past 12 months
  - `ai_trend`: Trend score (-1.0 to 1.0) indicating growth/decline

### 2. Enhanced Endpoint Updates

**Endpoint**: `POST /api/v1/keywords/enhanced`

**New Fields Added**:
```json
{
  "enhanced_analysis": {
    "keyword": {
      "search_volume": 110000,           // Traditional search volume
      "cpc": 16.04,
      "difficulty": "hard",
      "competition": 0.6,
      "ai_search_volume": 47955,         // NEW: AI search volume
      "ai_trend": 0.15,                   // NEW: AI trend score
      "ai_monthly_searches": [...]       // NEW: Monthly AI search history
    }
  }
}
```

### 3. New Dedicated AI Optimization Endpoint

**Endpoint**: `POST /api/v1/keywords/ai-optimization`

**Purpose**: Focused analysis specifically for AI optimization strategy

**Request**:
```json
{
  "keywords": ["digital marketing", "machine learning"],
  "location": "United States",
  "language": "en"
}
```

**Response**:
```json
{
  "ai_optimization_analysis": {
    "digital marketing": {
      "ai_search_volume": 47955,
      "traditional_search_volume": 110000,
      "ai_trend": 0.15,
      "ai_monthly_searches": [
        {
          "year": 2024,
          "month": 1,
          "search_volume": 45000
        },
        // ... 12 months of data
      ],
      "ai_optimization_score": 72,
      "ai_recommended": true,
      "ai_reason": "Excellent AI visibility - high volume and positive trend",
      "comparison": {
        "ai_to_traditional_ratio": 0.436,
        "ai_growth_trend": "increasing"
      }
    }
  },
  "summary": {
    "keywords_with_ai_volume": 2,
    "average_ai_score": 68,
    "recommended_keywords": ["digital marketing", "machine learning"]
  }
}
```

## AI Optimization Score Calculation

The AI optimization score (0-100) is calculated based on:

1. **Base Score (0-50)**: Logarithmic scale of AI search volume
   - Higher volume = higher base score
   - Formula: `min(50, log10(ai_search_volume + 1) * 10)`

2. **Trend Bonus (0-25)**: Positive trend adds to score
   - Growing AI volume = bonus points
   - Formula: `min(25, ai_trend * 25)`

3. **Growth Bonus (0-25)**: Recent growth vs older periods
   - Compares last 3 months vs first 3 months
   - Formula: `min(25, growth_percentage * 25)`

**Score Interpretation**:
- **70-100**: Excellent AI visibility - high volume and positive trend
- **50-69**: Good AI visibility - moderate volume with growth potential
- **30-49**: Moderate AI visibility - consider optimizing for AI search
- **0-29**: Low AI visibility - focus on traditional SEO or emerging AI trends

## Use Cases

### 1. Content Strategy for AI Citations

Target keywords with high AI search volume to increase the likelihood of your content being cited by AI systems:

```bash
curl -X POST https://your-api.com/api/v1/keywords/ai-optimization \
  -H 'Content-Type: application/json' \
  -d '{
    "keywords": ["your topic"],
    "location": "United States",
    "language": "en"
  }'
```

### 2. Compare AI vs Traditional Search

Use the comparison ratio to understand if a keyword is more popular in AI queries vs traditional search:

- `ai_to_traditional_ratio > 0.5`: Keyword is more popular in AI
- `ai_to_traditional_ratio < 0.3`: Keyword is more popular in traditional search

### 3. Trend Analysis

Monitor `ai_trend` and `ai_monthly_searches` to identify:
- Growing AI interest (positive trend)
- Declining AI interest (negative trend)
- Seasonal patterns in AI queries

### 4. ROI Tracking

Track if your content optimization increases AI visibility over time by monitoring monthly searches.

## Integration Examples

### Frontend Integration

```typescript
// Get AI optimization data
const response = await fetch('/api/v1/keywords/ai-optimization', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    keywords: ['your keyword'],
    location: 'United States',
    language: 'en'
  })
});

const data = await response.json();
const keywordData = data.ai_optimization_analysis['your keyword'];

// Display AI metrics
console.log(`AI Search Volume: ${keywordData.ai_search_volume}`);
console.log(`AI Optimization Score: ${keywordData.ai_optimization_score}`);
console.log(`Recommended: ${keywordData.ai_recommended ? 'Yes' : 'No'}`);
```

### Enhanced Endpoint with AI Data

```typescript
// Get comprehensive analysis including AI data
const response = await fetch('/api/v1/keywords/enhanced', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    keywords: ['your keyword'],
    location: 'United States',
    language: 'en',
    max_suggestions_per_keyword: 5
  })
});

const data = await response.json();
const keyword = data.enhanced_analysis['your keyword'];

// Access both traditional and AI metrics
console.log(`Traditional Search Volume: ${keyword.search_volume}`);
console.log(`AI Search Volume: ${keyword.ai_search_volume}`);
console.log(`AI Trend: ${keyword.ai_trend > 0 ? 'Growing' : 'Declining'}`);
```

## API Endpoints Summary

### 1. Enhanced Keywords Endpoint
- **URL**: `/api/v1/keywords/enhanced`
- **Includes**: Traditional SEO + AI optimization data
- **Use Case**: Comprehensive keyword analysis

### 2. AI Optimization Endpoint
- **URL**: `/api/v1/keywords/ai-optimization`
- **Focus**: AI-specific metrics and recommendations
- **Use Case**: AI-focused content strategy

## Response Fields Reference

### AI Optimization Fields

| Field | Type | Description |
|-------|------|-------------|
| `ai_search_volume` | integer | Current month's estimated volume in AI queries |
| `ai_trend` | float | Trend score (-1.0 to 1.0) indicating growth/decline |
| `ai_monthly_searches` | array | Historical monthly AI search volume (12 months) |
| `ai_optimization_score` | integer | Overall AI optimization score (0-100) |
| `ai_recommended` | boolean | Whether keyword is recommended for AI optimization |
| `ai_reason` | string | Explanation of recommendation |
| `comparison.ai_to_traditional_ratio` | float | Ratio of AI to traditional search volume |
| `comparison.ai_growth_trend` | string | "increasing", "decreasing", or "stable" |

## Best Practices

1. **Target High AI Volume Keywords**: Focus on keywords with `ai_search_volume > 1000` for better AI citation potential

2. **Monitor Trends**: Use `ai_trend` to identify growing AI interest early

3. **Compare Metrics**: Use `ai_to_traditional_ratio` to balance AI and traditional SEO strategy

4. **Track Monthly Changes**: Monitor `ai_monthly_searches` to see long-term patterns

5. **Optimize for AI Score**: Prioritize keywords with `ai_optimization_score >= 50`

## Troubleshooting

### AI Search Volume Returns 0

If `ai_search_volume` is 0, it could mean:
1. Keyword has no AI search volume (not referenced in AI queries)
2. DataForSEO API response format differs (check logs)
3. API endpoint requires different parameters

Check logs for debug information:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=blog-writer-api-dev" \
  --project api-ai-blog-writer \
  --limit 50 \
  --format="value(textPayload)" | grep -i "ai_optimization"
```

## Next Steps

1. Test endpoints with real keywords
2. Monitor AI search volume trends
3. Adjust content strategy based on AI optimization scores
4. Track ROI of AI-optimized content

## Files Modified

1. `src/blog_writer_sdk/integrations/dataforseo_integration.py` - Added `get_ai_search_volume()` method
2. `src/blog_writer_sdk/seo/enhanced_keyword_analyzer.py` - Integrated AI data into batch metrics
3. `main.py` - Added AI optimization endpoint and integrated AI data into enhanced endpoint

## Git Commits

- `b7dbb22`: Add AI optimization support: integrate DataForSEO AI search volume data
- `65531a7`: Improve AI optimization response parsing to handle multiple response formats

