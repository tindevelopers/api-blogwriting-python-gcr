# AI Prompting Strategy Guide

## Overview

This guide explains the **best approach** for prompting the AI to get desired results, specifically addressing product research and content structure requirements.

## ✅ Recommended Approach: Backend-Driven Prompting

### Why Backend Should Handle Prompting

1. **Intelligent Research Integration**: Backend can perform actual web searches, extract data, and include it in prompts
2. **Tool Optimization**: Backend knows what tools are available (Google Search, Knowledge Graph, DataForSEO) and optimizes prompts accordingly
3. **Consistency**: All prompts follow best practices and are maintained in one place
4. **Data Extraction**: Backend can extract brands, prices, features from search results and include them in context
5. **Maintainability**: Prompt improvements happen server-side without frontend changes

### Frontend Role: Send Structured Parameters

The frontend should send **structured parameters** that tell the backend **what to include**, not **how to write prompts**.

## Implementation

### Frontend Request Example

```typescript
const request = {
  topic: "best blow dryers for dogs",
  keywords: ["dog blow dryer", "pet grooming tools", "dog hair dryer"],
  tone: "professional",
  length: "long",
  
  // Enable product research
  include_product_research: true,
  include_brands: true,
  include_models: true,
  include_prices: true,
  include_features: true,
  include_reviews: true,
  include_pros_cons: true,
  
  // Content structure
  include_product_table: true,
  include_comparison_section: true,
  include_buying_guide: true,
  include_faq_section: true,
  
  // Research depth
  research_depth: "comprehensive",
  
  // Optional: Custom instructions for specific guidance
  custom_instructions: "Focus on products suitable for professional groomers",
  
  // Enable required features
  use_google_search: true,  // Required for product research
  use_knowledge_graph: true,
  use_citations: true
};
```

### Backend Processing Flow

1. **Detect Product Topic**: Backend checks if topic requires product research
2. **Perform Research**: 
   - Search Google for product reviews and comparisons
   - Extract brand names, models, features from search results
   - Use Knowledge Graph for entity information
3. **Build Context**: Include research data in prompt context
4. **Construct Prompt**: Backend builds optimized prompt with:
   - Research data (brands, features, prices)
   - Structure requirements (tables, comparisons, FAQs)
   - Custom instructions (if provided)
5. **Generate Content**: LLM receives rich context and generates comprehensive content

## Parameter Reference

### Product Research Parameters

| Parameter | Type | Default | Description |
|----------|------|---------|-------------|
| `include_product_research` | boolean | `false` | Enable comprehensive product research |
| `include_brands` | boolean | `true` | Include specific brand names |
| `include_models` | boolean | `true` | Include product model names |
| `include_prices` | boolean | `false` | Include current pricing (requires web scraping) |
| `include_features` | boolean | `true` | Include features and specifications |
| `include_reviews` | boolean | `true` | Include review summaries |
| `include_pros_cons` | boolean | `true` | Include pros/cons for each product |

### Content Structure Parameters

| Parameter | Type | Default | Description |
|----------|------|---------|-------------|
| `include_product_table` | boolean | `false` | Create product comparison table |
| `include_comparison_section` | boolean | `true` | Include detailed comparison section |
| `include_buying_guide` | boolean | `true` | Include buying guide section |
| `include_faq_section` | boolean | `true` | Include FAQ section |

### Research Depth

| Value | Description |
|-------|-------------|
| `basic` | Minimal research, quick generation |
| `standard` | Moderate research, balanced quality/speed |
| `comprehensive` | Extensive research, highest quality (slower) |

### Custom Instructions

Use `custom_instructions` for specific guidance that doesn't fit into structured parameters:

```typescript
custom_instructions: "Focus on budget-friendly options under $50. Emphasize safety features for nervous dogs."
```

## How Backend Handles Prompting

### 1. Research Stage (Stage 1)

Backend automatically:
- Searches Google for product reviews
- Extracts brand names from search results
- Gathers competitor information
- Identifies common features and specifications

**Prompt includes**:
- Extracted brand recommendations
- Research data from web searches
- Competitor analysis
- Product research requirements

### 2. Draft Stage (Stage 2)

Backend constructs prompt with:
- Research outline from Stage 1
- Brand recommendations (if extracted)
- Product research requirements
- Content structure requirements
- Custom instructions

**Example prompt section**:
```
PRODUCT RESEARCH REQUIREMENTS:
- Include specific brand names and recommendations
- Include specific product model names
- Include detailed features and specifications
- Include review summaries and user ratings
- Include pros and cons for each recommended product

CONTENT STRUCTURE:
- Create a product comparison table with key specifications
- Include a detailed comparison section
- Include a buying guide section with key considerations
- Include an FAQ section addressing common questions

PRODUCT BRAND RECOMMENDATIONS:
Include detailed information about these brands/models: Furminator, Andis, Wahl, Metro Air Force

For each brand, include:
- Key features and specifications
- Pros and cons
- Best use cases
- Price range (if available)
- User ratings/reviews summary
- Where to buy
```

## Frontend Implementation

### Automatic Detection (Recommended)

```typescript
function detectProductResearch(topic: string, keywords: string[]): boolean {
  const productIndicators = [
    "best", "top", "review", "recommendation", 
    "compare", "vs", "buy", "product", "guide"
  ];
  
  const topicLower = topic.toLowerCase();
  const keywordsLower = keywords.map(k => k.toLowerCase());
  
  return productIndicators.some(indicator => 
    topicLower.includes(indicator) || 
    keywordsLower.some(k => k.includes(indicator))
  );
}

// Usage
const isProductTopic = detectProductResearch(topic, keywords);

const request = {
  topic,
  keywords,
  include_product_research: isProductTopic,
  include_brands: isProductTopic,
  include_models: isProductTopic,
  include_product_table: isProductTopic,
  // ... other params
};
```

### Manual Configuration

```typescript
const request = {
  topic: "best blow dryers for dogs",
  keywords: ["dog blow dryer"],
  
  // Explicitly enable product research
  include_product_research: true,
  research_depth: "comprehensive",
  
  // Configure what to include
  include_brands: true,
  include_models: true,
  include_prices: true,
  include_features: true,
  include_reviews: true,
  include_pros_cons: true,
  
  // Configure content structure
  include_product_table: true,
  include_comparison_section: true,
  include_buying_guide: true,
  include_faq_section: true,
  
  // Custom guidance
  custom_instructions: "Focus on products suitable for home use, not professional grooming",
  
  // Required for research
  use_google_search: true,
  use_knowledge_graph: true
};
```

## Response Structure

The API response includes:

```typescript
{
  title: "...",
  content: "...",  // Includes product recommendations, comparison table, buying guide, FAQ
  brand_recommendations: ["Furminator", "Andis", "Wahl", ...],
  generated_images: [...],
  citations: [...],
  // ... other fields
}
```

## Best Practices

### ✅ DO

1. **Use Structured Parameters**: Send boolean flags for what to include
2. **Enable Google Search**: Set `use_google_search: true` for product research
3. **Use Custom Instructions Sparingly**: Only for specific guidance not covered by parameters
4. **Set Research Depth**: Use `comprehensive` for best results
5. **Enable Required Features**: `use_knowledge_graph`, `use_citations` for product content

### ❌ DON'T

1. **Don't Send Full Prompts**: Let backend construct optimized prompts
2. **Don't Skip Research**: Always enable `use_google_search` for product topics
3. **Don't Override with Custom Instructions**: Use parameters first, instructions for edge cases
4. **Don't Assume Data**: Backend extracts data from web searches, don't expect it to know current prices without research

## Example: Complete Request

```typescript
const generateProductBlog = async (topic: string, keywords: string[]) => {
  const isProductTopic = detectProductResearch(topic, keywords);
  
  const request = {
    topic,
    keywords,
    tone: "professional",
    length: "long",
    
    // Product research (auto-detected or manual)
    include_product_research: isProductTopic,
    include_brands: isProductTopic,
    include_models: isProductTopic,
    include_prices: isProductTopic,
    include_features: isProductTopic,
    include_reviews: isProductTopic,
    include_pros_cons: isProductTopic,
    
    // Content structure
    include_product_table: isProductTopic,
    include_comparison_section: isProductTopic,
    include_buying_guide: isProductTopic,
    include_faq_section: isProductTopic,
    
    // Research depth
    research_depth: isProductTopic ? "comprehensive" : "standard",
    
    // Required features
    use_google_search: true,
    use_knowledge_graph: true,
    use_citations: true,
    use_serp_optimization: true,
    
    // Optional custom instructions
    custom_instructions: isProductTopic 
      ? "Focus on products available in the US market"
      : undefined
  };
  
  const response = await fetch('/api/v1/blog/generate-enhanced', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  });
  
  return response.json();
};
```

## Summary

**Answer**: **Backend handles prompting intelligently**, frontend sends **structured parameters**.

- ✅ Frontend: Detects product topics, sends structured parameters
- ✅ Backend: Performs research, extracts data, constructs optimized prompts
- ✅ Result: Comprehensive content with brand recommendations, comparison tables, buying guides

This approach ensures:
- Consistent, high-quality prompts
- Actual research data included in content
- Maintainable code (prompts in one place)
- Flexible customization via parameters and custom instructions

