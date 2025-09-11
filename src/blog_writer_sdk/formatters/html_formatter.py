"""
HTML formatting module for blog content output.

This module handles formatting blog content into clean, SEO-friendly HTML.
"""

import re
from typing import List, Optional
from ..models.blog_models import BlogPost
from ..utils.text_utils import extract_headings


class HTMLFormatter:
    """
    Formats blog content into clean, SEO-optimized HTML.
    
    This class converts markdown content to HTML and adds
    SEO-friendly elements and structured data.
    """
    
    def __init__(self):
        """Initialize the HTML formatter."""
        self.include_schema = True
        self.include_meta_tags = True
        self.add_reading_time = True
    
    def format_blog_post(self, blog_post: BlogPost, include_full_html: bool = False) -> str:
        """
        Format a complete blog post as HTML.
        
        Args:
            blog_post: BlogPost object to format
            include_full_html: Whether to include full HTML document structure
            
        Returns:
            Formatted HTML content
        """
        if include_full_html:
            return self._generate_full_html_document(blog_post)
        else:
            return self._generate_html_content(blog_post)
    
    def format_content_only(self, content: str) -> str:
        """
        Format only the content portion as HTML.
        
        Args:
            content: Markdown content to convert
            
        Returns:
            HTML content
        """
        return self._markdown_to_html(content)
    
    def generate_meta_tags_html(self, blog_post: BlogPost) -> str:
        """
        Generate HTML meta tags for the blog post.
        
        Args:
            blog_post: BlogPost object
            
        Returns:
            HTML meta tags as string
        """
        if not blog_post.meta_tags:
            return ""
        
        meta_tags = []
        
        # Basic meta tags
        meta_tags.append(f'<title>{blog_post.meta_tags.title}</title>')
        meta_tags.append(f'<meta name="description" content="{blog_post.meta_tags.description}">')
        
        # Keywords
        if blog_post.meta_tags.keywords:
            keywords_str = ', '.join(blog_post.meta_tags.keywords)
            meta_tags.append(f'<meta name="keywords" content="{keywords_str}">')
        
        # Canonical URL
        if blog_post.meta_tags.canonical_url:
            meta_tags.append(f'<link rel="canonical" href="{blog_post.meta_tags.canonical_url}">')
        
        # Open Graph tags
        meta_tags.append(f'<meta property="og:title" content="{blog_post.meta_tags.og_title or blog_post.meta_tags.title}">')
        meta_tags.append(f'<meta property="og:description" content="{blog_post.meta_tags.og_description or blog_post.meta_tags.description}">')
        meta_tags.append(f'<meta property="og:type" content="{blog_post.meta_tags.og_type}">')
        
        if blog_post.meta_tags.og_image:
            meta_tags.append(f'<meta property="og:image" content="{blog_post.meta_tags.og_image}">')
        
        # Twitter Card tags
        meta_tags.append(f'<meta name="twitter:card" content="{blog_post.meta_tags.twitter_card}">')
        meta_tags.append(f'<meta name="twitter:title" content="{blog_post.meta_tags.twitter_title or blog_post.meta_tags.title}">')
        meta_tags.append(f'<meta name="twitter:description" content="{blog_post.meta_tags.twitter_description or blog_post.meta_tags.description}">')
        
        if blog_post.meta_tags.twitter_image:
            meta_tags.append(f'<meta name="twitter:image" content="{blog_post.meta_tags.twitter_image}">')
        
        return '\n'.join(meta_tags)
    
    def generate_schema_markup(self, blog_post: BlogPost) -> str:
        """
        Generate JSON-LD schema markup for the blog post.
        
        Args:
            blog_post: BlogPost object
            
        Returns:
            JSON-LD schema markup as HTML script tag
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": blog_post.title,
            "description": blog_post.meta_tags.description if blog_post.meta_tags else "",
            "datePublished": blog_post.created_at.isoformat(),
            "dateModified": blog_post.updated_at.isoformat() if blog_post.updated_at else blog_post.created_at.isoformat(),
        }
        
        # Add author if available
        if blog_post.author:
            schema["author"] = {
                "@type": "Person",
                "name": blog_post.author
            }
        
        # Add publisher information (you might want to make this configurable)
        schema["publisher"] = {
            "@type": "Organization",
            "name": "Your Blog Name"  # This should be configurable
        }
        
        # Add image if available
        if blog_post.featured_image:
            schema["image"] = {
                "@type": "ImageObject",
                "url": str(blog_post.featured_image)
            }
        
        # Add keywords if available
        if blog_post.meta_tags and blog_post.meta_tags.keywords:
            schema["keywords"] = blog_post.meta_tags.keywords
        
        # Add word count and reading time if available
        if blog_post.seo_metrics:
            schema["wordCount"] = blog_post.seo_metrics.word_count
            
        # Add article section/category
        if blog_post.categories:
            schema["articleSection"] = blog_post.categories[0]  # Use first category
        
        import json
        return f'<script type="application/ld+json">\n{json.dumps(schema, indent=2)}\n</script>'
    
    def _generate_full_html_document(self, blog_post: BlogPost) -> str:
        """Generate a complete HTML document."""
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="en">',
            '<head>',
            '    <meta charset="UTF-8">',
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
        ]
        
        # Add meta tags
        if self.include_meta_tags:
            meta_tags = self.generate_meta_tags_html(blog_post)
            html_parts.extend(f'    {line}' for line in meta_tags.split('\n'))
        
        # Add schema markup
        if self.include_schema:
            schema_markup = self.generate_schema_markup(blog_post)
            html_parts.extend(f'    {line}' for line in schema_markup.split('\n'))
        
        html_parts.extend([
            '</head>',
            '<body>',
            '    <article>',
        ])
        
        # Add content
        content_html = self._generate_html_content(blog_post)
        html_parts.extend(f'        {line}' for line in content_html.split('\n'))
        
        html_parts.extend([
            '    </article>',
            '</body>',
            '</html>'
        ])
        
        return '\n'.join(html_parts)
    
    def _generate_html_content(self, blog_post: BlogPost) -> str:
        """Generate HTML content for the blog post."""
        content_parts = []
        
        # Add header with title and metadata
        content_parts.append(f'<header>')
        content_parts.append(f'    <h1>{self._escape_html(blog_post.title)}</h1>')
        
        # Add metadata
        metadata_parts = []
        if blog_post.author:
            metadata_parts.append(f'<span class="author">By {self._escape_html(blog_post.author)}</span>')
        
        metadata_parts.append(f'<time datetime="{blog_post.created_at.isoformat()}">{blog_post.created_at.strftime("%B %d, %Y")}</time>')
        
        # Add reading time if available
        if self.add_reading_time and blog_post.seo_metrics:
            reading_time = int(blog_post.seo_metrics.reading_time_minutes)
            metadata_parts.append(f'<span class="reading-time">{reading_time} min read</span>')
        
        if metadata_parts:
            content_parts.append(f'    <div class="post-meta">{" • ".join(metadata_parts)}</div>')
        
        content_parts.append('</header>')
        
        # Add featured image if available
        if blog_post.featured_image:
            content_parts.append(f'<div class="featured-image">')
            content_parts.append(f'    <img src="{blog_post.featured_image}" alt="{self._escape_html(blog_post.title)}">')
            content_parts.append('</div>')
        
        # Add excerpt if available
        if blog_post.excerpt:
            content_parts.append(f'<div class="excerpt">')
            content_parts.append(f'    <p>{self._escape_html(blog_post.excerpt)}</p>')
            content_parts.append('</div>')
        
        # Add table of contents if content has headings
        toc_html = self._generate_table_of_contents(blog_post.content)
        if toc_html:
            content_parts.append(toc_html)
        
        # Add main content
        content_parts.append('<div class="content">')
        main_content = self._markdown_to_html(blog_post.content)
        content_parts.append(main_content)
        content_parts.append('</div>')
        
        # Add tags if available
        if blog_post.tags:
            content_parts.append('<div class="tags">')
            content_parts.append('    <span class="tags-label">Tags:</span>')
            for tag in blog_post.tags:
                content_parts.append(f'    <span class="tag">{self._escape_html(tag)}</span>')
            content_parts.append('</div>')
        
        return '\n'.join(content_parts)
    
    def _markdown_to_html(self, content: str) -> str:
        """Convert markdown content to HTML."""
        html_content = content
        
        # Convert headings
        html_content = re.sub(r'^(#{6})\s+(.+)$', r'<h6>\2</h6>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^(#{5})\s+(.+)$', r'<h5>\2</h5>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^(#{4})\s+(.+)$', r'<h4>\2</h4>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^(#{3})\s+(.+)$', r'<h3>\2</h3>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^(#{2})\s+(.+)$', r'<h2>\2</h2>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^(#{1})\s+(.+)$', r'<h1>\2</h1>', html_content, flags=re.MULTILINE)
        
        # Convert bold and italic
        html_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_content)
        html_content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html_content)
        html_content = re.sub(r'__(.+?)__', r'<strong>\1</strong>', html_content)
        html_content = re.sub(r'_(.+?)_', r'<em>\1</em>', html_content)
        
        # Convert links
        html_content = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', html_content)
        
        # Convert code blocks (simple version)
        html_content = re.sub(r'`([^`]+)`', r'<code>\1</code>', html_content)
        
        # Convert unordered lists
        html_content = re.sub(r'^- (.+)$', r'<li>\1</li>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'(<li>.*</li>)', r'<ul>\n\1\n</ul>', html_content, flags=re.DOTALL)
        
        # Convert ordered lists (simplified)
        html_content = re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', html_content, flags=re.MULTILINE)
        
        # Convert paragraphs
        paragraphs = html_content.split('\n\n')
        html_paragraphs = []
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph:
                # Skip if already wrapped in HTML tags
                if not (paragraph.startswith('<') and paragraph.endswith('>')):
                    # Don't wrap headings, lists, etc.
                    if not re.match(r'^<(h[1-6]|ul|ol|li|div|blockquote)', paragraph):
                        paragraph = f'<p>{paragraph}</p>'
                html_paragraphs.append(paragraph)
        
        html_content = '\n\n'.join(html_paragraphs)
        
        # Clean up extra whitespace
        html_content = re.sub(r'\n\s*\n', '\n\n', html_content)
        
        return html_content
    
    def _generate_table_of_contents(self, content: str) -> str:
        """Generate HTML table of contents from content headings."""
        headings = extract_headings(content)
        
        if len(headings) < 2:  # Need at least 2 headings for TOC
            return ""
        
        toc_parts = [
            '<nav class="table-of-contents">',
            '    <h2>Table of Contents</h2>',
            '    <ul>'
        ]
        
        for heading in headings:
            if heading['level'] <= 3:  # Only include H1-H3 in TOC
                indent = '    ' * heading['level']
                toc_parts.append(f'{indent}<li><a href="#{heading["slug"]}">{self._escape_html(heading["text"])}</a></li>')
        
        toc_parts.extend([
            '    </ul>',
            '</nav>'
        ])
        
        return '\n'.join(toc_parts)
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ""
        
        html_escape_table = {
            "&": "&amp;",
            '"': "&quot;",
            "'": "&#39;",
            ">": "&gt;",
            "<": "&lt;",
        }
        
        return "".join(html_escape_table.get(c, c) for c in text)
    
    def add_seo_attributes(self, html_content: str) -> str:
        """Add SEO-friendly attributes to HTML elements."""
        # Add alt attributes to images that don't have them
        html_content = re.sub(
            r'<img([^>]*?)src="([^"]*)"([^>]*?)(?<!alt="[^"]*")>',
            r'<img\1src="\2"\3 alt="Image">',
            html_content
        )
        
        # Add rel="noopener" to external links
        html_content = re.sub(
            r'<a href="(https?://[^"]*)"([^>]*)>',
            r'<a href="\1" rel="noopener"\2>',
            html_content
        )
        
        # Add heading IDs for anchor links
        def add_heading_id(match):
            level = match.group(1)
            text = match.group(2)
            # Create slug from heading text
            slug = re.sub(r'[^\w\s-]', '', text).strip()
            slug = re.sub(r'[-\s]+', '-', slug).lower()
            return f'<h{level} id="{slug}">{text}</h{level}>'
        
        html_content = re.sub(r'<h([1-6])>([^<]+)</h[1-6]>', add_heading_id, html_content)
        
        return html_content
