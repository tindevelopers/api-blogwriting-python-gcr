# Frontend Guide: Streaming Keyword Search Results

**Version:** 1.3.4  
**Date:** 2025-11-20  
**Status:** ✅ Ready for Integration

---

## 🎯 Overview

The streaming keyword search endpoint (`/api/v1/keywords/enhanced/stream`) provides real-time progress updates as the search progresses through different stages. This allows your frontend to show users exactly what's happening during the search process.

---

## 📡 Endpoint

**URL:** `POST /api/v1/keywords/enhanced/stream`  
**Content-Type:** `application/json`  
**Response:** `text/event-stream` (Server-Sent Events)

---

## 🔄 Search Stages

The search progresses through these stages:

1. **`initializing`** (5%) - Starting search
2. **`detecting_location`** (10-15%) - Detecting user location from IP
3. **`analyzing_keywords`** (20-30%) - Analyzing primary keywords
4. **`getting_suggestions`** (40-45%) - Fetching keyword suggestions from DataForSEO
5. **`analyzing_suggestions`** (50-55%) - Analyzing suggested keywords
6. **`clustering_keywords`** (60-65%) - Clustering keywords by topic
7. **`getting_ai_data`** (70-75%) - Getting AI optimization metrics
8. **`getting_related_keywords`** (80-82%) - Finding related keywords
9. **`getting_keyword_ideas`** (85-88%) - Getting keyword ideas (questions/topics)
10. **`analyzing_serp`** (92-95%) - Analyzing SERP features (if `include_serp: true`)
11. **`building_discovery`** (98%) - Building discovery data
12. **`completed`** (100%) - Final results

---

## 💻 Frontend Integration

### TypeScript Types

```typescript
interface KeywordSearchStage {
  stage: string;
  progress: number;
  timestamp: number;
  message?: string;
  data?: {
    keywords?: string[];
    location?: string;
    detected_location?: string;
    keywords_analyzed?: number;
    current_keyword?: string;
    suggestions_found?: number;
    suggestions_to_analyze?: number;
    total_keywords_analyzed?: number;
    clusters_found?: number;
    total_keywords?: number;
    ai_metrics_count?: number;
    serp_features_found?: number;
    keyword?: string;
    result?: EnhancedKeywordAnalysisResponse;
    error?: string;
  };
}

interface EnhancedKeywordAnalysisResponse {
  enhanced_analysis: Record<string, KeywordAnalysis>;
  total_keywords: number;
  original_keywords: string[];
  suggested_keywords: string[];
  clusters: KeywordCluster[];
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
  discovery: Record<string, any>;
  serp_analysis: Record<string, any>;
}
```

### React/Next.js Example

```typescript
import { useState, useEffect } from 'react';

interface UseKeywordSearchStreamProps {
  keywords: string[];
  location?: string;
  language?: string;
  includeSerp?: boolean;
  maxSuggestionsPerKeyword?: number;
}

export function useKeywordSearchStream({
  keywords,
  location,
  language = 'en',
  includeSerp = false,
  maxSuggestionsPerKeyword = 20
}: UseKeywordSearchStreamProps) {
  const [stage, setStage] = useState<string>('initializing');
  const [progress, setProgress] = useState<number>(0);
  const [message, setMessage] = useState<string>('');
  const [stageData, setStageData] = useState<any>(null);
  const [result, setResult] = useState<EnhancedKeywordAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const startSearch = async () => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    setProgress(0);

    try {
      const response = await fetch('/api/v1/keywords/enhanced/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          keywords,
          location,
          language,
          include_serp: includeSerp,
          max_suggestions_per_keyword: maxSuggestionsPerKeyword,
        }),
      });

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
              const update: KeywordSearchStage = JSON.parse(line.slice(6));
              
              setStage(update.stage);
              setProgress(update.progress);
              if (update.message) setMessage(update.message);
              if (update.data) setStageData(update.data);

              // Handle completion
              if (update.stage === 'completed' && update.data?.result) {
                setResult(update.data.result);
                setIsLoading(false);
              }

              // Handle errors
              if (update.stage === 'error') {
                setError(update.data?.error || 'Unknown error');
                setIsLoading(false);
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setIsLoading(false);
    }
  };

  return {
    stage,
    progress,
    message,
    stageData,
    result,
    error,
    isLoading,
    startSearch,
  };
}

// Usage in component
function KeywordSearchComponent() {
  const {
    stage,
    progress,
    message,
    stageData,
    result,
    error,
    isLoading,
    startSearch,
  } = useKeywordSearchStream({
    keywords: ['seo', 'keyword research'],
    location: 'United States',
    includeSerp: true,
  });

  return (
    <div>
      <button onClick={startSearch} disabled={isLoading}>
        {isLoading ? 'Searching...' : 'Start Search'}
      </button>

      {isLoading && (
        <div>
          <div>Stage: {stage}</div>
          <div>Progress: {progress.toFixed(1)}%</div>
          <div>Message: {message}</div>
          <progress value={progress} max={100} />
          
          {stageData && (
            <div>
              <pre>{JSON.stringify(stageData, null, 2)}</pre>
            </div>
          )}
        </div>
      )}

      {result && (
        <div>
          <h2>Results</h2>
          <p>Total Keywords: {result.total_keywords}</p>
          <p>Clusters: {result.cluster_summary.cluster_count}</p>
          {/* Render results */}
        </div>
      )}

      {error && <div className="error">Error: {error}</div>}
    </div>
  );
}
```

### Vanilla JavaScript Example

```javascript
async function streamKeywordSearch(keywords, location = 'United States') {
  const response = await fetch('/api/v1/keywords/enhanced/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      keywords,
      location,
      include_serp: true,
      max_suggestions_per_keyword: 20,
    }),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value, { stream: true });
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const update = JSON.parse(line.slice(6));
        
        console.log(`Stage: ${update.stage}`);
        console.log(`Progress: ${update.progress}%`);
        console.log(`Message: ${update.message}`);
        
        // Update UI
        updateProgressBar(update.progress);
        updateStageLabel(update.stage);
        updateMessage(update.message);
        
        // Handle stage-specific data
        if (update.data) {
          handleStageData(update.stage, update.data);
        }
        
        // Handle completion
        if (update.stage === 'completed') {
          displayResults(update.data.result);
        }
        
        // Handle errors
        if (update.stage === 'error') {
          displayError(update.data.error);
        }
      }
    }
  }
}

function updateProgressBar(progress) {
  document.getElementById('progress-bar').style.width = `${progress}%`;
}

function updateStageLabel(stage) {
  document.getElementById('stage-label').textContent = formatStageName(stage);
}

function updateMessage(message) {
  document.getElementById('message').textContent = message;
}

function handleStageData(stage, data) {
  switch (stage) {
    case 'analyzing_keywords':
      console.log(`Analyzing ${data.keywords?.length} keywords`);
      break;
    case 'getting_suggestions':
      console.log(`Found ${data.suggestions_found} suggestions so far`);
      break;
    case 'clustering_keywords':
      console.log(`Found ${data.clusters_found} clusters`);
      break;
    // ... handle other stages
  }
}

function formatStageName(stage) {
  const stageNames = {
    'initializing': 'Initializing...',
    'detecting_location': 'Detecting Location',
    'analyzing_keywords': 'Analyzing Keywords',
    'getting_suggestions': 'Getting Suggestions',
    'analyzing_suggestions': 'Analyzing Suggestions',
    'clustering_keywords': 'Clustering Keywords',
    'getting_ai_data': 'Getting AI Data',
    'getting_related_keywords': 'Finding Related Keywords',
    'getting_keyword_ideas': 'Getting Keyword Ideas',
    'analyzing_serp': 'Analyzing SERP',
    'building_discovery': 'Building Results',
    'completed': 'Completed',
    'error': 'Error',
  };
  return stageNames[stage] || stage;
}
```

---

## 📊 Stage Data Examples

### Initializing Stage
```json
{
  "stage": "initializing",
  "progress": 5.0,
  "message": "Initializing keyword search...",
  "timestamp": 1700000000.0
}
```

### Analyzing Keywords Stage
```json
{
  "stage": "analyzing_keywords",
  "progress": 25.0,
  "message": "Analyzing 3 keywords...",
  "data": {
    "keywords": ["seo", "keyword research", "content marketing"],
    "location": "United States"
  },
  "timestamp": 1700000001.0
}
```

### Getting Suggestions Stage
```json
{
  "stage": "getting_suggestions",
  "progress": 42.5,
  "message": "Getting suggestions for 'seo'...",
  "data": {
    "current_keyword": "seo",
    "suggestions_found": 15
  },
  "timestamp": 1700000002.0
}
```

### Completed Stage
```json
{
  "stage": "completed",
  "progress": 100.0,
  "message": "Search completed successfully",
  "data": {
    "result": {
      "enhanced_analysis": { /* ... */ },
      "total_keywords": 45,
      "clusters": [ /* ... */ ],
      "serp_analysis": { /* ... */ }
    }
  },
  "timestamp": 1700000005.0
}
```

---

## 🎨 UI/UX Recommendations

### Progress Indicator
- Show a progress bar (0-100%)
- Display current stage name
- Show stage-specific message
- Update in real-time as events arrive

### Stage-Specific UI
- **Analyzing Keywords**: Show list of keywords being analyzed
- **Getting Suggestions**: Show which keyword is being processed
- **Clustering**: Show number of clusters found
- **SERP Analysis**: Show which keyword's SERP is being analyzed

### Error Handling
- Listen for `error` stage events
- Display error message to user
- Allow retry functionality
- Log errors for debugging

---

## 🔄 Comparison: Streaming vs Non-Streaming

### Non-Streaming (`/api/v1/keywords/enhanced`)
- ✅ Simpler implementation
- ✅ Single response
- ❌ No progress updates
- ❌ User waits without feedback
- ❌ Can't cancel mid-search

### Streaming (`/api/v1/keywords/enhanced/stream`)
- ✅ Real-time progress updates
- ✅ Better UX with live feedback
- ✅ Can show stage-specific data
- ✅ Can potentially cancel (future feature)
- ❌ More complex frontend code
- ❌ Requires SSE handling

---

## 📝 Request Body

Same as non-streaming endpoint:

```typescript
{
  keywords: string[];                    // Required: Keywords to analyze
  location?: string;                      // Optional: Location (defaults to IP detection)
  language?: string;                      // Optional: Language code (default: "en")
  include_serp?: boolean;                // Optional: Include SERP analysis (default: false)
  max_suggestions_per_keyword?: number;  // Optional: Max suggestions per keyword (default: 20)
  search_type?: string;                  // Optional: Search type (default: "enhanced_keyword_analysis")
}
```

---

## ⚠️ Error Handling

Errors are sent as SSE events with `stage: "error"`:

```json
{
  "stage": "error",
  "progress": 0.0,
  "message": "Search failed: DataForSEO API error",
  "data": {
    "error": "API rate limit exceeded"
  },
  "timestamp": 1700000000.0
}
```

Always check for error stage in your frontend code.

---

## 🚀 Best Practices

1. **Show Progress**: Always display progress bar and current stage
2. **Stage Messages**: Show user-friendly messages for each stage
3. **Handle Errors**: Gracefully handle error events
4. **Loading States**: Show loading indicator while streaming
5. **Result Display**: Only show final results when `stage === "completed"`
6. **Cleanup**: Close stream connection when component unmounts

---

## 📚 Related Documentation

- `FRONTEND_INTEGRATION_V1.3.4.md` - Main integration guide
- `FRONTEND_ENHANCED_STREAMING_GUIDE.md` - Blog generation streaming guide
- `API_DOCUMENTATION_V1.3.4.md` - Complete API documentation

---

**Status:** ✅ Ready for Integration  
**Breaking Changes:** None (new endpoint, existing endpoints unchanged)

