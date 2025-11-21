# Frontend Integration Guide: Keyword Search Updates

**Version**: 2.0.0  
**Date**: 2025-11-19  
**Status**: ✅ Ready for Integration

---

## 🎯 Overview

The keyword search endpoints have been significantly enhanced with new data fields and improved accuracy. This guide provides everything your frontend team needs to integrate these updates.

### Key Improvements

1. **Real Search Volume Data** - Now returns actual search volumes (e.g., 135,000) instead of 0
2. **Enhanced Related Keywords** - Graph-based discovery with full metrics
3. **Question & Topic Categorization** - Automatic categorization of keyword ideas
4. **Global & Country Breakdown** - Search volume by country and global totals
5. **Trend Analysis** - Trend scores and monthly search history
6. **Traffic Metrics** - Clicks, CPS (cost per sale), and traffic potential

---

## 📋 What Changed

### Endpoint: `POST /api/v1/keywords/enhanced`

**Base URL:** `https://blog-writer-api-dev-613248238610.europe-west9.run.app`

### New Response Fields

The response now includes these **new fields** in addition to existing ones:

```typescript
{
  enhanced_analysis: {
    [keyword: string]: {
      // ✅ EXISTING FIELDS (still present, unchanged)
      search_volume: number;              // Now returns REAL values (was 0 before)
      difficulty: string;                 // "easy" | "medium" | "hard" | "very_easy" | "very_hard"
      difficulty_score: number;          // 0-100 numeric score
      competition: number;                // 0.0 - 1.0
      cpc: number;                        // Cost per click (USD)
      recommended: boolean;
      reason: string;
      related_keywords: string[];         // Basic related keywords (still present)
      long_tail_keywords: string[];       // Long-tail variations (still present)
      parent_topic: string;
      category_type: string;
      cluster_score: number;
      
      // 🆕 NEW FIELDS (added in this update)
      global_search_volume?: number;     // Global monthly search volume
      search_volume_by_country?: {       // Search volume breakdown by country
        [country: string]: number;
      };
      monthly_searches?: Array<{         // Historical monthly search data
        month: string;                    // Format: "YYYY-MM"
        search_volume: number;
      }>;
      clicks?: number;                     // Estimated monthly clicks
      cps?: number;                       // Cost per sale
      trend_score?: number;               // -1.0 to 1.0 (trending up/down)
      
      // 🆕 Enhanced Related Keywords (with full metrics)
      related_keywords_enhanced?: Array<{
        keyword: string;
        search_volume: number;
        cpc: number;
        competition: number;
        difficulty_score: number;
        difficulty?: string;
      }>;
      
      // 🆕 Question-Type Keywords
      questions?: Array<{
        keyword: string;
        search_volume: number;
        cpc: number;
        competition: number;
        difficulty_score: number;
        difficulty?: string;
      }>;
      
      // 🆕 Topic-Type Keywords
      topics?: Array<{
        keyword: string;
        search_volume: number;
        cpc: number;
        competition: number;
        difficulty_score: number;
        difficulty?: string;
      }>;
      
      // 🆕 All Keyword Ideas Combined
      keyword_ideas?: Array<{
        keyword: string;
        search_volume: number;
        cpc: number;
        competition: number;
        difficulty_score: number;
        difficulty?: string;
        type?: "question" | "topic";
      }>;
    }
  },
  // ... rest of response unchanged
}
```

---

## 🔄 Migration Guide

### Step 1: Update TypeScript Types

**Before:**
```typescript
interface KeywordAnalysis {
  search_volume: number;
  difficulty: string;
  competition: number;
  cpc: number;
  recommended: boolean;
  reason: string;
  related_keywords: string[];
  long_tail_keywords: string[];
}
```

**After:**
```typescript
interface RelatedKeyword {
  keyword: string;
  search_volume: number;
  cpc: number;
  competition: number;
  difficulty_score: number;
  difficulty?: string;
}

interface KeywordAnalysis {
  // Existing fields
  search_volume: number;
  difficulty: string;
  difficulty_score: number;
  competition: number;
  cpc: number;
  recommended: boolean;
  reason: string;
  related_keywords: string[];
  long_tail_keywords: string[];
  
  // New fields (all optional for backward compatibility)
  global_search_volume?: number;
  search_volume_by_country?: Record<string, number>;
  monthly_searches?: Array<{ month: string; search_volume: number }>;
  clicks?: number;
  cps?: number;
  trend_score?: number;
  related_keywords_enhanced?: RelatedKeyword[];
  questions?: RelatedKeyword[];
  topics?: RelatedKeyword[];
  keyword_ideas?: Array<RelatedKeyword & { type?: "question" | "topic" }>;
}
```

### Step 2: Update Display Components

#### Example: Keyword Card Component

**Before:**
```typescript
function KeywordCard({ keyword, data }: { keyword: string; data: KeywordAnalysis }) {
  return (
    <div className="keyword-card">
      <h3>{keyword}</h3>
      <div className="metrics">
        <div>Search Volume: {data.search_volume || 'N/A'}</div>
        <div>CPC: ${data.cpc.toFixed(2)}</div>
        <div>Difficulty: {data.difficulty}</div>
      </div>
      {data.related_keywords.length > 0 && (
        <div className="related-keywords">
          <h4>Related Keywords</h4>
          <ul>
            {data.related_keywords.map(kw => <li key={kw}>{kw}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
```

**After:**
```typescript
function KeywordCard({ keyword, data }: { keyword: string; data: KeywordAnalysis }) {
  return (
    <div className="keyword-card">
      <h3>{keyword}</h3>
      
      {/* Primary Metrics */}
      <div className="metrics">
        <div className="metric">
          <label>Search Volume</label>
          <span className="value large">
            {data.search_volume?.toLocaleString() || 'N/A'}
          </span>
          {data.global_search_volume && (
            <span className="sub-value">
              Global: {data.global_search_volume.toLocaleString()}
            </span>
          )}
        </div>
        
        <div className="metric">
          <label>CPC</label>
          <span className="value">${data.cpc.toFixed(2)}</span>
        </div>
        
        <div className="metric">
          <label>Difficulty</label>
          <span className={`badge difficulty-${data.difficulty}`}>
            {data.difficulty}
          </span>
          {data.difficulty_score !== undefined && (
            <span className="sub-value">Score: {data.difficulty_score}/100</span>
          )}
        </div>
        
        {data.trend_score !== undefined && (
          <div className="metric">
            <label>Trend</label>
            <span className={`trend ${data.trend_score > 0 ? 'up' : 'down'}`}>
              {data.trend_score > 0 ? '↑' : '↓'} {Math.abs(data.trend_score * 100).toFixed(0)}%
            </span>
          </div>
        )}
      </div>
      
      {/* Enhanced Related Keywords */}
      {data.related_keywords_enhanced && data.related_keywords_enhanced.length > 0 && (
        <div className="related-keywords-enhanced">
          <h4>Related Keywords ({data.related_keywords_enhanced.length})</h4>
          <div className="keyword-grid">
            {data.related_keywords_enhanced.slice(0, 5).map((rk, idx) => (
              <div key={idx} className="related-keyword-item">
                <span className="keyword">{rk.keyword}</span>
                <div className="mini-metrics">
                  <span>Vol: {rk.search_volume.toLocaleString()}</span>
                  <span>CPC: ${rk.cpc.toFixed(2)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Questions */}
      {data.questions && data.questions.length > 0 && (
        <div className="questions-section">
          <h4>Question Keywords ({data.questions.length})</h4>
          <ul>
            {data.questions.slice(0, 3).map((q, idx) => (
              <li key={idx}>
                {q.keyword} 
                <span className="mini-badge">Vol: {q.search_volume.toLocaleString()}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {/* Topics */}
      {data.topics && data.topics.length > 0 && (
        <div className="topics-section">
          <h4>Topic Keywords ({data.topics.length})</h4>
          <ul>
            {data.topics.slice(0, 3).map((t, idx) => (
              <li key={idx}>
                {t.keyword}
                <span className="mini-badge">Vol: {t.search_volume.toLocaleString()}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {/* Monthly Search Trends */}
      {data.monthly_searches && data.monthly_searches.length > 0 && (
        <div className="trend-chart">
          <h4>Monthly Search Trends</h4>
          <TrendChart data={data.monthly_searches} />
        </div>
      )}
    </div>
  );
}
```

---

## 📊 Display Examples

### 1. Search Volume Display

```typescript
function SearchVolumeDisplay({ volume, globalVolume }: { volume: number; globalVolume?: number }) {
  return (
    <div className="search-volume">
      <span className="primary-value">
        {formatNumber(volume)}
      </span>
      {globalVolume && (
        <span className="global-indicator">
          🌍 Global: {formatNumber(globalVolume)}
        </span>
      )}
    </div>
  );
}

function formatNumber(num: number): string {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
}
```

### 2. Trend Score Indicator

```typescript
function TrendIndicator({ score }: { score: number }) {
  const isPositive = score > 0;
  const percentage = Math.abs(score * 100);
  
  return (
    <div className={`trend-indicator ${isPositive ? 'trending-up' : 'trending-down'}`}>
      <span className="arrow">{isPositive ? '↑' : '↓'}</span>
      <span className="percentage">{percentage.toFixed(0)}%</span>
      <span className="label">{isPositive ? 'Trending Up' : 'Trending Down'}</span>
    </div>
  );
}
```

### 3. Enhanced Related Keywords Table

```typescript
function RelatedKeywordsTable({ keywords }: { keywords: RelatedKeyword[] }) {
  return (
    <table className="related-keywords-table">
      <thead>
        <tr>
          <th>Keyword</th>
          <th>Search Volume</th>
          <th>CPC</th>
          <th>Competition</th>
          <th>Difficulty</th>
        </tr>
      </thead>
      <tbody>
        {keywords.map((kw, idx) => (
          <tr key={idx}>
            <td className="keyword-cell">{kw.keyword}</td>
            <td>{kw.search_volume.toLocaleString()}</td>
            <td>${kw.cpc.toFixed(2)}</td>
            <td>{(kw.competition * 100).toFixed(0)}%</td>
            <td>
              <span className={`badge difficulty-${kw.difficulty || 'medium'}`}>
                {kw.difficulty_score}/100
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

### 4. Questions vs Topics Tabs

```typescript
function KeywordIdeasTabs({ questions, topics }: { 
  questions?: RelatedKeyword[]; 
  topics?: RelatedKeyword[] 
}) {
  const [activeTab, setActiveTab] = useState<'questions' | 'topics'>('questions');
  
  return (
    <div className="keyword-ideas-tabs">
      <div className="tab-headers">
        <button 
          className={activeTab === 'questions' ? 'active' : ''}
          onClick={() => setActiveTab('questions')}
        >
          Questions ({questions?.length || 0})
        </button>
        <button 
          className={activeTab === 'topics' ? 'active' : ''}
          onClick={() => setActiveTab('topics')}
        >
          Topics ({topics?.length || 0})
        </button>
      </div>
      
      <div className="tab-content">
        {activeTab === 'questions' && questions && (
          <KeywordList keywords={questions} />
        )}
        {activeTab === 'topics' && topics && (
          <KeywordList keywords={topics} />
        )}
      </div>
    </div>
  );
}
```

---

## 🎨 CSS Styling Examples

```css
/* Trend Indicator */
.trend-indicator {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.875rem;
}

.trend-indicator.trending-up {
  background-color: #d4edda;
  color: #155724;
}

.trend-indicator.trending-down {
  background-color: #f8d7da;
  color: #721c24;
}

.trend-indicator .arrow {
  font-weight: bold;
}

/* Related Keywords Grid */
.keyword-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.related-keyword-item {
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: #f9f9f9;
}

.related-keyword-item .keyword {
  font-weight: 600;
  display: block;
  margin-bottom: 8px;
}

.related-keyword-item .mini-metrics {
  display: flex;
  gap: 12px;
  font-size: 0.75rem;
  color: #666;
}

/* Difficulty Badge */
.badge.difficulty-easy {
  background-color: #28a745;
  color: white;
}

.badge.difficulty-medium {
  background-color: #ffc107;
  color: #000;
}

.badge.difficulty-hard {
  background-color: #dc3545;
  color: white;
}
```

---

## 🔍 Testing Checklist

Use this checklist to verify your integration:

- [ ] Search volume displays real numbers (not 0)
- [ ] Global search volume shows when available
- [ ] Trend score displays correctly (up/down indicator)
- [ ] Enhanced related keywords table shows metrics
- [ ] Questions section displays question-type keywords
- [ ] Topics section displays topic-type keywords
- [ ] Monthly searches chart renders (if implemented)
- [ ] Country breakdown shows (if implemented)
- [ ] All new fields are optional (backward compatible)
- [ ] Error handling for missing fields works

---

## 📝 API Request Examples

### Basic Request (Unchanged)

```typescript
const response = await fetch('/api/v1/keywords/enhanced', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    keywords: ['pet grooming'],
    location: 'United States',
    language: 'en'
  })
});
```

### Request with More Suggestions

```typescript
const response = await fetch('/api/v1/keywords/enhanced', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    keywords: ['pet grooming', 'dog care'],
    location: 'United States',
    language: 'en',
    max_suggestions_per_keyword: 50  // Get more related keywords
  })
});
```

---

## ⚠️ Important Notes

### Backward Compatibility

- **All new fields are optional** - Existing code will continue to work
- **Existing fields unchanged** - `search_volume`, `cpc`, `difficulty`, etc. still work the same
- **Search volume now has real values** - Previously returned 0, now returns actual numbers

### Performance

- Enhanced related keywords are only fetched for primary keywords (max 5)
- Results are cached for 1 hour
- Response times: 5-10 seconds for enhanced analysis

### Data Availability

- Some fields may be `null` or `undefined` if DataForSEO data is unavailable
- Always check for field existence before displaying
- Use fallback values when appropriate

---

## 🚀 Quick Start

1. **Update your TypeScript types** (see Step 1 above)
2. **Update your display components** (see Step 2 above)
3. **Test with a real keyword**:
   ```typescript
   const testKeyword = 'pet grooming';
   const analysis = await getKeywordAnalysis([testKeyword]);
   console.log('Search Volume:', analysis.enhanced_analysis[testKeyword].search_volume);
   console.log('Related Keywords:', analysis.enhanced_analysis[testKeyword].related_keywords_enhanced);
   ```
4. **Verify all fields display correctly**

---

## 📞 Support

If you encounter any issues:

1. Check the API response structure matches the types above
2. Verify DataForSEO credentials are configured
3. Check browser console for errors
4. Review the test results in `test_keyword_endpoints.py`

---

## ✅ Summary

### What You Need to Do

1. ✅ Update TypeScript types to include new optional fields
2. ✅ Update UI components to display new data
3. ✅ Add trend indicators and enhanced related keywords display
4. ✅ Test with real keywords to verify data appears

### What's Backward Compatible

- ✅ All existing code continues to work
- ✅ Existing fields unchanged
- ✅ New fields are optional

### What's Improved

- ✅ Search volume now shows real numbers
- ✅ Enhanced related keywords with metrics
- ✅ Question/topic categorization
- ✅ Trend analysis and monthly history

---

**Ready to integrate?** Start with updating your TypeScript types, then gradually add UI components for the new fields!

