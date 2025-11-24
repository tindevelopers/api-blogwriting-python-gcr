# AI Topic Suggestions API Integration Guide

**Version:** 1.3.6  
**API Endpoints:**
- `POST /api/v1/keywords/ai-mentions` - LLM Mentions Search
- `POST /api/v1/keywords/ai-topic-suggestions` - AI Topic Suggestions

**Base URL:** `https://blog-writer-api-dev-kq42l26tuq-od.a.run.app`

---

## 🎯 Overview

These endpoints provide AI-optimized topic discovery by analyzing what AI agents (ChatGPT, Claude, Gemini, Perplexity) are citing and searching for. This is critical for creating content that gets discovered and cited by AI agents.

---

## 📡 Endpoint 1: LLM Mentions Search

### Purpose

Find what topics, keywords, and URLs are being cited by AI agents in their responses.

### Endpoint

```
POST /api/v1/keywords/ai-mentions
```

### Request Body

```typescript
interface LLMMentionsRequest {
  target: string;                    // Keyword or domain to search for
  target_type?: "keyword" | "domain"; // Default: "keyword"
  location?: string;                 // Default: "United States"
  language?: string;                  // Default: "en"
  platform?: "chat_gpt" | "google";  // Default: "chat_gpt"
  limit?: number;                     // Default: 100, Max: 1000
}
```

### Response Structure

```typescript
interface LLMMentionsResponse {
  target: string;
  target_type: string;
  platform: string;
  llm_mentions: {
    target: string;
    ai_search_volume: number;
    mentions_count: number;
    top_pages: Array<{
      url: string;
      title: string;
      domain: string;
      mentions: number;
      ai_search_volume: number;
      platforms: string[];
      rank_group: number;
    }>;
    top_domains: Array<{
      domain: string;
      mentions: number;
      ai_search_volume: number;
      backlinks: number;
      referring_domains: number;
      rank: number;
    }>;
    topics: Array<{
      topic: string;
      mentions: number;
      ai_search_volume: number;
    }>;
    aggregated_metrics: {
      ai_search_volume: number;
      mentions_count: number;
      // ... other metrics
    };
  };
  top_pages: {
    target: string;
    top_pages: Array<{
      url: string;
      title: string;
      domain: string;
      mentions: number;
      ai_search_volume: number;
      rank_group: number;
      platforms: string[];
    }>;
    citation_patterns: {
      avg_mentions: number;
      common_domains: Array<[string, number]>;
      platform_distribution: Record<string, number>;
    };
  };
  top_domains: {
    target: string;
    top_domains: Array<{
      domain: string;
      mentions: number;
      ai_search_volume: number;
      backlinks: number;
      referring_domains: number;
      rank: number;
    }>;
  };
  insights: string[];  // AI-generated insights
}
```

### Example Request

```typescript
const response = await fetch('/api/v1/keywords/ai-mentions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    target: 'pet grooming',
    target_type: 'keyword',
    location: 'United States',
    language: 'en',
    platform: 'chat_gpt',
    limit: 50
  })
});

const data = await response.json();
```

---

## 📡 Endpoint 2: AI Topic Suggestions

### Purpose

Get AI-optimized topic suggestions combining:
- AI Search Volume: Keywords with high AI search volume
- LLM Mentions: Topics cited by AI agents
- LLM Responses: AI-generated topic research (optional)

### Endpoint

```
POST /api/v1/keywords/ai-topic-suggestions
```

### Request Body

```typescript
interface AITopicSuggestionsRequest {
  keywords?: string[];                // OPTIONAL: 1-10 seed keywords (required if content_objective not provided)
  content_objective?: string;         // NEW: Content objective text to extract keywords from (e.g., "I want to write articles about concrete remediation")
  target_audience?: string;           // NEW: Target audience description (e.g., "general consumers")
  industry?: string;                  // NEW: Industry/niche (e.g., "Construction")
  content_goals?: string[];           // NEW: Content goals (e.g., ["SEO & Rankings", "Engagement"])
  location?: string;                  // Default: "United States"
  language?: string;                   // Default: "en"
  include_ai_search_volume?: boolean; // Default: true
  include_llm_mentions?: boolean;     // Default: true
  include_llm_responses?: boolean;    // Default: false (costs more)
  limit?: number;                     // Default: 50, Max: 200
}
```

**Note**: Either `keywords` OR `content_objective` must be provided. If `content_objective` is provided, keywords will be automatically extracted from it.

### Response Structure

```typescript
interface AITopicSuggestionsResponse {
  seed_keywords: string[];
  location: string;
  language: string;
  topic_suggestions: Array<{
    topic: string;                    // Full blog post idea (e.g., "Complete Guide to Concrete Remediation")
    source_keyword: string;            // Primary keyword for the topic
    ai_search_volume: number;          // AI search volume (0 if not available)
    ai_optimization_score: number;     // NEW: AI optimization score (0-100)
    mentions: number;                  // LLM mentions count
    search_volume: number;             // Traditional search volume
    difficulty: number;                // Keyword difficulty (0-100)
    competition: number;               // Competition level (0-1)
    cpc: number;                       // Cost per click
    ranking_score: number;             // Ranking score (0-100)
    opportunity_score: number;         // Opportunity score (0-100)
    estimated_traffic: number;         // Estimated monthly traffic potential
    reason: string;                    // Why this topic would rank well
    related_keywords: string[];        // Related keywords (up to 5)
    url?: string;                      // If from top_cited_pages
    source: "ai_generated" | "llm_mentions" | "top_cited_pages" | "llm_responses";
    confidence?: "high" | "medium" | "low";
  }>;
  content_gaps: Array<{
    keyword: string;
    ai_search_volume: number;
    mentions_count: number;
    opportunity_score: number;
  }>;
  citation_opportunities: Array<{
    keyword: string;
    avg_mentions: number;
    competitor_count: number;
    opportunity: string;
  }>;
  ai_metrics: {
    search_volume?: Record<string, any>;
    llm_mentions?: Record<string, any>;
  };
  summary: {
    total_suggestions: number;
    high_priority_topics: number;      // NEW: High priority topics count
    trending_topics: number;           // NEW: Trending topics count
    low_competition_topics: number;    // NEW: Low competition topics count
    content_gaps_count: number;
    citation_opportunities_count: number;
    top_sources?: Record<string, number>;
  };
}
```

### Example Requests

**Option 1: Using Keywords (Existing Method)**
```typescript
const response = await fetch('/api/v1/keywords/ai-topic-suggestions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    keywords: ['pet grooming', 'dog grooming'],
    location: 'United States',
    language: 'en',
    include_ai_search_volume: true,
    include_llm_mentions: true,
    include_llm_responses: false,
    limit: 50
  })
});

const data = await response.json();
```

**Option 2: Using Content Objective (NEW - Recommended)**
```typescript
const response = await fetch('/api/v1/keywords/ai-topic-suggestions', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    content_objective: 'I want to write articles about concrete remediation or construction remediation',
    target_audience: 'general consumers',
    industry: 'Construction',
    content_goals: ['SEO & Rankings', 'Engagement'],
    location: 'United States',
    language: 'en',
    include_ai_search_volume: true,
    include_llm_mentions: true,
    limit: 50
  })
});

const data = await response.json();
// Keywords will be automatically extracted: ['concrete remediation', 'construction remediation']
```

---

## 💻 Frontend Integration

### React Hook for LLM Mentions

```typescript
import { useState } from 'react';

export function useLLMMentions() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const searchMentions = async (request: {
    target: string;
    target_type?: string;
    location?: string;
    language?: string;
    platform?: string;
    limit?: number;
  }) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        'https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/keywords/ai-mentions',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
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

  return { searchMentions, loading, results, error };
}
```

### React Hook for AI Topic Suggestions

```typescript
export function useAITopicSuggestions() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const getSuggestions = async (request: {
    keywords: string[];
    location?: string;
    language?: string;
    include_ai_search_volume?: boolean;
    include_llm_mentions?: boolean;
    include_llm_responses?: boolean;
    limit?: number;
  }) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        'https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/keywords/ai-topic-suggestions',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
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

  return { getSuggestions, loading, results, error };
}
```

### React Component Example

```typescript
import React, { useState } from 'react';
import { useAITopicSuggestions } from './hooks/useAITopicSuggestions';

export function AITopicSuggestions() {
  const [keywords, setKeywords] = useState<string[]>([]);
  const { getSuggestions, loading, results, error } = useAITopicSuggestions();

  const handleGetSuggestions = async () => {
    if (keywords.length === 0) return;

    await getSuggestions({
      keywords,
      location: 'United States',
      language: 'en',
      include_ai_search_volume: true,
      include_llm_mentions: true,
      include_llm_responses: false,
      limit: 50
    });
  };

  return (
    <div className="ai-topic-suggestions">
      <h2>AI Topic Suggestions</h2>

      {/* Keywords Input */}
      <div className="keywords-input">
        <label>Seed Keywords (comma-separated):</label>
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

      {/* Get Suggestions Button */}
      <button onClick={handleGetSuggestions} disabled={loading || keywords.length === 0}>
        {loading ? 'Getting AI Suggestions...' : 'Get AI Topic Suggestions'}
      </button>

      {/* Error Display */}
      {error && <div className="error">Error: {error}</div>}

      {/* Results Display */}
      {results && (
        <div className="results">
          <h3>AI Topic Suggestions</h3>

          {/* Summary */}
          <div className="summary">
            <p>Total Suggestions: {results.summary.total_suggestions}</p>
            <p>Content Gaps: {results.summary.content_gaps_count}</p>
            <p>Citation Opportunities: {results.summary.citation_opportunities_count}</p>
          </div>

          {/* Topic Suggestions */}
          <div className="topic-suggestions">
            <h4>Suggested Topics:</h4>
            <ul>
              {results.topic_suggestions.map((suggestion: any, idx: number) => (
                <li key={idx}>
                  <strong>{suggestion.topic}</strong>
                  <ul>
                    <li>Source: {suggestion.source}</li>
                    <li>AI Search Volume: {suggestion.ai_search_volume?.toLocaleString()}</li>
                    <li>Mentions: {suggestion.mentions}</li>
                    {suggestion.url && <li>URL: <a href={suggestion.url} target="_blank" rel="noopener noreferrer">{suggestion.url}</a></li>}
                  </ul>
                </li>
              ))}
            </ul>
          </div>

          {/* Content Gaps */}
          {results.content_gaps.length > 0 && (
            <div className="content-gaps">
              <h4>Content Gaps (High Opportunity):</h4>
              <ul>
                {results.content_gaps.map((gap: any, idx: number) => (
                  <li key={idx}>
                    <strong>{gap.keyword}</strong>
                    <ul>
                      <li>AI Search Volume: {gap.ai_search_volume?.toLocaleString()}</li>
                      <li>Mentions: {gap.mentions_count}</li>
                      <li>Opportunity Score: {gap.opportunity_score?.toFixed(2)}</li>
                    </ul>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Citation Opportunities */}
          {results.citation_opportunities.length > 0 && (
            <div className="citation-opportunities">
              <h4>Citation Opportunities:</h4>
              <ul>
                {results.citation_opportunities.map((opp: any, idx: number) => (
                  <li key={idx}>
                    <strong>{opp.keyword}</strong>
                    <ul>
                      <li>Avg Mentions: {opp.avg_mentions}</li>
                      <li>Competitors: {opp.competitor_count}</li>
                      <li>{opp.opportunity}</li>
                    </ul>
                  </li>
                ))}
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

## 🔄 Integration with Goal-Based Routing

The goal-based routing endpoint (`/api/v1/keywords/goal-based-analysis`) now includes LLM Mentions data for all 4 content goals:

### SEO & Rankings
- Includes LLM Mentions to find topics with high AI citation potential
- Optimizes for both traditional search AND AI citations

### Engagement
- Includes LLM Mentions to find topics AI agents frequently discuss
- Creates content that answers AI agent queries

### Conversions
- Includes LLM Mentions to identify commercial topics AI agents cite
- Optimizes product/service content for AI citations

### Brand Awareness ⭐⭐⭐ **MOST CRITICAL**
- Includes comprehensive LLM Mentions analysis
- Tracks brand mentions in AI agent responses
- Finds topics where brand can get cited
- Monitors brand visibility in AI search

---

## 📊 Use Cases

### 1. Topic Discovery for AI Agents

```typescript
// Find topics AI agents are citing
const mentions = await searchMentions({
  target: 'pet grooming',
  target_type: 'keyword',
  platform: 'chat_gpt'
});

// Extract topics from mentions
const topics = mentions.llm_mentions.topics;
```

### 2. Content Gap Analysis

```typescript
// Get AI topic suggestions
const suggestions = await getSuggestions({
  keywords: ['pet grooming'],
  include_llm_mentions: true
});

// Content gaps = High AI search volume but low citations
const gaps = suggestions.content_gaps;
```

### 3. Citation Opportunity Identification

```typescript
// Find citation opportunities
const suggestions = await getSuggestions({
  keywords: ['pet grooming'],
  include_llm_mentions: true
});

// Opportunities = Low competition, high citation potential
const opportunities = suggestions.citation_opportunities;
```

---

## 💡 Best Practices

1. **Use LLM Mentions for Brand Awareness**
   - Most critical use case
   - Track brand visibility in AI search
   - Find topics where brand can get cited

2. **Combine Multiple Sources**
   - Use AI Topic Suggestions endpoint (combines multiple sources)
   - More comprehensive than individual endpoints

3. **Monitor Citation Patterns**
   - Analyze top-cited pages
   - Understand what content format AI agents prefer
   - Optimize content structure accordingly

4. **Focus on Content Gaps**
   - High AI search volume + Low citations = Opportunity
   - Prioritize content creation for these topics

---

## 📚 Related Documentation

- [Goal-Based Keyword Analysis](./FRONTEND_GOAL_BASED_KEYWORD_ANALYSIS.md)
- [AI Topic Recommendations](./FRONTEND_AI_TOPIC_RECOMMENDATIONS.md)
- [Frontend Integration Guide v1.3.5](./FRONTEND_INTEGRATION_V1.3.5.md)

