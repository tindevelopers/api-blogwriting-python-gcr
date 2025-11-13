# Frontend Integration Guide: Phase 1-3 New Endpoints

**Date:** 2025-11-12  
**Version:** 1.3.0  
**API Base URL:** `https://blog-writer-api-dev-kq42l26tuq-ew.a.run.app`

---

## Overview

This guide covers integration for the new Phase 1-3 endpoints:
- **Keyword Difficulty Analysis** - Multi-factor difficulty analysis with time-to-rank estimates
- **Quota Management** - Per-organization quota tracking and limits
- **Quota Limits Configuration** - Set custom quota limits

---

## Table of Contents

1. [Keyword Difficulty Analysis](#keyword-difficulty-analysis)
2. [Quota Management](#quota-management)
3. [TypeScript Types](#typescript-types)
4. [API Client Implementation](#api-client-implementation)
5. [React Hooks](#react-hooks)
6. [Usage Examples](#usage-examples)
7. [Error Handling](#error-handling)
8. [Best Practices](#best-practices)

---

## Keyword Difficulty Analysis

### Endpoint

```
POST /api/v1/keywords/difficulty
```

### Purpose

Analyzes keyword difficulty with multi-factor analysis including:
- Domain authority requirements
- Backlink requirements
- Content length needs
- Competition level
- Time-to-rank estimates
- Ranking probability over time

### Request Body

```typescript
interface KeywordDifficultyRequest {
  keyword: string;                    // Required: Keyword to analyze
  search_volume?: number;             // Optional: Monthly search volume (default: 0)
  difficulty?: number;               // Optional: Basic difficulty score 0-100 (default: 50.0)
  competition?: number;               // Optional: Competition index 0-1 (default: 0.5)
  location?: string;                  // Optional: Location for analysis (default: "United States")
  language?: string;                  // Optional: Language code (default: "en")
}
```

### Response

```typescript
interface KeywordDifficultyResponse {
  keyword: string;
  overall_difficulty: number;         // 0-100
  domain_authority_required: number;  // 0-100
  backlink_requirements: "low" | "medium" | "high";
  content_length_needed: number;      // Word count
  competition_level: "low" | "medium" | "high";
  time_to_rank: string;               // e.g., "1-3 months", "6-12 months"
  ranking_probability: {
    "1_month": number;                // 0-1 probability
    "3_months": number;
    "6_months": number;
  };
  recommendations: string[];           // Actionable recommendations
  metadata: {
    keyword: string;
    search_volume: number;
    competition_index: number;
  };
}
```

### Example Request

```typescript
const request: KeywordDifficultyRequest = {
  keyword: "pet grooming services",
  search_volume: 5000,
  difficulty: 45.0,
  competition: 0.6,
  location: "United States",
  language: "en"
};
```

### Example Response

```json
{
  "keyword": "pet grooming services",
  "overall_difficulty": 45.0,
  "domain_authority_required": 52.5,
  "backlink_requirements": "medium",
  "content_length_needed": 2500,
  "competition_level": "medium",
  "time_to_rank": "1-3 months",
  "ranking_probability": {
    "1_month": 0.35,
    "3_months": 0.65,
    "6_months": 0.85
  },
  "recommendations": [
    "Build 15-30 quality backlinks from relevant sites",
    "Create comprehensive content of at least 2500 words",
    "Optimize for related keywords to capture more traffic",
    "Expected ranking time: 1-3 months"
  ],
  "metadata": {
    "keyword": "pet grooming services",
    "search_volume": 5000,
    "competition_index": 0.6
  }
}
```

---

## Quota Management

### Endpoint 1: Get Quota Information

```
GET /api/v1/quota/{organization_id}
```

### Purpose

Retrieves quota information for an organization including:
- Monthly, daily, and hourly limits
- Current usage
- Remaining quota
- Warnings if approaching limits

### Path Parameters

- `organization_id` (string, required): Organization identifier

### Response

```typescript
interface QuotaInfoResponse {
  organization_id: string;
  monthly_limit: number;
  monthly_used: number;
  monthly_remaining: number;
  monthly_reset_date: string;        // ISO 8601 date
  daily_limit: number | null;
  daily_used: number;
  daily_remaining: number;
  daily_reset_date: string | null;     // ISO 8601 date
  hourly_limit: number | null;
  hourly_used: number;
  hourly_remaining: number;
  hourly_reset_date: string | null;   // ISO 8601 date
  breakdown: Record<string, number>;   // Usage by operation type
  warnings: Array<{
    threshold: string;                 // e.g., "80%", "90%"
    message: string;
  }>;
}
```

### Example Response

```json
{
  "organization_id": "org_123",
  "monthly_limit": 10000,
  "monthly_used": 7500,
  "monthly_remaining": 2500,
  "monthly_reset_date": "2025-12-01T00:00:00",
  "daily_limit": 1000,
  "daily_used": 850,
  "daily_remaining": 150,
  "daily_reset_date": "2025-11-13T00:00:00",
  "hourly_limit": 100,
  "hourly_used": 45,
  "hourly_remaining": 55,
  "hourly_reset_date": "2025-11-12T18:00:00",
  "breakdown": {
    "keyword_analysis": 5000,
    "content_generation": 2500
  },
  "warnings": [
    {
      "threshold": "80%",
      "message": "80% of monthly quota used (7500/10000)"
    }
  ]
}
```

### Endpoint 2: Set Quota Limits

```
POST /api/v1/quota/{organization_id}/set-limits
```

### Purpose

Sets custom quota limits for an organization. Only updates provided limits, leaves others unchanged.

### Path Parameters

- `organization_id` (string, required): Organization identifier

### Request Body

```typescript
interface SetQuotaLimitsRequest {
  monthly_limit?: number;             // Optional: Monthly limit
  daily_limit?: number;               // Optional: Daily limit
  hourly_limit?: number;              // Optional: Hourly limit
}
```

### Response

```typescript
interface SetQuotaLimitsResponse {
  message: string;                     // e.g., "Quota limits updated successfully"
}
```

### Example Request

```typescript
const request: SetQuotaLimitsRequest = {
  monthly_limit: 20000,
  daily_limit: 2000,
  hourly_limit: 200
};
```

### Example Response

```json
{
  "message": "Quota limits updated successfully"
}
```

---

## TypeScript Types

### Complete Type Definitions

```typescript
// Keyword Difficulty Types
export interface KeywordDifficultyRequest {
  keyword: string;
  search_volume?: number;
  difficulty?: number;
  competition?: number;
  location?: string;
  language?: string;
}

export interface KeywordDifficultyResponse {
  keyword: string;
  overall_difficulty: number;
  domain_authority_required: number;
  backlink_requirements: "low" | "medium" | "high";
  content_length_needed: number;
  competition_level: "low" | "medium" | "high";
  time_to_rank: string;
  ranking_probability: {
    "1_month": number;
    "3_months": number;
    "6_months": number;
  };
  recommendations: string[];
  metadata: {
    keyword: string;
    search_volume: number;
    competition_index: number;
  };
}

// Quota Types
export interface QuotaInfoResponse {
  organization_id: string;
  monthly_limit: number;
  monthly_used: number;
  monthly_remaining: number;
  monthly_reset_date: string;
  daily_limit: number | null;
  daily_used: number;
  daily_remaining: number;
  daily_reset_date: string | null;
  hourly_limit: number | null;
  hourly_used: number;
  hourly_remaining: number;
  hourly_reset_date: string | null;
  breakdown: Record<string, number>;
  warnings: Array<{
    threshold: string;
    message: string;
  }>;
}

export interface SetQuotaLimitsRequest {
  monthly_limit?: number;
  daily_limit?: number;
  hourly_limit?: number;
}

export interface SetQuotaLimitsResponse {
  message: string;
}

// Error Types
export interface APIError {
  error: string;
  detail?: string;
  status_code?: number;
}
```

---

## API Client Implementation

### Base API Client Class

```typescript
class BlogWriterAPIClient {
  private baseURL: string;
  private apiKey?: string;

  constructor(baseURL: string, apiKey?: string) {
    this.baseURL = baseURL.replace(/\/$/, '');
    this.apiKey = apiKey;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: 'Unknown error',
        detail: `HTTP ${response.status}: ${response.statusText}`,
      }));
      throw new Error(error.detail || error.error || 'Request failed');
    }

    return response.json();
  }

  // Keyword Difficulty Analysis
  async analyzeKeywordDifficulty(
    request: KeywordDifficultyRequest
  ): Promise<KeywordDifficultyResponse> {
    return this.request<KeywordDifficultyResponse>(
      '/api/v1/keywords/difficulty',
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );
  }

  // Get Quota Information
  async getQuotaInfo(organizationId: string): Promise<QuotaInfoResponse> {
    return this.request<QuotaInfoResponse>(
      `/api/v1/quota/${encodeURIComponent(organizationId)}`,
      {
        method: 'GET',
      }
    );
  }

  // Set Quota Limits
  async setQuotaLimits(
    organizationId: string,
    limits: SetQuotaLimitsRequest
  ): Promise<SetQuotaLimitsResponse> {
    return this.request<SetQuotaLimitsResponse>(
      `/api/v1/quota/${encodeURIComponent(organizationId)}/set-limits`,
      {
        method: 'POST',
        body: JSON.stringify(limits),
      }
    );
  }
}

// Export singleton instance
export const apiClient = new BlogWriterAPIClient(
  process.env.NEXT_PUBLIC_API_URL || 'https://blog-writer-api-dev-kq42l26tuq-ew.a.run.app',
  process.env.NEXT_PUBLIC_API_KEY
);
```

---

## React Hooks

### useKeywordDifficulty Hook

```typescript
import { useState, useCallback } from 'react';
import { apiClient } from './api-client';
import type { KeywordDifficultyRequest, KeywordDifficultyResponse } from './types';

interface UseKeywordDifficultyResult {
  analyzeDifficulty: (request: KeywordDifficultyRequest) => Promise<void>;
  data: KeywordDifficultyResponse | null;
  loading: boolean;
  error: Error | null;
}

export function useKeywordDifficulty(): UseKeywordDifficultyResult {
  const [data, setData] = useState<KeywordDifficultyResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const analyzeDifficulty = useCallback(async (request: KeywordDifficultyRequest) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiClient.analyzeKeywordDifficulty(request);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to analyze difficulty'));
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  return { analyzeDifficulty, data, loading, error };
}
```

### useQuotaInfo Hook

```typescript
import { useState, useEffect, useCallback } from 'react';
import { apiClient } from './api-client';
import type { QuotaInfoResponse } from './types';

interface UseQuotaInfoResult {
  quotaInfo: QuotaInfoResponse | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

export function useQuotaInfo(organizationId: string | null): UseQuotaInfoResult {
  const [quotaInfo, setQuotaInfo] = useState<QuotaInfoResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchQuotaInfo = useCallback(async () => {
    if (!organizationId) {
      setQuotaInfo(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await apiClient.getQuotaInfo(organizationId);
      setQuotaInfo(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch quota info'));
      setQuotaInfo(null);
    } finally {
      setLoading(false);
    }
  }, [organizationId]);

  useEffect(() => {
    fetchQuotaInfo();
    // Refresh every 30 seconds
    const interval = setInterval(fetchQuotaInfo, 30000);
    return () => clearInterval(interval);
  }, [fetchQuotaInfo]);

  return { quotaInfo, loading, error, refetch: fetchQuotaInfo };
}
```

### useSetQuotaLimits Hook

```typescript
import { useState, useCallback } from 'react';
import { apiClient } from './api-client';
import type { SetQuotaLimitsRequest, SetQuotaLimitsResponse } from './types';

interface UseSetQuotaLimitsResult {
  setLimits: (
    organizationId: string,
    limits: SetQuotaLimitsRequest
  ) => Promise<void>;
  loading: boolean;
  error: Error | null;
  success: boolean;
}

export function useSetQuotaLimits(): UseSetQuotaLimitsResult {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [success, setSuccess] = useState(false);

  const setLimits = useCallback(
    async (organizationId: string, limits: SetQuotaLimitsRequest) => {
      setLoading(true);
      setError(null);
      setSuccess(false);

      try {
        await apiClient.setQuotaLimits(organizationId, limits);
        setSuccess(true);
        // Reset success flag after 3 seconds
        setTimeout(() => setSuccess(false), 3000);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to set quota limits'));
        setSuccess(false);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return { setLimits, loading, error, success };
}
```

---

## Usage Examples

### Example 1: Keyword Difficulty Analysis Component

```typescript
import React, { useState } from 'react';
import { useKeywordDifficulty } from './hooks/useKeywordDifficulty';

export function KeywordDifficultyAnalyzer() {
  const { analyzeDifficulty, data, loading, error } = useKeywordDifficulty();
  const [keyword, setKeyword] = useState('');
  const [searchVolume, setSearchVolume] = useState(0);
  const [difficulty, setDifficulty] = useState(50);

  const handleAnalyze = async () => {
    if (!keyword.trim()) return;

    await analyzeDifficulty({
      keyword: keyword.trim(),
      search_volume: searchVolume || undefined,
      difficulty: difficulty || undefined,
      location: 'United States',
      language: 'en',
    });
  };

  return (
    <div className="keyword-difficulty-analyzer">
      <h2>Keyword Difficulty Analysis</h2>
      
      <div className="form-group">
        <label>Keyword</label>
        <input
          type="text"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          placeholder="Enter keyword"
        />
      </div>

      <div className="form-group">
        <label>Search Volume (optional)</label>
        <input
          type="number"
          value={searchVolume}
          onChange={(e) => setSearchVolume(Number(e.target.value))}
          placeholder="Monthly search volume"
        />
      </div>

      <div className="form-group">
        <label>Difficulty (0-100, optional)</label>
        <input
          type="number"
          min="0"
          max="100"
          value={difficulty}
          onChange={(e) => setDifficulty(Number(e.target.value))}
        />
      </div>

      <button onClick={handleAnalyze} disabled={loading || !keyword.trim()}>
        {loading ? 'Analyzing...' : 'Analyze Difficulty'}
      </button>

      {error && (
        <div className="error">
          Error: {error.message}
        </div>
      )}

      {data && (
        <div className="results">
          <h3>Analysis Results</h3>
          
          <div className="metric">
            <label>Overall Difficulty:</label>
            <span>{data.overall_difficulty}/100</span>
          </div>

          <div className="metric">
            <label>Domain Authority Required:</label>
            <span>{data.domain_authority_required}/100</span>
          </div>

          <div className="metric">
            <label>Backlink Requirements:</label>
            <span className={`badge ${data.backlink_requirements}`}>
              {data.backlink_requirements}
            </span>
          </div>

          <div className="metric">
            <label>Content Length Needed:</label>
            <span>{data.content_length_needed} words</span>
          </div>

          <div className="metric">
            <label>Competition Level:</label>
            <span className={`badge ${data.competition_level}`}>
              {data.competition_level}
            </span>
          </div>

          <div className="metric">
            <label>Time to Rank:</label>
            <span>{data.time_to_rank}</span>
          </div>

          <div className="metric">
            <label>Ranking Probability:</label>
            <div className="probability-chart">
              <div>1 month: {(data.ranking_probability['1_month'] * 100).toFixed(0)}%</div>
              <div>3 months: {(data.ranking_probability['3_months'] * 100).toFixed(0)}%</div>
              <div>6 months: {(data.ranking_probability['6_months'] * 100).toFixed(0)}%</div>
            </div>
          </div>

          <div className="recommendations">
            <h4>Recommendations:</h4>
            <ul>
              {data.recommendations.map((rec, idx) => (
                <li key={idx}>{rec}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
```

### Example 2: Quota Dashboard Component

```typescript
import React from 'react';
import { useQuotaInfo } from './hooks/useQuotaInfo';
import { useSetQuotaLimits } from './hooks/useSetQuotaLimits';

interface QuotaDashboardProps {
  organizationId: string;
}

export function QuotaDashboard({ organizationId }: QuotaDashboardProps) {
  const { quotaInfo, loading, error, refetch } = useQuotaInfo(organizationId);
  const { setLimits, loading: settingLimits, error: setError, success } = useSetQuotaLimits();

  const handleUpdateLimits = async (limits: { monthly_limit?: number; daily_limit?: number }) => {
    await setLimits(organizationId, limits);
    // Refetch quota info after updating
    setTimeout(refetch, 1000);
  };

  if (loading) return <div>Loading quota information...</div>;
  if (error) return <div>Error: {error.message}</div>;
  if (!quotaInfo) return <div>No quota information available</div>;

  const monthlyUsagePercent = (quotaInfo.monthly_used / quotaInfo.monthly_limit) * 100;
  const dailyUsagePercent = quotaInfo.daily_limit
    ? (quotaInfo.daily_used / quotaInfo.daily_limit) * 100
    : 0;

  return (
    <div className="quota-dashboard">
      <h2>Quota Management</h2>

      {quotaInfo.warnings.length > 0 && (
        <div className="warnings">
          {quotaInfo.warnings.map((warning, idx) => (
            <div key={idx} className={`warning ${warning.threshold}`}>
              ⚠️ {warning.message}
            </div>
          ))}
        </div>
      )}

      <div className="quota-cards">
        {/* Monthly Quota */}
        <div className="quota-card">
          <h3>Monthly Quota</h3>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${Math.min(monthlyUsagePercent, 100)}%` }}
            />
          </div>
          <div className="quota-stats">
            <span>{quotaInfo.monthly_used.toLocaleString()}</span>
            <span>/</span>
            <span>{quotaInfo.monthly_limit.toLocaleString()}</span>
            <span>({quotaInfo.monthly_remaining.toLocaleString()} remaining)</span>
          </div>
          <div className="reset-date">
            Resets: {new Date(quotaInfo.monthly_reset_date).toLocaleDateString()}
          </div>
        </div>

        {/* Daily Quota */}
        {quotaInfo.daily_limit && (
          <div className="quota-card">
            <h3>Daily Quota</h3>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${Math.min(dailyUsagePercent, 100)}%` }}
              />
            </div>
            <div className="quota-stats">
              <span>{quotaInfo.daily_used.toLocaleString()}</span>
              <span>/</span>
              <span>{quotaInfo.daily_limit.toLocaleString()}</span>
              <span>({quotaInfo.daily_remaining.toLocaleString()} remaining)</span>
            </div>
            <div className="reset-date">
              Resets: {new Date(quotaInfo.daily_reset_date!).toLocaleDateString()}
            </div>
          </div>
        )}

        {/* Hourly Quota */}
        {quotaInfo.hourly_limit && (
          <div className="quota-card">
            <h3>Hourly Quota</h3>
            <div className="quota-stats">
              <span>{quotaInfo.hourly_used.toLocaleString()}</span>
              <span>/</span>
              <span>{quotaInfo.hourly_limit.toLocaleString()}</span>
              <span>({quotaInfo.hourly_remaining.toLocaleString()} remaining)</span>
            </div>
            <div className="reset-date">
              Resets: {new Date(quotaInfo.hourly_reset_date!).toLocaleTimeString()}
            </div>
          </div>
        )}
      </div>

      {/* Usage Breakdown */}
      <div className="usage-breakdown">
        <h3>Usage Breakdown</h3>
        <table>
          <thead>
            <tr>
              <th>Operation Type</th>
              <th>Usage</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(quotaInfo.breakdown).map(([type, count]) => (
              <tr key={type}>
                <td>{type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</td>
                <td>{count.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Update Limits Form */}
      <div className="update-limits">
        <h3>Update Limits</h3>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const formData = new FormData(e.currentTarget);
            handleUpdateLimits({
              monthly_limit: formData.get('monthly_limit')
                ? Number(formData.get('monthly_limit'))
                : undefined,
              daily_limit: formData.get('daily_limit')
                ? Number(formData.get('daily_limit'))
                : undefined,
            });
          }}
        >
          <div className="form-group">
            <label>Monthly Limit</label>
            <input
              type="number"
              name="monthly_limit"
              placeholder={quotaInfo.monthly_limit.toString()}
              min="1"
            />
          </div>
          <div className="form-group">
            <label>Daily Limit</label>
            <input
              type="number"
              name="daily_limit"
              placeholder={quotaInfo.daily_limit?.toString() || 'Not set'}
              min="1"
            />
          </div>
          <button type="submit" disabled={settingLimits}>
            {settingLimits ? 'Updating...' : 'Update Limits'}
          </button>
          {success && <div className="success">Limits updated successfully!</div>}
          {setError && <div className="error">Error: {setError.message}</div>}
        </form>
      </div>
    </div>
  );
}
```

### Example 3: Integration with Keyword Analysis

```typescript
import React, { useEffect } from 'react';
import { useKeywordDifficulty } from './hooks/useKeywordDifficulty';
import { useQuotaInfo } from './hooks/useQuotaInfo';

interface KeywordAnalysisWithDifficultyProps {
  keyword: string;
  searchVolume: number;
  difficulty: number;
  competition: number;
  organizationId: string;
}

export function KeywordAnalysisWithDifficulty({
  keyword,
  searchVolume,
  difficulty,
  competition,
  organizationId,
}: KeywordAnalysisWithDifficultyProps) {
  const { analyzeDifficulty, data: difficultyData, loading } = useKeywordDifficulty();
  const { quotaInfo } = useQuotaInfo(organizationId);

  useEffect(() => {
    // Check quota before analyzing
    if (quotaInfo && quotaInfo.monthly_remaining < 1) {
      console.warn('Monthly quota exceeded');
      return;
    }

    // Analyze difficulty when keyword data is available
    if (keyword && searchVolume > 0) {
      analyzeDifficulty({
        keyword,
        search_volume: searchVolume,
        difficulty,
        competition,
      });
    }
  }, [keyword, searchVolume, difficulty, competition, quotaInfo]);

  if (loading) return <div>Analyzing difficulty...</div>;
  if (!difficultyData) return null;

  return (
    <div className="difficulty-summary">
      <h4>Difficulty Analysis</h4>
      <div className="metrics">
        <div className="metric">
          <span className="label">Domain Authority Needed:</span>
          <span className="value">{difficultyData.domain_authority_required}/100</span>
        </div>
        <div className="metric">
          <span className="label">Content Length:</span>
          <span className="value">{difficultyData.content_length_needed} words</span>
        </div>
        <div className="metric">
          <span className="label">Time to Rank:</span>
          <span className="value">{difficultyData.time_to_rank}</span>
        </div>
        <div className="metric">
          <span className="label">6-Month Probability:</span>
          <span className="value">
            {(difficultyData.ranking_probability['6_months'] * 100).toFixed(0)}%
          </span>
        </div>
      </div>
    </div>
  );
}
```

---

## Error Handling

### Error Response Format

```typescript
interface APIErrorResponse {
  error: string;
  detail?: string;
  status_code?: number;
}
```

### Error Handling Utility

```typescript
export class APIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public detail?: string
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export async function handleAPIError(response: Response): Promise<never> {
  let errorData: APIErrorResponse;
  
  try {
    errorData = await response.json();
  } catch {
    errorData = {
      error: 'Unknown error',
      detail: `HTTP ${response.status}: ${response.statusText}`,
    };
  }

  throw new APIError(
    errorData.error || 'Request failed',
    response.status,
    errorData.detail
  );
}
```

### Error Handling in Components

```typescript
import { useState, useEffect } from 'react';
import { useKeywordDifficulty } from './hooks/useKeywordDifficulty';

export function KeywordDifficultyComponent() {
  const { analyzeDifficulty, data, loading, error } = useKeywordDifficulty();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (error) {
      // Handle different error types
      if (error.message.includes('503')) {
        setErrorMessage('Service temporarily unavailable. Please try again later.');
      } else if (error.message.includes('429')) {
        setErrorMessage('Rate limit exceeded. Please wait before trying again.');
      } else if (error.message.includes('404')) {
        setErrorMessage('Resource not found.');
      } else {
        setErrorMessage(error.message);
      }
    } else {
      setErrorMessage(null);
    }
  }, [error]);

  return (
    <div>
      {errorMessage && (
        <div className="error-banner">
          {errorMessage}
        </div>
      )}
      {/* Rest of component */}
    </div>
  );
}
```

---

## Best Practices

### 1. Quota Checking Before Operations

Always check quota before performing operations:

```typescript
async function performKeywordAnalysis(keyword: string, organizationId: string) {
  // Check quota first
  const quotaInfo = await apiClient.getQuotaInfo(organizationId);
  
  if (quotaInfo.monthly_remaining < 1) {
    throw new Error('Monthly quota exceeded');
  }
  
  if (quotaInfo.daily_limit && quotaInfo.daily_remaining < 1) {
    throw new Error('Daily quota exceeded');
  }
  
  // Proceed with operation
  // ... perform keyword analysis
}
```

### 2. Caching Quota Information

Cache quota information to reduce API calls:

```typescript
import { useMemo } from 'react';

const QUOTA_CACHE_TTL = 30000; // 30 seconds

let quotaCache: {
  data: QuotaInfoResponse | null;
  timestamp: number;
} = { data: null, timestamp: 0 };

export function useCachedQuotaInfo(organizationId: string) {
  const { quotaInfo, loading, refetch } = useQuotaInfo(organizationId);
  
  const cachedQuotaInfo = useMemo(() => {
    const now = Date.now();
    if (quotaCache.data && (now - quotaCache.timestamp) < QUOTA_CACHE_TTL) {
      return quotaCache.data;
    }
    if (quotaInfo) {
      quotaCache = { data: quotaInfo, timestamp: now };
    }
    return quotaInfo;
  }, [quotaInfo]);
  
  return { quotaInfo: cachedQuotaInfo, loading, refetch };
}
```

### 3. Retry Logic for Transient Errors

```typescript
async function analyzeDifficultyWithRetry(
  request: KeywordDifficultyRequest,
  maxRetries = 3
): Promise<KeywordDifficultyResponse> {
  let lastError: Error | null = null;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await apiClient.analyzeKeywordDifficulty(request);
    } catch (error) {
      lastError = error instanceof Error ? error : new Error('Unknown error');
      
      // Don't retry on 4xx errors (client errors)
      if (lastError.message.includes('40')) {
        throw lastError;
      }
      
      // Wait before retry (exponential backoff)
      await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
    }
  }
  
  throw lastError || new Error('Max retries exceeded');
}
```

### 4. Loading States and User Feedback

```typescript
export function QuotaIndicator({ organizationId }: { organizationId: string }) {
  const { quotaInfo, loading } = useQuotaInfo(organizationId);
  
  if (loading) {
    return <div className="quota-loading">Loading quota...</div>;
  }
  
  if (!quotaInfo) {
    return <div className="quota-error">Unable to load quota information</div>;
  }
  
  const usagePercent = (quotaInfo.monthly_used / quotaInfo.monthly_limit) * 100;
  const isWarning = usagePercent >= 80;
  const isCritical = usagePercent >= 90;
  
  return (
    <div className={`quota-indicator ${isCritical ? 'critical' : isWarning ? 'warning' : 'normal'}`}>
      <div className="quota-label">Monthly Quota</div>
      <div className="quota-bar">
        <div
          className="quota-fill"
          style={{ width: `${usagePercent}%` }}
        />
      </div>
      <div className="quota-text">
        {quotaInfo.monthly_used.toLocaleString()} / {quotaInfo.monthly_limit.toLocaleString()}
        {isWarning && ' ⚠️'}
      </div>
    </div>
  );
}
```

### 5. Type Safety

Always use TypeScript types for type safety:

```typescript
// ✅ Good - Type-safe
const result: KeywordDifficultyResponse = await apiClient.analyzeKeywordDifficulty({
  keyword: 'pet care',
  search_volume: 5000,
});

// ❌ Bad - No type safety
const result = await apiClient.analyzeKeywordDifficulty({
  keyword: 'pet care',
  search_volume: 5000,
});
```

---

## Environment Variables

Add these to your `.env.local`:

```bash
NEXT_PUBLIC_API_URL=https://blog-writer-api-dev-kq42l26tuq-ew.a.run.app
NEXT_PUBLIC_API_KEY=your-api-key-if-needed
```

---

## Testing Examples

### Unit Test Example

```typescript
import { describe, it, expect, vi } from 'vitest';
import { apiClient } from './api-client';

describe('Keyword Difficulty API', () => {
  it('should analyze keyword difficulty', async () => {
    const mockResponse: KeywordDifficultyResponse = {
      keyword: 'test keyword',
      overall_difficulty: 50,
      domain_authority_required: 60,
      backlink_requirements: 'medium',
      content_length_needed: 2000,
      competition_level: 'medium',
      time_to_rank: '1-3 months',
      ranking_probability: {
        '1_month': 0.3,
        '3_months': 0.6,
        '6_months': 0.9,
      },
      recommendations: ['Test recommendation'],
      metadata: {
        keyword: 'test keyword',
        search_volume: 1000,
        competition_index: 0.5,
      },
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    });

    const result = await apiClient.analyzeKeywordDifficulty({
      keyword: 'test keyword',
    });

    expect(result).toEqual(mockResponse);
  });
});
```

---

## Summary

### Quick Reference

**Keyword Difficulty:**
- Endpoint: `POST /api/v1/keywords/difficulty`
- Use when: You need detailed difficulty analysis with time-to-rank estimates
- Key fields: `domain_authority_required`, `time_to_rank`, `ranking_probability`

**Quota Management:**
- Endpoint: `GET /api/v1/quota/{organization_id}`
- Use when: Displaying quota usage, checking limits before operations
- Key fields: `monthly_remaining`, `daily_remaining`, `warnings`

**Set Quota Limits:**
- Endpoint: `POST /api/v1/quota/{organization_id}/set-limits`
- Use when: Admin needs to update organization limits
- Key fields: `monthly_limit`, `daily_limit`, `hourly_limit`

### Integration Checklist

- [ ] Add TypeScript types to your project
- [ ] Implement API client methods
- [ ] Create React hooks for each endpoint
- [ ] Add error handling
- [ ] Implement quota checking before operations
- [ ] Add loading states and user feedback
- [ ] Test all endpoints with real data
- [ ] Add quota indicators to UI
- [ ] Implement retry logic for transient errors

---

**Need Help?** Check the main [FRONTEND_API_INTEGRATION_GUIDE.md](./FRONTEND_API_INTEGRATION_GUIDE.md) for comprehensive integration patterns and best practices.

