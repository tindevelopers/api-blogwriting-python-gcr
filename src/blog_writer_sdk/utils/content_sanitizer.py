"""
Content Sanitizer for LLM Output

This module provides comprehensive sanitization of LLM-generated content
to remove artifacts, preamble phrases, and other unwanted patterns.

Based on Frontend Quality Enhancement Requirements (December 2025).
"""

import re
from typing import Tuple, List, Optional


def sanitize_llm_output(content: str) -> Tuple[str, List[str]]:
    """
    Remove common LLM artifacts before returning to frontend.
    
    This function removes:
    - Preamble phrases ("Here's the enhanced version...")
    - Meta-commentary ("Enhancements Made:", "Key Points:")
    - Malformed image placeholders
    - Truncated text artifacts
    
    Args:
        content: Raw LLM output content
        
    Returns:
        Tuple of (sanitized_content, list_of_artifacts_removed)
    """
    if not content:
        return content, []
    
    artifacts_removed = []
    
    patterns = [
        # Preamble patterns (must be at start or after newline)
        (r"^Here's (?:the |an )?(?:enhanced |revised |updated |improved )?"
         r"(?:version|content|blog post|article).*?:\s*\n?", "preamble"),
        (r"^Here is (?:the |an )?(?:enhanced |revised |updated |improved )?"
         r"(?:version|content|blog post|article).*?:\s*\n?", "preamble"),
        (r"^I'll provide.*?:\s*\n?", "preamble"),
        (r"^I will provide.*?:\s*\n?", "preamble"),
        (r"^I've (?:created|written|prepared|enhanced).*?:\s*\n?", "preamble"),
        (r"^Addressing the specified.*?:\s*\n?", "preamble"),
        (r"^Let me (?:provide|create|write|enhance).*?:\s*\n?", "preamble"),
        (r"^Below is (?:the |an )?(?:enhanced |revised |updated )?.*?:\s*\n?", "preamble"),
        (r"^The following (?:is |contains ).*?:\s*\n?", "preamble"),
        (r"^I(?:'ve| have) (?:enhanced|revised|updated|improved).*?:\s*\n?", "preamble"),
        
        # Meta-commentary patterns (can appear anywhere, typically at end)
        (r"\n*Enhancements Made:[\s\S]*?(?=\n\n(?:#|\Z)|\Z)", "meta_commentary"),
        (r"\n*Key Enhancements:[\s\S]*?(?=\n\n(?:#|\Z)|\Z)", "meta_commentary"),
        (r"\n*Changes Made:[\s\S]*?(?=\n\n(?:#|\Z)|\Z)", "meta_commentary"),
        (r"\n*Improvements:[\s\S]*?(?=\n\n(?:#|\Z)|\Z)", "meta_commentary"),
        (r"\n*Summary of Changes:[\s\S]*?(?=\n\n(?:#|\Z)|\Z)", "meta_commentary"),
        (r"\n*Notes?:[\s\S]*?(?=\n\n(?:#|\Z)|\Z)", "meta_commentary"),
        (r"Citations added where appropriate.*?(?=\n|$)", "meta_commentary"),
        (r"Methodology Note:.*?(?=\n|$)", "meta_commentary"),
        (r"\*Last updated:.*?\*", "meta_commentary"),
        (r"The revised content.*?:\s*\n?", "meta_commentary"),
        (r"readability concerns:.*?(?=\n|$)", "meta_commentary"),
        (r"\n*---\s*\n*(?:Note|Disclaimer|Editor's Note):[\s\S]*$", "meta_commentary"),
        
        # Malformed image placeholders (no URL or empty URL)
        (r"!\[[^\]]*\]\(\s*\)", "malformed_image"),
        (r"!\[[^\]]*\]\(image-url\)", "malformed_image"),
        (r"!\[[^\]]*\]\(https?://placeholder[^\)]*\)", "malformed_image"),
        (r"^!(?:AI|Featured|Modern|Content|Image)\s+[^\n!\[\]]{5,50}(?=\s|\n|$)", "malformed_image"),
        (r"!\s*([A-Z][a-zA-Z\s]{5,40})(?=\n|$)", "malformed_image"),
        
        # Truncated text artifacts (from DataForSEO or other sources)
        (r"\bf\.\s+(?=\d{4})", "truncated_text"),  # "f. 2025" -> "2025"
        (r"\s+\.\s+(?=[a-z])", "broken_punctuation"),  # ". word" -> " word"
        
        # Thinking/reasoning tags (already in ai_gateway but include for completeness)
        (r'<thinking>.*?</thinking>', "thinking_tag"),
        (r'<thought>.*?</thought>', "thinking_tag"),
        (r'<reasoning>.*?</reasoning>', "thinking_tag"),
        (r'<reflection>.*?</reflection>', "thinking_tag"),
        (r'<internal>.*?</internal>', "thinking_tag"),
        (r'\[THINKING\].*?\[/THINKING\]', "thinking_tag"),
        (r'\[THOUGHT\].*?\[/THOUGHT\]', "thinking_tag"),
        (r'\*\*Thinking:\*\*.*?(?=\n\n|\Z)', "thinking_tag"),
        (r'\*\*Internal:\*\*.*?(?=\n\n|\Z)', "thinking_tag"),
        (r'---\s*thinking\s*---.*?---\s*end\s*thinking\s*---', "thinking_tag"),
    ]
    
    for pattern, artifact_type in patterns:
        matches = re.findall(pattern, content, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if matches:
            artifacts_removed.append(f"{artifact_type}: {len(matches)} instance(s)")
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
    
    # Clean up resulting whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = content.strip()
    
    return content, artifacts_removed


def sanitize_excerpt(excerpt: str, primary_keyword: Optional[str] = None) -> str:
    """
    Clean excerpt/meta description of common issues.
    
    This function:
    - Removes keyword-only prefixes
    - Removes preamble phrases
    - Fixes truncated text
    - Ensures proper ending punctuation
    - Truncates to 160 characters properly
    
    Args:
        excerpt: Raw excerpt text
        primary_keyword: Optional primary keyword to check for prefix issues
        
    Returns:
        Cleaned excerpt string
    """
    if not excerpt:
        return ""
    
    cleaned = excerpt.strip()
    
    # Remove keyword-only prefix (e.g., "best ai voice agents Here's why...")
    if primary_keyword:
        keyword_lower = primary_keyword.lower()
        if cleaned.lower().startswith(keyword_lower):
            cleaned = cleaned[len(primary_keyword):].lstrip()
            # Capitalize first letter of remaining text
            if cleaned:
                cleaned = cleaned[0].upper() + cleaned[1:]
    
    # Remove preamble phrases
    preamble_patterns = [
        r"^Here's (?:the |an |a )?.*?:\s*",
        r"^This (?:article|post|guide|blog) (?:will |explains? |covers? |discusses? |explores? ).*?:\s*",
        r"^In this (?:article|post|guide|blog),?\s*",
        r"^Welcome to (?:our|this|the).*?[.!]\s*",
        r"^Let(?:'s| us) (?:explore|dive|look).*?[.!]\s*",
    ]
    for pattern in preamble_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Fix truncated text
    cleaned = re.sub(r'\bf\.\s+', 'for ', cleaned)
    cleaned = re.sub(r'\s+\.\s+', '. ', cleaned)
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)  # Multiple spaces
    
    # Ensure proper ending
    cleaned = cleaned.rstrip()
    if cleaned and cleaned[-1] not in '.!?':
        # Find last complete sentence
        last_sentence_end = max(
            cleaned.rfind('. '),
            cleaned.rfind('! '),
            cleaned.rfind('? ')
        )
        if last_sentence_end > len(cleaned) * 0.5:
            cleaned = cleaned[:last_sentence_end + 1]
        else:
            cleaned = cleaned.rstrip(',:;-') + '.'
    
    # Truncate to 160 chars properly (for meta description)
    if len(cleaned) > 160:
        # Find a good break point
        truncated = cleaned[:157]
        # Try to break at a word boundary
        last_space = truncated.rfind(' ')
        if last_space > 120:  # Only if we have a reasonable length
            truncated = truncated[:last_space]
        cleaned = truncated.rstrip(',:;-') + '...'
    
    return cleaned.strip()


def detect_artifacts(content: str) -> List[dict]:
    """
    Detect artifacts in content without removing them.
    
    Useful for content validation endpoint.
    
    Args:
        content: Content to check for artifacts
        
    Returns:
        List of detected artifact details
    """
    if not content:
        return []
    
    detected = []
    
    detection_patterns = [
        (r"^Here's (?:the |an )?(?:enhanced |revised |updated )?"
         r"(?:version|content|blog post).*?:", "preamble",
         "Content starts with LLM preamble phrase"),
        (r"Enhancements Made:", "meta_commentary", "Contains 'Enhancements Made' section"),
        (r"Key Enhancements:", "meta_commentary", "Contains 'Key Enhancements' section"),
        (r"!\[[^\]]*\]\(\s*\)", "malformed_image", "Contains empty image placeholder"),
        (r"^!(?:AI|Featured|Modern|Content)\s+", "malformed_image", "Contains malformed image reference"),
        (r"<thinking>", "thinking_tag", "Contains <thinking> tags"),
        (r"\*Last updated:.*?\*", "meta_commentary", "Contains 'Last updated' metadata"),
    ]
    
    for pattern, artifact_type, description in detection_patterns:
        matches = re.findall(pattern, content, flags=re.IGNORECASE | re.MULTILINE)
        if matches:
            detected.append({
                "type": artifact_type,
                "description": description,
                "count": len(matches),
                "severity": "error" if artifact_type in ["preamble", "thinking_tag"] else "warning"
            })
    
    return detected


def strip_markdown_for_analysis(content: str) -> str:
    """
    Strip markdown formatting for text analysis.
    
    Args:
        content: Markdown content
        
    Returns:
        Plain text content
    """
    if not content:
        return ""
    
    cleaned = content
    
    # Remove code blocks
    cleaned = re.sub(r'```[\s\S]*?```', '', cleaned)
    cleaned = re.sub(r'`[^`]+`', '', cleaned)
    
    # Remove headings markers
    cleaned = re.sub(r'^#{1,6}\s+', '', cleaned, flags=re.MULTILINE)
    
    # Remove images
    cleaned = re.sub(r'!\[[^\]]*\]\([^\)]+\)', '', cleaned)
    
    # Remove links but keep text
    cleaned = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cleaned)
    
    # Remove bold/italic
    cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)
    cleaned = re.sub(r'\*([^*]+)\*', r'\1', cleaned)
    cleaned = re.sub(r'__([^_]+)__', r'\1', cleaned)
    cleaned = re.sub(r'_([^_]+)_', r'\1', cleaned)
    
    # Remove horizontal rules
    cleaned = re.sub(r'^---+$', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'^\*\*\*+$', '', cleaned, flags=re.MULTILINE)
    
    # Remove list markers
    cleaned = re.sub(r'^[\s]*[-*+]\s+', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'^[\s]*\d+\.\s+', '', cleaned, flags=re.MULTILINE)
    
    # Clean up whitespace
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    cleaned = re.sub(r' {2,}', ' ', cleaned)
    
    return cleaned.strip()

