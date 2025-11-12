# Frontend Migration Guide: Getting 150+ Keywords

## Quick Answer

**YES**, you need to update your frontend API calls to request 150 keywords instead of the default 20.

---

## Required Frontend Changes

### 1. Update `/api/v1/keywords/suggest` Call

**Before (Current - Only 14-20 keywords):**
```typescript
const response = await fetch('/api/v1/keywords/suggest', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    keyword: 'pet care'
    // No limit parameter = defaults to 20
  })
});
```

**After (150+ keywords):**
```typescript
const response = await fetch('/api/v1/keywords/suggest', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    keyword: 'pet care',
    limit: 150  // ✅ ADD THIS - requests up to 150 suggestions
  })
});
```

---

### 2. Update `/api/v1/keywords/enhanced` Call

**Before (Current - Only analyzes provided keywords):**
```typescript
const response = await fetch('/api/v1/keywords/enhanced', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    keywords: ['pet care']
    // No max_suggestions_per_keyword = defaults to 20
  })
});
```

**After (150+ keywords with auto-suggestions):**
```typescript
const response = await fetch('/api/v1/keywords/enhanced', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    keywords: ['pet care'],
    max_suggestions_per_keyword: 150  // ✅ ADD THIS - auto-generates 150 suggestions per keyword
  })
});
```

---

## Response Structure Changes

### `/api/v1/keywords/suggest` Response

**New fields added:**
```typescript
{
  keyword_suggestions: string[],  // Up to 150 keywords
  suggestions_with_topics: Array<{
    keyword: string;
    parent_topic: string;
    cluster_score: number;
    category_type: string;
  }>,
  total_suggestions: number,  // ✅ NEW - total count
  clusters: Array<{...}>,
  cluster_summary: {...}
}
```

### `/api/v1/keywords/enhanced` Response

**New fields added:**
```typescript
{
  enhanced_analysis: {...},
  total_keywords: number,  // ✅ NEW - total keywords analyzed
  original_keywords: string[],  // ✅ NEW - seed keywords you provided
  suggested_keywords: string[],  // ✅ NEW - auto-generated suggestions
  clusters: Array<{...}>,
  cluster_summary: {...}
}
```

---

## Example: Complete Frontend Implementation

```typescript
// Function to get comprehensive keyword research (150+ keywords)
async function getComprehensiveKeywords(seedKeyword: string) {
  // Step 1: Get 150 keyword suggestions
  const suggestResponse = await fetch('/api/v1/keywords/suggest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      keyword: seedKeyword,
      limit: 150  // ✅ Request 150 suggestions
    })
  });
  
  const suggestData = await suggestResponse.json();
  console.log(`Got ${suggestData.total_suggestions} keyword suggestions`);
  
  // Step 2: Analyze all keywords with enhanced analysis
  const analyzeResponse = await fetch('/api/v1/keywords/enhanced', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      keywords: suggestData.keyword_suggestions.slice(0, 200),  // Max 200 at once
      max_suggestions_per_keyword: 0  // Already have suggestions, don't generate more
    })
  });
  
  const analyzeData = await analyzeResponse.json();
  console.log(`Analyzed ${analyzeData.total_keywords} keywords`);
  
  return analyzeData;
}

// OR: Use enhanced endpoint with auto-suggestions
async function getComprehensiveKeywordsAuto(seedKeyword: string) {
  const response = await fetch('/api/v1/keywords/enhanced', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      keywords: [seedKeyword],
      max_suggestions_per_keyword: 150  // ✅ Auto-generate 150 suggestions
    })
  });
  
  const data = await response.json();
  console.log(`Total keywords: ${data.total_keywords}`);
  console.log(`Original: ${data.original_keywords.length}`);
  console.log(`Suggested: ${data.suggested_keywords.length}`);
  
  return data;
}
```

---

## Migration Checklist

- [ ] Update `/api/v1/keywords/suggest` calls to include `limit: 150`
- [ ] Update `/api/v1/keywords/enhanced` calls to include `max_suggestions_per_keyword: 150`
- [ ] Update UI to handle 150+ keywords (virtual scrolling, pagination, etc.)
- [ ] Update keyword display to use `suggestions_with_topics` for parent topics
- [ ] Update keyword count displays to use `total_keywords` or `total_suggestions`
- [ ] Test with "pet care" keyword to verify 150+ results

---

## Performance Considerations

### Handling 150+ Keywords in UI

1. **Virtual Scrolling**: Use virtual scrolling for large keyword lists
   ```typescript
   import { useVirtualizer } from '@tanstack/react-virtual';
   
   const virtualizer = useVirtualizer({
     count: keywords.length,
     getScrollElement: () => parentRef.current,
     estimateSize: () => 50,
   });
   ```

2. **Pagination**: Paginate keywords if needed
   ```typescript
   const [page, setPage] = useState(1);
   const keywordsPerPage = 50;
   const paginatedKeywords = keywords.slice(
     (page - 1) * keywordsPerPage,
     page * keywordsPerPage
   );
   ```

3. **Filtering**: Add search/filter for large lists
   ```typescript
   const [searchTerm, setSearchTerm] = useState('');
   const filteredKeywords = keywords.filter(kw =>
     kw.keyword.toLowerCase().includes(searchTerm.toLowerCase())
   );
   ```

---

## Testing

After updating your frontend:

1. **Test with "pet care":**
   ```typescript
   const result = await getComprehensiveKeywords('pet care');
   console.assert(result.total_keywords >= 150, 'Should have 150+ keywords');
   ```

2. **Verify parent topics:**
   ```typescript
   result.suggestions_with_topics.forEach(kw => {
     console.assert(kw.parent_topic, 'Each keyword should have parent_topic');
   });
   ```

3. **Check clustering:**
   ```typescript
   console.assert(result.clusters.length > 0, 'Should have clusters');
   console.log(`Found ${result.cluster_summary.cluster_count} clusters`);
   ```

---

## Summary

**Required Changes:**
1. ✅ Add `limit: 150` to `/api/v1/keywords/suggest` requests
2. ✅ Add `max_suggestions_per_keyword: 150` to `/api/v1/keywords/enhanced` requests
3. ✅ Update UI to handle 150+ keywords (virtual scrolling/pagination)
4. ✅ Use new response fields (`total_keywords`, `suggested_keywords`, etc.)

**No Changes Needed:**
- ❌ API endpoint URLs (same endpoints)
- ❌ Authentication/headers (same as before)
- ❌ Response structure (backward compatible, just more data)

The API is backward compatible - if you don't pass `limit` or `max_suggestions_per_keyword`, it will default to 20 (current behavior). To get 150+ keywords like AHREFs, you must explicitly request it.

