# Goal-Based Keyword Analysis API

**Version:** 1.3.6  
**API Endpoint:** `POST /api/v1/keywords/goal-based-analysis`  
**Base URL:** `https://blog-writer-api-dev-kq42l26tuq-od.a.run.app`

---

## 🎯 Overview

The Goal-Based Keyword Analysis endpoint routes to optimized DataForSEO endpoints based on your content goal. Each goal uses a different combination of endpoints to provide the most relevant insights.

---

## 📋 Content Goals

### 1. SEO & Rankings
**Focus:** High search volume, low difficulty, ranking opportunities

**Endpoints Used:**
- `keywords_data/google_ads/search_volume/live` - Search volume, CPC, competition
- `dataforseo_labs/google/keyword_difficulty/live` - Keyword difficulty scoring
- `serp/google/organic/live/advanced` - SERP analysis
- `dataforseo_labs/google/keyword_overview/live` - Comprehensive metrics

**Best For:**
- Finding keywords with ranking potential
- Identifying high-value keywords
- Understanding competition

---

### 2. Engagement
**Focus:** Question-based keywords, trending topics, discussion-worthy content

**Endpoints Used:**
- `dataforseo_labs/google/search_intent/live` - Intent analysis (informational)
- `serp/google/organic/live/advanced` - PAA questions extraction
- `content_analysis/search/live` - Content sentiment and engagement signals
- `dataforseo_labs/google/related_keywords/live` - Related keywords

**Best For:**
- Creating Q&A content
- Finding discussion topics
- Identifying shareable content ideas

---

### 3. Conversions
**Focus:** Commercial intent keywords, high CPC, transactional queries

**Endpoints Used:**
- `keywords_data/google_ads/search_volume/live` - CPC analysis
- `dataforseo_labs/google/search_intent/live` - Commercial/transactional intent
- `serp/google/organic/live/advanced` - Shopping results analysis
- `dataforseo_labs/google/keyword_overview/live` - Intent classification

**Best For:**
- E-commerce content
- Product comparison pages
- Conversion-focused content

---

### 4. Brand Awareness
**Focus:** Brand mentions, industry keywords, thought leadership topics

**Endpoints Used:**
- `content_analysis/search/live` - Brand mentions and sentiment
- `content_analysis/summary/live` - Content analysis summary
- `dataforseo_labs/google/keyword_overview/live` - Brand + industry keywords
- `serp/google/organic/live/advanced` - Brand presence analysis
- `dataforseo_labs/google/keyword_ideas/live` - Branded keyword opportunities

**Best For:**
- Brand-building content
- Thought leadership pieces
- Industry insights

---

## 📡 API Request

### Endpoint
```
POST /api/v1/keywords/goal-based-analysis
```

### Request Body

```typescript
interface GoalBasedAnalysisRequest {
  keywords: string[];                    // 1-50 keywords to analyze
  content_goal: ContentGoal;            // One of: "SEO & Rankings", "Engagement", "Conversions", "Brand Awareness"
  location?: string;                     // Default: "United States"
  language?: string;                     // Default: "en"
  include_content_analysis?: boolean;   // Default: true (for Engagement & Brand Awareness)
  include_serp?: boolean;                // Default: true
}
```

### Content Goal Enum

```typescript
enum ContentGoal {
  SEO_RANKINGS = "SEO & Rankings",
  ENGAGEMENT = "Engagement",
  CONVERSIONS = "Conversions",
  BRAND_AWARENESS = "Brand Awareness"
}
```

### Example Request

```typescript
const request = {
  keywords: ["pet grooming", "dog grooming"],
  content_goal: "SEO & Rankings",
  location: "United States",
  language: "en",
  include_serp: true
};
```

---

## 📥 API Response

### Response Structure

```typescript
interface GoalBasedAnalysisResponse {
  content_goal: string;
  keywords: string[];
  location: string;
  language: string;
  analysis: {
    // Goal-specific analysis data
    search_volume?: Record<string, KeywordMetrics>;
    difficulty?: Record<string, number>;
    keyword_overview?: any;
    serp_analysis?: SERPAnalysis;
    search_intent?: IntentAnalysis;
    content_analysis?: ContentAnalysis;
    related_keywords?: RelatedKeywords;
    keyword_ideas?: KeywordIdeas;
    recommendations: string[];  // AI-generated recommendations
  };
}
```

### SEO & Rankings Response

```typescript
{
  content_goal: "SEO & Rankings",
  keywords: ["pet grooming"],
  location: "United States",
  language: "en",
  analysis: {
    search_volume: {
      "pet grooming": {
        search_volume: 135000,
        cpc: 2.5,
        competition: 0.65,
        trend: 0.8
      }
    },
    difficulty: {
      "pet grooming": 45.2
    },
    keyword_overview: { /* ... */ },
    serp_analysis: { /* ... */ },
    recommendations: [
      "✅ 'pet grooming': High volume (135000) with low difficulty (45.2) - Great ranking opportunity"
    ]
  }
}
```

### Engagement Response

```typescript
{
  content_goal: "Engagement",
  keywords: ["how to groom a dog"],
  location: "United States",
  language: "en",
  analysis: {
    search_intent: { /* ... */ },
    serp_analysis: {
      people_also_ask: [
        "How often should I groom my dog?",
        "What tools do I need for dog grooming?"
      ]
    },
    content_analysis: {
      citations: [ /* ... */ ],
      sentiment: {
        positive: 15,
        negative: 2,
        neutral: 8
      },
      engagement_signals: [ /* ... */ ]
    },
    related_keywords: { /* ... */ },
    recommendations: [
      "✅ 'how to groom a dog': Informational intent - Great for engagement content",
      "✅ Found 12 People Also Ask questions - Create Q&A content"
    ]
  }
}
```

### Conversions Response

```typescript
{
  content_goal: "Conversions",
  keywords: ["best dog grooming products"],
  location: "United States",
  language: "en",
  analysis: {
    search_volume: {
      "best dog grooming products": {
        search_volume: 8900,
        cpc: 3.2,
        competition: 0.7
      }
    },
    search_intent: { /* ... */ },
    serp_analysis: {
      shopping_results: [ /* ... */ ]
    },
    keyword_overview: { /* ... */ },
    recommendations: [
      "✅ 'best dog grooming products': High CPC ($3.20) - Strong commercial value",
      "✅ Shopping results present - E-commerce opportunity"
    ]
  }
}
```

### Brand Awareness Response

```typescript
{
  content_goal: "Brand Awareness",
  keywords: ["petco grooming"],
  location: "United States",
  language: "en",
  analysis: {
    content_analysis: {
      citations: [ /* ... */ ],
      sentiment: {
        positive: 20,
        negative: 3,
        neutral: 12
      },
      brand_mentions: [ /* ... */ ],
      summary: {
        total_citations: 35,
        engagement_score: 0.75
      }
    },
    keyword_overview: { /* ... */ },
    serp_analysis: { /* ... */ },
    keyword_ideas: { /* ... */ },
    recommendations: [
      "✅ Found 8 brand mentions - Track brand visibility",
      "✅ Positive sentiment outweighs negative - Good brand perception"
    ]
  }
}
```

---

## 💻 Frontend Integration

### React Hook Example

```typescript
import { useState } from 'react';

type ContentGoal = "SEO & Rankings" | "Engagement" | "Conversions" | "Brand Awareness";

interface GoalBasedAnalysisRequest {
  keywords: string[];
  content_goal: ContentGoal;
  location?: string;
  language?: string;
  include_content_analysis?: boolean;
  include_serp?: boolean;
}

export function useGoalBasedAnalysis() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const analyzeKeywords = async (request: GoalBasedAnalysisRequest) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        'https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/keywords/goal-based-analysis',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(request),
        }
      );

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      setResults(data);
      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { analyzeKeywords, loading, results, error };
}
```

### React Component Example

```typescript
import React, { useState } from 'react';
import { useGoalBasedAnalysis } from './hooks/useGoalBasedAnalysis';

type ContentGoal = "SEO & Rankings" | "Engagement" | "Conversions" | "Brand Awareness";

export function GoalBasedKeywordAnalysis() {
  const [keywords, setKeywords] = useState<string[]>([]);
  const [contentGoal, setContentGoal] = useState<ContentGoal>("SEO & Rankings");
  const { analyzeKeywords, loading, results, error } = useGoalBasedAnalysis();

  const handleAnalyze = async () => {
    if (keywords.length === 0) return;

    await analyzeKeywords({
      keywords,
      content_goal: contentGoal,
      location: "United States",
      language: "en",
      include_serp: true,
      include_content_analysis: true,
    });
  };

  return (
    <div className="goal-based-analysis">
      <h2>Goal-Based Keyword Analysis</h2>

      {/* Content Goal Selection */}
      <div className="goal-selector">
        <label>Content Goal:</label>
        <select
          value={contentGoal}
          onChange={(e) => setContentGoal(e.target.value as ContentGoal)}
        >
          <option value="SEO & Rankings">SEO & Rankings</option>
          <option value="Engagement">Engagement</option>
          <option value="Conversions">Conversions</option>
          <option value="Brand Awareness">Brand Awareness</option>
        </select>
      </div>

      {/* Keywords Input */}
      <div className="keywords-input">
        <label>Keywords (comma-separated):</label>
        <input
          type="text"
          value={keywords.join(', ')}
          onChange={(e) =>
            setKeywords(
              e.target.value.split(',').map((k) => k.trim()).filter(Boolean)
            )
          }
          placeholder="pet grooming, dog grooming"
        />
      </div>

      {/* Analyze Button */}
      <button onClick={handleAnalyze} disabled={loading || keywords.length === 0}>
        {loading ? 'Analyzing...' : 'Analyze Keywords'}
      </button>

      {/* Error Display */}
      {error && <div className="error">Error: {error}</div>}

      {/* Results Display */}
      {results && (
        <div className="results">
          <h3>Analysis Results for {results.content_goal}</h3>

          {/* Recommendations */}
          {results.analysis.recommendations && (
            <div className="recommendations">
              <h4>Recommendations:</h4>
              <ul>
                {results.analysis.recommendations.map((rec: string, idx: number) => (
                  <li key={idx}>{rec}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Goal-Specific Data */}
          {contentGoal === "SEO & Rankings" && results.analysis.search_volume && (
            <div className="seo-data">
              <h4>SEO Metrics:</h4>
              {Object.entries(results.analysis.search_volume).map(([keyword, data]: [string, any]) => (
                <div key={keyword}>
                  <strong>{keyword}:</strong>
                  <ul>
                    <li>Search Volume: {data.search_volume?.toLocaleString()}</li>
                    <li>CPC: ${data.cpc?.toFixed(2)}</li>
                    <li>Difficulty: {results.analysis.difficulty?.[keyword]?.toFixed(1)}</li>
                  </ul>
                </div>
              ))}
            </div>
          )}

          {contentGoal === "Engagement" && results.analysis.serp_analysis?.people_also_ask && (
            <div className="engagement-data">
              <h4>People Also Ask:</h4>
              <ul>
                {results.analysis.serp_analysis.people_also_ask.map((question: string, idx: number) => (
                  <li key={idx}>{question}</li>
                ))}
              </ul>
            </div>
          )}

          {contentGoal === "Conversions" && results.analysis.search_volume && (
            <div className="conversion-data">
              <h4>Conversion Metrics:</h4>
              {Object.entries(results.analysis.search_volume).map(([keyword, data]: [string, any]) => (
                <div key={keyword}>
                  <strong>{keyword}:</strong>
                  <ul>
                    <li>CPC: ${data.cpc?.toFixed(2)}</li>
                    <li>Search Volume: {data.search_volume?.toLocaleString()}</li>
                  </ul>
                </div>
              ))}
            </div>
          )}

          {contentGoal === "Brand Awareness" && results.analysis.content_analysis && (
            <div className="brand-data">
              <h4>Brand Analysis:</h4>
              <ul>
                <li>
                  Sentiment: Positive ({results.analysis.content_analysis.sentiment?.positive}),
                  Negative ({results.analysis.content_analysis.sentiment?.negative}),
                  Neutral ({results.analysis.content_analysis.sentiment?.neutral})
                </li>
                <li>
                  Engagement Score: {results.analysis.content_analysis.summary?.engagement_score?.toFixed(2)}
                </li>
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

---

## 🎨 UI Integration with Content Goal Selector

This endpoint is designed to work seamlessly with the frontend interface showing 4 content goal cards:

```typescript
// When user selects a content goal card
const handleGoalSelect = async (goal: ContentGoal, keywords: string[]) => {
  const results = await analyzeKeywords({
    keywords,
    content_goal: goal,
    location: "United States",
    language: "en",
  });

  // Display results in goal-specific UI
  displayGoalResults(goal, results);
};
```

---

## 📊 Data Availability by Goal

| Data Type | SEO & Rankings | Engagement | Conversions | Brand Awareness |
|-----------|---------------|------------|-------------|-----------------|
| Search Volume | ✅ | ⚠️ | ✅✅ | ⚠️ |
| Keyword Difficulty | ✅✅ | ⚠️ | ⚠️ | ⚠️ |
| Search Intent | ⚠️ | ✅✅ | ✅✅ | ⚠️ |
| SERP Analysis | ✅✅ | ✅✅ | ✅✅ | ✅✅ |
| Content Analysis | ❌ | ✅✅ | ❌ | ✅✅ |
| Related Keywords | ⚠️ | ✅✅ | ⚠️ | ⚠️ |
| Keyword Ideas | ✅ | ⚠️ | ⚠️ | ✅✅ |
| Recommendations | ✅✅ | ✅✅ | ✅✅ | ✅✅ |

**Legend:**
- ✅✅ = Critical for this goal
- ✅ = Important for this goal
- ⚠️ = Optional/supplementary
- ❌ = Not included

---

## 🔄 Migration from Enhanced Endpoint

If you're currently using `/api/v1/keywords/enhanced`, you can migrate to goal-based analysis:

```typescript
// Old approach
const results = await fetch('/api/v1/keywords/enhanced', {
  method: 'POST',
  body: JSON.stringify({
    keywords: ['pet grooming'],
    location: 'United States',
  }),
});

// New goal-based approach
const results = await fetch('/api/v1/keywords/goal-based-analysis', {
  method: 'POST',
  body: JSON.stringify({
    keywords: ['pet grooming'],
    content_goal: 'SEO & Rankings',  // Specify your goal
    location: 'United States',
  }),
});
```

---

## ⚡ Performance Notes

- **SEO & Rankings**: Fastest (uses cached search volume data)
- **Engagement**: Medium (includes content analysis)
- **Conversions**: Fast (focuses on CPC and intent)
- **Brand Awareness**: Slower (includes comprehensive content analysis)

---

## 🐛 Error Handling

```typescript
try {
  const results = await analyzeKeywords({
    keywords: ['pet grooming'],
    content_goal: 'SEO & Rankings',
  });
} catch (error) {
  if (error.message.includes('503')) {
    // DataForSEO API not configured
    console.error('DataForSEO API not available');
  } else {
    // Other errors
    console.error('Analysis failed:', error);
  }
}
```

---

## 📚 Related Documentation

- [Frontend Integration Guide v1.3.5](./FRONTEND_INTEGRATION_V1.3.5.md)
- [Keyword Data Guide](./FRONTEND_KEYWORD_DATA_GUIDE.md)
- [AI Topic Recommendations](./FRONTEND_AI_TOPIC_RECOMMENDATIONS.md)

