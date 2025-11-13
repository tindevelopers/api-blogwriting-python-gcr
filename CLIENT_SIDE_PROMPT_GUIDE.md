# Client-Side Prompt Customization Guide

**Date:** 2025-11-13  
**Version:** 1.3.0  
**Focus:** How to Use Custom Instructions for Better Blog Quality

---

## 🎯 Overview

The API supports **client-side prompt customization** through the `custom_instructions` field. This allows you to control content structure, formatting, linking, and quality directly from your frontend application.

---

## ✅ Current AI Models Used

### Multi-Stage Pipeline Models:

**Stage 1: Research & Outline**
- **Model:** Claude 3.5 Sonnet (`claude-3-5-sonnet-20241022`)
- **Provider:** Anthropic
- **Why:** Superior reasoning for research and structure planning

**Stage 2: Draft Generation**
- **Model:** GPT-4o (`gpt-4o`) OR Consensus (GPT-4o + Claude)
- **Provider:** OpenAI
- **Why:** Comprehensive content generation
- **Consensus Mode:** When `use_consensus_generation: true`, uses both GPT-4o and Claude 3.5 Sonnet, then synthesizes best parts

**Stage 3: Enhancement & Fact-Checking**
- **Model:** Claude 3.5 Sonnet (`claude-3-5-sonnet-20241022`)
- **Provider:** Anthropic
- **Why:** Best for refinement, fact-checking, and quality improvement

**Stage 4: SEO Polish**
- **Model:** GPT-4o-mini (`gpt-4o-mini`)
- **Provider:** OpenAI
- **Why:** Cost-effective for final SEO optimization

### Model Selection:

✅ **Latest Models:** The API uses the latest available models by default
- Claude: `claude-3-5-sonnet-20241022` (latest as of Nov 2024)
- GPT-4: `gpt-4o` (latest GPT-4 variant)

✅ **Best Quality:** Enable `use_consensus_generation: true` for GPT-4o + Claude consensus

---

## 📝 Using Custom Instructions

### Basic Usage

```typescript
const request = {
  topic: "pet grooming services",
  keywords: ["pet grooming", "dog grooming"],
  custom_instructions: "Write in a friendly, approachable tone. Include step-by-step instructions."
};
```

### Advanced Usage - Complete Structure Control

```typescript
const request = {
  topic: "pet grooming services",
  keywords: ["pet grooming", "dog grooming"],
  tone: "professional",
  length: "long",
  
  // Enable all quality features
  use_google_search: true,
  use_fact_checking: true,
  use_citations: true,
  use_serp_optimization: true,
  use_consensus_generation: true,  // Best quality: GPT-4o + Claude
  use_knowledge_graph: true,
  use_semantic_keywords: true,
  use_quality_scoring: true,
  
  // CRITICAL: Custom instructions for structure and quality
  custom_instructions: `
CRITICAL STRUCTURE REQUIREMENTS:

1. HEADING HIERARCHY (MANDATORY):
   - Start with exactly ONE H1: # [Title]
   - Use H2 (##) for main sections (minimum 4 sections)
   - Use H3 (###) for subsections
   - Ensure proper nesting: H1 > H2 > H3
   - Each H2 section must have 3-5 paragraphs

2. CONTENT FORMAT:
   - Introduction: 2-3 paragraphs after H1
   - Main sections: Each H2 with 3-5 paragraphs
   - Use bullet points and numbered lists
   - Keep paragraphs to 3-4 sentences
   - Add transitions between sections
   - Conclusion: H2 section summarizing key points

3. LINKING REQUIREMENTS:
   - Include 4-6 internal links: [descriptive text](/related-topic)
   - Include 3-4 external links: [source name](https://authoritative-url.com)
   - Links must be natural and contextual
   - Use descriptive anchor text (not "click here")
   - Place links within relevant paragraphs

4. IMAGE PLACEMENT:
   - Add image placeholder after H1: ![Featured image](image-url)
   - Add image placeholders before major H2 sections
   - Use descriptive alt text for SEO

5. WRITING QUALITY:
   - Use specific examples and real-world scenarios
   - Include actionable advice and step-by-step instructions
   - Add data points and statistics where relevant
   - Write for human readers first, SEO second
   - Use active voice and clear language
   - Avoid generic or vague statements

6. CONTENT DEPTH:
   - Provide unique insights, not just rehashed information
   - Include specific examples, case studies, or real-world applications
   - Cite sources naturally within the content
   - Demonstrate expertise and authority
   - Include current information from 2025 where relevant
  `,
  
  template_type: "how_to_guide",  // Options: expert_authority, how_to_guide, comparison, etc.
  target_audience: "Pet owners and pet care professionals"
};
```

---

## 🎨 Prompt Templates

### Available Templates:

1. **expert_authority** (Default)
   - Position as domain expert
   - Data-driven analysis
   - Professional terminology

2. **how_to_guide**
   - Step-by-step instructions
   - Clear prerequisites
   - Troubleshooting tips

3. **comparison**
   - Structured comparison format
   - Pros and cons
   - Recommendations

4. **case_study**
   - Real-world examples
   - Results with data
   - Actionable insights

5. **news_update**
   - Recent developments
   - Expert opinions
   - Current information

6. **tutorial**
   - Learning objectives
   - Practice exercises
   - Progress checkpoints

7. **listicle**
   - Numbered/bulleted format
   - Substantial items
   - Engaging headings

8. **review**
   - Comprehensive evaluation
   - Pros and cons
   - Clear recommendations

---

## 🔧 Best Practices for Custom Instructions

### 1. Be Specific

❌ **Bad:**
```
"Write good content"
```

✅ **Good:**
```
"Write comprehensive, well-researched content with:
- Minimum 4 H2 sections
- 3-5 paragraphs per section
- Specific examples and data points
- Natural keyword integration"
```

### 2. Enforce Structure

```
STRUCTURE REQUIREMENTS:
1. Exactly ONE H1 at start: # Title
2. Minimum 4 H2 sections: ## Section Title
3. H3 subsections: ### Subsection Title
4. Proper markdown formatting
5. Conclusion section at end
```

### 3. Specify Linking

```
LINKING REQUIREMENTS:
- 4-6 internal links: [text](/topic)
- 3-4 external links: [text](https://source.com)
- Natural placement within paragraphs
- Descriptive anchor text
```

### 4. Request Images

```
IMAGE PLACEMENT:
- Featured image after H1: ![alt](url)
- Section images before H2: ![alt](url)
- Descriptive alt text for SEO
```

### 5. Quality Standards

```
QUALITY REQUIREMENTS:
- Specific examples, not generic statements
- Actionable advice readers can implement
- Data points and statistics
- Current information from 2025
- Unique insights, not rehashed content
```

---

## 📋 Complete Example Request

```typescript
interface BlogGenerationRequest {
  topic: string;
  keywords: string[];
  tone?: "professional" | "casual" | "friendly" | "academic";
  length?: "short" | "medium" | "long" | "very_long";
  
  // Quality features
  use_google_search?: boolean;
  use_fact_checking?: boolean;
  use_citations?: boolean;
  use_serp_optimization?: boolean;
  use_consensus_generation?: boolean;  // Best quality
  use_knowledge_graph?: boolean;
  use_semantic_keywords?: boolean;
  use_quality_scoring?: boolean;
  
  // Customization
  custom_instructions?: string;
  template_type?: string;
  target_audience?: string;
}

// Example usage
const generateHighQualityBlog = async (topic: string, keywords: string[]) => {
  const request: BlogGenerationRequest = {
    topic,
    keywords,
    tone: "professional",
    length: "long",
    
    // Enable all quality features
    use_google_search: true,
    use_fact_checking: true,
    use_citations: true,
    use_serp_optimization: true,
    use_consensus_generation: true,  // GPT-4o + Claude for best quality
    use_knowledge_graph: true,
    use_semantic_keywords: true,
    use_quality_scoring: true,
    
    // Custom instructions for guaranteed structure
    custom_instructions: `
MANDATORY STRUCTURE:
1. Start with ONE H1: # [Title]
2. Introduction: 2-3 paragraphs
3. Minimum 4 H2 sections (##) with 3-5 paragraphs each
4. H3 subsections (###) for detailed points
5. Conclusion: H2 section summarizing key points

LINKING:
- 4-6 internal links: [text](/topic)
- 3-4 external links: [text](https://source.com)
- Natural placement, descriptive anchor text

IMAGES:
- Featured image after H1: ![alt](url)
- Section images before H2: ![alt](url)

QUALITY:
- Specific examples and data points
- Actionable advice
- Current 2025 information
- Unique insights
    `,
    
    template_type: "how_to_guide",
    target_audience: "Pet owners"
  };
  
  const response = await fetch('/api/v1/blog/generate-enhanced', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  });
  
  return await response.json();
};
```

---

## 🎯 Quality Checklist

After generation, verify:

- [ ] **H1:** Exactly one H1 at start
- [ ] **H2:** Minimum 3-5 H2 sections
- [ ] **H3:** Proper subsections
- [ ] **Images:** Images inserted in content (check `content` field)
- [ ] **Links:** Internal and external links present
- [ ] **Quality Score:** Should be 80+ (check `quality_score`)
- [ ] **Readability:** Should be 60+ (check `readability_score`)
- [ ] **SEO Score:** Should be 70+ (check `seo_score`)

---

## 🚀 Quick Start Template

**Copy-paste this for guaranteed quality:**

```typescript
const qualityBlogRequest = {
  topic: "your topic",
  keywords: ["keyword1", "keyword2"],
  tone: "professional",
  length: "long",
  
  use_google_search: true,
  use_consensus_generation: true,  // Best quality
  use_quality_scoring: true,
  
  custom_instructions: `
STRUCTURE: ONE H1, 4+ H2 sections, H3 subsections
LINKS: 4-6 internal, 3-4 external
IMAGES: Featured after H1, section images before H2
QUALITY: Specific examples, actionable advice, 2025 data
  `
};
```

---

**Last Updated:** 2025-11-13  
**Status:** ✅ Ready to Use

