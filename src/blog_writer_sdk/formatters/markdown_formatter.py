"""
Markdown formatting module for blog content output.

This module handles formatting blog content into clean, SEO-friendly markdown.
"""

import re
from typing import List, Optional
from ..models.blog_models import BlogPost
from ..utils.text_utils import generate_table_of_contents, extract_headings


class MarkdownFormatter:
    """
    Formats blog content into clean, SEO-optimized markdown.
    
    This class ensures consistent markdown formatting and
    includes SEO-friendly elements like table of contents.
    """
    
    def __init__(self):
        """Initialize the markdown formatter."""
        self.include_toc = True
        self.include_meta_comments = True
    
    def format_blog_post(self, blog_post: BlogPost, include_frontmatter: bool = True) -> str:
        """
        Format a complete blog post as markdown.
        
        Args:
            blog_post: BlogPost object to format
            include_frontmatter: Whether to include YAML frontmatter
            
        Returns:
            Formatted markdown content
        """
        markdown_parts = []
        
        # Add frontmatter if requested
        if include_frontmatter:
            frontmatter = self._generate_frontmatter(blog_post)
            markdown_parts.append(frontmatter)
        
        # Add title
        markdown_parts.append(f"# {blog_post.title}\n")
        
        # Add meta information as comments if enabled
        if self.include_meta_comments:
            meta_comments = self._generate_meta_comments(blog_post)
            markdown_parts.append(meta_comments)
        
        # Add table of contents if enabled and content has headings
        if self.include_toc:
            toc = generate_table_of_contents(blog_post.content, max_level=3)
            if toc.strip():
                markdown_parts.append(toc)
        
        # Add main content
        formatted_content = self._format_content(blog_post.content)
        markdown_parts.append(formatted_content)
        
        # Join all parts
        return "\n".join(markdown_parts)
    
    def format_content_only(self, content: str) -> str:
        """
        Format only the content portion as markdown.
        
        Args:
            content: Raw content to format
            
        Returns:
            Formatted markdown content
        """
        return self._format_content(content)
    
    def add_seo_elements(self, content: str, keywords: Optional[List[str]] = None) -> str:
        """
        Add SEO-friendly elements to markdown content.
        
        Args:
            content: Original content
            keywords: Keywords to optimize for
            
        Returns:
            Content with SEO elements added
        """
        formatted_content = content
        
        # Add internal linking suggestions as comments
        formatted_content = self._add_linking_suggestions(formatted_content)
        
        # Add keyword optimization comments
        if keywords:
            formatted_content = self._add_keyword_suggestions(formatted_content, keywords)
        
        # Ensure proper heading structure
        formatted_content = self._optimize_heading_structure(formatted_content)
        
        return formatted_content
    
    def _generate_frontmatter(self, blog_post: BlogPost) -> str:
        """Generate YAML frontmatter for the blog post."""
        frontmatter_lines = ["---"]
        
        # Basic metadata
        frontmatter_lines.append(f'title: "{blog_post.title}"')
        if blog_post.excerpt:
            frontmatter_lines.append(f'description: "{blog_post.excerpt}"')
        frontmatter_lines.append(f'slug: "{blog_post.slug}"')
        
        # Dates
        frontmatter_lines.append(f'date: "{blog_post.created_at.isoformat()}"')
        if blog_post.updated_at:
            frontmatter_lines.append(f'updated: "{blog_post.updated_at.isoformat()}"')
        
        # Author
        if blog_post.author:
            frontmatter_lines.append(f'author: "{blog_post.author}"')
        
        # Categories and tags
        if blog_post.categories:
            categories_str = ', '.join(f'"{cat}"' for cat in blog_post.categories)
            frontmatter_lines.append(f'categories: [{categories_str}]')
        
        if blog_post.tags:
            tags_str = ', '.join(f'"{tag}"' for tag in blog_post.tags)
            frontmatter_lines.append(f'tags: [{tags_str}]')
        
        # SEO metadata
        if blog_post.meta_tags:
            frontmatter_lines.append(f'seo_title: "{blog_post.meta_tags.title}"')
            frontmatter_lines.append(f'seo_description: "{blog_post.meta_tags.description}"')
            
            if blog_post.meta_tags.keywords:
                keywords_str = ', '.join(f'"{kw}"' for kw in blog_post.meta_tags.keywords)
                frontmatter_lines.append(f'keywords: [{keywords_str}]')
        
        # Featured image
        if blog_post.featured_image:
            frontmatter_lines.append(f'featured_image: "{blog_post.featured_image}"')
        
        # Status
        frontmatter_lines.append(f'status: "{blog_post.status}"')
        
        frontmatter_lines.append("---\n")
        
        return "\n".join(frontmatter_lines)
    
    def _generate_meta_comments(self, blog_post: BlogPost) -> str:
        """Generate meta information as HTML comments."""
        comments = []
        
        # SEO metrics
        if blog_post.seo_metrics:
            comments.append(f"<!-- SEO Score: {blog_post.seo_metrics.overall_seo_score:.1f}/100 -->")
            comments.append(f"<!-- Word Count: {blog_post.seo_metrics.word_count} -->")
            comments.append(f"<!-- Reading Time: {blog_post.seo_metrics.reading_time_minutes:.1f} minutes -->")
        
        # Content quality
        if blog_post.content_quality:
            comments.append(f"<!-- Readability Score: {blog_post.content_quality.readability_score:.1f}/100 -->")
            comments.append(f"<!-- Flesch Reading Ease: {blog_post.content_quality.flesch_reading_ease:.1f} -->")
        
        if comments:
            return "\n".join(comments) + "\n"
        
        return ""
    
    def _format_content(self, content: str) -> str:
        """Format and clean up content markdown."""
        # Normalize line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Fix heading spacing
        content = re.sub(r'^(#{1,6})\s*(.+)$', r'\1 \2', content, flags=re.MULTILINE)
        
        # Ensure proper spacing around headings
        content = re.sub(r'\n(#{1,6}\s+.+)\n', r'\n\n\1\n\n', content)
        
        # Fix list formatting
        content = re.sub(r'^(\s*)[-*+]\s+', r'\1- ', content, flags=re.MULTILINE)
        content = re.sub(r'^(\s*)\d+\.\s+', r'\1\g<0>', content, flags=re.MULTILINE)
        
        # Ensure proper paragraph spacing
        content = re.sub(r'\n\n\n+', '\n\n', content)
        
        # Clean up emphasis formatting
        content = re.sub(r'\*\*\s+(.+?)\s+\*\*', r'**\1**', content)
        content = re.sub(r'\*\s+(.+?)\s+\*', r'*\1*', content)
        
        # Fix link formatting
        content = re.sub(r'\[\s*(.+?)\s*\]\(\s*(.+?)\s*\)', r'[\1](\2)', content)
        
        return content.strip()
    
    def _add_linking_suggestions(self, content: str) -> str:
        """Add internal linking suggestions as comments."""
        # Find potential linking opportunities
        sentences = content.split('. ')
        enhanced_sentences = []
        
        # Common topics that could benefit from internal links
        link_topics = {
            'seo': 'SEO guide',
            'content marketing': 'content marketing strategy',
            'blog writing': 'blog writing tips',
            'keyword research': 'keyword research tools',
            'social media': 'social media marketing',
            'email marketing': 'email marketing best practices',
        }
        
        for sentence in sentences:
            enhanced_sentence = sentence
            
            for topic, suggested_link in link_topics.items():
                if topic in sentence.lower() and f'<!-- Link: {suggested_link} -->' not in sentence:
                    enhanced_sentence += f' <!-- Consider linking to: {suggested_link} -->'
                    break  # Only add one suggestion per sentence
            
            enhanced_sentences.append(enhanced_sentence)
        
        return '. '.join(enhanced_sentences)
    
    def _add_keyword_suggestions(self, content: str, keywords: List[str]) -> str:
        """Add keyword optimization suggestions as comments."""
        if not keywords:
            return content
        
        # Add comment about keyword usage
        keyword_comment = f"<!-- Target keywords: {', '.join(keywords[:5])} -->\n"
        
        # Check if keywords are well distributed
        paragraphs = content.split('\n\n')
        if len(paragraphs) > 3:
            # Add suggestion for keyword distribution
            keyword_comment += "<!-- Ensure keywords are naturally distributed throughout the content -->\n"
        
        return keyword_comment + content
    
    def _optimize_heading_structure(self, content: str) -> str:
        """Optimize heading structure for better SEO."""
        lines = content.split('\n')
        optimized_lines = []
        h1_found = False
        
        for line in lines:
            if line.startswith('#'):
                heading_level = len(line) - len(line.lstrip('#'))
                heading_text = line.lstrip('#').strip()
                
                # Ensure only one H1
                if heading_level == 1:
                    if h1_found:
                        # Convert additional H1s to H2s
                        optimized_lines.append(f"## {heading_text}")
                        optimized_lines.append("<!-- Note: Converted H1 to H2 for better SEO structure -->")
                    else:
                        optimized_lines.append(line)
                        h1_found = True
                else:
                    optimized_lines.append(line)
            else:
                optimized_lines.append(line)
        
        return '\n'.join(optimized_lines)
    
    def generate_schema_markup(self, blog_post: BlogPost) -> str:
        """
        Generate JSON-LD schema markup for the blog post.
        
        Args:
            blog_post: BlogPost object
            
        Returns:
            JSON-LD schema markup as string
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
        
        # Add image if available
        if blog_post.featured_image:
            schema["image"] = str(blog_post.featured_image)
        
        # Add keywords if available
        if blog_post.meta_tags and blog_post.meta_tags.keywords:
            schema["keywords"] = blog_post.meta_tags.keywords
        
        # Add word count if available
        if blog_post.seo_metrics:
            schema["wordCount"] = blog_post.seo_metrics.word_count
        
        import json
        return f'<script type="application/ld+json">\n{json.dumps(schema, indent=2)}\n</script>'
    
    def validate_markdown(self, content: str) -> List[str]:
        """
        Validate markdown content and return issues.
        
        Args:
            content: Markdown content to validate
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Check heading structure
        headings = extract_headings(content)
        h1_count = sum(1 for h in headings if h['level'] == 1)
        
        if h1_count == 0:
            issues.append("No H1 heading found")
        elif h1_count > 1:
            issues.append(f"Multiple H1 headings found ({h1_count})")
        
        # Check for broken links
        links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content)
        for link_text, link_url in links:
            if not link_url.strip():
                issues.append(f"Empty link URL for text: '{link_text}'")
        
        # Check for unbalanced emphasis
        bold_count = content.count('**')
        if bold_count % 2 != 0:
            issues.append("Unbalanced bold emphasis (**) markers")
        
        italic_count = content.count('*') - bold_count
        if italic_count % 2 != 0:
            issues.append("Unbalanced italic emphasis (*) markers")
        
        return issues
