# DataForSEO SERP Endpoints Analysis

## Current Implementation

### Endpoint Used
- **Endpoint:** `serp/google/organic/live/advanced`
- **Base URL:** `https://api.dataforseo.com/v3`
- **Full URL:** `https://api.dataforseo.com/v3/serp/google/organic/live/advanced`
- **Method:** POST
- **Type:** Live (immediate results)

### Request Payload
```json
[{
  "keyword": "plumbers in miami",
  "location_name": "United States",
  "language_code": "en",
  "depth": 10,
  "people_also_ask_click_depth": 2
}]
```

### Expected Response Structure (from DataForSEO docs)
```json
{
  "version": "0.1.20251117",
  "status_code": 20000,
  "status_message": "Ok.",
  "time": "2.5 sec.",
  "cost": 0.01,
  "tasks_count": 1,
  "tasks_error": 0,
  "tasks": [
    {
      "id": "...",
      "status_code": 20000,
      "status_message": "Ok.",
      "time": "2.5 sec.",
      "cost": 0.01,
      "result_count": 1,
      "path": ["v3", "serp", "google", "organic", "live", "advanced"],
      "data": {...},
      "result": [
        {
          "keyword": "plumbers in miami",
          "location_code": 2840,
          "language_code": "en",
          "check_url": "...",
          "datetime": "...",
          "items": [
            {
              "type": "organic",
              "rank_group": 1,
              "rank_absolute": 1,
              "position": "1",
              "xpath": "...",
              "title": "...",
              "url": "...",
              "domain": "...",
              "description": "...",
              "breadcrumb": "..."
            },
            {
              "type": "people_also_ask",
              "items": [
                {
                  "type": "people_also_ask_element",
                  "rank_group": 1,
                  "rank_absolute": 1,
                  "position": "1",
                  "xpath": "...",
                  "question": "...",
                  "title": "...",
                  "url": "...",
                  "description": "..."
                }
              ]
            },
            {
              "type": "featured_snippet",
              "rank_group": 1,
              "rank_absolute": 1,
              "position": "1",
              "xpath": "...",
              "title": "...",
              "url": "...",
              "domain": "...",
              "description": "...",
              "text": "..."
            }
          ]
        }
      ]
    }
  ]
}
```

## Available SERP Endpoints

### Google SERP Endpoints
1. **`serp/google/organic/live`** - Regular organic results (top 100)
2. **`serp/google/organic/live/advanced`** - Advanced with SERP features ✅ (Currently using)
3. **`serp/google/organic/standard`** - Standard method (async)
4. **`serp/google/organic/standard/advanced`** - Standard advanced
5. **`serp/google/organic/html`** - Raw HTML response

### Other SERP Endpoints
- `serp/google/images/live`
- `serp/google/news/live`
- `serp/google/videos/live`
- `serp/google/maps/live`
- `serp/google/shopping/live`

## Response Structure Analysis

### Key Points:
1. **Tasks Array:** Always present at top level
2. **Result Array:** Inside each task, `result` is an **array** (not a single object)
3. **Items Array:** Inside each result object, `items` contains the SERP elements
4. **Item Types:** Each item has a `type` field (organic, people_also_ask, featured_snippet, etc.)

### Current Code Logic:
```python
if data.get("tasks") and len(data["tasks"]) > 0:
    first_task = data["tasks"][0]
    result_data = first_task.get("result")  # This is an array
    
    if isinstance(result_data, list) and len(result_data) > 0:
        task_result = result_data[0]  # Get first result object
        # Then look for "items" in task_result
```

### Potential Issues:
1. **Result might be None:** For `/live` endpoints, if there's an error or the task isn't ready
2. **Result might be empty array:** If no results found
3. **Items might be missing:** If the result structure is different
4. **Task status:** Need to check `status_code` before processing result

## Recommendations

### 1. Check Task Status First
```python
first_task = data["tasks"][0]
task_status = first_task.get("status_code")
if task_status != 20000:  # 20000 = Ok
    logger.warning(f"Task failed with status {task_status}: {first_task.get('status_message')}")
    return result
```

### 2. Handle Empty Result Array
```python
result_data = first_task.get("result")
if not result_data or (isinstance(result_data, list) and len(result_data) == 0):
    logger.warning(f"No results returned for keyword: {keyword}")
    return result
```

### 3. Verify Items Exist
```python
if "items" not in task_result:
    logger.warning(f"No 'items' field in result for keyword: {keyword}")
    logger.debug(f"Result keys: {list(task_result.keys())}")
    return result
```

### 4. Alternative: Use Standard Method
If `/live` endpoints are unreliable, consider using `/standard` method:
- Post task
- Poll for completion
- Retrieve results

## Next Steps

1. ✅ Add task status checking
2. ✅ Add better logging for empty results
3. ✅ Verify response structure matches expectations
4. ⏳ Test with actual API response once deployed
5. ⏳ Consider fallback to standard method if live fails

