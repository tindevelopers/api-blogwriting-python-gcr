# Content Sentiment Analysis API

**Version:** 1.0  
**Date:** January 1, 2026  
**Endpoint:** `POST /api/v1/content/analyze-sentiment`  
**Base URL:** `https://blog-writer-api-dev-613248238610.europe-west9.run.app`

---

## Overview

The Content Sentiment Analysis endpoint provides comprehensive content intelligence using DataForSEO's Content Analysis API. This endpoint analyzes how content, keywords, or brands are perceived online by examining sentiment, brand mentions, engagement signals, and citation patterns.

### Purpose

- **Sentiment Analysis**: Understand positive, negative, and neutral sentiment around keywords/brands
- **Brand Monitoring**: Track brand mentions and citations across the web
- **Engagement Intelligence**: Identify high-performing content and engagement patterns
- **Content Strategy**: Discover top topics and domains for content optimization
- **Competitive Analysis**: Understand how competitors' content is perceived

---

## API Endpoint

### Request

**Endpoint:** `POST /api/v1/content/analyze-sentiment`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```typescript
interface ContentSentimentAnalysisRequest {
  keyword: string;                    // Required: Keyword to analyze (1-200 chars)
  location?: string;                  // Optional: Location for analysis (default: "United States")
  language?: string;                  // Optional: Language code (default: "en")
  include_summary?: boolean;          // Optional: Include summary analysis (default: true)
  limit?: number;                    // Optional: Max citations to analyze (1-1000, default: 100)
}
```

**Example Request:**
```bash
curl -X POST "https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/content/analyze-sentiment" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "sustainable gardening",
    "location": "United States",
    "language": "en",
    "include_summary": true,
    "limit": 100
  }'
```

### Response

**Success Response (200 OK):**
```typescript
interface ContentSentimentAnalysisResponse {
  keyword: string;
  location: string;
  language: string;
  analysis: {
    citations: Array<{
      title: string;
      url: string;
      domain: string;
      snippet: string;
      sentiment: "positive" | "negative" | "neutral";
    }>;
    total_citations: number;
    sentiment: {
      breakdown: {
        positive: number;
        negative: number;
        neutral: number;
      };
      score: number;              // 0-100 sentiment score
      overall: "positive" | "negative" | "neutral";
    };
    engagement_signals: Array<{
      url: string;
      score: number;              // 0-1 engagement score
    }>;
    top_domains: Array<{
      domain: string;
      citation_count: number;
      sentiment_breakdown: {
        positive: number;
        negative: number;
        neutral: number;
      };
    }>;
    metadata: object;
  };
  summary?: {                      // Included if include_summary=true
    total_citations: number;
    sentiment_breakdown: object;
    top_topics: Array<string>;
    brand_mentions: Array<object>;
    engagement_score: number;
    metadata: object;
  };
  recommendations: Array<string>;   // Actionable recommendations
}
```

**Example Response:**
```json
{
  "keyword": "sustainable gardening",
  "location": "United States",
  "language": "en",
  "analysis": {
    "citations": [
      {
        "title": "10 Sustainable Gardening Tips for Beginners",
        "url": "https://example.com/sustainable-gardening-tips",
        "domain": "example.com",
        "snippet": "Sustainable gardening practices help reduce environmental impact...",
        "sentiment": "positive"
      }
    ],
    "total_citations": 87,
    "sentiment": {
      "breakdown": {
        "positive": 65,
        "negative": 8,
        "neutral": 14
      },
      "score": 72.5,
      "overall": "positive"
    },
    "engagement_signals": [
      {
        "url": "https://example.com/top-content",
        "score": 0.85
      }
    ],
    "top_domains": [
      {
        "domain": "example.com",
        "citation_count": 12,
        "sentiment_breakdown": {
          "positive": 10,
          "negative": 1,
          "neutral": 1
        }
      }
    ],
    "metadata": {}
  },
  "summary": {
    "total_citations": 87,
    "sentiment_breakdown": {},
    "top_topics": [
      "organic gardening",
      "composting",
      "water conservation"
    ],
    "brand_mentions": [],
    "engagement_score": 0.68,
    "metadata": {}
  },
  "recommendations": [
    "Strong positive sentiment detected - leverage this for brand awareness campaigns",
    "High engagement signals detected - analyze top-performing content for best practices"
  ]
}
```

**Error Responses:**

- **503 Service Unavailable**: DataForSEO client not available or not configured
- **500 Internal Server Error**: Analysis failed

---

## Use Cases

### 1. Brand Monitoring

**Scenario:** Monitor how your brand is mentioned online

```typescript
const response = await fetch('/api/v1/content/analyze-sentiment', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    keyword: 'Your Brand Name',
    include_summary: true,
    limit: 200
  })
});

const data = await response.json();
console.log(`Sentiment Score: ${data.analysis.sentiment.score}/100`);
console.log(`Brand Mentions: ${data.summary?.brand_mentions.length || 0}`);
```

### 2. Content Performance Analysis

**Scenario:** Analyze how content about a topic performs

```typescript
const response = await fetch('/api/v1/content/analyze-sentiment', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    keyword: 'machine learning basics',
    include_summary: true
  })
});

const data = await response.json();
// Identify top-performing content
const topContent = data.analysis.engagement_signals
  .sort((a, b) => b.score - a.score)
  .slice(0, 5);
```

### 3. Competitive Analysis

**Scenario:** Understand competitor content sentiment

```typescript
const response = await fetch('/api/v1/content/analyze-sentiment', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    keyword: 'competitor product name',
    limit: 500
  })
});

const data = await response.json();
// Analyze sentiment distribution
const sentimentRatio = {
  positive: data.analysis.sentiment.breakdown.positive / data.analysis.total_citations,
  negative: data.analysis.sentiment.breakdown.negative / data.analysis.total_citations,
  neutral: data.analysis.sentiment.breakdown.neutral / data.analysis.total_citations
};
```

### 4. Topic Research

**Scenario:** Discover top topics and domains for content strategy

```typescript
const response = await fetch('/api/v1/content/analyze-sentiment', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    keyword: 'digital marketing',
    include_summary: true
  })
});

const data = await response.json();
// Get top topics for content ideas
const topTopics = data.summary?.top_topics || [];
// Get top domains for outreach
const topDomains = data.analysis.top_domains.slice(0, 10);
```

---

## Frontend Integration

### React/TypeScript Example

```typescript
import { useState } from 'react';

interface SentimentAnalysisResult {
  keyword: string;
  analysis: {
    sentiment: {
      score: number;
      overall: string;
      breakdown: {
        positive: number;
        negative: number;
        neutral: number;
      };
    };
    citations: Array<{
      title: string;
      url: string;
      sentiment: string;
    }>;
    top_domains: Array<{
      domain: string;
      citation_count: number;
    }>;
  };
  summary?: {
    top_topics: string[];
    brand_mentions: Array<unknown>;
  };
  recommendations: string[];
}

export function ContentSentimentAnalyzer() {
  const [keyword, setKeyword] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SentimentAnalysisResult | null>(null);

  const analyzeSentiment = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        'https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/content/analyze-sentiment',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            keyword,
            include_summary: true,
            limit: 100
          })
        }
      );

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Failed to analyze sentiment:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input
        value={keyword}
        onChange={(e) => setKeyword(e.target.value)}
        placeholder="Enter keyword or brand name"
      />
      <button onClick={analyzeSentiment} disabled={loading || !keyword}>
        {loading ? 'Analyzing...' : 'Analyze Sentiment'}
      </button>

      {result && (
        <div>
          <h3>Sentiment Score: {result.analysis.sentiment.score}/100</h3>
          <p>Overall: {result.analysis.sentiment.overall}</p>
          
          <div>
            <h4>Sentiment Breakdown</h4>
            <p>Positive: {result.analysis.sentiment.breakdown.positive}</p>
            <p>Negative: {result.analysis.sentiment.breakdown.negative}</p>
            <p>Neutral: {result.analysis.sentiment.breakdown.neutral}</p>
          </div>

          {result.summary && (
            <div>
              <h4>Top Topics</h4>
              <ul>
                {result.summary.top_topics.map((topic, i) => (
                  <li key={i}>{topic}</li>
                ))}
              </ul>
            </div>
          )}

          <div>
            <h4>Recommendations</h4>
            <ul>
              {result.recommendations.map((rec, i) => (
                <li key={i}>{rec}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## DataForSEO Integration

This endpoint uses DataForSEO's Content Analysis API:

- **Search Endpoint**: `content_analysis/search/live` - Provides citations, sentiment, and engagement signals
- **Summary Endpoint**: `content_analysis/summary/live` - Provides brand mentions, top topics, and aggregated metrics

**DataForSEO Documentation:**
- [Content Analysis API Overview](https://dataforseo.com/apis/content-analysis-api)
- [API Documentation](https://docs.dataforseo.com/v3/content_analysis/)

---

## Best Practices

1. **Keyword Selection**: Use specific keywords or brand names for better results
2. **Limit Usage**: Use appropriate `limit` values (100-200 is usually sufficient)
3. **Summary Analysis**: Enable `include_summary` for brand mentions and topic discovery
4. **Error Handling**: Always handle 503 errors (service unavailable) gracefully
5. **Caching**: Consider caching results for frequently analyzed keywords
6. **Rate Limiting**: Be mindful of API rate limits when making multiple requests

---

## Comparison with Other Endpoints

| Endpoint | Purpose | DataForSEO API Used |
|----------|---------|---------------------|
| `/api/v1/analyze` | SEO and readability analysis | None (internal analysis) |
| `/api/v1/content/analyze-sentiment` | Sentiment, brand mentions, engagement | Content Analysis API |
| `/api/v1/keywords/goal-based-analysis` | Goal-based keyword research | Multiple APIs (includes Content Analysis) |
| `/api/v1/keywords/ai-optimization` | AI search volume and optimization | AI Optimization API |

---

## Support

For questions or issues:
- Backend API documentation: `https://blog-writer-api-dev-613248238610.europe-west9.run.app/docs`
- DataForSEO API: [https://docs.dataforseo.com/v3/content_analysis/](https://docs.dataforseo.com/v3/content_analysis/)

---

## Changelog

### Version 1.0 (January 1, 2026)
- Initial Content Sentiment Analysis endpoint
- Integration with DataForSEO Content Analysis API
- Sentiment scoring and recommendations
- Brand mentions and topic discovery

