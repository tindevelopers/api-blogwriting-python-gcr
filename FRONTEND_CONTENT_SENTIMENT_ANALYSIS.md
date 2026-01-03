# Content Sentiment Analysis API - Frontend Integration Guide

**Version:** 1.0  
**Date:** January 1, 2026  
**Endpoint:** `POST /api/v1/content/analyze-sentiment`  
**Base URL:** `https://blog-writer-api-dev-613248238610.europe-west9.run.app`

---

## 🎯 Overview

The Content Sentiment Analysis API provides real-time intelligence about how keywords, brands, or topics are perceived online. This endpoint uses DataForSEO's Content Analysis API to deliver:

- ✅ **Sentiment Analysis** - Positive, negative, and neutral sentiment breakdown
- ✅ **Brand Mentions** - Track where and how your brand is mentioned
- ✅ **Engagement Signals** - Identify high-performing content
- ✅ **Top Topics** - Discover trending topics and content opportunities
- ✅ **Domain Analysis** - See which domains mention your keywords most

**Perfect for:** Brand monitoring dashboards, content intelligence panels, competitive analysis tools, and content strategy features.

---

## 📡 API Endpoint

### Endpoint Details

```
POST /api/v1/content/analyze-sentiment
```

**Base URL:** `https://blog-writer-api-dev-613248238610.europe-west9.run.app`

**Authentication:** Currently none required (may change in future)

**Rate Limits:** Subject to DataForSEO API limits

---

## 📥 Request Format

### Request Body

```typescript
interface ContentSentimentAnalysisRequest {
  keyword: string;           // Required: Keyword or brand name to analyze (1-200 chars)
  location?: string;          // Optional: Location (default: "United States")
  language?: string;          // Optional: Language code (default: "en")
  include_summary?: boolean;  // Optional: Include brand mentions & topics (default: true)
  limit?: number;            // Optional: Max citations (1-1000, default: 100)
}
```

### Example Request

```typescript
const requestBody = {
  keyword: "sustainable gardening",
  location: "United States",
  language: "en",
  include_summary: true,
  limit: 100
};
```

---

## 📤 Response Format

### Success Response (200 OK)

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
  summary?: {
    total_citations: number;
    sentiment_breakdown: object;
    top_topics: Array<string>;
    brand_mentions: Array<object>;
    engagement_score: number;
    metadata: object;
  };
  recommendations: Array<string>;
}
```

### Error Responses

**503 Service Unavailable**
```json
{
  "detail": "DataForSEO client not available"
}
```
or
```json
{
  "detail": "DataForSEO API not configured"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Content sentiment analysis failed: [error message]"
}
```

---

## 💻 Frontend Implementation Examples

### React/TypeScript Hook

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
      domain: string;
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

const API_BASE_URL = 'https://blog-writer-api-dev-613248238610.europe-west9.run.app';

export function useContentSentimentAnalysis() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SentimentAnalysisResult | null>(null);

  const analyzeSentiment = async (
    keyword: string,
    options?: {
      location?: string;
      language?: string;
      includeSummary?: boolean;
      limit?: number;
    }
  ) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/content/analyze-sentiment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          keyword,
          location: options?.location || 'United States',
          language: options?.language || 'en',
          include_summary: options?.includeSummary !== false,
          limit: options?.limit || 100,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to analyze sentiment';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    analyzeSentiment,
    loading,
    error,
    result,
  };
}
```

### React Component Example

```typescript
import React, { useState } from 'react';
import { useContentSentimentAnalysis } from './hooks/useContentSentimentAnalysis';

export function ContentSentimentAnalyzer() {
  const [keyword, setKeyword] = useState('');
  const { analyzeSentiment, loading, error, result } = useContentSentimentAnalysis();

  const handleAnalyze = async () => {
    if (!keyword.trim()) return;
    await analyzeSentiment(keyword, { includeSummary: true });
  };

  return (
    <div className="content-sentiment-analyzer">
      <div className="input-section">
        <input
          type="text"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          placeholder="Enter keyword or brand name"
          disabled={loading}
          onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
        />
        <button onClick={handleAnalyze} disabled={loading || !keyword.trim()}>
          {loading ? 'Analyzing...' : 'Analyze Sentiment'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          Error: {error}
        </div>
      )}

      {result && (
        <div className="results">
          {/* Sentiment Score Card */}
          <div className="sentiment-card">
            <h3>Sentiment Score</h3>
            <div className="score-display">
              <span className="score-value">{result.analysis.sentiment.score}</span>
              <span className="score-max">/100</span>
            </div>
            <div className={`sentiment-badge ${result.analysis.sentiment.overall}`}>
              {result.analysis.sentiment.overall.toUpperCase()}
            </div>
          </div>

          {/* Sentiment Breakdown */}
          <div className="sentiment-breakdown">
            <h4>Sentiment Breakdown</h4>
            <div className="breakdown-bars">
              <div className="breakdown-item positive">
                <span className="label">Positive</span>
                <div className="bar">
                  <div
                    className="fill"
                    style={{
                      width: `${(result.analysis.sentiment.breakdown.positive / result.analysis.total_citations) * 100}%`,
                    }}
                  />
                </div>
                <span className="count">{result.analysis.sentiment.breakdown.positive}</span>
              </div>
              <div className="breakdown-item neutral">
                <span className="label">Neutral</span>
                <div className="bar">
                  <div
                    className="fill"
                    style={{
                      width: `${(result.analysis.sentiment.breakdown.neutral / result.analysis.total_citations) * 100}%`,
                    }}
                  />
                </div>
                <span className="count">{result.analysis.sentiment.breakdown.neutral}</span>
              </div>
              <div className="breakdown-item negative">
                <span className="label">Negative</span>
                <div className="bar">
                  <div
                    className="fill"
                    style={{
                      width: `${(result.analysis.sentiment.breakdown.negative / result.analysis.total_citations) * 100}%`,
                    }}
                  />
                </div>
                <span className="count">{result.analysis.sentiment.breakdown.negative}</span>
              </div>
            </div>
          </div>

          {/* Top Topics */}
          {result.summary?.top_topics && result.summary.top_topics.length > 0 && (
            <div className="top-topics">
              <h4>Top Topics</h4>
              <div className="topics-list">
                {result.summary.top_topics.map((topic, index) => (
                  <span key={index} className="topic-tag">
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Top Domains */}
          {result.analysis.top_domains.length > 0 && (
            <div className="top-domains">
              <h4>Top Domains</h4>
              <ul>
                {result.analysis.top_domains.slice(0, 10).map((domain, index) => (
                  <li key={index}>
                    <span className="domain-name">{domain.domain}</span>
                    <span className="citation-count">{domain.citation_count} citations</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommendations */}
          {result.recommendations.length > 0 && (
            <div className="recommendations">
              <h4>Recommendations</h4>
              <ul>
                {result.recommendations.map((rec, index) => (
                  <li key={index}>{rec}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Citations List */}
          <div className="citations">
            <h4>Top Citations ({result.analysis.total_citations} total)</h4>
            <div className="citations-list">
              {result.analysis.citations.slice(0, 10).map((citation, index) => (
                <div key={index} className="citation-item">
                  <a href={citation.url} target="_blank" rel="noopener noreferrer">
                    <h5>{citation.title}</h5>
                  </a>
                  <p className="domain">{citation.domain}</p>
                  <p className="snippet">{citation.snippet}</p>
                  <span className={`sentiment-badge small ${citation.sentiment}`}>
                    {citation.sentiment}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

### CSS Styling Example

```css
.content-sentiment-analyzer {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.input-section {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
}

.input-section input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.input-section button {
  padding: 0.75rem 1.5rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}

.input-section button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.sentiment-card {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.score-display {
  font-size: 3rem;
  font-weight: bold;
  margin: 1rem 0;
}

.score-value {
  color: #007bff;
}

.sentiment-badge {
  display: inline-block;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-weight: bold;
  text-transform: uppercase;
  font-size: 0.875rem;
}

.sentiment-badge.positive {
  background: #d4edda;
  color: #155724;
}

.sentiment-badge.negative {
  background: #f8d7da;
  color: #721c24;
}

.sentiment-badge.neutral {
  background: #e2e3e5;
  color: #383d41;
}

.breakdown-bars {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.breakdown-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.breakdown-item .bar {
  flex: 1;
  height: 24px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
}

.breakdown-item .fill {
  height: 100%;
  transition: width 0.3s ease;
}

.breakdown-item.positive .fill {
  background: #28a745;
}

.breakdown-item.neutral .fill {
  background: #6c757d;
}

.breakdown-item.negative .fill {
  background: #dc3545;
}

.topics-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.topic-tag {
  padding: 0.5rem 1rem;
  background: #e9ecef;
  border-radius: 20px;
  font-size: 0.875rem;
}

.citation-item {
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.citation-item h5 {
  margin: 0 0 0.5rem 0;
  color: #007bff;
}

.citation-item .domain {
  color: #6c757d;
  font-size: 0.875rem;
  margin: 0.25rem 0;
}

.citation-item .snippet {
  color: #495057;
  margin: 0.5rem 0;
}
```

---

## 🎨 UI/UX Recommendations

### 1. Loading States
- Show a spinner or skeleton loader while analyzing
- Display progress indicator if analysis takes > 2 seconds
- Disable form inputs during analysis

### 2. Error Handling
- Display user-friendly error messages
- Provide retry button for failed requests
- Show 503 errors with message: "Content analysis service temporarily unavailable"

### 3. Data Visualization
- **Sentiment Score**: Large, color-coded display (green: 60+, yellow: 40-60, red: <40)
- **Breakdown**: Horizontal bar chart or pie chart
- **Top Domains**: Table or list with citation counts
- **Citations**: Card-based layout with sentiment badges

### 4. Performance
- Cache results for frequently analyzed keywords
- Debounce input if implementing live search
- Paginate citations if showing large lists

---

## 🔗 Integration with Other Endpoints

This endpoint works well with:

- **`/api/v1/keywords/ai-optimization`** - Combine sentiment analysis with AI search volume
- **`/api/v1/keywords/goal-based-analysis`** - Use sentiment data in goal-based research
- **`/api/v1/keywords/ai-mentions`** - Compare sentiment with LLM mentions

---

## 📊 Use Cases

### 1. Brand Monitoring Dashboard
Monitor brand sentiment over time and track mentions across domains.

### 2. Content Intelligence Panel
Show content creators how their topics are perceived and identify opportunities.

### 3. Competitive Analysis Tool
Compare sentiment for competitor keywords and products.

### 4. Content Strategy Feature
Discover top topics and engagement signals to inform content planning.

---

## ⚠️ Important Notes

1. **Rate Limits**: Subject to DataForSEO API rate limits
2. **Response Time**: Typically 2-5 seconds, can be longer for large limits
3. **Data Freshness**: Results reflect current web content (updated regularly)
4. **Keyword Specificity**: More specific keywords yield better results
5. **Summary Data**: Enable `include_summary` for brand mentions and topics

---

## 🐛 Troubleshooting

### Issue: 503 Service Unavailable
**Solution:** Check if DataForSEO credentials are configured. This is a backend configuration issue.

### Issue: Empty Results
**Solution:** Try a more specific keyword or different location. Some keywords may have limited online mentions.

### Issue: Slow Response
**Solution:** Reduce the `limit` parameter. Large limits (500+) take longer to process.

---

## 📚 Additional Resources

- **Backend API Docs**: `https://blog-writer-api-dev-613248238610.europe-west9.run.app/docs`
- **DataForSEO API**: [https://dataforseo.com/apis/content-analysis-api](https://dataforseo.com/apis/content-analysis-api)
- **Full API Documentation**: See `CONTENT_SENTIMENT_ANALYSIS_API.md`

---

## 📝 Changelog

### Version 1.0 (January 1, 2026)
- Initial frontend integration guide
- React/TypeScript examples
- UI/UX recommendations
- Error handling patterns

