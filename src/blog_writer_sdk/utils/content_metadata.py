"""
Content metadata extraction utility.

Extracts structured metadata from markdown content for frontend processing.
This supports the unified + remark + rehype frontend stack.
"""

import re
from typing import List, Dict, Any, Optional


def extract_content_metadata(content: str) -> Dict[str, Any]:
    """
    Extract metadata from markdown content for frontend processing.
    
    This provides structured data that frontend tools (unified, remark, rehype)
    can use for enhanced rendering, table of contents generation, and SEO.
    
    Args:
        content: Markdown content string
        
    Returns:
        Dictionary containing:
        - headings: List of heading structures with level, text, and id
        - images: List of image references with alt text and src
        - links: List of links with text, href, and external flag
        - code_blocks: List of code blocks with language and code
        - word_count: Total word count
        - reading_time: Estimated reading time in minutes
        - has_tables: Boolean indicating if content contains tables
        - has_lists: Boolean indicating if content contains lists
    """
    headings = _extract_headings(content)
    images = _extract_images(content)
    links = _extract_links(content)
    code_blocks = _extract_code_blocks(content)
    
    # Calculate word count (excluding code blocks and headings)
    word_count = _calculate_word_count(content, code_blocks)
    
    # Calculate reading time (average 200 words per minute)
    reading_time = max(1, round(word_count / 200))
    
    # Check for other content types
    has_tables = bool(re.search(r'\|.*\|', content, re.MULTILINE))
    has_lists = bool(re.search(r'^[\s]*[-*+]\s+|^[\s]*\d+\.\s+', content, re.MULTILINE))
    
    return {
        "headings": headings,
        "images": images,
        "links": links,
        "code_blocks": code_blocks,
        "word_count": word_count,
        "reading_time": reading_time,
        "has_tables": has_tables,
        "has_lists": has_lists,
        "paragraph_count": len([p for p in content.split('\n\n') if p.strip() and not p.strip().startswith('#')]),
    }


def _extract_headings(content: str) -> List[Dict[str, Any]]:
    """Extract heading structure from markdown."""
    headings = []
    heading_pattern = r'^(#{1,6})\s+(.+)$'
    
    for match in re.finditer(heading_pattern, content, re.MULTILINE):
        level = len(match.group(1))
        text = match.group(2).strip()
        
        # Remove inline formatting
        text_clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Bold
        text_clean = re.sub(r'\*([^*]+)\*', r'\1', text_clean)  # Italic
        text_clean = re.sub(r'`([^`]+)`', r'\1', text_clean)  # Code
        text_clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text_clean)  # Links
        
        headings.append({
            "level": level,
            "text": text_clean,
            "id": _slugify(text_clean),
            "raw": text  # Keep original for reference
        })
    
    return headings


def _extract_images(content: str) -> List[Dict[str, Any]]:
    """Extract image references from markdown."""
    images = []
    image_pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'
    
    for match in re.finditer(image_pattern, content):
        alt_text = match.group(1)
        src = match.group(2)
        
        images.append({
            "alt": alt_text,
            "src": src,
            "is_external": src.startswith('http'),
            "has_alt": bool(alt_text.strip())
        })
    
    return images


def _extract_links(content: str) -> List[Dict[str, Any]]:
    """Extract links from markdown."""
    links = []
    link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    
    for match in re.finditer(link_pattern, content):
        text = match.group(1)
        href = match.group(2)
        
        # Skip image links (already captured)
        if not re.search(r'^!\[', match.group(0)):
            links.append({
                "text": text,
                "href": href,
                "is_external": href.startswith('http'),
                "is_anchor": href.startswith('#'),
                "is_mailto": href.startswith('mailto:'),
            })
    
    return links


def _extract_code_blocks(content: str) -> List[Dict[str, Any]]:
    """Extract code blocks from markdown."""
    code_blocks = []
    code_pattern = r'```(\w+)?\n(.*?)```'
    
    for match in re.finditer(code_pattern, content, re.DOTALL):
        language = match.group(1) or "text"
        code = match.group(2).strip()
        
        code_blocks.append({
            "language": language,
            "code": code,
            "line_count": len(code.split('\n')),
            "char_count": len(code)
        })
    
    # Also extract inline code
    inline_code_pattern = r'`([^`]+)`'
    inline_codes = []
    for match in re.finditer(inline_code_pattern, content):
        inline_codes.append({
            "language": None,
            "code": match.group(1),
            "is_inline": True
        })
    
    return code_blocks + inline_codes


def _calculate_word_count(content: str, code_blocks: List[Dict[str, Any]]) -> int:
    """Calculate word count excluding code blocks."""
    # Remove code blocks
    content_clean = content
    for code_block in code_blocks:
        if not code_block.get('is_inline'):
            # Remove code block from content
            code_pattern = rf'```{re.escape(code_block.get("language", ""))}?\n.*?```'
            content_clean = re.sub(code_pattern, '', content_clean, flags=re.DOTALL)
        else:
            # Remove inline code
            content_clean = re.sub(rf'`{re.escape(code_block["code"])}`', '', content_clean)
    
    # Remove markdown syntax
    content_clean = re.sub(r'#{1,6}\s+', '', content_clean)  # Headings
    content_clean = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', content_clean)  # Images
    content_clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content_clean)  # Links (keep text)
    content_clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', content_clean)  # Bold
    content_clean = re.sub(r'\*([^*]+)\*', r'\1', content_clean)  # Italic
    content_clean = re.sub(r'`([^`]+)`', r'\1', content_clean)  # Inline code
    
    # Count words
    words = re.findall(r'\b\w+\b', content_clean)
    return len(words)


def _slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug.
    
    This matches the behavior of remark-slug plugin used in frontend.
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters
    text = re.sub(r'[^\w\s-]', '', text)
    
    # Replace whitespace with hyphens
    text = re.sub(r'\s+', '-', text)
    
    # Remove leading/trailing hyphens
    text = text.strip('-')
    
    # Collapse multiple hyphens
    text = re.sub(r'-+', '-', text)
    
    return text


def generate_table_of_contents_structure(headings: List[Dict[str, Any]], max_level: int = 3) -> List[Dict[str, Any]]:
    """
    Generate hierarchical table of contents structure.
    
    Args:
        headings: List of heading dictionaries from extract_content_metadata
        max_level: Maximum heading level to include (default: 3 for H1-H3)
        
    Returns:
        Hierarchical structure suitable for frontend TOC rendering
    """
    toc = []
    stack = []  # Stack to track parent headings
    
    for heading in headings:
        if heading["level"] > max_level:
            continue
        
        # Pop stack until we find the parent level
        while stack and stack[-1]["level"] >= heading["level"]:
            stack.pop()
        
        toc_item = {
            "id": heading["id"],
            "text": heading["text"],
            "level": heading["level"],
            "children": []
        }
        
        if stack:
            # Add as child of current parent
            stack[-1]["children"].append(toc_item)
        else:
            # Top-level item
            toc.append(toc_item)
        
        stack.append(toc_item)
    
    return toc

