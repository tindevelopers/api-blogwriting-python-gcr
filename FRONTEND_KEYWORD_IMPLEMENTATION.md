# Frontend Implementation Guide: Keyword Research Endpoints

**Version:** 1.3.5  
**Date:** 2025-01-15  
**API Base URL:** `https://blog-writer-api-dev-kq42l26tuq-od.a.run.app`

---

## 🎯 Overview

This guide provides complete frontend implementation instructions for the keyword research endpoints, including:
- Enhanced keyword analysis (with AI metrics, discovery, SERP data)
- Streaming keyword analysis (real-time progress updates)
- Complete data structure and TypeScript types

---

## 📡 Endpoints

### 1. Enhanced Keyword Analysis
**Endpoint:** `POST /api/v1/keywords/enhanced`  
**Response:** Complete keyword analysis with AI metrics, discovery data, and SERP analysis

### 2. Streaming Keyword Analysis
**Endpoint:** `POST /api/v1/keywords/enhanced/stream`  
**Response:** Server-Sent Events (SSE) stream with real-time progress updates

---

## 🚀 Quick Start Implementation

### Step 1: Install Dependencies

```bash
npm install axios  # or use fetch API
```

### Step 2: Create API Client

```typescript
// lib/api/keywords.ts

const API_BASE_URL = 'https://blog-writer-api-dev-kq42l26tuq-od.a.run.app';

export interface EnhancedKeywordRequest {
  keywords: string[];
  location?: string;
  language?: string;
  include_serp?: boolean;
  max_suggestions_per_keyword?: number;
}

export interface KeywordAnalysis {
  search_volume: number;
  global_search_volume: number;
  difficulty: string;
  difficulty_score: number;
  competition: number;
  cpc: number;
  cpc_currency: string | null;
  trend_score: number;
  
  // AI Metrics
  ai_search_volume: number;
  ai_trend: number;
  ai_monthly_searches: Array<{
    year: number;
    month: number;
    search_volume: number;
  }>;
  
  // Related Keywords
  related_keywords: string[];
  related_keywords_enhanced: Array<{
    keyword: string;
    search_volume: number;
    cpc: number;
    competition: number;
    difficulty_score: number;
  }>;
  
  // Long-tail & Variations
  long_tail_keywords: string[];
  
  // Questions & Topics (with metrics)
  questions: Array<{
    keyword: string;
    search_volume: number;
    cpc: number;
    competition: number;
    difficulty_score: number;
  }>;
  
  topics: Array<{
    keyword: string;
    search_volume: number;
    cpc: number;
    competition: number;
    difficulty_score: number;
  }>;
  
  // Also Rank For / Also Talk About
  also_rank_for?: string[];
  also_talk_about?: string[];
  
  // Clustering
  parent_topic: string;
  category_type: string;
  cluster_score: number;
  
  // Additional
  recommended: boolean;
  reason: string;
  traffic_potential?: number;
  serp_features?: Record<string, any>;
  primary_intent?: string;
}

export interface MatchingTerm {
  keyword: string;
  search_volume: number;
  keyword_difficulty: number;
  cpc: number;
  competition: number;
  parent_topic?: string;
  intent?: string;
}

export interface PeopleAlsoAsk {
  question: string;
  snippet: string;
  url?: string;
}

export interface EnhancedKeywordResponse {
  enhanced_analysis: Record<string, KeywordAnalysis>;
  total_keywords: number;
  original_keywords: string[];
  suggested_keywords: string[];
  clusters: Array<{
    parent_topic: string;
    keywords: string[];
    cluster_score: number;
    category_type: string;
    keyword_count: number;
  }>;
  cluster_summary: {
    total_keywords: number;
    cluster_count: number;
    unclustered_count: number;
  };
  location: {
    used: string;
    detected_from_ip: boolean;
    specified: boolean;
  };
  discovery: {
    matching_terms: MatchingTerm[];
    questions: MatchingTerm[];
    related_terms: MatchingTerm[];
  };
  serp_analysis: {
    keyword: string;
    organic_results: Array<{
      title: string;
      url: string;
      domain: string;
      snippet: string;
      position: number;
    }>;
    people_also_ask: PeopleAlsoAsk[];
    featured_snippet?: {
      title: string;
      snippet: string;
      url: string;
    };
    video_results: Array<{
      title: string;
      url: string;
      thumbnail: string;
    }>;
    image_results: Array<{
      title: string;
      url: string;
      thumbnail: string;
    }>;
    related_searches: string[];
    serp_features: {
      has_featured_snippet: boolean;
      has_people_also_ask: boolean;
      has_videos: boolean;
      has_images: boolean;
    };
  };
}

export async function analyzeKeywordsEnhanced(
  request: EnhancedKeywordRequest
): Promise<EnhancedKeywordResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/keywords/enhanced`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}
```

---

## 💻 React Hook Implementation

### Enhanced Keywords Hook

```typescript
// hooks/useKeywordAnalysis.ts

import { useState, useCallback } from 'react';
import { analyzeKeywordsEnhanced, EnhancedKeywordResponse } from '@/lib/api/keywords';

export function useKeywordAnalysis() {
  const [data, setData] = useState<EnhancedKeywordResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyze = useCallback(async (
    keywords: string[],
    location: string = 'United States',
    language: string = 'en'
  ) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await analyzeKeywordsEnhanced({
        keywords,
        location,
        language,
      });
      setData(result);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    data,
    loading,
    error,
    analyze,
  };
}
```

---

## 🎨 React Component Examples

### 1. Complete Keyword Analysis Display

```typescript
// components/KeywordAnalysis.tsx

import React from 'react';
import { useKeywordAnalysis } from '@/hooks/useKeywordAnalysis';

interface KeywordAnalysisProps {
  keyword: string;
  location?: string;
}

export function KeywordAnalysis({ keyword, location = 'United States' }: KeywordAnalysisProps) {
  const { data, loading, error, analyze } = useKeywordAnalysis();

  React.useEffect(() => {
    analyze([keyword], location);
  }, [keyword, location, analyze]);

  if (loading) return <div>Loading keyword analysis...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!data) return null;

  const analysis = data.enhanced_analysis[keyword];
  const discovery = data.discovery;
  const serp = data.serp_analysis;

  return (
    <div className="keyword-analysis">
      {/* Main Metrics */}
      <div className="metrics-grid">
        <MetricCard label="Search Volume" value={analysis.search_volume} />
        <MetricCard label="AI Search Volume" value={analysis.ai_search_volume} />
        <MetricCard label="Difficulty" value={analysis.difficulty_score} max={100} />
        <MetricCard label="CPC" value={`$${analysis.cpc.toFixed(2)}`} />
      </div>

      {/* Matching Terms */}
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
      {analysis.also_rank_for && analysis.also_rank_for.length > 0 && (
        <Section title="Also Rank For">
          <KeywordChips keywords={analysis.also_rank_for} />
        </Section>
      )}

      {/* Also Talk About */}
      {analysis.also_talk_about && analysis.also_talk_about.length > 0 && (
        <Section title="Also Talk About">
          <KeywordChips keywords={analysis.also_talk_about} />
        </Section>
      )}

      {/* Long-Tail Keywords */}
      {analysis.long_tail_keywords && analysis.long_tail_keywords.length > 0 && (
        <Section title="Long-Tail Keywords">
          <KeywordList keywords={analysis.long_tail_keywords.map(kw => ({ keyword: kw }))} />
        </Section>
      )}

      {/* Questions */}
      {analysis.questions && analysis.questions.length > 0 && (
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

function KeywordChips({ keywords }: { keywords: string[] }) {
  return (
    <div className="keyword-chips">
      {keywords.map((kw, idx) => (
        <span key={idx} className="chip">{kw}</span>
      ))}
    </div>
  );
}
```

---

## 🔄 Streaming Implementation

### Streaming Hook

```typescript
// hooks/useKeywordStream.ts

import { useState, useCallback, useRef } from 'react';

export interface StreamUpdate {
  stage: string;
  progress: number;
  message?: string;
  data?: any;
  timestamp: number;
}

export function useKeywordStream() {
  const [stage, setStage] = useState<string>('initializing');
  const [progress, setProgress] = useState<number>(0);
  const [message, setMessage] = useState<string>('');
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const startStream = useCallback(async (
    keywords: string[],
    location: string = 'United States',
    language: string = 'en'
  ) => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    setProgress(0);
    setStage('initializing');

    // Cancel previous stream if exists
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/keywords/enhanced/stream`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            keywords,
            location,
            language,
          }),
          signal: abortControllerRef.current.signal,
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('Response body is not readable');
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const update: StreamUpdate = JSON.parse(line.slice(6));
              
              setStage(update.stage);
              setProgress(update.progress);
              if (update.message) setMessage(update.message);

              // Handle completion
              if (update.stage === 'completed' && update.data?.result) {
                setResult(update.data.result);
                setIsLoading(false);
                return update.data.result;
              }

              // Handle errors
              if (update.stage === 'error') {
                setError(update.data?.error || 'Unknown error');
                setIsLoading(false);
                throw new Error(update.data?.error || 'Unknown error');
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        // Stream was cancelled, ignore
        return;
      }
      setError(err instanceof Error ? err.message : 'Unknown error');
      setIsLoading(false);
      throw err;
    }
  }, []);

  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsLoading(false);
    }
  }, []);

  return {
    stage,
    progress,
    message,
    result,
    error,
    isLoading,
    startStream,
    cancel,
  };
}
```

### Streaming Component

```typescript
// components/KeywordStreamAnalysis.tsx

import React from 'react';
import { useKeywordStream } from '@/hooks/useKeywordStream';

export function KeywordStreamAnalysis({ keyword }: { keyword: string }) {
  const {
    stage,
    progress,
    message,
    result,
    error,
    isLoading,
    startStream,
    cancel,
  } = useKeywordStream();

  const handleStart = () => {
    startStream([keyword], 'United States', 'en');
  };

  return (
    <div className="keyword-stream-analysis">
      <button onClick={handleStart} disabled={isLoading}>
        {isLoading ? 'Analyzing...' : 'Start Analysis'}
      </button>
      
      {isLoading && (
        <div className="progress-section">
          <div className="stage-label">{stage}</div>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="progress-text">{progress.toFixed(1)}%</div>
          <div className="message">{message}</div>
        </div>
      )}

      {result && (
        <div className="results">
          <h3>Analysis Complete!</h3>
          {/* Display results same as KeywordAnalysis component */}
        </div>
      )}

      {error && (
        <div className="error">
          Error: {error}
        </div>
      )}

      {isLoading && (
        <button onClick={cancel}>Cancel</button>
      )}
    </div>
  );
}
```

---

## 📊 Data Access Examples

### Access Matching Terms

```typescript
const { data } = useKeywordAnalysis();

// Matching terms (like Ahrefs "Matching terms")
const matchingTerms = data?.discovery?.matching_terms || [];
matchingTerms.forEach(term => {
  console.log(`${term.keyword}: ${term.search_volume} searches, KD: ${term.keyword_difficulty}`);
});
```

### Access People Also Ask

```typescript
const paaQuestions = data?.serp_analysis?.people_also_ask || [];
paaQuestions.forEach(paa => {
  console.log(`Q: ${paa.question}`);
  console.log(`A: ${paa.snippet}`);
});
```

### Access Also Rank For / Also Talk About

```typescript
const analysis = data?.enhanced_analysis[keyword];

// Also Rank For (like Ahrefs)
const alsoRankFor = analysis?.also_rank_for || [];
console.log('Keywords that also rank for:', alsoRankFor);

// Also Talk About (like Ahrefs)
const alsoTalkAbout = analysis?.also_talk_about || [];
console.log('Topics that also talk about:', alsoTalkAbout);
```

### Access Long-Tail Keywords

```typescript
const longTail = analysis?.long_tail_keywords || [];
console.log('Long-tail variations:', longTail);
```

### Access Questions & Topics (with metrics)

```typescript
// Questions with full metrics
const questions = analysis?.questions || [];
questions.forEach(q => {
  console.log(`Q: ${q.keyword} (${q.search_volume} searches, KD: ${q.difficulty_score})`);
});

// Topics with full metrics
const topics = analysis?.topics || [];
topics.forEach(t => {
  console.log(`Topic: ${t.keyword} (${t.search_volume} searches)`);
});
```

---

## 🎨 CSS Styling Examples

```css
/* components/KeywordAnalysis.css */

.keyword-analysis {
  padding: 20px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.metric-card {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.metric-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.metric-bar {
  height: 4px;
  background: #e0e0e0;
  border-radius: 2px;
  margin-top: 8px;
}

.metric-fill {
  height: 100%;
  background: #6366f1;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.section {
  margin-bottom: 32px;
}

.section h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #333;
}

.keyword-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  background: #f3f4f6;
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 14px;
  color: #374151;
}

.paa-item {
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.paa-item h4 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #111;
}

.paa-item p {
  color: #666;
  font-size: 14px;
}

.organic-result {
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.organic-result h4 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
  color: #1a0dab;
}

.organic-result a {
  color: #006621;
  font-size: 14px;
  text-decoration: none;
}

.organic-result p {
  color: #545454;
  font-size: 14px;
  margin-top: 8px;
}

/* Streaming progress */
.progress-section {
  margin: 24px 0;
}

.stage-label {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  text-transform: capitalize;
}

.progress-bar {
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 14px;
  color: #666;
  margin-bottom: 4px;
}

.message {
  font-size: 14px;
  color: #666;
  font-style: italic;
}
```

---

## ✅ Complete Implementation Checklist

- [ ] Install dependencies (`axios` or use native `fetch`)
- [ ] Create API client (`lib/api/keywords.ts`)
- [ ] Define TypeScript types
- [ ] Create `useKeywordAnalysis` hook
- [ ] Create `useKeywordStream` hook (optional, for streaming)
- [ ] Create `KeywordAnalysis` component
- [ ] Create `KeywordStreamAnalysis` component (optional)
- [ ] Add CSS styling
- [ ] Test with sample keywords
- [ ] Handle error states
- [ ] Add loading states
- [ ] Display all data sections:
  - [ ] Main metrics (search volume, difficulty, CPC)
  - [ ] Matching terms
  - [ ] People Also Ask
  - [ ] Also Rank For
  - [ ] Also Talk About
  - [ ] Long-tail keywords
  - [ ] Questions & Topics
  - [ ] Organic results

---

## 🧪 Testing

```typescript
// Test the endpoint
const testKeyword = async () => {
  const result = await analyzeKeywordsEnhanced({
    keywords: ['pet grooming miami'],
    location: 'United States',
    language: 'en',
  });
  
  console.log('Matching Terms:', result.discovery.matching_terms);
  console.log('People Also Ask:', result.serp_analysis.people_also_ask);
  console.log('Also Rank For:', result.enhanced_analysis['pet grooming miami'].also_rank_for);
};
```

---

## 📚 Additional Resources

- **Complete Data Guide:** `FRONTEND_KEYWORD_DATA_GUIDE.md`
- **Quick Reference:** `FRONTEND_KEYWORD_QUICK_REFERENCE.md`
- **Streaming Guide:** `FRONTEND_KEYWORD_STREAMING_GUIDE.md`
- **API Documentation:** `https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/docs`

