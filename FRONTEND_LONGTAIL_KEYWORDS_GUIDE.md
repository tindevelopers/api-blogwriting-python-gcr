# Frontend Guide: Accessing Longtail Keyword Suggestions

## Overview

The API supports longtail keyword suggestions (3+ words) through multiple endpoints. This guide shows you how to access them in your frontend.

---

## Method 1: Using `/api/v1/keywords/enhanced` (Recommended)

**Best for:** Getting longtail keywords with full SEO metrics

### Request

```typescript
const response = await fetch('/api/v1/keywords/enhanced', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    keywords: ['pet care'],
    max_suggestions_per_keyword: 150
  })
});

const data = await response.json();
```

### Accessing Longtail Keywords

**Option A: From `long_tail_keywords` field (per keyword)**
```typescript
// Get longtail keywords for a specific keyword
const keyword = 'pet care';
const longtailKeywords = data.enhanced_analysis[keyword]?.long_tail_keywords || [];

console.log('Longtail keywords:', longtailKeywords);
// Output: ["how to use pet care", "what is pet care", "pet care for beginners", ...]
```

**Option B: Filter all suggestions to get longtail keywords**
```typescript
// Get all keywords and filter for longtail (3+ words)
const allKeywords = Object.keys(data.enhanced_analysis);
const longtailKeywords = allKeywords.filter(
  kw => kw.split(' ').length >= 3
);

console.log(`Found ${longtailKeywords.length} longtail keywords`);
```

**Option C: Extract from `suggested_keywords` array**
```typescript
// Filter suggested keywords for longtail
const longtailFromSuggestions = data.suggested_keywords.filter(
  kw => kw.split(' ').length >= 3
);
```

### Complete Example

```typescript
async function getLongtailKeywords(seedKeyword: string) {
  const response = await fetch('/api/v1/keywords/enhanced', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      keywords: [seedKeyword],
      max_suggestions_per_keyword: 150
    })
  });
  
  const data = await response.json();
  
  // Method 1: Get from long_tail_keywords field
  const explicitLongtail = data.enhanced_analysis[seedKeyword]?.long_tail_keywords || [];
  
  // Method 2: Filter all analyzed keywords
  const allKeywords = Object.keys(data.enhanced_analysis);
  const filteredLongtail = allKeywords.filter(kw => kw.split(' ').length >= 3);
  
  // Method 3: Filter suggested keywords
  const suggestedLongtail = data.suggested_keywords?.filter(
    kw => kw.split(' ').length >= 3
  ) || [];
  
  // Combine all sources (deduplicate)
  const allLongtail = [
    ...explicitLongtail,
    ...filteredLongtail,
    ...suggestedLongtail
  ];
  
  const uniqueLongtail = [...new Set(allLongtail)];
  
  return {
    explicit: explicitLongtail,
    filtered: filteredLongtail,
    suggested: suggestedLongtail,
    all: uniqueLongtail,
    total: uniqueLongtail.length
  };
}

// Usage
const result = await getLongtailKeywords('pet care');
console.log(`Found ${result.total} unique longtail keywords`);
```

---

## Method 2: Using `/api/v1/keywords/suggest`

**Best for:** Quick longtail keyword discovery without full SEO analysis

### Request

```typescript
const response = await fetch('/api/v1/keywords/suggest', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    keyword: 'pet care',
    limit: 150
  })
});

const data = await response.json();
```

### Filtering for Longtail Keywords

```typescript
// Filter suggestions to get only longtail keywords (3+ words)
const longtailKeywords = data.keyword_suggestions.filter(
  keyword => keyword.split(' ').length >= 3
);

console.log(`Found ${longtailKeywords.length} longtail keywords`);
```

### With Parent Topics

```typescript
// Get longtail keywords with their parent topics
const longtailWithTopics = data.suggestions_with_topics.filter(
  item => item.keyword.split(' ').length >= 3
);

// Group by parent topic
const groupedByTopic = longtailWithTopics.reduce((acc, item) => {
  const topic = item.parent_topic;
  if (!acc[topic]) acc[topic] = [];
  acc[topic].push(item);
  return acc;
}, {});

console.log('Longtail keywords grouped by topic:', groupedByTopic);
```

---

## Method 3: Filtering Strategy Helper Function

Create a reusable utility function:

```typescript
/**
 * Extract longtail keywords from API responses
 */
export function extractLongtailKeywords(
  data: any,
  minWords: number = 3
): {
  keywords: string[];
  withMetrics?: Array<{
    keyword: string;
    search_volume?: number;
    difficulty?: string;
    parent_topic?: string;
  }>;
} {
  const longtailKeywords: string[] = [];
  const withMetrics: any[] = [];
  
  // Method 1: From enhanced_analysis long_tail_keywords field
  if (data.enhanced_analysis) {
    Object.values(data.enhanced_analysis).forEach((analysis: any) => {
      if (analysis.long_tail_keywords) {
        longtailKeywords.push(...analysis.long_tail_keywords);
      }
    });
  }
  
  // Method 2: Filter keyword_suggestions
  if (data.keyword_suggestions) {
    const filtered = data.keyword_suggestions.filter(
      (kw: string) => kw.split(' ').length >= minWords
    );
    longtailKeywords.push(...filtered);
  }
  
  // Method 3: Filter suggestions_with_topics
  if (data.suggestions_with_topics) {
    const filtered = data.suggestions_with_topics.filter(
      (item: any) => item.keyword.split(' ').length >= minWords
    );
    filtered.forEach((item: any) => {
      longtailKeywords.push(item.keyword);
      withMetrics.push({
        keyword: item.keyword,
        parent_topic: item.parent_topic,
        cluster_score: item.cluster_score,
        category_type: item.category_type
      });
    });
  }
  
  // Method 4: Filter enhanced_analysis keys
  if (data.enhanced_analysis) {
    Object.keys(data.enhanced_analysis).forEach(keyword => {
      if (keyword.split(' ').length >= minWords) {
        longtailKeywords.push(keyword);
        const analysis = data.enhanced_analysis[keyword];
        withMetrics.push({
          keyword,
          search_volume: analysis.search_volume,
          difficulty: analysis.difficulty,
          parent_topic: analysis.parent_topic,
          cluster_score: analysis.cluster_score
        });
      }
    });
  }
  
  // Deduplicate
  const uniqueKeywords = [...new Set(longtailKeywords)];
  
  return {
    keywords: uniqueKeywords,
    withMetrics: withMetrics.length > 0 ? withMetrics : undefined
  };
}

// Usage
const response = await fetch('/api/v1/keywords/enhanced', {...});
const data = await response.json();
const longtail = extractLongtailKeywords(data);

console.log(`Found ${longtail.keywords.length} longtail keywords`);
if (longtail.withMetrics) {
  console.log('With metrics:', longtail.withMetrics);
}
```

---

## React Component Example

```typescript
import React, { useState, useEffect } from 'react';

interface LongtailKeyword {
  keyword: string;
  search_volume?: number;
  difficulty?: string;
  parent_topic?: string;
  cluster_score?: number;
}

export function LongtailKeywordsList({ seedKeyword }: { seedKeyword: string }) {
  const [longtailKeywords, setLongtailKeywords] = useState<LongtailKeyword[]>([]);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    async function fetchLongtailKeywords() {
      setLoading(true);
      try {
        const response = await fetch('/api/v1/keywords/enhanced', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            keywords: [seedKeyword],
            max_suggestions_per_keyword: 150
          })
        });
        
        const data = await response.json();
        
        // Extract longtail keywords with metrics
        const longtail: LongtailKeyword[] = [];
        
        // From explicit long_tail_keywords field
        const explicit = data.enhanced_analysis[seedKeyword]?.long_tail_keywords || [];
        explicit.forEach(kw => {
          longtail.push({
            keyword: kw,
            parent_topic: data.enhanced_analysis[seedKeyword]?.parent_topic
          });
        });
        
        // From all analyzed keywords (filter 3+ words)
        Object.entries(data.enhanced_analysis).forEach(([kw, analysis]: [string, any]) => {
          if (kw.split(' ').length >= 3 && !explicit.includes(kw)) {
            longtail.push({
              keyword: kw,
              search_volume: analysis.search_volume,
              difficulty: analysis.difficulty,
              parent_topic: analysis.parent_topic,
              cluster_score: analysis.cluster_score
            });
          }
        });
        
        // Deduplicate
        const unique = Array.from(
          new Map(longtail.map(item => [item.keyword, item])).values()
        );
        
        setLongtailKeywords(unique);
      } catch (error) {
        console.error('Failed to fetch longtail keywords:', error);
      } finally {
        setLoading(false);
      }
    }
    
    if (seedKeyword) {
      fetchLongtailKeywords();
    }
  }, [seedKeyword]);
  
  if (loading) return <div>Loading longtail keywords...</div>;
  
  return (
    <div className="longtail-keywords">
      <h3>Longtail Keywords ({longtailKeywords.length})</h3>
      <ul>
        {longtailKeywords.map((item, idx) => (
          <li key={idx}>
            <strong>{item.keyword}</strong>
            {item.parent_topic && (
              <span className="badge">{item.parent_topic}</span>
            )}
            {item.search_volume && (
              <span className="metric">SV: {item.search_volume.toLocaleString()}</span>
            )}
            {item.difficulty && (
              <span className="metric">Difficulty: {item.difficulty}</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## Best Practices

### 1. **Use Enhanced Endpoint for Full Metrics**
```typescript
// ✅ Best: Get longtail keywords with SEO metrics
const data = await fetch('/api/v1/keywords/enhanced', {...});
const longtail = data.enhanced_analysis[keyword].long_tail_keywords;
```

### 2. **Filter by Word Count**
```typescript
// ✅ Filter for longtail (3+ words)
const longtail = keywords.filter(kw => kw.split(' ').length >= 3);
```

### 3. **Combine Multiple Sources**
```typescript
// ✅ Get from multiple sources and deduplicate
const allLongtail = [
  ...data.enhanced_analysis[keyword].long_tail_keywords,
  ...data.suggested_keywords.filter(kw => kw.split(' ').length >= 3),
  ...Object.keys(data.enhanced_analysis).filter(kw => kw.split(' ').length >= 3)
];
const unique = [...new Set(allLongtail)];
```

### 4. **Group by Parent Topic**
```typescript
// ✅ Group longtail keywords by parent topic
const grouped = longtailKeywords.reduce((acc, kw) => {
  const topic = kw.parent_topic || 'Other';
  if (!acc[topic]) acc[topic] = [];
  acc[topic].push(kw);
  return acc;
}, {});
```

---

## Summary

**Recommended Approach:**

1. **Use `/api/v1/keywords/enhanced`** with `max_suggestions_per_keyword: 150`
2. **Access `long_tail_keywords` field** from the response
3. **Also filter all keywords** by word count (3+) for comprehensive coverage
4. **Combine and deduplicate** for complete longtail keyword list

**Quick Example:**
```typescript
const response = await fetch('/api/v1/keywords/enhanced', {
  method: 'POST',
  body: JSON.stringify({
    keywords: ['pet care'],
    max_suggestions_per_keyword: 150
  })
});

const data = await response.json();

// Get explicit longtail keywords
const explicit = data.enhanced_analysis['pet care'].long_tail_keywords;

// Filter all keywords for longtail
const filtered = Object.keys(data.enhanced_analysis).filter(
  kw => kw.split(' ').length >= 3
);

// Combine and deduplicate
const allLongtail = [...new Set([...explicit, ...filtered])];
```

This gives you comprehensive longtail keyword coverage with full SEO metrics!

