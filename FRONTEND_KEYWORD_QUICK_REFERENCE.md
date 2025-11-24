# Frontend Quick Reference: Keyword Data Access

**Version:** 1.3.5  
**Quick Reference** - See `FRONTEND_KEYWORD_DATA_GUIDE.md` for complete details

---

## 🚀 Quick Access Guide

### Where to Find Each Data Type

```typescript
const response = await fetch('/api/v1/keywords/enhanced', {
  method: 'POST',
  body: JSON.stringify({ keywords: ['pet grooming miami'] })
});
const data = await response.json();

// ✅ MATCHING TERMS (like Ahrefs "Matching terms")
const matchingTerms = data.discovery?.matching_terms || [];
// Returns: Array<{ keyword, search_volume, keyword_difficulty, cpc, competition }>

// ✅ PEOPLE ALSO ASK (PAA questions)
const paaQuestions = data.serp_analysis?.people_also_ask || [];
// Returns: Array<{ question, snippet, url? }>

// ✅ ALSO RANK FOR (per keyword)
const alsoRankFor = data.enhanced_analysis['pet grooming miami']?.also_rank_for || [];
// Returns: string[]

// ✅ ALSO TALK ABOUT (per keyword)
const alsoTalkAbout = data.enhanced_analysis['pet grooming miami']?.also_talk_about || [];
// Returns: string[]

// ✅ LONG-TAIL KEYWORDS (per keyword)
const longTail = data.enhanced_analysis['pet grooming miami']?.long_tail_keywords || [];
// Returns: string[]

// ✅ QUESTIONS WITH METRICS (per keyword)
const questions = data.enhanced_analysis['pet grooming miami']?.questions || [];
// Returns: Array<{ keyword, search_volume, cpc, competition, difficulty_score }>

// ✅ TOPICS WITH METRICS (per keyword)
const topics = data.enhanced_analysis['pet grooming miami']?.topics || [];
// Returns: Array<{ keyword, search_volume, cpc, competition, difficulty_score }>

// ✅ RELATED TERMS (discovery level)
const relatedTerms = data.discovery?.related_terms || [];
// Returns: Array<{ keyword, search_volume, keyword_difficulty, cpc, competition }>

// ✅ ORGANIC RESULTS (top 10-20)
const organicResults = data.serp_analysis?.organic_results || [];
// Returns: Array<{ title, url, domain, snippet, position }>

// ✅ FEATURED SNIPPET
const featuredSnippet = data.serp_analysis?.featured_snippet;
// Returns: { title, snippet, url } | undefined
```

---

## 📊 Data Structure Map

```
response
├── enhanced_analysis[keyword]
│   ├── also_rank_for: string[]           ← "Also Rank For"
│   ├── also_talk_about: string[]         ← "Also Talk About"
│   ├── long_tail_keywords: string[]      ← Long-tail variations
│   ├── questions: Array<with metrics>    ← Question keywords with metrics
│   ├── topics: Array<with metrics>       ← Topic keywords with metrics
│   ├── related_keywords_enhanced: Array  ← Related keywords with metrics
│   └── ... (other metrics)
│
├── discovery
│   ├── matching_terms: Array             ← "Matching Terms" (like Ahrefs)
│   ├── questions: Array                  ← Question keywords extracted
│   └── related_terms: Array              ← Related terms from ideas
│
└── serp_analysis
    ├── people_also_ask: Array            ← "People Also Ask" questions
    ├── organic_results: Array            ← Top organic results
    ├── featured_snippet: Object          ← Featured snippet (if present)
    ├── video_results: Array              ← Video results
    ├── image_results: Array              ← Image results
    └── related_searches: string[]        ← Related search queries
```

---

## 💡 Common Use Cases

### Display Matching Terms Table
```typescript
const matchingTerms = data.discovery?.matching_terms || [];
// Display in table: keyword | search_volume | difficulty | CPC
```

### Display People Also Ask Accordion
```typescript
const paa = data.serp_analysis?.people_also_ask || [];
// Display as expandable accordion: question → snippet
```

### Display "Also Rank For" Section
```typescript
const alsoRankFor = data.enhanced_analysis[keyword]?.also_rank_for || [];
// Display as keyword chips/tags
```

### Display Long-Tail Keywords
```typescript
const longTail = data.enhanced_analysis[keyword]?.long_tail_keywords || [];
// Display as list or chips
```

---

## ⚡ All Data is Always Included

✅ **No need to set `include_serp: true`** - All discovery and SERP data is always included now!

---

## 📚 Full Documentation

See `FRONTEND_KEYWORD_DATA_GUIDE.md` for:
- Complete TypeScript type definitions
- React component examples
- Streaming endpoint usage
- Detailed field descriptions
