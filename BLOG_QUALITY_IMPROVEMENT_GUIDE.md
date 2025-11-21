# Blog Quality Improvement Guide

**Date:** 2025-11-13  
**Version:** 1.3.0  
**Focus:** Images, Formatting, Links, AI Models, and Prompt Customization

---

## 🔍 Current Issues & Solutions

### Issue 1: No Images in Frontend ❌

**Problem:** Images are generated but not inserted into markdown content.

**Root Cause:** 
- Images are generated and returned in `generated_images` field
- But they're NOT automatically inserted into the markdown content
- Frontend needs to manually insert images

**Solution:** Two approaches:

#### Option A: Backend Auto-Insertion (Recommended)
The backend should insert images into content automatically. Currently, images are only returned separately.

#### Option B: Frontend Manual Insertion
Frontend receives images in `generated_images` field and inserts them into content.

**Current API Response:**
```json
{
  "content": "# Blog Title\n\nContent without images...",
  "generated_images": [
    {
      "type": "featured",
      "image_url": "https://...",
      "alt_text": "Featured image for topic"
    }
  ]
}
```

**What Frontend Should Do:**
```typescript
// Insert images into content
function insertImagesIntoContent(
  content: string,
  images: GeneratedImage[]
): string {
  let contentWithImages = content;
  
  // Insert featured image after H1
  const featuredImage = images.find(img => img.type === 'featured');
  if (featuredImage) {
    contentWithImages = contentWithImages.replace(
      /^(# .+)$/m,
      `$1\n\n![${featuredImage.alt_text}](${featuredImage.image_url})\n\n`
    );
  }
  
  // Insert section images before H2 headings
  const sectionImages = images.filter(img => img.type !== 'featured');
  const h2Matches = [...contentWithImages.matchAll(/^(## .+)$/gm)];
  
  sectionImages.forEach((image, index) => {
    if (index < h2Matches.length - 1) {
      const h2Index = h2Matches[index + 1].index;
      contentWithImages = 
        contentWithImages.slice(0, h2Index) +
        `\n\n![${image.alt_text}](${image.image_url})\n\n` +
        contentWithImages.slice(h2Index);
    }
  });
  
  return contentWithImages;
}
```

---

### Issue 2: Proper H1/H2 Formatting ❌

**Problem:** Content may not have proper heading hierarchy.

**Current Behavior:**
- Prompts mention headings but don't enforce structure
- Content may have inconsistent heading levels
- No validation that H1 exists

**Solution:** Enhanced prompts with explicit structure requirements.

**Current Prompt (Stage 2):**
```
STRUCTURE REQUIREMENTS:
- Start with a compelling introduction that hooks the reader
- Use proper heading hierarchy (H1 for title, H2 for main sections, H3 for subsections)
```

**Enhanced Prompt Needed:**
```
STRUCTURE REQUIREMENTS (MANDATORY):
1. Content MUST start with exactly ONE H1 heading (# Title)
2. Main sections MUST use H2 headings (## Section Title)
3. Subsections MUST use H3 headings (### Subsection Title)
4. Use H4-H6 only for deeper nesting
5. Each H2 section should have 2-4 paragraphs before next H2
6. Include at least 3-5 H2 sections
7. Use proper markdown formatting:
   - H1: # Title
   - H2: ## Section
   - H3: ### Subsection
```

---

### Issue 3: Interlinks and Backlinks ❌

**Problem:** Content lacks internal and external links.

**Current Behavior:**
- `internal_links` field exists in response but links may not be in content
- No automatic link insertion
- External links not generated

**Solution:** Enhanced prompts and post-processing.

**Enhanced Prompt Addition:**
```
LINKING REQUIREMENTS:
1. Include 3-5 internal links to related topics (use markdown format: [link text](/related-topic))
2. Include 2-3 external authoritative links (use markdown format: [link text](https://authoritative-source.com))
3. Links should be natural and contextual, not forced
4. Use descriptive anchor text (not "click here" or "read more")
5. External links should open in new tab (add to frontend rendering)
```

---

### Issue 4: AI Model Selection ❓

**Current Models Used:**

**Stage 1: Research & Outline**
- **Model:** Claude 3.5 Sonnet (`claude-3-5-sonnet-20241022`)
- **Why:** Superior reasoning for research and structure

**Stage 2: Draft Generation**
- **Model:** GPT-4o (`gpt-4o`) OR Consensus (GPT-4o + Claude)
- **Why:** Comprehensive content generation
- **If Consensus Enabled:** Uses both GPT-4o and Claude, then synthesizes best parts

**Stage 3: Enhancement**
- **Model:** Claude 3.5 Sonnet (`claude-3-5-sonnet-20241022`)
- **Why:** Best for refinement and fact-checking

**Stage 4: SEO Polish**
- **Model:** GPT-4o-mini (`gpt-4o-mini`)
- **Why:** Cost-effective for final optimization

**How to Use Latest Models:**

The API uses the latest available models by default:
- Claude: `claude-3-5-sonnet-20241022` (latest as of Nov 2024)
- GPT-4: `gpt-4o` (latest GPT-4 variant)

**To Force Specific Models:**
Currently not exposed via API, but you can check which models are available:
```bash
curl https://your-api-domain.com/api/v1/ai/providers/list
```

---

### Issue 5: Prompt Customization ✅

**Current Support:** `custom_instructions` field exists!

**How to Use:**
```json
{
  "topic": "pet grooming services",
  "keywords": ["pet grooming", "dog grooming"],
  "custom_instructions": "Write in a friendly, approachable tone. Include step-by-step instructions. Add images descriptions where relevant. Use H2 headings for each major step. Include internal links to related pet care topics."
}
```

**What Gets Enhanced:**
- Custom instructions are added to Stage 2 (Draft) prompt
- They're also included in Stage 3 (Enhancement) context
- Use them to specify:
  - Writing style preferences
  - Structure requirements
  - Content focus areas
  - Link requirements
  - Image placement instructions

---

## 🚀 Recommended Solutions

### Solution 1: Enhanced Request with Better Prompts

**Updated Request Format:**
```json
{
  "topic": "pet grooming services",
  "keywords": ["pet grooming", "dog grooming"],
  "tone": "professional",
  "length": "medium",
  
  // Enable all quality features
  "use_google_search": true,
  "use_fact_checking": true,
  "use_citations": true,
  "use_serp_optimization": true,
  "use_consensus_generation": true,  // Use GPT-4o + Claude for best quality
  "use_knowledge_graph": true,
  "use_semantic_keywords": true,
  "use_quality_scoring": true,
  
  // Custom instructions for better quality
  "custom_instructions": "CRITICAL REQUIREMENTS:\n1. Content MUST start with exactly ONE H1 heading (# Title)\n2. Use H2 headings (##) for main sections (minimum 3 sections)\n3. Use H3 headings (###) for subsections\n4. Include 3-5 internal links to related topics in markdown format: [link text](/related-topic)\n5. Include 2-3 external authoritative links: [link text](https://source.com)\n6. Add image placeholders where relevant: ![Alt text](image-url)\n7. Write in clear, scannable format with short paragraphs\n8. Use bullet points and numbered lists\n9. Include specific examples and actionable advice\n10. End with a strong conclusion summarizing key points",
  
  // Template for better structure
  "template_type": "how_to_guide",  // or "expert_authority", "comparison", etc.
  
  "target_audience": "Pet owners and pet care professionals"
}
```

### Solution 2: Backend Enhancement - Auto-Insert Images

**Recommended Backend Change:**
After generating images, automatically insert them into markdown content:

```python
# After image generation, insert into content
if generated_images:
    # Insert featured image after H1
    featured_image = next((img for img in generated_images if img.get("type") == "featured"), None)
    if featured_image:
        # Find H1 and insert image after it
        h1_pattern = r'^(# .+)$'
        if re.search(h1_pattern, final_content, re.MULTILINE):
            final_content = re.sub(
                h1_pattern,
                r'\1\n\n![' + featured_image.get("alt_text", "Featured image") + '](' + featured_image.get("image_url") + ')\n\n',
                final_content,
                count=1,
                flags=re.MULTILINE
            )
    
    # Insert section images before H2 headings
    section_images = [img for img in generated_images if img.get("type") != "featured"]
    h2_positions = [m.start() for m in re.finditer(r'^(## .+)$', final_content, re.MULTILINE)]
    
    for i, image in enumerate(section_images[:len(h2_positions)]):
        if i < len(h2_positions) - 1:
            insert_pos = h2_positions[i + 1]
            image_markdown = f"\n\n![{image.get('alt_text', 'Section image')}]({image.get('image_url')})\n\n"
            final_content = final_content[:insert_pos] + image_markdown + final_content[insert_pos:]
```

### Solution 3: Enhanced Prompt Templates

**Add to `custom_instructions` for guaranteed structure:**

```
STRUCTURE REQUIREMENTS (MANDATORY):
1. Start with exactly ONE H1: # [Title]
2. Introduction paragraph (3-4 sentences)
3. Main content with H2 sections (##):
   - ## Section 1 Title
   - Content paragraphs
   - ## Section 2 Title
   - Content paragraphs
   - ## Section 3 Title
   - Content paragraphs
4. Conclusion section (## Conclusion)
5. Each H2 section should have 2-4 paragraphs
6. Use H3 (###) for subsections within H2 sections

LINKING REQUIREMENTS:
- Include 3-5 internal links: [descriptive text](/related-topic)
- Include 2-3 external links: [descriptive text](https://authoritative-source.com)
- Links should be natural and contextual

IMAGE PLACEMENT:
- Add image placeholder after H1: ![Featured image](image-url)
- Add image placeholders before major H2 sections: ![Section image](image-url)
- Use descriptive alt text
```

---

## 📝 Complete Example Request

```json
{
  "topic": "The Complete Guide to Pet Grooming Services",
  "keywords": ["pet grooming", "dog grooming", "pet care"],
  "tone": "professional",
  "length": "long",
  
  // Enable all quality features
  "use_google_search": true,
  "use_fact_checking": true,
  "use_citations": true,
  "use_serp_optimization": true,
  "use_consensus_generation": true,  // Best quality: GPT-4o + Claude
  "use_knowledge_graph": true,
  "use_semantic_keywords": true,
  "use_quality_scoring": true,
  
  // Enhanced custom instructions
  "custom_instructions": "CONTENT STRUCTURE (MANDATORY):\n\n1. HEADING HIERARCHY:\n   - Start with exactly ONE H1: # The Complete Guide to Pet Grooming Services\n   - Use H2 (##) for main sections (minimum 4 sections)\n   - Use H3 (###) for subsections\n   - Ensure proper nesting (H1 > H2 > H3)\n\n2. CONTENT FORMAT:\n   - Introduction: 3-4 paragraphs after H1\n   - Each H2 section: 3-5 paragraphs\n   - Use bullet points and numbered lists\n   - Keep paragraphs to 3-4 sentences\n   - Add transitions between sections\n\n3. LINKING REQUIREMENTS:\n   - Include 4-6 internal links: [descriptive anchor text](/related-topic)\n   - Include 3-4 external authoritative links: [source name](https://authoritative-url.com)\n   - Links should be natural and contextual\n   - Place links within relevant paragraphs\n\n4. IMAGE PLACEMENT:\n   - Add image placeholder after H1: ![Pet grooming featured image](image-url)\n   - Add image placeholders before major H2 sections\n   - Use descriptive alt text for SEO\n\n5. WRITING QUALITY:\n   - Use specific examples and real-world scenarios\n   - Include actionable advice and step-by-step instructions\n   - Add data points and statistics where relevant\n   - Write for human readers first, SEO second\n   - Use active voice and clear language\n\n6. CONCLUSION:\n   - End with H2: ## Conclusion\n   - Summarize key points\n   - Provide actionable next steps\n   - Include call-to-action",
  
  "template_type": "how_to_guide",
  "target_audience": "Pet owners and pet care professionals"
}
```

---

## 🎯 AI Model Configuration

### Current Default Models

| Stage | Model | Provider | Why |
|-------|-------|----------|-----|
| Research | Claude 3.5 Sonnet | Anthropic | Best reasoning |
| Draft | GPT-4o | OpenAI | Comprehensive generation |
| Enhancement | Claude 3.5 Sonnet | Anthropic | Best refinement |
| SEO | GPT-4o-mini | OpenAI | Cost-effective |

### Using Consensus Generation (Best Quality)

**Enable:** `"use_consensus_generation": true`

**What It Does:**
- Generates draft with BOTH GPT-4o and Claude 3.5 Sonnet
- Synthesizes best sections from both models
- Results in higher quality content
- Takes longer (~15-20 seconds vs 10-15 seconds)
- Costs more (~$0.040-$0.080 vs $0.015-$0.030 per article)

**When to Use:**
- High-value content
- Important blog posts
- When quality is priority over speed/cost

---

## 📋 Frontend Integration Checklist

### Images
- [ ] Check `generated_images` field in response
- [ ] Insert featured image after H1 heading
- [ ] Insert section images before H2 headings
- [ ] Handle image URLs (may be base64 data URIs)
- [ ] Add proper alt text from `alt_text` field
- [ ] Display images in content preview

### Formatting
- [ ] Verify H1 exists (should be exactly one)
- [ ] Check H2/H3 hierarchy is correct
- [ ] Validate markdown formatting
- [ ] Display proper heading structure in preview
- [ ] Generate table of contents from headings

### Links
- [ ] Extract internal links from `internal_links` field
- [ ] Extract links from markdown content
- [ ] Verify external links have `rel="noopener"`
- [ ] Check internal links point to valid routes
- [ ] Display link previews (optional)

### Content Quality
- [ ] Check `quality_score` (should be 80+)
- [ ] Review `quality_dimensions` for specific scores
- [ ] Check `readability_score` (should be 60+)
- [ ] Verify `seo_score` (should be 70+)
- [ ] Review `warnings` field for issues

---

## 🔧 Backend Improvements Needed

### 1. Auto-Insert Images into Content

**File:** `main.py` (around line 1020)

**Add after image generation:**
```python
# Auto-insert images into content
if generated_images and final_content:
    final_content = insert_images_into_markdown(final_content, generated_images)
```

**New Function Needed:**
```python
def insert_images_into_markdown(content: str, images: List[Dict[str, Any]]) -> str:
    """Insert generated images into markdown content."""
    import re
    
    # Insert featured image after H1
    featured = next((img for img in images if img.get("type") == "featured"), None)
    if featured:
        h1_pattern = r'^(# .+)$'
        if re.search(h1_pattern, content, re.MULTILINE):
            content = re.sub(
                h1_pattern,
                r'\1\n\n![' + featured.get("alt_text", "Featured image") + '](' + featured.get("image_url", "") + ')\n\n',
                content,
                count=1,
                flags=re.MULTILINE
            )
    
    # Insert section images before H2 headings
    section_images = [img for img in images if img.get("type") != "featured"]
    h2_matches = list(re.finditer(r'^(## .+)$', content, re.MULTILINE))
    
    # Insert images before H2 sections (skip first H2, insert before 2nd, 3rd, etc.)
    for i, image in enumerate(section_images[:len(h2_matches)]):
        if i < len(h2_matches) - 1:  # Don't insert after last H2
            insert_pos = h2_matches[i + 1].start()
            image_markdown = f"\n\n![{image.get('alt_text', 'Section image')}]({image.get('image_url', '')})\n\n"
            content = content[:insert_pos] + image_markdown + content[insert_pos:]
    
    return content
```

### 2. Enhanced Prompt for Structure

**File:** `src/blog_writer_sdk/ai/enhanced_prompts.py`

**Update `build_draft_prompt` method:**
```python
STRUCTURE REQUIREMENTS (MANDATORY):
1. Content MUST start with exactly ONE H1 heading: # [Title]
2. After H1, write 2-3 introduction paragraphs
3. Main sections MUST use H2 headings: ## [Section Title]
   - Minimum 3 H2 sections required
   - Each H2 section should have 3-5 paragraphs
4. Subsections MUST use H3 headings: ### [Subsection Title]
5. Use proper markdown formatting:
   - H1: # Title (only one, at the start)
   - H2: ## Section Title
   - H3: ### Subsection Title
6. Include at least one list (bulleted or numbered) per H2 section
7. End with H2 Conclusion section: ## Conclusion

LINKING REQUIREMENTS:
1. Include 3-5 internal links using markdown format: [link text](/related-topic)
2. Include 2-3 external authoritative links: [source name](https://authoritative-url.com)
3. Links should be natural and contextual within paragraphs
4. Use descriptive anchor text (not generic "click here")

IMAGE PLACEMENT:
1. Add image placeholder after H1: ![Featured image description](image-url)
2. Add image placeholders before major H2 sections: ![Section image description](image-url)
3. Use descriptive alt text for SEO
```

### 3. Generate Internal Links Automatically

**File:** `src/blog_writer_sdk/ai/multi_stage_pipeline.py`

**Add link generation in Stage 4 (SEO Polish):**
```python
# Generate internal links based on keywords and content
internal_links = generate_internal_links(enhanced_content, keywords)
# Insert links into content naturally
enhanced_content = insert_internal_links(enhanced_content, internal_links)
```

---

## 📊 Response Format Reference

### Current Response Structure

```json
{
  "title": "Blog Title",
  "content": "# H1 Title\n\nContent...",
  "meta_title": "SEO Title",
  "meta_description": "SEO Description",
  
  // Quality scores
  "readability_score": 75.5,
  "seo_score": 85.0,
  "quality_score": 88.5,
  "quality_dimensions": {
    "readability": 80.0,
    "seo": 85.0,
    "structure": 90.0,
    "factual": 85.0,
    "uniqueness": 90.0,
    "engagement": 85.0
  },
  
  // Content metadata (for frontend)
  "content_metadata": {
    "headings": [
      {"level": 1, "text": "Title", "id": "title"},
      {"level": 2, "text": "Section 1", "id": "section-1"}
    ],
    "images": [
      {"alt": "Featured image", "src": "https://...", "is_external": true}
    ],
    "links": [
      {"text": "Link text", "href": "/related-topic", "is_external": false}
    ],
    "word_count": 1500,
    "reading_time": 6
  },
  
  // Generated images (need to be inserted)
  "generated_images": [
    {
      "type": "featured",
      "image_url": "https://...",
      "alt_text": "Featured image"
    }
  ],
  
  // Internal links (suggestions)
  "internal_links": [
    {"anchor_text": "pet care", "target_topic": "/pet-care-guide"}
  ],
  
  // Citations
  "citations": [
    {"text": "...", "url": "https://...", "title": "Source Title"}
  ],
  
  "success": true,
  "warnings": []
}
```

---

## ✅ Action Items

### For Frontend Team:

1. **Image Integration:**
   - Extract `generated_images` from response
   - Insert featured image after H1
   - Insert section images before H2 headings
   - Handle both URL and base64 image data

2. **Formatting Validation:**
   - Check `content_metadata.headings` for structure
   - Verify H1 exists and is unique
   - Validate H2/H3 hierarchy
   - Display table of contents from headings

3. **Link Handling:**
   - Extract links from `content_metadata.links`
   - Use `internal_links` for navigation
   - Add `rel="noopener"` to external links
   - Verify internal link routes exist

4. **Quality Checks:**
   - Display quality scores
   - Show warnings if any
   - Validate content meets thresholds

### For Backend Team:

1. **Auto-Insert Images** (Priority: High)
   - Add function to insert images into markdown
   - Insert featured image after H1
   - Insert section images before H2 sections

2. **Enhanced Prompts** (Priority: High)
   - Enforce H1/H2/H3 structure in prompts
   - Require internal/external links
   - Add image placeholder instructions

3. **Link Generation** (Priority: Medium)
   - Generate internal links automatically
   - Insert links naturally into content
   - Provide link suggestions in response

---

## 🎯 Quick Fix: Use Enhanced Request

**Immediate Solution - Use this request format:**

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
  use_consensus_generation: true,  // Best quality
  use_knowledge_graph: true,
  use_semantic_keywords: true,
  use_quality_scoring: true,
  
  // Critical custom instructions
  custom_instructions: `MANDATORY STRUCTURE:
1. Start with exactly ONE H1: # [Title]
2. Use H2 (##) for main sections (minimum 4 sections)
3. Use H3 (###) for subsections
4. Include 4-6 internal links: [text](/topic)
5. Include 3-4 external links: [text](https://source.com)
6. Add image placeholders: ![alt](url)
7. Write clear, scannable content with short paragraphs`,
  
  template_type: "how_to_guide",
  target_audience: "Pet owners"
};
```

---

**Last Updated:** 2025-11-13  
**Status:** Ready for Implementation

