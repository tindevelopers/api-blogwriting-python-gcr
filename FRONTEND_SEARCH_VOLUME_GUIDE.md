# Frontend Guide: Getting Search Volume Data

**Version**: 1.2.0  
**Date**: 2025-11-12

---

## Endpoint: Search Volume Data

### `POST /api/v1/keywords/enhanced`

This endpoint returns comprehensive keyword analysis including **search volume** for each keyword.

---

## API Endpoint Details

### Request

**URL:** `https://blog-writer-api-dev-613248238610.europe-west1.run.app/api/v1/keywords/enhanced`

**Method:** `POST`

**Headers:**
```typescript
{
  "Content-Type": "application/json"
}
```

**Request Body:**
```typescript
{
  keywords: string[];                    // Required: Array of keywords (1-200)
  location?: string;                      // Optional: Default "United States"
  language?: string;                     // Optional: Default "en"
  include_serp?: boolean;                // Optional: Default false
  max_suggestions_per_keyword?: number;  // Optional: Default 20, max 150
}
```

**Example Request:**
```json
{
  "keywords": ["pet grooming", "dog care", "pet health"],
  "location": "United States",
  "language": "en",
  "max_suggestions_per_keyword": 150
}
```

---

## Response Structure

### Success Response (200 OK)

```typescript
{
  enhanced_analysis: {
    [keyword: string]: {
      search_volume: number;              // ✅ Monthly search volume
      difficulty: string;                  // "easy" | "medium" | "hard"
      competition: number;                 // 0.0 - 1.0
      cpc: number;                         // Cost per click (USD)
      trend_score: number;                  // -1.0 to 1.0
      recommended: boolean;
      reason: string;
      related_keywords: string[];
      long_tail_keywords: string[];
      parent_topic: string;
      category_type: string;               // "topic" | "question" | "action"
      cluster_score: number;               // 0.0 - 1.0
    }
  },
  clusters: Array<{
    parent_topic: string;
    keywords: string[];
    cluster_score: number;
    category_type: string;
    keyword_count: number;
  }>,
  cluster_summary: {
    total_keywords: number;
    cluster_count: number;
    unclustered_count: number;
  },
  total_keywords: number;
  original_keywords: string[];
  suggested_keywords: string[];
}
```

### Error Response (400/500)

```typescript
{
  detail: string;  // Error message
}
```

---

## Frontend Integration

### TypeScript Types

```typescript
// Request types
interface EnhancedKeywordAnalysisRequest {
  keywords: string[];
  location?: string;
  language?: string;
  include_serp?: boolean;
  max_suggestions_per_keyword?: number;
}

// Response types
interface KeywordAnalysis {
  search_volume: number;              // Monthly search volume
  difficulty: string;                 // "easy" | "medium" | "hard"
  competition: number;                 // 0.0 - 1.0
  cpc: number;                         // Cost per click
  trend_score: number;                 // -1.0 to 1.0
  recommended: boolean;
  reason: string;
  related_keywords: string[];
  long_tail_keywords: string[];
  parent_topic: string;
  category_type: string;
  cluster_score: number;
}

interface EnhancedKeywordAnalysisResponse {
  enhanced_analysis: Record<string, KeywordAnalysis>;
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
  total_keywords: number;
  original_keywords: string[];
  suggested_keywords: string[];
}
```

### API Client Function

```typescript
class KeywordAnalysisClient {
  private apiUrl: string;

  constructor(apiUrl: string = 'https://blog-writer-api-dev-613248238610.europe-west1.run.app') {
    this.apiUrl = apiUrl;
  }

  /**
   * Get search volume and comprehensive keyword analysis
   */
  async getKeywordAnalysis(
    keywords: string[],
    options: {
      location?: string;
      language?: string;
      max_suggestions_per_keyword?: number;
    } = {}
  ): Promise<EnhancedKeywordAnalysisResponse> {
    const response = await fetch(`${this.apiUrl}/api/v1/keywords/enhanced`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        keywords,
        location: options.location || 'United States',
        language: options.language || 'en',
        max_suggestions_per_keyword: options.max_suggestions_per_keyword || 150,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Keyword analysis failed: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Get search volume for a single keyword
   */
  async getSearchVolume(
    keyword: string,
    location: string = 'United States',
    language: string = 'en'
  ): Promise<number | null> {
    try {
      const analysis = await this.getKeywordAnalysis([keyword], { location, language });
      return analysis.enhanced_analysis[keyword]?.search_volume || null;
    } catch (error) {
      console.error(`Failed to get search volume for "${keyword}":`, error);
      return null;
    }
  }

  /**
   * Get search volume for multiple keywords
   */
  async getSearchVolumes(
    keywords: string[],
    location: string = 'United States',
    language: string = 'en'
  ): Promise<Record<string, number>> {
    try {
      const analysis = await this.getKeywordAnalysis(keywords, { location, language });
      const volumes: Record<string, number> = {};
      
      for (const keyword of keywords) {
        volumes[keyword] = analysis.enhanced_analysis[keyword]?.search_volume || 0;
      }
      
      return volumes;
    } catch (error) {
      console.error('Failed to get search volumes:', error);
      return {};
    }
  }
}
```

---

## React Hook Example

```typescript
import { useState, useCallback } from 'react';

interface UseKeywordAnalysisReturn {
  analyzing: boolean;
  analysis: EnhancedKeywordAnalysisResponse | null;
  error: string | null;
  analyzeKeywords: (keywords: string[], options?: {
    location?: string;
    language?: string;
    max_suggestions_per_keyword?: number;
  }) => Promise<void>;
  getSearchVolume: (keyword: string) => number | null;
  reset: () => void;
}

export function useKeywordAnalysis(apiUrl?: string): UseKeywordAnalysisReturn {
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<EnhancedKeywordAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const client = new KeywordAnalysisClient(apiUrl);

  const analyzeKeywords = useCallback(async (
    keywords: string[],
    options: {
      location?: string;
      language?: string;
      max_suggestions_per_keyword?: number;
    } = {}
  ) => {
    setAnalyzing(true);
    setError(null);
    try {
      const result = await client.getKeywordAnalysis(keywords, options);
      setAnalysis(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setAnalysis(null);
    } finally {
      setAnalyzing(false);
    }
  }, [apiUrl]);

  const getSearchVolume = useCallback((keyword: string): number | null => {
    if (!analysis) return null;
    return analysis.enhanced_analysis[keyword]?.search_volume || null;
  }, [analysis]);

  const reset = useCallback(() => {
    setAnalysis(null);
    setError(null);
    setAnalyzing(false);
  }, []);

  return {
    analyzing,
    analysis,
    error,
    analyzeKeywords,
    getSearchVolume,
    reset,
  };
}
```

---

## React Component Example

```typescript
import React, { useState } from 'react';
import { useKeywordAnalysis } from './hooks/useKeywordAnalysis';

export function KeywordSearchVolumeDisplay() {
  const { analyzing, analysis, error, analyzeKeywords, getSearchVolume } = useKeywordAnalysis();
  const [keywords, setKeywords] = useState<string[]>([]);
  const [inputValue, setInputValue] = useState('');

  const handleAnalyze = async () => {
    const keywordList = inputValue.split(',').map(k => k.trim()).filter(k => k);
    if (keywordList.length === 0) {
      alert('Please enter at least one keyword');
      return;
    }
    await analyzeKeywords(keywordList);
  };

  return (
    <div className="keyword-analysis">
      <div className="input-section">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Enter keywords (comma-separated)"
          className="keyword-input"
        />
        <button
          onClick={handleAnalyze}
          disabled={analyzing}
          className="analyze-button"
        >
          {analyzing ? 'Analyzing...' : 'Get Search Volume'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      {analysis && (
        <div className="results-section">
          <h3>Search Volume Results</h3>
          <table className="keyword-table">
            <thead>
              <tr>
                <th>Keyword</th>
                <th>Search Volume</th>
                <th>Difficulty</th>
                <th>Competition</th>
                <th>CPC</th>
                <th>Recommended</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(analysis.enhanced_analysis).map(([keyword, data]) => (
                <tr key={keyword}>
                  <td>{keyword}</td>
                  <td className="search-volume">
                    {data.search_volume ? (
                      <span className="volume-badge">
                        {data.search_volume.toLocaleString()}
                      </span>
                    ) : (
                      <span className="no-data">N/A</span>
                    )}
                  </td>
                  <td>
                    <span className={`difficulty-badge difficulty-${data.difficulty}`}>
                      {data.difficulty}
                    </span>
                  </td>
                  <td>{(data.competition * 100).toFixed(0)}%</td>
                  <td>${data.cpc.toFixed(2)}</td>
                  <td>
                    {data.recommended ? (
                      <span className="recommended">✓ Recommended</span>
                    ) : (
                      <span className="not-recommended">Not recommended</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Additional metrics */}
          <div className="additional-metrics">
            <h4>Additional Information</h4>
            {Object.entries(analysis.enhanced_analysis).map(([keyword, data]) => (
              <div key={keyword} className="keyword-details">
                <h5>{keyword}</h5>
                <p><strong>Parent Topic:</strong> {data.parent_topic}</p>
                <p><strong>Category:</strong> {data.category_type}</p>
                <p><strong>Reason:</strong> {data.reason}</p>
                {data.related_keywords.length > 0 && (
                  <div>
                    <strong>Related Keywords:</strong>
                    <ul>
                      {data.related_keywords.slice(0, 5).map(kw => (
                        <li key={kw}>{kw}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {analyzing && (
        <div className="loading-indicator">
          <div className="spinner" />
          <p>Analyzing keywords and fetching search volume data...</p>
        </div>
      )}
    </div>
  );
}
```

---

## Quick Usage Examples

### Example 1: Get Search Volume for Single Keyword

```typescript
const client = new KeywordAnalysisClient();

// Get search volume for one keyword
const volume = await client.getSearchVolume('pet grooming');
console.log(`Search volume: ${volume}`); // e.g., 1200
```

### Example 2: Get Search Volume for Multiple Keywords

```typescript
const client = new KeywordAnalysisClient();

// Get search volumes for multiple keywords
const volumes = await client.getSearchVolumes([
  'pet grooming',
  'dog care',
  'pet health'
]);

console.log(volumes);
// {
//   "pet grooming": 1200,
//   "dog care": 8900,
//   "pet health": 5400
// }
```

### Example 3: Full Analysis with All Metrics

```typescript
const client = new KeywordAnalysisClient();

// Get comprehensive analysis
const analysis = await client.getKeywordAnalysis(
  ['pet grooming', 'dog care'],
  {
    location: 'United States',
    language: 'en',
    max_suggestions_per_keyword: 150
  }
);

// Access search volume
const petGroomingVolume = analysis.enhanced_analysis['pet grooming'].search_volume;
const dogCareVolume = analysis.enhanced_analysis['dog care'].search_volume;

console.log(`Pet grooming: ${petGroomingVolume} monthly searches`);
console.log(`Dog care: ${dogCareVolume} monthly searches`);

// Access other metrics
const petGroomingData = analysis.enhanced_analysis['pet grooming'];
console.log({
  searchVolume: petGroomingData.search_volume,
  difficulty: petGroomingData.difficulty,
  competition: petGroomingData.competition,
  cpc: petGroomingData.cpc,
  recommended: petGroomingData.recommended,
  reason: petGroomingData.reason
});
```

### Example 4: Filter Keywords by Search Volume

```typescript
const client = new KeywordAnalysisClient();

const analysis = await client.getKeywordAnalysis(['pet grooming', 'dog care', 'cat food']);

// Filter keywords with search volume >= 1000
const highVolumeKeywords = Object.entries(analysis.enhanced_analysis)
  .filter(([keyword, data]) => data.search_volume >= 1000)
  .map(([keyword, data]) => ({
    keyword,
    searchVolume: data.search_volume,
    difficulty: data.difficulty
  }));

console.log('High volume keywords:', highVolumeKeywords);
```

### Example 5: Sort Keywords by Search Volume

```typescript
const client = new KeywordAnalysisClient();

const analysis = await client.getKeywordAnalysis([
  'pet grooming',
  'dog care',
  'cat food',
  'pet insurance'
]);

// Sort by search volume (descending)
const sortedKeywords = Object.entries(analysis.enhanced_analysis)
  .map(([keyword, data]) => ({
    keyword,
    searchVolume: data.search_volume,
    difficulty: data.difficulty,
    cpc: data.cpc
  }))
  .sort((a, b) => (b.searchVolume || 0) - (a.searchVolume || 0));

console.log('Keywords sorted by search volume:');
sortedKeywords.forEach((item, index) => {
  console.log(`${index + 1}. ${item.keyword}: ${item.searchVolume} searches/month`);
});
```

---

## Error Handling

```typescript
async function getSearchVolumeSafely(keyword: string): Promise<number | null> {
  try {
    const client = new KeywordAnalysisClient();
    const volume = await client.getSearchVolume(keyword);
    return volume;
  } catch (error) {
    if (error instanceof Error) {
      // Handle specific errors
      if (error.message.includes('503')) {
        console.error('DataForSEO service unavailable');
      } else if (error.message.includes('401')) {
        console.error('API authentication failed');
      } else {
        console.error('Failed to get search volume:', error.message);
      }
    }
    return null;
  }
}
```

---

## Best Practices

### 1. Batch Requests

```typescript
// ✅ Good: Batch multiple keywords in one request
const analysis = await client.getKeywordAnalysis([
  'pet grooming',
  'dog care',
  'cat food'
]);

// ❌ Bad: Multiple separate requests
const volume1 = await client.getSearchVolume('pet grooming');
const volume2 = await client.getSearchVolume('dog care');
const volume3 = await client.getSearchVolume('cat food');
```

### 2. Cache Results

```typescript
// Cache search volume results to avoid repeated API calls
const searchVolumeCache = new Map<string, { volume: number; timestamp: number }>();
const CACHE_TTL = 3600000; // 1 hour

async function getCachedSearchVolume(keyword: string): Promise<number | null> {
  const cached = searchVolumeCache.get(keyword);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.volume;
  }

  const volume = await client.getSearchVolume(keyword);
  if (volume !== null) {
    searchVolumeCache.set(keyword, {
      volume,
      timestamp: Date.now()
    });
  }
  return volume;
}
```

### 3. Handle Missing Data

```typescript
// Always check if search_volume exists
const analysis = await client.getKeywordAnalysis(['pet grooming']);
const keywordData = analysis.enhanced_analysis['pet grooming'];

if (keywordData.search_volume !== null && keywordData.search_volume !== undefined) {
  console.log(`Search volume: ${keywordData.search_volume}`);
} else {
  console.log('Search volume data not available');
}
```

### 4. Display Formatting

```typescript
// Format search volume for display
function formatSearchVolume(volume: number | null): string {
  if (volume === null || volume === undefined) {
    return 'N/A';
  }
  
  if (volume >= 1000000) {
    return `${(volume / 1000000).toFixed(1)}M`;
  } else if (volume >= 1000) {
    return `${(volume / 1000).toFixed(1)}K`;
  } else {
    return volume.toString();
  }
}

// Usage
const volume = 1200;
console.log(formatSearchVolume(volume)); // "1.2K"

const volume2 = 1500000;
console.log(formatSearchVolume(volume2)); // "1.5M"
```

---

## Complete Example: Search Volume Dashboard

```typescript
import React, { useState, useEffect } from 'react';
import { useKeywordAnalysis } from './hooks/useKeywordAnalysis';

interface KeywordRow {
  keyword: string;
  searchVolume: number;
  difficulty: string;
  competition: number;
  cpc: number;
  recommended: boolean;
}

export function SearchVolumeDashboard() {
  const { analyzing, analysis, error, analyzeKeywords } = useKeywordAnalysis();
  const [keywords, setKeywords] = useState<string[]>([]);
  const [filteredKeywords, setFilteredKeywords] = useState<KeywordRow[]>([]);
  const [minVolume, setMinVolume] = useState(0);
  const [sortBy, setSortBy] = useState<'volume' | 'difficulty' | 'cpc'>('volume');

  useEffect(() => {
    if (analysis) {
      const rows: KeywordRow[] = Object.entries(analysis.enhanced_analysis)
        .map(([keyword, data]) => ({
          keyword,
          searchVolume: data.search_volume || 0,
          difficulty: data.difficulty,
          competition: data.competition,
          cpc: data.cpc,
          recommended: data.recommended,
        }))
        .filter(row => row.searchVolume >= minVolume)
        .sort((a, b) => {
          if (sortBy === 'volume') {
            return b.searchVolume - a.searchVolume;
          } else if (sortBy === 'difficulty') {
            const difficultyOrder = { easy: 1, medium: 2, hard: 3 };
            return difficultyOrder[a.difficulty] - difficultyOrder[b.difficulty];
          } else {
            return b.cpc - a.cpc;
          }
        });
      
      setFilteredKeywords(rows);
    }
  }, [analysis, minVolume, sortBy]);

  const handleAnalyze = async (keywordList: string[]) => {
    await analyzeKeywords(keywordList, {
      location: 'United States',
      language: 'en',
      max_suggestions_per_keyword: 150
    });
  };

  return (
    <div className="search-volume-dashboard">
      <h2>Keyword Search Volume Analysis</h2>
      
      {/* Input */}
      <div className="controls">
        <input
          type="text"
          placeholder="Enter keywords (comma-separated)"
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              const keywordList = (e.target as HTMLInputElement).value
                .split(',')
                .map(k => k.trim())
                .filter(k => k);
              if (keywordList.length > 0) {
                handleAnalyze(keywordList);
              }
            }
          }}
        />
        <button onClick={() => handleAnalyze(keywords)} disabled={analyzing}>
          Analyze
        </button>
      </div>

      {/* Filters */}
      {analysis && (
        <div className="filters">
          <label>
            Min Search Volume:
            <input
              type="number"
              value={minVolume}
              onChange={(e) => setMinVolume(Number(e.target.value))}
              min={0}
            />
          </label>
          <label>
            Sort By:
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value as any)}>
              <option value="volume">Search Volume</option>
              <option value="difficulty">Difficulty</option>
              <option value="cpc">CPC</option>
            </select>
          </label>
        </div>
      )}

      {/* Results Table */}
      {filteredKeywords.length > 0 && (
        <table className="results-table">
          <thead>
            <tr>
              <th>Keyword</th>
              <th>Search Volume</th>
              <th>Difficulty</th>
              <th>Competition</th>
              <th>CPC</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {filteredKeywords.map((row) => (
              <tr key={row.keyword}>
                <td>{row.keyword}</td>
                <td className="volume-cell">
                  {row.searchVolume.toLocaleString()}
                </td>
                <td>
                  <span className={`badge difficulty-${row.difficulty}`}>
                    {row.difficulty}
                  </span>
                </td>
                <td>{(row.competition * 100).toFixed(0)}%</td>
                <td>${row.cpc.toFixed(2)}</td>
                <td>
                  {row.recommended ? (
                    <span className="badge recommended">✓ Recommended</span>
                  ) : (
                    <span className="badge not-recommended">Not Recommended</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {analyzing && <div className="loading">Loading search volume data...</div>}
      {error && <div className="error">Error: {error}</div>}
    </div>
  );
}
```

---

## Summary

### Endpoint
- **URL:** `POST /api/v1/keywords/enhanced`
- **Returns:** Search volume + comprehensive keyword metrics

### Key Response Field
```typescript
enhanced_analysis[keyword].search_volume  // number (monthly searches)
```

### Quick Access Pattern
```typescript
const analysis = await client.getKeywordAnalysis(['pet grooming']);
const searchVolume = analysis.enhanced_analysis['pet grooming'].search_volume;
```

### Requirements
- DataForSEO credentials must be configured in Secret Manager
- If not configured, returns estimated values (less accurate)

---

**Need Help?** Check the API documentation at `/docs` or review error messages for specific guidance.

