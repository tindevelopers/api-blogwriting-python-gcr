"""
Blog Writer SDK - A powerful Python SDK for AI-driven blog writing with SEO optimization.

This SDK provides comprehensive tools for creating, optimizing, and managing blog content
with a focus on SEO best practices and content quality.
"""

from .core.blog_writer import BlogWriter
from .core.content_analyzer import ContentAnalyzer
from .core.seo_optimizer import SEOOptimizer
from .models.blog_models import (
    BlogPost,
    BlogRequest,
    SEOMetrics,
    ContentQuality,
    BlogGenerationResult,
)
from .seo.keyword_analyzer import KeywordAnalyzer
from .seo.meta_generator import MetaTagGenerator
from .formatters.markdown_formatter import MarkdownFormatter
from .formatters.html_formatter import HTMLFormatter

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

__all__ = [
    # Core classes
    "BlogWriter",
    "ContentAnalyzer", 
    "SEOOptimizer",
    # Models
    "BlogPost",
    "BlogRequest",
    "SEOMetrics",
    "ContentQuality",
    "BlogGenerationResult",
    # SEO tools
    "KeywordAnalyzer",
    "MetaTagGenerator",
    # Formatters
    "MarkdownFormatter",
    "HTMLFormatter",
    # Metadata
    "__version__",
    "__author__",
    "__email__",
]
