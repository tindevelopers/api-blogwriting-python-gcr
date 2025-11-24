# Frontend Guide: Complete Keyword Data Structure

**Version:** 1.3.5  
**Date:** 2025-01-15  
**Status:** ✅ Latest - All Discovery & SERP Data Included

---

## 🎯 Overview

This guide documents the **complete data structure** returned by the enhanced keyword analysis endpoints (`/api/v1/keywords/enhanced` and `/api/v1/keywords/enhanced/stream`). All discovery, SERP, and enhanced analysis data is now **always included** (no longer conditional on `include_serp`).

---

## 📡 Endpoints

- **Non-Streaming:** `POST /api/v1/keywords/enhanced`
- **Streaming:** `POST /api/v1/keywords/enhanced/stream` (Server-Sent Events)

Both endpoints return the **same data structure**.

---

## 📊 Complete Response Structure

```typescript
interface EnhancedKeywordAnalysisResponse {
  // Core keyword analysis per keyword
  enhanced_analysis: Record<string, KeywordAnalysis>;
  
  // Summary data
  total_keywords: number;
  original_keywords: string[];
  suggested_keywords: string[];
  
  // Clustering data
  clusters: KeywordCluster[];
  cluster_summary: {
    total_keywords: number;
    cluster_count: number;
    unclustered_count: number;
  };
  
  // Location data
  location: {
    used: string;                    // Location used for analysis
    detected_from_ip: boolean;        // Was location auto-detected?
    specified: boolean;               // Was location manually specified?
  };
  
  // 🆕 DISCOVERY DATA (Always included)
  discovery: {
    matching_terms: MatchingTerm[];   // Matching keywords (like Ahrefs "Matching terms")
    questions: QuestionKeyword[];     // Question-type keywords
    related_terms: RelatedTerm[];     // Related keywords from keyword ideas
  };
  
  // 🆕 SERP ANALYSIS (Always included)
  serp_analysis: {
    keyword: string;
    organic_results: OrganicResult[];
    people_also_ask: PeopleAlsoAsk[];
    featured_snippet?: FeaturedSnippet;
    video_results: VideoResult[];
    image_results: ImageResult[];
    related_searches: string[];
    top_domains: DomainInfo[];
    competition_level: string;
    content_gaps: string[];
    serp_features: {
      has_featured_snippet: boolean;
      has_people_also_ask: boolean;
      has_videos: boolean;
      has_images: boolean;
    };
  };
}
```

---

## 🔍 Detailed Type Definitions

### KeywordAnalysis (per keyword)

```typescript
interface KeywordAnalysis {
  // Basic metrics
  search_volume: number;              // Monthly search volume
  global_search_volume: number;        // Global monthly searches
  search_volume_by_country?: Record<string, number>;
  monthly_searches?: Array<{
    year: number;
    month: number;
    search_volume: number;
  }>;
  
  // Difficulty & competition
  difficulty: string;                  // "VERY_EASY" | "EASY" | "MEDIUM" | "HARD" | "VERY_HARD"
  difficulty_score: number;           // 0-100 numeric score
  competition: number;                 // 0.0-1.0
  
  // Cost metrics
  cpc: number;                         // Cost per click (USD)
  cpc_currency: string | null;
  cps?: number;                       // Cost per sale
  clicks?: number;                     // Estimated monthly clicks
  
  // Trends
  trend_score: number;                 // -1.0 to 1.0
  
  // Recommendations
  recommended: boolean;
  reason: string;
  
  // 🆕 RELATED KEYWORDS
  related_keywords: string[];          // Basic related keywords (strings only, no metrics)
  related_keywords_enhanced: Array<{  // Enhanced with full metrics
    keyword: string;
    search_volume: number;
    cpc: number;
    competition: number;
    difficulty_score: number;
    difficulty?: string;
  }>;
  
  // 🆕 LONG-TAIL KEYWORDS
  long_tail_keywords: string[];       // Long-tail variations (strings only)
  
  // 🆕 QUESTION & TOPIC KEYWORDS (with metrics)
  questions: Array<{
    keyword: string;
    search_volume: number;
    cpc: number;
    competition: number;
    difficulty_score: number;
    difficulty?: string;
  }>;
  
  topics: Array<{
    keyword: string;
    search_volume: number;
    cpc: number;
    competition: number;
    difficulty_score: number;
    difficulty?: string;
  }>;
  
  keyword_ideas: Array<{              // All keyword ideas combined
    keyword: string;
    search_volume: number;
    cpc: number;
    competition: number;
    difficulty_score: number;
    difficulty?: string;
  }>;
  
  // Clustering
  parent_topic: string;
  category_type: string;
  cluster_score: number;
  
  // AI Optimization
  ai_search_volume?: number;
  ai_trend?: number;
  ai_monthly_searches?: Array<any>;
  
  // 🆕 ALSO RANK FOR / ALSO TALK ABOUT
  also_rank_for?: string[];           // Keywords that also rank for (like Ahrefs)
  also_talk_about?: string[];         // Topics that also talk about (like Ahrefs)
  
  // Additional SEO
  traffic_potential?: number;
  serp_features?: Record<string, any>;
  serp_feature_counts?: Record<string, number>;
  primary_intent?: string;
  intent_probabilities?: Record<string, number>;
  top_competitors?: Array<{
    domain: string;
    rank: number;
  }>;
  first_seen?: string;
  last_updated?: string;
}
```

### Discovery Data Types

```typescript
// Matching terms (like Ahrefs "Matching terms" section)
interface MatchingTerm {
  keyword: string;
  search_volume: number;
  keyword_difficulty: number;
  cpc: number;
  competition: number;
  parent_topic?: string;
  intent?: string;
}

// Question keywords extracted from matching terms
interface QuestionKeyword {
  keyword: string;
  search_volume: number;
  keyword_difficulty: number;
  cpc: number;
  competition: number;
  parent_topic?: string;
  intent?: string;
}

// Related terms from keyword ideas
interface RelatedTerm {
  keyword: string;
  search_volume: number;
  keyword_difficulty: number;
  cpc: number;
  competition: number;
  parent_topic?: string;
  intent?: string;
}
```

### SERP Analysis Types

```typescript
interface OrganicResult {
  title: string;
  url: string;
  domain: string;
  snippet: string;
  position: number;
}

interface PeopleAlsoAsk {
  question: string;
  snippet: string;
  url?: string;
}

interface FeaturedSnippet {
  title: string;
  snippet: string;
  url: string;
}

interface VideoResult {
  title: string;
  url: string;
  thumbnail: string;
  duration?: string;
}

interface ImageResult {
  title: string;
  url: string;
  thumbnail: string;
}

interface DomainInfo {
  domain: string;
  rank: number;
  backlinks?: number;
}
```

---

## 💻 Frontend Usage Examples

### 1. Access Discovery Data (Matching Terms, Questions, Related Terms)

```typescript
const response = await fetch('/api/v1/keywords/enhanced', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    keywords: ['pet grooming miami'],
    location: 'United States'
  })
});

const data: EnhancedKeywordAnalysisResponse = await response.json();

// Access matching terms (like Ahrefs "Matching terms")
const matchingTerms = data.discovery?.matching_terms || [];
console.log(`Found ${matchingTerms.length} matching terms`);
matchingTerms.forEach(term => {
  console.log(`${term.keyword}: ${term.search_volume} searches, KD: ${term.keyword_difficulty}`);
});

// Access questions
const questions = data.discovery?.questions || [];
console.log(`Found ${questions.length} question keywords`);
questions.forEach(q => {
  console.log(`Q: ${q.keyword} (${q.search_volume} searches)`);
});

// Access related terms
const relatedTerms = data.discovery?.related_terms || [];
console.log(`Found ${relatedTerms.length} related terms`);
```

### 2. Access SERP Analysis (People Also Ask, Organic Results)

```typescript
const serpAnalysis = data.serp_analysis;

// People Also Ask questions
const paaQuestions = serpAnalysis?.people_also_ask || [];
console.log(`Found ${paaQuestions.length} People Also Ask questions`);
paaQuestions.forEach(paa => {
  console.log(`PAA: ${paa.question}`);
  console.log(`Answer: ${paa.snippet}`);
});

// Top organic results
const organicResults = serpAnalysis?.organic_results || [];
console.log(`Top ${organicResults.length} organic results:`);
organicResults.slice(0, 10).forEach((result, index) => {
  console.log(`${index + 1}. ${result.title}`);
  console.log(`   ${result.url}`);
  console.log(`   ${result.snippet}`);
});

// Featured snippet
if (serpAnalysis?.featured_snippet) {
  console.log('Featured Snippet:', serpAnalysis.featured_snippet.title);
  console.log(serpAnalysis.featured_snippet.snippet);
}

// SERP features detected
const features = serpAnalysis?.serp_features || {};
console.log('SERP Features:', {
  hasFeaturedSnippet: features.has_featured_snippet,
  hasPeopleAlsoAsk: features.has_people_also_ask,
  hasVideos: features.has_videos,
  hasImages: features.has_images
});
```

### 3. Access Enhanced Analysis Per Keyword

```typescript
const keyword = 'pet grooming miami';
const analysis = data.enhanced_analysis[keyword];

if (analysis) {
  // Also rank for (like Ahrefs "Also rank for")
  const alsoRankFor = analysis.also_rank_for || [];
  console.log(`Keywords that also rank for "${keyword}":`, alsoRankFor);
  
  // Also talk about (like Ahrefs "Also talk about")
  const alsoTalkAbout = analysis.also_talk_about || [];
  console.log(`Topics that also talk about "${keyword}":`, alsoTalkAbout);
  
  // Long-tail keywords
  const longTail = analysis.long_tail_keywords || [];
  console.log(`Long-tail variations:`, longTail);
  
  // Questions with metrics
  const questions = analysis.questions || [];
  console.log(`Question keywords:`, questions.map(q => ({
    question: q.keyword,
    volume: q.search_volume,
    difficulty: q.difficulty_score
  })));
  
  // Topics with metrics
  const topics = analysis.topics || [];
  console.log(`Topic keywords:`, topics.map(t => ({
    topic: t.keyword,
    volume: t.search_volume,
    difficulty: t.difficulty_score
  })));
  
  // Related keywords with metrics
  const relatedEnhanced = analysis.related_keywords_enhanced || [];
  console.log(`Related keywords (with metrics):`, relatedEnhanced);
}
```

### 4. Complete React Component Example

```typescript
import React, { useState, useEffect } from 'react';
import { EnhancedKeywordAnalysisResponse } from './types';

function KeywordAnalysisDisplay({ keyword }: { keyword: string }) {
  const [data, setData] = useState<EnhancedKeywordAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const response = await fetch('/api/v1/keywords/enhanced', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            keywords: [keyword],
            location: 'United States'
          })
        });
        const result = await response.json();
        setData(result);
      } catch (error) {
        console.error('Failed to fetch keyword data:', error);
      } finally {
        setLoading(false);
      }
    };

    if (keyword) {
      fetchData();
    }
  }, [keyword]);

  if (loading) return <div>Loading...</div>;
  if (!data) return null;

  const analysis = data.enhanced_analysis[keyword];
  const discovery = data.discovery || {};
  const serp = data.serp_analysis || {};

  return (
    <div className="keyword-analysis">
      {/* Main Keyword Metrics */}
      <div className="metrics-grid">
        <MetricCard
          label="Search Volume"
          value={analysis?.search_volume || 0}
        />
        <MetricCard
          label="Difficulty"
          value={analysis?.difficulty_score || 0}
          max={100}
        />
        <MetricCard
          label="CPC"
          value={`$${analysis?.cpc?.toFixed(2) || '0.00'}`}
        />
      </div>

      {/* Matching Terms (like Ahrefs) */}
      {discovery.matching_terms && discovery.matching_terms.length > 0 && (
        <Section title="Matching Terms">
          <KeywordList keywords={discovery.matching_terms} />
        </Section>
      )}

      {/* People Also Ask */}
      {serp.people_also_ask && serp.people_also_ask.length > 0 && (
        <Section title="People Also Ask">
          {serp.people_also_ask.map((paa, idx) => (
            <div key={idx} className="paa-item">
              <h4>{paa.question}</h4>
              <p>{paa.snippet}</p>
            </div>
          ))}
        </Section>
      )}

      {/* Also Rank For */}
      {analysis?.also_rank_for && analysis.also_rank_for.length > 0 && (
        <Section title="Also Rank For">
          <KeywordList keywords={analysis.also_rank_for.map(kw => ({ keyword: kw }))} />
        </Section>
      )}

      {/* Also Talk About */}
      {analysis?.also_talk_about && analysis.also_talk_about.length > 0 && (
        <Section title="Also Talk About">
          <KeywordList keywords={analysis.also_talk_about.map(kw => ({ keyword: kw }))} />
        </Section>
      )}

      {/* Long-Tail Keywords */}
      {analysis?.long_tail_keywords && analysis.long_tail_keywords.length > 0 && (
        <Section title="Long-Tail Keywords">
          <KeywordList keywords={analysis.long_tail_keywords.map(kw => ({ keyword: kw }))} />
        </Section>
      )}

      {/* Questions */}
      {analysis?.questions && analysis.questions.length > 0 && (
        <Section title="Question Keywords">
          <KeywordList keywords={analysis.questions} />
        </Section>
      )}

      {/* Top Organic Results */}
      {serp.organic_results && serp.organic_results.length > 0 && (
        <Section title="Top Organic Results">
          {serp.organic_results.slice(0, 10).map((result, idx) => (
            <div key={idx} className="organic-result">
              <h4>{result.title}</h4>
              <a href={result.url} target="_blank" rel="noopener noreferrer">
                {result.domain}
              </a>
              <p>{result.snippet}</p>
            </div>
          ))}
        </Section>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="section">
      <h3>{title}</h3>
      {children}
    </div>
  );
}

function KeywordList({ keywords }: { keywords: Array<{ keyword: string; search_volume?: number }> }) {
  return (
    <ul>
      {keywords.map((kw, idx) => (
        <li key={idx}>
          {kw.keyword}
          {kw.search_volume !== undefined && (
            <span className="volume"> ({kw.search_volume} searches)</span>
          )}
        </li>
      ))}
    </ul>
  );
}

function MetricCard({ label, value, max }: { label: string; value: number | string; max?: number }) {
  return (
    <div className="metric-card">
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      {max && (
        <div className="metric-bar">
          <div
            className="metric-fill"
            style={{ width: `${(Number(value) / max) * 100}%` }}
          />
        </div>
      )}
    </div>
  );
}
```

### 5. Streaming Endpoint Example

```typescript
async function streamKeywordAnalysis(keywords: string[]) {
  const response = await fetch('/api/v1/keywords/enhanced/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ keywords, location: 'United States' })
  });

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  let finalResult: EnhancedKeywordAnalysisResponse | null = null;

  while (reader) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value, { stream: true });
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const update = JSON.parse(line.slice(6));
        
        // Update progress
        if (update.stage === 'analyzing_serp') {
          console.log(`SERP Analysis: ${update.message}`);
          console.log(`Found ${update.data?.matching_terms_count} matching terms`);
          console.log(`Found ${update.data?.people_also_ask_count} PAA questions`);
        }
        
        // Capture final result
        if (update.stage === 'completed' && update.data?.result) {
          finalResult = update.data.result;
        }
      }
    }
  }

  // Use final result
  if (finalResult) {
    console.log('Matching Terms:', finalResult.discovery?.matching_terms);
    console.log('People Also Ask:', finalResult.serp_analysis?.people_also_ask);
    console.log('Also Rank For:', finalResult.enhanced_analysis[keywords[0]]?.also_rank_for);
  }

  return finalResult;
}
```

---

## 📋 Data Availability Summary

| Data Type | Location | Always Included? | Notes |
|-----------|----------|-------------------|-------|
| **Matching Terms** | `discovery.matching_terms` | ✅ Yes | Like Ahrefs "Matching terms" |
| **Questions** | `discovery.questions` | ✅ Yes | Extracted from matching terms |
| **Related Terms** | `discovery.related_terms` | ✅ Yes | From keyword ideas API |
| **People Also Ask** | `serp_analysis.people_also_ask` | ✅ Yes | From SERP analysis |
| **Organic Results** | `serp_analysis.organic_results` | ✅ Yes | Top 10-20 results |
| **Featured Snippet** | `serp_analysis.featured_snippet` | ✅ Yes | If present |
| **Also Rank For** | `enhanced_analysis[keyword].also_rank_for` | ✅ Yes | Per keyword |
| **Also Talk About** | `enhanced_analysis[keyword].also_talk_about` | ✅ Yes | Per keyword |
| **Long-Tail Keywords** | `enhanced_analysis[keyword].long_tail_keywords` | ✅ Yes | Per keyword |
| **Questions (with metrics)** | `enhanced_analysis[keyword].questions` | ✅ Yes | Per keyword, with metrics |
| **Topics (with metrics)** | `enhanced_analysis[keyword].topics` | ✅ Yes | Per keyword, with metrics |

---

## 🎯 Key Points

1. **All discovery and SERP data is now ALWAYS included** - no need to set `include_serp: true`
2. **Matching terms** are in `discovery.matching_terms` (like Ahrefs "Matching terms")
3. **People Also Ask** are in `serp_analysis.people_also_ask`
4. **Also Rank For** and **Also Talk About** are per-keyword in `enhanced_analysis[keyword]`
5. **Long-tail keywords** are per-keyword in `enhanced_analysis[keyword].long_tail_keywords`
6. **Questions and Topics** have full metrics when available

---

## 🔗 Related Documentation

- `FRONTEND_INTEGRATION_V1.3.5.md` - Complete frontend integration guide
- `FRONTEND_KEYWORD_STREAMING_GUIDE.md` - Streaming endpoint guide
- `BACKEND_KEYWORD_ENDPOINT_RECOMMENDATIONS.md` - Backend improvements roadmap

