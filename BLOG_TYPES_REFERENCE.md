# Blog Content Types Reference

**Date:** 2025-11-23  
**Status:** ✅ Implemented

---

## Overview

This document lists all supported blog content types, representing the **top 80% of popular content formats** that drive traffic and engagement.

---

## Available Blog Types

### Core Types (Original)

| Type | Value | Description | Best For |
|------|-------|-------------|----------|
| **Custom** | `custom` | Custom content with specific instructions | Flexible content needs |
| **Brand** | `brand` | Brand overviews and histories | Brand awareness, company pages |
| **Top 10** | `top_10` | Ranking lists with detailed entries | Product comparisons, recommendations |
| **Product Review** | `product_review` | Detailed product analysis | E-commerce, buyer guides |
| **How To** | `how_to` | Step-by-step guides | Tutorials, instructions |
| **Comparison** | `comparison` | Side-by-side comparisons | Decision-making content |
| **Guide** | `guide` | Comprehensive guides | Educational content |

### Popular Content Types (Top 80%)

| Type | Value | Description | Best For |
|------|-------|-------------|----------|
| **Tutorial** | `tutorial` | Step-by-step learning content | Educational content, courses |
| **Listicle** | `listicle` | Numbered lists (Top 5, Top 20, etc.) | Viral content, quick reads |
| **Case Study** | `case_study` | Real-world examples and results | B2B content, social proof |
| **News** | `news` | Current events and updates | News sites, industry updates |
| **Opinion** | `opinion` | Editorial and thought leadership | Thought leadership, commentary |
| **Interview** | `interview` | Q&A with experts | Authority building, expert content |
| **FAQ** | `faq` | Frequently asked questions | Support content, SEO |
| **Checklist** | `checklist` | Actionable checklists | Productivity, actionable content |
| **Tips** | `tips` | Tips and tricks | Quick value, social shares |
| **Definition** | `definition` | What is X? Explanatory content | SEO, educational content |
| **Benefits** | `benefits` | Benefits-focused content | Marketing, conversion content |
| **Problem Solution** | `problem_solution` | Problem-solving content | Support, educational content |
| **Trend Analysis** | `trend_analysis` | Industry trends | Thought leadership, news |
| **Statistics** | `statistics` | Data-driven content | Research, authority content |
| **Resource List** | `resource_list` | Curated resources | Link building, value content |
| **Timeline** | `timeline` | Historical or process timelines | Educational, historical content |
| **Myth Busting** | `myth_busting` | Debunking myths | Educational, viral content |
| **Best Practices** | `best_practices` | Industry best practices | Professional content, guides |
| **Getting Started** | `getting_started` | Beginner guides | Onboarding, tutorials |
| **Advanced** | `advanced` | Advanced topics | Expert content, deep dives |
| **Troubleshooting** | `troubleshooting` | Problem-solving guides | Support, technical content |

---

## Usage Examples

### Tutorial Blog

```json
{
  "topic": "How to Build a REST API with Python",
  "keywords": ["python", "rest api", "flask"],
  "blog_type": "tutorial",
  "tone": "professional",
  "length": "medium"
}
```

### Case Study Blog

```json
{
  "topic": "How Company X Increased Revenue by 300%",
  "keywords": ["case study", "revenue growth", "marketing"],
  "blog_type": "case_study",
  "tone": "professional",
  "length": "long"
}
```

### FAQ Blog

```json
{
  "topic": "Frequently Asked Questions About SEO",
  "keywords": ["seo", "search engine optimization", "faq"],
  "blog_type": "faq",
  "tone": "professional",
  "length": "medium"
}
```

### Tips Blog

```json
{
  "topic": "10 Tips for Better Blog Writing",
  "keywords": ["blog writing", "content creation", "tips"],
  "blog_type": "tips",
  "tone": "friendly",
  "length": "short"
}
```

---

## Word Count Tolerance

All blog types support **±25% word count tolerance**:

- **Target:** 300 words
- **Acceptable Range:** 225-375 words
- **Priority:** Quality over exact word count

---

## SEO Optimization

All blog types include automatic SEO optimization:

- Keyword density analysis (optimal: 1-2%)
- Heading structure optimization
- Readability scoring
- Meta tag generation
- Semantic keyword integration

---

## Backlink Analysis (Premium)

For premium blogs, you can analyze backlinks to extract high-performing keywords:

```json
{
  "topic": "Advanced Python Techniques",
  "keywords": ["python", "programming"],
  "blog_type": "advanced",
  "analyze_backlinks": true,
  "backlink_url": "https://example.com/premium-blog-post"
}
```

This will:
1. Analyze backlinks from the premium blog URL
2. Extract keywords from anchor texts
3. Merge extracted keywords with your provided keywords
4. Generate content optimized with proven keywords

---

## Adding Custom Blog Types

To add a new blog type:

1. Add to `BlogType` enum in `dataforseo_content_generation_service.py`
2. Add prompt template in `_build_prompt_for_blog_type()` method
3. Add mapping in `main.py` blog_type_map
4. Update this documentation

---

## Traffic Optimization Features

All blog types include:

- **SEO Post-Processing:** Keyword density, heading structure, readability
- **Traffic Optimization:** Content structure optimized for engagement
- **Quality Scoring:** Comprehensive quality metrics
- **Word Count Tolerance:** ±25% flexibility for natural content

---

## Cost

All blog types use the same pricing:
- Generate Text: $0.00005 per token
- Generate Subtopics: $0.0001 per task
- Generate Meta Tags: $0.001 per task

**Typical cost:** ~$0.10 per blog post (1,500 words)

