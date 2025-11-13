# Frontend TypeScript Stack Implementation Guide

**Focus:** High-Quality Blog Rendering with unified + remark + rehype + Cheerio + schema-dts

**Date:** 2025-01-12  
**Status:** Implementation Guide

---

## Overview

This guide provides a complete implementation strategy for building a high-quality blog frontend using the recommended TypeScript stack:

1. **Pre-processing:** unified + remark + rehype ecosystem
2. **Post-processing:** Cheerio 1.0+ (server-side only)
3. **Schema generation:** schema-dts + react-schemaorg

---

## Backend Enhancements Required

### 1. Enhanced API Response Format

The backend should provide structured data optimized for frontend processing:

```python
# Enhanced response structure needed
{
  "content": {
    "markdown": "...",           # Raw markdown content
    "html": "...",               # Pre-rendered HTML (optional)
    "ast": {...},                # Unified AST (optional, for advanced use)
    "metadata": {
      "headings": [...],         # Heading structure for TOC
      "word_count": 1500,
      "reading_time": 6,
      "images": [...],           # Image references
      "links": [...],            # Internal/external links
      "code_blocks": [...]       # Code block metadata
    }
  },
  "structured_data": {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    // ... complete schema.org structure
  },
  "seo": {
    "meta_title": "...",
    "meta_description": "...",
    "keywords": [...],
    "canonical_url": "...",
    "og_tags": {...},
    "twitter_tags": {...}
  }
}
```

### 2. Backend Implementation Tasks

#### Task 1: Enhanced Markdown Response
**File:** `src/blog_writer_sdk/formatters/markdown_formatter.py`

**Enhancements:**
- Add heading extraction method
- Add metadata extraction (images, links, code blocks)
- Add AST generation option (using markdown-it or similar)
- Ensure clean, parseable markdown output

#### Task 2: Structured Data Enhancement
**File:** `src/blog_writer_sdk/integrations/google_knowledge_graph.py`

**Enhancements:**
- Ensure structured_data follows schema-dts compatible format
- Add all required BlogPosting fields
- Include FAQPage schema if FAQ section exists
- Include HowTo schema if applicable
- Include Article schema for news content

#### Task 3: Metadata Extraction
**File:** `src/blog_writer_sdk/utils/content_metadata.py` (new)

**Features:**
- Extract heading hierarchy
- Extract image references with alt text
- Extract internal/external links
- Extract code blocks with language
- Calculate reading time
- Extract table of contents structure

---

## Frontend Implementation

### Phase 1: Project Setup (Week 1)

#### 1.1 Initialize Next.js Project

```bash
npx create-next-app@latest blog-frontend --typescript --tailwind --app
cd blog-frontend
```

#### 1.2 Install Dependencies

```bash
# Core markdown processing
npm install unified remark-parse remark-rehype rehype-react
npm install remark-gfm remark-slug rehype-autolink-headings
npm install rehype-highlight rehype-sanitize

# HTML manipulation (server-side only)
npm install cheerio

# Schema generation
npm install schema-dts react-schemaorg

# TypeScript types
npm install --save-dev @types/unified @types/remark @types/rehype

# Additional utilities
npm install date-fns reading-time
```

#### 1.3 Project Structure

```
blog-frontend/
├── src/
│   ├── app/
│   │   ├── blog/
│   │   │   └── [slug]/
│   │   │       └── page.tsx
│   │   └── layout.tsx
│   ├── components/
│   │   ├── blog/
│   │   │   ├── BlogContent.tsx
│   │   │   ├── BlogHeader.tsx
│   │   │   ├── TableOfContents.tsx
│   │   │   └── BlogMetadata.tsx
│   │   └── seo/
│   │       ├── SchemaMarkup.tsx
│   │       └── MetaTags.tsx
│   ├── lib/
│   │   ├── markdown/
│   │   │   ├── processor.ts
│   │   │   ├── plugins.ts
│   │   │   └── types.ts
│   │   ├── html/
│   │   │   └── post-processor.ts
│   │   └── api/
│   │       └── blog-api.ts
│   └── types/
│       ├── blog.ts
│       └── schema.ts
```

---

### Phase 2: Markdown Processing (Week 1-2)

#### 2.1 Unified Processor Setup

**File:** `src/lib/markdown/processor.ts`

```typescript
import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkGfm from 'remark-gfm';
import remarkSlug from 'remark-slug';
import remarkRehype from 'remark-rehype';
import rehypeAutolinkHeadings from 'rehype-autolink-headings';
import rehypeHighlight from 'rehype-highlight';
import rehypeSanitize from 'rehype-sanitize';
import rehypeReact from 'rehype-react';
import { createElement, Fragment } from 'react';

// Custom components for React rendering
const components = {
  h1: ({ children, id, ...props }: any) => (
    <h1 id={id} className="text-4xl font-bold mt-8 mb-4" {...props}>
      {children}
    </h1>
  ),
  h2: ({ children, id, ...props }: any) => (
    <h2 id={id} className="text-3xl font-semibold mt-6 mb-3" {...props}>
      {children}
    </h2>
  ),
  h3: ({ children, id, ...props }: any) => (
    <h3 id={id} className="text-2xl font-semibold mt-4 mb-2" {...props}>
      {children}
    </h3>
  ),
  p: ({ children, ...props }: any) => (
    <p className="mb-4 leading-7" {...props}>{children}</p>
  ),
  a: ({ href, children, ...props }: any) => (
    <a 
      href={href} 
      className="text-blue-600 hover:text-blue-800 underline"
      target={href?.startsWith('http') ? '_blank' : undefined}
      rel={href?.startsWith('http') ? 'noopener noreferrer' : undefined}
      {...props}
    >
      {children}
    </a>
  ),
  code: ({ className, children, ...props }: any) => {
    const isInline = !className;
    return isInline ? (
      <code className="bg-gray-100 px-1 py-0.5 rounded text-sm" {...props}>
        {children}
      </code>
    ) : (
      <code className={className} {...props}>{children}</code>
    );
  },
  pre: ({ children, ...props }: any) => (
    <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto mb-4" {...props}>
      {children}
    </pre>
  ),
  ul: ({ children, ...props }: any) => (
    <ul className="list-disc list-inside mb-4 space-y-2" {...props}>
      {children}
    </ul>
  ),
  ol: ({ children, ...props }: any) => (
    <ol className="list-decimal list-inside mb-4 space-y-2" {...props}>
      {children}
    </ol>
  ),
  blockquote: ({ children, ...props }: any) => (
    <blockquote className="border-l-4 border-blue-500 pl-4 italic my-4" {...props}>
      {children}
    </blockquote>
  ),
  img: ({ src, alt, ...props }: any) => (
    <img 
      src={src} 
      alt={alt}
      className="rounded-lg my-4 max-w-full h-auto"
      loading="lazy"
      {...props}
    />
  ),
};

export function createMarkdownProcessor() {
  return unified()
    .use(remarkParse)
    .use(remarkGfm) // GitHub Flavored Markdown
    .use(remarkSlug) // Add IDs to headings
    .use(remarkRehype, { allowDangerousHtml: false })
    .use(rehypeAutolinkHeadings, {
      behavior: 'wrap',
      properties: {
        className: ['anchor-link'],
      },
    })
    .use(rehypeHighlight) // Syntax highlighting
    .use(rehypeSanitize) // Sanitize HTML
    .use(rehypeReact, {
      createElement,
      Fragment,
      components,
    });
}

export async function processMarkdown(markdown: string) {
  const processor = createMarkdownProcessor();
  const result = await processor.process(markdown);
  return result;
}
```

#### 2.2 Heading Extraction

**File:** `src/lib/markdown/plugins.ts`

```typescript
import { visit } from 'unist-util-visit';
import type { Root, Heading } from 'mdast';

export interface HeadingNode {
  id: string;
  level: number;
  text: string;
}

export function extractHeadings(markdown: string): HeadingNode[] {
  const headings: HeadingNode[] = [];
  
  // Simple regex-based extraction (can be enhanced with unified)
  const headingRegex = /^(#{1,6})\s+(.+)$/gm;
  let match;
  
  while ((match = headingRegex.exec(markdown)) !== null) {
    const level = match[1].length;
    const text = match[2].trim();
    const id = text
      .toLowerCase()
      .replace(/[^\w\s-]/g, '')
      .replace(/\s+/g, '-');
    
    headings.push({ id, level, text });
  }
  
  return headings;
}
```

---

### Phase 3: Schema Generation (Week 2)

#### 3.1 Schema Types Setup

**File:** `src/types/schema.ts`

```typescript
import type { BlogPosting, Person, Organization } from 'schema-dts';

export interface BlogPostingSchema extends BlogPosting {
  '@context': 'https://schema.org';
  '@type': 'BlogPosting';
  headline: string;
  description: string;
  datePublished: string;
  dateModified: string;
  author: Person;
  publisher: Organization;
  image?: string | string[];
  keywords?: string[];
  wordCount?: number;
  articleSection?: string;
  mainEntityOfPage?: {
    '@type': 'WebPage';
    '@id': string;
  };
}

export interface FAQPageSchema {
  '@context': 'https://schema.org';
  '@type': 'FAQPage';
  mainEntity: Array<{
    '@type': 'Question';
    name: string;
    acceptedAnswer: {
      '@type': 'Answer';
      text: string;
    };
  }>;
}
```

#### 3.2 Schema Component

**File:** `src/components/seo/SchemaMarkup.tsx`

```typescript
'use client';

import { BlogPosting } from 'schema-dts';
import { BlogPostingJsonLd } from 'react-schemaorg';

interface SchemaMarkupProps {
  blogPost: {
    title: string;
    description: string;
    publishedAt: string;
    updatedAt: string;
    author: {
      name: string;
      url?: string;
    };
    publisher: {
      name: string;
      logo?: string;
    };
    image?: string;
    url: string;
    keywords?: string[];
    wordCount?: number;
  };
}

export function SchemaMarkup({ blogPost }: SchemaMarkupProps) {
  const schema: BlogPosting = {
    '@context': 'https://schema.org',
    '@type': 'BlogPosting',
    headline: blogPost.title,
    description: blogPost.description,
    datePublished: blogPost.publishedAt,
    dateModified: blogPost.updatedAt,
    author: {
      '@type': 'Person',
      name: blogPost.author.name,
      ...(blogPost.author.url && { url: blogPost.author.url }),
    },
    publisher: {
      '@type': 'Organization',
      name: blogPost.publisher.name,
      ...(blogPost.publisher.logo && {
        logo: {
          '@type': 'ImageObject',
          url: blogPost.publisher.logo,
        },
      }),
    },
    ...(blogPost.image && { image: blogPost.image }),
    ...(blogPost.keywords && { keywords: blogPost.keywords.join(', ') }),
    ...(blogPost.wordCount && { wordCount: blogPost.wordCount }),
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': blogPost.url,
    },
  };

  return <BlogPostingJsonLd item={schema} />;
}
```

---

### Phase 4: HTML Post-Processing (Week 2-3)

#### 4.1 Cheerio Post-Processor

**File:** `src/lib/html/post-processor.ts`

```typescript
import * as cheerio from 'cheerio';

interface PostProcessOptions {
  addTableOfContents?: boolean;
  optimizeImages?: boolean;
  addReadingProgress?: boolean;
  enhanceLinks?: boolean;
}

export function postProcessHTML(
  html: string,
  options: PostProcessOptions = {}
): string {
  const $ = cheerio.load(html);

  // Optimize images
  if (options.optimizeImages) {
    $('img').each((_, el) => {
      const $img = $(el);
      if (!$img.attr('loading')) {
        $img.attr('loading', 'lazy');
      }
      if (!$img.attr('decoding')) {
        $img.attr('decoding', 'async');
      }
      // Add srcset if not present
      if (!$img.attr('srcset') && $img.attr('src')) {
        const src = $img.attr('src')!;
        $img.attr('srcset', `${src} 1x`);
      }
    });
  }

  // Enhance internal links
  if (options.enhanceLinks) {
    $('a[href^="/"]').addClass('internal-link');
    $('a[href^="http"]').each((_, el) => {
      const $link = $(el);
      $link.attr('target', '_blank');
      $link.attr('rel', 'noopener noreferrer');
    });
  }

  // Add reading progress indicators
  if (options.addReadingProgress) {
    $('h2, h3').each((_, el) => {
      const $heading = $(el);
      $heading.addClass('reading-section');
    });
  }

  return $.html();
}
```

**Note:** This must be used server-side only (in API routes or `getServerSideProps`)

---

### Phase 5: Blog Component Integration (Week 3)

#### 5.1 Main Blog Component

**File:** `src/components/blog/BlogContent.tsx`

```typescript
'use client';

import { useMemo } from 'react';
import { processMarkdown } from '@/lib/markdown/processor';
import { extractHeadings } from '@/lib/markdown/plugins';
import { TableOfContents } from './TableOfContents';

interface BlogContentProps {
  markdown: string;
  className?: string;
}

export function BlogContent({ markdown, className }: BlogContentProps) {
  const { content, headings } = useMemo(() => {
    const headings = extractHeadings(markdown);
    return { content: null, headings }; // Content will be processed server-side
  }, [markdown]);

  return (
    <div className={className}>
      <TableOfContents headings={headings} />
      <article className="prose prose-lg max-w-none">
        {/* Content will be rendered server-side */}
        <div dangerouslySetInnerHTML={{ __html: markdown }} />
      </div>
    </div>
  );
}
```

#### 5.2 Server-Side Rendering

**File:** `src/app/blog/[slug]/page.tsx`

```typescript
import { Metadata } from 'next';
import { processMarkdown } from '@/lib/markdown/processor';
import { postProcessHTML } from '@/lib/html/post-processor';
import { SchemaMarkup } from '@/components/seo/SchemaMarkup';
import { BlogHeader } from '@/components/blog/BlogHeader';
import { BlogMetadata } from '@/components/blog/BlogMetadata';
import { fetchBlogPost } from '@/lib/api/blog-api';

interface PageProps {
  params: { slug: string };
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const post = await fetchBlogPost(params.slug);
  
  return {
    title: post.seo.meta_title,
    description: post.seo.meta_description,
    keywords: post.seo.keywords,
    openGraph: {
      title: post.seo.og_tags?.title || post.title,
      description: post.seo.og_tags?.description || post.seo.meta_description,
      images: post.seo.og_tags?.image ? [post.seo.og_tags.image] : [],
    },
    twitter: {
      card: 'summary_large_image',
      title: post.seo.twitter_tags?.title || post.title,
      description: post.seo.twitter_tags?.description || post.seo.meta_description,
    },
  };
}

export default async function BlogPostPage({ params }: PageProps) {
  const post = await fetchBlogPost(params.slug);
  
  // Process markdown server-side
  const processed = await processMarkdown(post.content.markdown);
  const html = processed.toString();
  
  // Post-process with Cheerio (server-side only)
  const optimizedHTML = postProcessHTML(html, {
    optimizeImages: true,
    enhanceLinks: true,
    addReadingProgress: true,
  });

  return (
    <>
      <SchemaMarkup blogPost={{
        title: post.title,
        description: post.seo.meta_description,
        publishedAt: post.published_at,
        updatedAt: post.updated_at,
        author: post.author,
        publisher: post.publisher,
        image: post.featured_image,
        url: post.canonical_url,
        keywords: post.seo.keywords,
        wordCount: post.content.metadata.word_count,
      }} />
      
      <article>
        <BlogHeader 
          title={post.title}
          author={post.author}
          publishedAt={post.published_at}
          readingTime={post.content.metadata.reading_time}
        />
        
        <BlogMetadata 
          wordCount={post.content.metadata.word_count}
          keywords={post.seo.keywords}
        />
        
        <div 
          className="blog-content"
          dangerouslySetInnerHTML={{ __html: optimizedHTML }}
        />
      </article>
    </>
  );
}
```

---

## Backend API Enhancements Needed

### 1. Enhanced Response Format

Update `EnhancedBlogGenerationResponse` to include:

```python
class EnhancedBlogGenerationResponse(BaseModel):
    # ... existing fields ...
    
    # Enhanced content structure
    content_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Content metadata for frontend processing"
    )
    
    # Structured data (already exists, ensure it's complete)
    structured_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Complete Schema.org JSON-LD structure"
    )
    
    # SEO metadata (enhance existing)
    seo_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Complete SEO metadata including OG and Twitter tags"
    )
```

### 2. Content Metadata Extraction

**New File:** `src/blog_writer_sdk/utils/content_metadata.py`

```python
from typing import List, Dict, Any
import re
from datetime import datetime

def extract_content_metadata(content: str) -> Dict[str, Any]:
    """Extract metadata from markdown content for frontend processing."""
    
    # Extract headings
    headings = []
    heading_pattern = r'^(#{1,6})\s+(.+)$'
    for match in re.finditer(heading_pattern, content, re.MULTILINE):
        level = len(match.group(1))
        text = match.group(2).strip()
        headings.append({
            "level": level,
            "text": text,
            "id": _slugify(text)
        })
    
    # Extract images
    images = []
    image_pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'
    for match in re.finditer(image_pattern, content):
        images.append({
            "alt": match.group(1),
            "src": match.group(2)
        })
    
    # Extract links
    links = []
    link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    for match in re.finditer(link_pattern, content):
        href = match.group(2)
        links.append({
            "text": match.group(1),
            "href": href,
            "is_external": href.startswith('http')
        })
    
    # Extract code blocks
    code_blocks = []
    code_pattern = r'```(\w+)?\n(.*?)```'
    for match in re.finditer(code_pattern, content, re.DOTALL):
        code_blocks.append({
            "language": match.group(1) or "text",
            "code": match.group(2)
        })
    
    # Calculate reading time (average 200 words per minute)
    word_count = len(content.split())
    reading_time = max(1, round(word_count / 200))
    
    return {
        "headings": headings,
        "images": images,
        "links": links,
        "code_blocks": code_blocks,
        "word_count": word_count,
        "reading_time": reading_time
    }

def _slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    return text.strip('-')
```

---

## Implementation Checklist

### Backend Tasks
- [ ] Enhance `EnhancedBlogGenerationResponse` model
- [ ] Create `content_metadata.py` utility
- [ ] Update blog generation endpoint to include metadata
- [ ] Ensure structured_data is complete and schema-dts compatible
- [ ] Add OG and Twitter tag generation
- [ ] Test API response format

### Frontend Tasks
- [ ] Set up Next.js project with TypeScript
- [ ] Install all required dependencies
- [ ] Create unified markdown processor
- [ ] Implement schema-dts types
- [ ] Create SchemaMarkup component
- [ ] Implement Cheerio post-processor (server-side)
- [ ] Create blog page component
- [ ] Add table of contents component
- [ ] Implement SEO meta tags
- [ ] Add reading progress indicator
- [ ] Test markdown rendering
- [ ] Test schema markup
- [ ] Test HTML optimization

---

## Best Practices

### 1. Markdown Processing
- Always process markdown server-side for better performance
- Use unified plugins for consistent parsing
- Sanitize HTML output to prevent XSS
- Add syntax highlighting for code blocks

### 2. Schema Generation
- Use schema-dts for type safety
- Include all required BlogPosting fields
- Add FAQPage schema if FAQ section exists
- Validate schema with Google's Rich Results Test

### 3. HTML Post-Processing
- Use Cheerio only server-side (never in browser)
- Optimize images (lazy loading, srcset)
- Enhance links (external link indicators)
- Add reading progress indicators

### 4. Performance
- Cache processed markdown
- Use React Server Components
- Lazy load images
- Minimize client-side JavaScript

---

## Testing

### 1. Markdown Rendering
```typescript
// Test markdown processing
const markdown = "# Test Heading\n\nThis is a test.";
const result = await processMarkdown(markdown);
expect(result).toContain('<h1');
```

### 2. Schema Validation
```typescript
// Test schema markup
const schema = generateSchema(blogPost);
expect(schema['@type']).toBe('BlogPosting');
expect(schema.headline).toBeDefined();
```

### 3. HTML Optimization
```typescript
// Test Cheerio post-processing
const html = '<img src="test.jpg">';
const optimized = postProcessHTML(html, { optimizeImages: true });
expect(optimized).toContain('loading="lazy"');
```

---

## Next Steps

1. **Week 1:** Backend enhancements + Frontend setup
2. **Week 2:** Markdown processing + Schema generation
3. **Week 3:** HTML post-processing + Component integration
4. **Week 4:** Testing + Optimization + Documentation

---

## Resources

- [unified Documentation](https://unifiedjs.com/)
- [remark Plugins](https://github.com/remarkjs/remark/blob/main/doc/plugins.md)
- [rehype Plugins](https://github.com/rehypejs/rehype/blob/main/doc/plugins.md)
- [schema-dts Types](https://github.com/google/schema-dts)
- [react-schemaorg](https://github.com/google/react-schemaorg)
- [Cheerio Documentation](https://cheerio.js.org/)

