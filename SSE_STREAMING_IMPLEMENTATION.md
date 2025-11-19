# SSE Streaming Implementation for Keyword Search

**Date**: 2025-11-19  
**Status**: ✅ Implemented

---

## 🎯 Overview

Implemented Server-Sent Events (SSE) streaming for the keyword search endpoint to provide real-time progress updates as each stage completes.

---

## ✅ What Was Implemented

### 1. New Streaming Endpoint

**Endpoint**: `POST /api/v1/keywords/enhanced/stream`

- Returns SSE events with progress updates
- Emits ~10-15 progress events during analysis
- Sends final JSON result as completion event
- Handles errors gracefully

### 2. Shared Analysis Function

**Function**: `_analyze_keywords_with_progress()`

- Extracted keyword analysis logic into reusable function
- Supports optional progress callbacks
- Used by both standard and streaming endpoints
- Maintains all existing functionality

### 3. Progress Tracking

**10 Stages Tracked:**

1. **Initialization** (5%) - Setup and location detection
2. **Primary Keyword Analysis** (20%) - Analyze seed keywords
3. **Getting Suggestions** (40%) - Fetch keyword suggestions
4. **Analyzing Suggestions** (60%) - Analyze suggested keywords
5. **Clustering** (75%) - Group keywords by topics
6. **AI Optimization Data** (85%) - Get AI search volume
7. **Related Keywords** (92%) - Get related keywords
8. **Keyword Ideas** (97%) - Get questions and topics
9. **SERP Analysis** (99%) - Optional SERP analysis
10. **Finalization** (100%) - Compile response

---

## 📊 Progress Update Format

Each SSE event contains:

```json
{
  "stage": "keyword_analysis",
  "stage_number": 2,
  "total_stages": 10,
  "progress_percentage": 20.0,
  "status": "Analyzing primary keywords",
  "details": "Analyzing 3 keywords for search volume, CPC, and competition",
  "metadata": {
    "keywords": ["pet grooming", "dog care", "cat health"]
  },
  "timestamp": 1703064703.123
}
```

**Completion Event:**
```json
{
  "type": "complete",
  "result": {
    "enhanced_analysis": {...},
    "total_keywords": 50,
    "clusters": [...],
    ...
  }
}
```

**Error Event:**
```json
{
  "type": "error",
  "error": "Error message",
  "status_code": 500
}
```

---

## 🔧 Technical Implementation

### Backend Changes

**File**: `main.py`

1. **Added `_analyze_keywords_with_progress()` function**
   - Extracted from existing endpoint
   - Added progress callback support
   - Emits progress at each stage

2. **Created `/api/v1/keywords/enhanced/stream` endpoint**
   - Uses `StreamingResponse` with `text/event-stream`
   - Queue-based progress emission
   - Background task processing
   - Proper error handling

3. **Updated standard endpoint**
   - Now uses shared function
   - No progress callbacks (backward compatible)
   - Same response format

### Architecture

```
Request → SSE Endpoint → Queue → Background Task
                              ↓
                         Progress Updates
                              ↓
                         SSE Stream → Frontend
```

**Key Components:**
- `asyncio.Queue` - Thread-safe progress queue
- `asyncio.create_task()` - Background processing
- `StreamingResponse` - SSE response handler
- Progress callbacks - Stage completion notifications

---

## 💻 Frontend Integration

### TypeScript Example

```typescript
async function analyzeKeywordsWithProgress(
  keywords: string[],
  onProgress: (update: ProgressUpdate) => void,
  onComplete: (result: any) => void,
  onError: (error: string) => void
) {
  const response = await fetch('/api/v1/keywords/enhanced/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      keywords: keywords,
      location: 'United States',
      language: 'en',
      max_suggestions_per_keyword: 150
    })
  });

  if (!response.ok) {
    onError(`HTTP ${response.status}`);
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    onError('Stream not available');
    return;
  }

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            
            if (data.type === 'complete') {
              onComplete(data.result);
            } else if (data.type === 'error') {
              onError(data.error);
            } else {
              // Progress update
              onProgress(data);
            }
          } catch (e) {
            console.error('Failed to parse SSE data:', e);
          }
        }
      }
    }
  } catch (error) {
    onError(error instanceof Error ? error.message : 'Unknown error');
  } finally {
    reader.releaseLock();
  }
}
```

### React Hook Example

```typescript
import { useState, useCallback } from 'react';

interface ProgressUpdate {
  stage: string;
  stage_number: number;
  total_stages: number;
  progress_percentage: number;
  status: string;
  details?: string;
  metadata: Record<string, any>;
  timestamp: number;
}

export function useKeywordAnalysis() {
  const [progress, setProgress] = useState<ProgressUpdate | null>(null);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const analyze = useCallback(async (keywords: string[]) => {
    setIsLoading(true);
    setProgress(null);
    setResult(null);
    setError(null);

    await analyzeKeywordsWithProgress(
      keywords,
      (update) => {
        setProgress(update);
        console.log(`${update.progress_percentage}% - ${update.status}`);
      },
      (result) => {
        setResult(result);
        setIsLoading(false);
      },
      (error) => {
        setError(error);
        setIsLoading(false);
      }
    );
  }, []);

  return { analyze, progress, result, error, isLoading };
}
```

### React Component Example

```tsx
function KeywordAnalysisComponent() {
  const { analyze, progress, result, error, isLoading } = useKeywordAnalysis();

  return (
    <div>
      <button onClick={() => analyze(['pet grooming'])} disabled={isLoading}>
        Analyze Keywords
      </button>

      {isLoading && progress && (
        <div>
          <ProgressBar value={progress.progress_percentage} />
          <p>Stage {progress.stage_number}/{progress.total_stages}: {progress.status}</p>
          {progress.details && <p className="details">{progress.details}</p>}
        </div>
      )}

      {result && <KeywordResults data={result} />}
      {error && <ErrorMessage error={error} />}
    </div>
  );
}
```

---

## 📋 API Usage

### Standard Endpoint (No Streaming)

```bash
curl -X POST "https://api.example.com/api/v1/keywords/enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["pet grooming"],
    "max_suggestions_per_keyword": 150
  }'
```

**Response**: Single JSON response with all data

### Streaming Endpoint (SSE)

```bash
curl -X POST "https://api.example.com/api/v1/keywords/enhanced/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["pet grooming"],
    "max_suggestions_per_keyword": 150
  }' \
  --no-buffer
```

**Response**: SSE stream with progress updates, then final result

---

## 🔍 Testing

### Test Progress Updates

```python
import asyncio
import json
import httpx

async def test_streaming():
    async with httpx.AsyncClient() as client:
        async with client.stream(
            'POST',
            'https://api.example.com/api/v1/keywords/enhanced/stream',
            json={'keywords': ['pet grooming']},
            headers={'Content-Type': 'application/json'}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    print(f"{data.get('progress_percentage', 0)}% - {data.get('status', '')}")

asyncio.run(test_streaming())
```

---

## ✅ Benefits

### User Experience
- ✅ **Real-time feedback** - Users see progress as it happens
- ✅ **Transparency** - Clear indication of what's happening
- ✅ **Reduced perceived wait time** - Progress bars feel faster
- ✅ **Professional UX** - Modern, responsive interface

### Technical
- ✅ **Low overhead** - Minimal cost increase (~$0.000001 per request)
- ✅ **No async complexity** - Direct SSE connection
- ✅ **Existing infrastructure** - Uses FastAPI StreamingResponse
- ✅ **Backward compatible** - Standard endpoint unchanged

### Cost
- ✅ **Negligible** - Less than $0.10/month for 10K requests
- ✅ **No additional infrastructure** - Uses existing Cloud Run
- ✅ **No storage costs** - No job storage needed

---

## 📝 Notes

### EventSource Limitation

**Important**: `EventSource` API doesn't support POST requests. Use `fetch()` with `ReadableStream` instead (see TypeScript example above).

### Connection Management

- Connection stays open for ~10-15 seconds
- Keepalive events sent every 30 seconds if no updates
- Automatic cleanup on completion or error
- Cloud Run timeout: 900s (plenty for keyword search)

### Error Handling

- Errors emitted as SSE events
- Connection closed gracefully on error
- Frontend can handle errors in stream
- Standard HTTP errors still apply

---

## 🚀 Deployment

### Changes Made

1. ✅ Added `_analyze_keywords_with_progress()` function
2. ✅ Created `/api/v1/keywords/enhanced/stream` endpoint
3. ✅ Updated standard endpoint to use shared function
4. ✅ Added progress tracking to all 10 stages
5. ✅ Added JSON import for SSE formatting

### Files Modified

- `main.py` - Added streaming endpoint and progress tracking

### Testing Checklist

- [ ] Test with 1 keyword
- [ ] Test with 3 keywords (testing mode)
- [ ] Test with 10 keywords (production)
- [ ] Test error scenarios
- [ ] Test timeout scenarios
- [ ] Verify progress updates appear correctly
- [ ] Verify final result is correct

---

## 📚 Related Documentation

- `KEYWORD_SEARCH_STREAMING_ANALYSIS.md` - Cost analysis and recommendations
- `FRONTEND_KEYWORD_ENDPOINT_UPDATE.md` - Frontend integration guide
- `MAX_SEARCH_PARAMETERS.json` - Maximum parameter values

---

## ✅ Summary

**SSE streaming is now implemented!**

- ✅ New `/api/v1/keywords/enhanced/stream` endpoint
- ✅ Real-time progress updates (10 stages)
- ✅ Queue-based architecture
- ✅ Backward compatible (standard endpoint unchanged)
- ✅ Minimal cost impact (<$0.10/month for 10K requests)
- ✅ Ready for frontend integration

**Next Steps:**
1. Deploy to staging
2. Test with real requests
3. Integrate frontend EventSource/fetch handling
4. Monitor performance and costs

