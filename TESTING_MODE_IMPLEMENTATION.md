# Testing Mode Implementation

## Overview

Testing mode has been implemented to reduce API calls, processing time, and costs during testing while maintaining full test coverage of all features.

## Configuration

### Environment Variable

Set `TESTING_MODE=true` to enable testing limits:

```bash
export TESTING_MODE=true
```

Or in Cloud Run:
```bash
gcloud run services update blog-writer-api-dev \
  --update-env-vars TESTING_MODE=true \
  --region=europe-west9
```

### Testing Limits Applied

When `TESTING_MODE=true`, the following limits are automatically applied:

#### Keyword Research Limits
- **Primary keywords**: 3-5 per search session
- **Related keywords**: 3-5 per primary keyword
- **Long-tail keywords**: 3-5 per primary keyword
- **Total keywords**: 15-25 per session (primary + related + long-tail)

#### Backlinks Data Limits
- **Backlinks per domain**: 10-20
- **Referring domains**: 5-10
- **Anchor texts**: Top 5-10

#### SERP Data Limits
- **SERP results**: Top 5-10 organic results
- **SERP features**: Top 3-5 features (featured snippets, people also ask, etc.)

#### Trend Data Limits
- **Monthly searches**: Last 3-6 months (instead of 12)
- **Historical data**: Skipped during testing

#### Clustering Limits
- **Clusters**: Top 3-5 per session
- **Keywords per cluster**: 5-10

#### Content Brief Limits
- **Competitor domains**: 2-3
- **Content ideas**: 5-10 per cluster

## Implementation Details

### Files Modified

1. **`src/blog_writer_sdk/config/testing_limits.py`** (NEW)
   - Core testing limits configuration
   - Functions to apply limits based on testing mode
   - Logging when limits are applied

2. **`main.py`**
   - Imports testing limits module
   - Applies limits in keyword analysis endpoints
   - Applies limits in enhanced keyword analysis
   - Applies clustering limits
   - Adds `testing_mode` flag to root endpoint response

3. **`src/blog_writer_sdk/config/__init__.py`** (NEW)
   - Exports testing limits functions

### Endpoints Affected

1. **`POST /api/v1/keywords/analyze`**
   - Limits primary keywords to 3-5
   - Limits suggestions per keyword to 3-5
   - Logs when limits are applied

2. **`POST /api/v1/keywords/enhanced`**
   - Limits primary keywords to 3-5
   - Limits suggestions per keyword to 3-5
   - Limits total keywords to 15-25
   - Applies clustering limits (3-5 clusters, 5-10 keywords per cluster)

3. **`GET /`** (Root endpoint)
   - Returns `testing_mode: true/false` in response

## Usage Examples

### Basic Keyword Research (Testing Mode)

```bash
curl -X POST https://api.example.com/api/v1/keywords/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["dog grooming", "pet care", "veterinary services"],
    "location": "United States",
    "language": "en"
  }'
```

**With Testing Mode**: Only processes first 3-5 keywords, limits suggestions to 3-5 per keyword.

**Without Testing Mode**: Processes all keywords, up to 20 suggestions per keyword.

### Enhanced Keyword Analysis (Testing Mode)

```bash
curl -X POST https://api.example.com/api/v1/keywords/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["dog grooming"],
    "max_suggestions_per_keyword": 150,
    "location": "United States",
    "language": "en"
  }'
```

**With Testing Mode**: 
- Limits to 3-5 primary keywords
- Reduces `max_suggestions_per_keyword` from 150 to 5
- Limits total keywords to 15-25
- Limits clusters to 3-5
- Limits keywords per cluster to 5-10

**Without Testing Mode**: Uses requested limits (up to 150 suggestions, 200 total keywords).

## Logging

When testing mode is active, the following log messages are generated:

```
🧪 TESTING MODE: Limited keywords from 10 to 5
🧪 TESTING MODE: Limited suggestions from 150 to 5
🧪 TESTING MODE: Keyword limits - 5 primary, 5 suggestions/keyword, 25 total max
🧪 TESTING MODE: Clustering limits - 5 clusters, 10 keywords per cluster
```

## Cost/Time Savings

### Estimated Reductions

- **API calls**: 70-80% reduction
- **Processing time**: 60-70% reduction
- **Data transfer**: 75-85% reduction
- **Storage**: 70-80% reduction

### Testing Coverage

Despite reduced limits, testing mode still covers:
- ✅ All features and functionality
- ✅ Data flow and UI components
- ✅ API integration
- ✅ Error handling
- ✅ Clustering and analysis algorithms

## Recommended Test Scenarios

### Scenario 1: Basic Keyword Research
- 1 primary keyword
- 3 related keywords
- 3 long-tail keywords
- **Total**: ~7 keywords

### Scenario 2: Cluster Testing
- 3 primary keywords
- 2 related per keyword
- 2 long-tail per keyword
- **Total**: ~15 keywords, 3-5 clusters

### Scenario 3: Full Workflow
- 5 primary keywords
- 3 related per keyword
- 3 long-tail per keyword
- 2-3 clusters
- **Total**: ~25 keywords

## Disabling Testing Mode

To disable testing mode and use full limits:

```bash
# Remove environment variable or set to false
export TESTING_MODE=false

# Or in Cloud Run
gcloud run services update blog-writer-api-dev \
  --update-env-vars TESTING_MODE=false \
  --region=europe-west9
```

## Verification

Check if testing mode is active:

```bash
curl https://api.example.com/ | jq '.testing_mode'
```

Should return `true` or `false`.

## Notes

- Testing mode is **opt-in** - defaults to `false` if not set
- Limits are applied **automatically** when enabled
- All limits are **configurable** via the `testing_limits.py` module
- Logging provides **visibility** into when limits are applied
- **No breaking changes** - existing API contracts remain unchanged

