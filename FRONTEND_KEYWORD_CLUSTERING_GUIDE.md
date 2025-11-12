# Frontend Keyword Clustering Integration Guide

## Overview

The API now returns keywords with **parent topics** and clustering information. This guide explains how the frontend should handle this data for optimal display and user experience.

---

## API Response Structure

### `/api/v1/keywords/extract` Response

```json
{
  "extracted_keywords": ["keyword1", "keyword2", ...],
  "keywords_with_topics": [
    {
      "keyword": "pet grooming services",
      "parent_topic": "Pet Grooming",
      "cluster_score": 0.85,
      "category_type": "topic"
    },
    {
      "keyword": "why pet grooming services",
      "parent_topic": "Why",
      "cluster_score": 0.8,
      "category_type": "question"
    }
  ],
  "clusters": [
    {
      "parent_topic": "Pet Grooming",
      "keywords": ["pet grooming services", "pet grooming tips"],
      "cluster_score": 0.85,
      "category_type": "topic",
      "keyword_count": 2
    }
  ],
  "cluster_summary": {
    "total_keywords": 15,
    "cluster_count": 5,
    "unclustered_count": 0
  }
}
```

### `/api/v1/keywords/enhanced` Response

```json
{
  "enhanced_analysis": {
    "pet grooming services": {
      "search_volume": 1200,
      "difficulty": "easy",
      "competition": 0.4,
      "cpc": 1.2,
      "parent_topic": "Pet Grooming",
      "category_type": "topic",
      "cluster_score": 0.85,
      "recommended": true,
      "related_keywords": [...],
      "long_tail_keywords": [...]
    }
  },
  "clusters": [...],
  "cluster_summary": {...}
}
```

---

## Frontend Implementation Recommendations

### 1. **Display Parent Topics Properly**

**✅ DO:**
- Display the **full parent topic** from the API response
- Use `parent_topic` field directly: `keyword.parent_topic`
- Group keywords by parent topic in UI

**❌ DON'T:**
- Extract first word from keyword string
- Parse keywords to guess parent topics
- Use single-word extraction (e.g., "Pet" from "pet grooming services")

### 2. **Group Keywords by Parent Topic**

```typescript
// Example: Group keywords by parent topic
interface KeywordWithTopic {
  keyword: string;
  parent_topic: string;
  cluster_score?: number;
  category_type?: string;
  // ... other fields
}

function groupKeywordsByParentTopic(
  keywords: KeywordWithTopic[]
): Map<string, KeywordWithTopic[]> {
  const grouped = new Map<string, KeywordWithTopic[]>();
  
  keywords.forEach(kw => {
    const topic = kw.parent_topic || 'Uncategorized';
    if (!grouped.has(topic)) {
      grouped.set(topic, []);
    }
    grouped.get(topic)!.push(kw);
  });
  
  return grouped;
}
```

### 3. **Display Clusters in UI**

```typescript
// Example: Display clusters with parent topics
function KeywordClusters({ clusters }: { clusters: Cluster[] }) {
  return (
    <div className="keyword-clusters">
      {clusters.map(cluster => (
        <div key={cluster.parent_topic} className="cluster">
          <h3>{cluster.parent_topic}</h3>
          <p className="cluster-meta">
            {cluster.keyword_count} keywords • 
            Score: {(cluster.cluster_score * 100).toFixed(0)}% • 
            Type: {cluster.category_type}
          </p>
          <ul>
            {cluster.keywords.map(keyword => (
              <li key={keyword}>{keyword}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
```

### 4. **Table Display with Parent Topics**

```typescript
// Example: Table row component
function KeywordTableRow({ keyword }: { keyword: KeywordWithTopic }) {
  return (
    <tr>
      <td>{keyword.keyword}</td>
      <td>
        <span className="parent-topic-badge">
          {keyword.parent_topic}
        </span>
      </td>
      <td>{keyword.search_volume || '-'}</td>
      <td>{keyword.difficulty}</td>
      <td>{keyword.competition}</td>
      {/* ... other columns */}
    </tr>
  );
}
```

### 5. **Filter by Parent Topic**

```typescript
// Example: Filter dropdown
function ParentTopicFilter({ 
  clusters, 
  onFilterChange 
}: { 
  clusters: Cluster[];
  onFilterChange: (topic: string | null) => void;
}) {
  const topics = clusters.map(c => c.parent_topic);
  
  return (
    <select onChange={(e) => onFilterChange(e.target.value || null)}>
      <option value="">All Topics</option>
      {topics.map(topic => (
        <option key={topic} value={topic}>{topic}</option>
      ))}
    </select>
  );
}
```

### 6. **Sort by Cluster Score**

```typescript
// Example: Sort keywords by cluster relevance
function sortKeywordsByClusterScore(
  keywords: KeywordWithTopic[]
): KeywordWithTopic[] {
  return [...keywords].sort((a, b) => {
    const scoreA = a.cluster_score || 0;
    const scoreB = b.cluster_score || 0;
    return scoreB - scoreA; // Descending
  });
}
```

---

## Visual Recommendations

### Parent Topic Display

1. **Badge/Pill Style:**
   ```
   [Pet Grooming] pet grooming services
   [Why] why pet grooming services
   ```

2. **Grouped Sections:**
   ```
   📁 Pet Grooming (8 keywords)
     • pet grooming services
     • pet grooming tips
     • ...
   
   📁 Why (3 keywords)
     • why pet grooming services
     • ...
   ```

3. **Table Column:**
   ```
   KEYWORD              | PARENT TOPIC      | ...
   pet grooming services| Pet Grooming      | ...
   why pet grooming... | Why               | ...
   ```

### Category Type Indicators

Use visual indicators for different category types:

- **Question** (`category_type: "question"`): Use `?` icon or "Q:" prefix
- **Action** (`category_type: "action"`): Use action icon (⚡, 🎯)
- **Topic** (`category_type: "topic"`): Use topic icon (📁, 📝)
- **Entity** (`category_type: "entity"`): Use entity icon (🏢, 👤)

---

## Error Handling

### Fallback Behavior

If `parent_topic` is missing or empty:

```typescript
function getParentTopic(keyword: KeywordWithTopic): string {
  // Use API-provided parent topic
  if (keyword.parent_topic) {
    return keyword.parent_topic;
  }
  
  // Fallback: Extract from keyword (only if API doesn't provide)
  const words = keyword.keyword.split(' ');
  if (words.length > 1) {
    // Use first 2-3 meaningful words
    return words.slice(0, 2).join(' ').trim();
  }
  
  return 'Uncategorized';
}
```

---

## Performance Considerations

1. **Caching:** Cache cluster data to avoid re-clustering on every render
2. **Virtualization:** Use virtual scrolling for large keyword lists
3. **Memoization:** Memoize grouped/clustered data structures

```typescript
import { useMemo } from 'react';

function useGroupedKeywords(keywords: KeywordWithTopic[]) {
  return useMemo(() => {
    return groupKeywordsByParentTopic(keywords);
  }, [keywords]);
}
```

---

## Migration Guide

### Before (Incorrect)

```typescript
// ❌ DON'T: Extract first word from keyword
const parentTopic = keyword.split(' ')[0]; // "Pet" from "pet grooming services"
```

### After (Correct)

```typescript
// ✅ DO: Use API-provided parent topic
const parentTopic = keyword.parent_topic; // "Pet Grooming" from API
```

---

## Example: Complete Component

```typescript
import React, { useMemo } from 'react';

interface Keyword {
  keyword: string;
  parent_topic: string;
  cluster_score?: number;
  category_type?: string;
  search_volume?: number;
  difficulty?: string;
  competition?: number;
}

interface KeywordTableProps {
  keywords: Keyword[];
}

export function KeywordTable({ keywords }: KeywordTableProps) {
  const groupedKeywords = useMemo(() => {
    return groupKeywordsByParentTopic(keywords);
  }, [keywords]);
  
  return (
    <div className="keyword-table-container">
      <table>
        <thead>
          <tr>
            <th>Keyword</th>
            <th>Parent Topic</th>
            <th>Search Volume</th>
            <th>Difficulty</th>
            <th>Competition</th>
          </tr>
        </thead>
        <tbody>
          {keywords.map((kw, idx) => (
            <tr key={idx}>
              <td>{kw.keyword}</td>
              <td>
                <span className="parent-topic">
                  {kw.parent_topic}
                </span>
              </td>
              <td>{kw.search_volume || '-'}</td>
              <td>{kw.difficulty || '-'}</td>
              <td>{kw.competition ? `${(kw.competition * 100).toFixed(0)}%` : '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

## Summary

✅ **Use `parent_topic` field directly from API**  
✅ **Group keywords by parent topic for better UX**  
✅ **Display full parent topic text (not single words)**  
✅ **Use cluster information for filtering/sorting**  
✅ **Handle missing parent topics gracefully**  

❌ **Don't parse keywords to extract parent topics**  
❌ **Don't use single-word extraction**  
❌ **Don't ignore the clustering data**

The API now provides semantic clustering and parent topic extraction. The frontend should use this data directly rather than attempting to parse keywords.

