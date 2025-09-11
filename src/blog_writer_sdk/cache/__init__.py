"""
Caching components for the BlogWriter SDK.

This module provides Redis-based caching with intelligent fallback
to in-memory caching for improved performance.
"""

from .redis_cache import (
    CacheManager,
    cache_keyword_analysis,
    cache_seo_analysis,
    initialize_cache,
    get_cache_manager,
    cache_manager
)

__all__ = [
    "CacheManager",
    "cache_keyword_analysis",
    "cache_seo_analysis", 
    "initialize_cache",
    "get_cache_manager",
    "cache_manager"
]
