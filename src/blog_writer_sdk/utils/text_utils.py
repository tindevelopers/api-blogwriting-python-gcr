"""
Text utility functions for the Blog Writer SDK.

This module provides common text processing utilities used throughout the SDK.
"""

import re
import unicodedata
from typing import List, Optional


def create_slug(text: str, max_length: int = 50) -> str:
    """
    Create a URL-friendly slug from text.
    
    Args:
        text: Input text to convert to slug
        max_length: Maximum length of the slug
        
    Returns:
        URL-friendly slug
    """
    if not text:
        return "untitled"
    
    # Convert to lowercase and normalize unicode
    slug = text.lower()
    slug = unicodedata.normalize('NFKD', slug)
    
    # Remove non-alphanumeric characters and replace with hyphens
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Truncate to max length
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')
    
    return slug or "untitled"


def extract_excerpt(content: str, max_length: int = 250) -> str:
    """
    Extract an excerpt from content.
    
    Args:
        content: Full content text
        max_length: Maximum length of excerpt
        
    Returns:
        Content excerpt
    """
    if not content:
        return ""
    
    # Clean content (remove markdown/HTML)
    clean_content = clean_text_for_excerpt(content)
    
    # If content is short enough, return as-is
    if len(clean_content) <= max_length:
        return clean_content
    
    # Find the best break point (end of sentence)
    excerpt = clean_content[:max_length]
    
    # Look for sentence endings
    sentence_endings = ['. ', '! ', '? ']
    best_break = -1
    
    for ending in sentence_endings:
        last_occurrence = excerpt.rfind(ending)
        if last_occurrence > best_break:
            best_break = last_occurrence + 1
    
    # If we found a good break point, use it
    if best_break > max_length * 0.7:  # At least 70% of max length
        return clean_content[:best_break].strip()
    
    # Otherwise, break at word boundary
    words = excerpt.split()
    if len(words) > 1:
        words = words[:-1]  # Remove last potentially incomplete word
        return ' '.join(words) + '...'
    
    return excerpt + '...'


def clean_text_for_excerpt(text: str) -> str:
    """
    Clean text for excerpt generation.
    
    Args:
        text: Raw text with potential markdown/HTML
        
    Returns:
        Cleaned text suitable for excerpts
    """
    # Remove markdown headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Remove markdown links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove markdown emphasis
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Clean up whitespace
    text = re.sub(r'\n\s*\n', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def count_words(text: str) -> int:
    """
    Count words in text.
    
    Args:
        text: Text to count words in
        
    Returns:
        Number of words
    """
    if not text:
        return 0
    
    # Clean text and split by whitespace
    clean_text = clean_text_for_excerpt(text)
    words = clean_text.split()
    
    return len(words)


def estimate_reading_time(text: str, words_per_minute: int = 225) -> float:
    """
    Estimate reading time for text.
    
    Args:
        text: Text to estimate reading time for
        words_per_minute: Average reading speed
        
    Returns:
        Estimated reading time in minutes
    """
    word_count = count_words(text)
    return word_count / words_per_minute


def extract_keywords_from_text(text: str, min_length: int = 3, max_keywords: int = 20) -> List[str]:
    """
    Extract potential keywords from text.
    
    Args:
        text: Text to extract keywords from
        min_length: Minimum keyword length
        max_keywords: Maximum number of keywords to return
        
    Returns:
        List of potential keywords
    """
    if not text:
        return []
    
    # Clean and normalize text
    clean_text = clean_text_for_excerpt(text).lower()
    
    # Extract words
    words = re.findall(r'\b[a-zA-Z]+\b', clean_text)
    
    # Filter by length and remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'among', 'this', 'that',
        'these', 'those', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
        'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself',
        'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their',
        'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'these',
        'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
        'had', 'having', 'do', 'does', 'did', 'doing', 'will', 'would', 'should', 'could',
        'can', 'may', 'might', 'must', 'shall'
    }
    
    filtered_words = [
        word for word in words 
        if len(word) >= min_length and word not in stop_words
    ]
    
    # Count frequency
    from collections import Counter
    word_counts = Counter(filtered_words)
    
    # Get most common words
    common_words = word_counts.most_common(max_keywords)
    
    return [word for word, count in common_words]


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    # Account for suffix length
    truncate_length = max_length - len(suffix)
    
    if truncate_length <= 0:
        return suffix[:max_length]
    
    # Try to break at word boundary
    truncated = text[:truncate_length]
    last_space = truncated.rfind(' ')
    
    if last_space > truncate_length * 0.8:  # At least 80% of target length
        truncated = truncated[:last_space]
    
    return truncated + suffix


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.
    
    Args:
        text: Text to normalize
        
    Returns:
        Text with normalized whitespace
    """
    if not text:
        return ""
    
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    
    # Replace multiple newlines with double newlines
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # Remove trailing whitespace from lines
    lines = text.split('\n')
    lines = [line.rstrip() for line in lines]
    
    return '\n'.join(lines).strip()


def extract_headings(content: str) -> List[dict]:
    """
    Extract headings from markdown content.
    
    Args:
        content: Markdown content
        
    Returns:
        List of heading dictionaries with level and text
    """
    headings = []
    
    # Find markdown headings
    heading_pattern = r'^(#{1,6})\s+(.+)$'
    matches = re.finditer(heading_pattern, content, re.MULTILINE)
    
    for match in matches:
        level = len(match.group(1))
        text = match.group(2).strip()
        
        headings.append({
            'level': level,
            'text': text,
            'slug': create_slug(text),
        })
    
    return headings


def generate_table_of_contents(content: str, max_level: int = 3) -> str:
    """
    Generate table of contents from content headings.
    
    Args:
        content: Markdown content
        max_level: Maximum heading level to include
        
    Returns:
        Table of contents in markdown format
    """
    headings = extract_headings(content)
    
    if not headings:
        return ""
    
    toc_lines = ["## Table of Contents\n"]
    
    for heading in headings:
        if heading['level'] <= max_level:
            indent = "  " * (heading['level'] - 1)
            link = f"[{heading['text']}](#{heading['slug']})"
            toc_lines.append(f"{indent}- {link}")
    
    return "\n".join(toc_lines) + "\n"


def validate_markdown(content: str) -> List[str]:
    """
    Validate markdown content and return list of issues.
    
    Args:
        content: Markdown content to validate
        
    Returns:
        List of validation issues
    """
    issues = []
    
    # Check for multiple H1 headings
    h1_count = len(re.findall(r'^#\s+', content, re.MULTILINE))
    if h1_count > 1:
        issues.append(f"Multiple H1 headings found ({h1_count}). Should have only one.")
    elif h1_count == 0:
        issues.append("No H1 heading found. Content should start with an H1.")
    
    # Check for broken links
    links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content)
    for link_text, link_url in links:
        if not link_url.strip():
            issues.append(f"Empty link URL for text: '{link_text}'")
        elif link_url.startswith('http') and ' ' in link_url:
            issues.append(f"Link URL contains spaces: '{link_url}'")
    
    # Check for unbalanced emphasis
    bold_count = content.count('**')
    if bold_count % 2 != 0:
        issues.append("Unbalanced bold emphasis (**) markers found.")
    
    italic_count = content.count('*') - bold_count
    if italic_count % 2 != 0:
        issues.append("Unbalanced italic emphasis (*) markers found.")
    
    # Check for very long lines (readability)
    lines = content.split('\n')
    long_lines = [i + 1 for i, line in enumerate(lines) if len(line) > 120 and not line.startswith('#')]
    if long_lines:
        issues.append(f"Very long lines found (>120 chars): lines {', '.join(map(str, long_lines[:5]))}")
    
    return issues


def clean_html_tags(text: str) -> str:
    """
    Remove HTML tags from text.
    
    Args:
        text: Text with potential HTML tags
        
    Returns:
        Text with HTML tags removed
    """
    if not text:
        return ""
    
    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', '', text)
    
    # Decode common HTML entities
    html_entities = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
        '&nbsp;': ' ',
    }
    
    for entity, replacement in html_entities.items():
        clean_text = clean_text.replace(entity, replacement)
    
    return clean_text


def format_title_case(text: str) -> str:
    """
    Format text in title case following standard rules.
    
    Args:
        text: Text to format
        
    Returns:
        Text in title case
    """
    if not text:
        return ""
    
    # Words that should not be capitalized (unless first or last word)
    small_words = {
        'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'if', 'in', 'nor',
        'of', 'on', 'or', 'so', 'the', 'to', 'up', 'yet'
    }
    
    words = text.lower().split()
    title_words = []
    
    for i, word in enumerate(words):
        if i == 0 or i == len(words) - 1 or word not in small_words:
            title_words.append(word.capitalize())
        else:
            title_words.append(word)
    
    return ' '.join(title_words)
