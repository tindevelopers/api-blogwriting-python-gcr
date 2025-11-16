"""
Testing phase data limits configuration.

This module provides limits for testing mode to reduce API calls,
processing time, and costs while maintaining test coverage.
"""

import os
from typing import Dict, Any, Optional


def is_testing_mode() -> bool:
    """Check if testing mode is enabled."""
    return os.getenv("TESTING_MODE", "false").lower() in ("true", "1", "yes", "on")


def get_testing_limits() -> Dict[str, Any]:
    """
    Get testing phase data limits.
    
    Returns:
        Dictionary with all testing limits
    """
    return {
        # Keyword research limits
        "max_keywords": 5,  # Primary keywords per search session
        "max_suggestions_per_keyword": 5,  # Related keywords per primary
        "max_long_tail": 5,  # Long-tail variations per primary
        "max_total_keywords": 25,  # Total keywords per session (primary + related + long-tail)
        
        # Backlinks data limits
        "max_backlinks": 20,  # Backlinks per domain
        "max_referring_domains": 10,  # Referring domains
        "max_anchors": 10,  # Top anchor texts
        
        # SERP data limits
        "max_serp_results": 10,  # Top organic results
        "max_serp_features": 5,  # Top SERP features (featured snippets, etc.)
        
        # Trend data limits
        "trend_months": 6,  # Last N months instead of 12
        "include_historical": False,  # Skip historical comparisons
        
        # Clustering limits
        "max_clusters": 5,  # Top clusters per session
        "max_keywords_per_cluster": 10,  # Keywords per cluster
        
        # Content brief limits
        "max_competitors": 3,  # Competitor domains
        "max_content_ideas": 10,  # Content ideas per cluster
    }


def apply_keyword_limits(keywords: list, max_keywords: Optional[int] = None) -> list:
    """
    Apply keyword limits for testing mode.
    
    Args:
        keywords: List of keywords
        max_keywords: Optional override for max keywords
        
    Returns:
        Limited list of keywords
    """
    if not is_testing_mode():
        return keywords
    
    limits = get_testing_limits()
    limit = max_keywords or limits["max_keywords"]
    limited = keywords[:limit]
    
    if len(limited) < len(keywords):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🧪 TESTING MODE: Limited keywords from {len(keywords)} to {len(limited)}")
    
    return limited


def apply_suggestions_limit(max_suggestions: int) -> int:
    """
    Apply suggestions limit for testing mode.
    
    Args:
        max_suggestions: Requested max suggestions
        
    Returns:
        Limited max suggestions
    """
    if not is_testing_mode():
        return max_suggestions
    
    limits = get_testing_limits()
    limit = limits["max_suggestions_per_keyword"]
    
    if max_suggestions > limit:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🧪 TESTING MODE: Limited suggestions from {max_suggestions} to {limit}")
        return limit
    
    return max_suggestions


def apply_clustering_limits(max_clusters: Optional[int] = None, max_keywords_per_cluster: Optional[int] = None) -> tuple[int, int]:
    """
    Apply clustering limits for testing mode.
    
    Args:
        max_clusters: Optional override for max clusters
        max_keywords_per_cluster: Optional override for keywords per cluster
        
    Returns:
        Tuple of (max_clusters, max_keywords_per_cluster)
    """
    if not is_testing_mode():
        return max_clusters or 10, max_keywords_per_cluster or 20
    
    limits = get_testing_limits()
    clusters = max_clusters or limits["max_clusters"]
    keywords = max_keywords_per_cluster or limits["max_keywords_per_cluster"]
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"🧪 TESTING MODE: Clustering limits - {clusters} clusters, {keywords} keywords per cluster")
    
    return clusters, keywords


def apply_backlink_limits(max_backlinks: Optional[int] = None, max_domains: Optional[int] = None) -> tuple[int, int]:
    """
    Apply backlink limits for testing mode.
    
    Args:
        max_backlinks: Optional override for max backlinks
        max_domains: Optional override for max referring domains
        
    Returns:
        Tuple of (max_backlinks, max_domains)
    """
    if not is_testing_mode():
        return max_backlinks or 100, max_domains or 50
    
    limits = get_testing_limits()
    backlinks = max_backlinks or limits["max_backlinks"]
    domains = max_domains or limits["max_referring_domains"]
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"🧪 TESTING MODE: Backlink limits - {backlinks} backlinks, {domains} domains")
    
    return backlinks, domains


def apply_serp_limits(max_results: Optional[int] = None, max_features: Optional[int] = None) -> tuple[int, int]:
    """
    Apply SERP limits for testing mode.
    
    Args:
        max_results: Optional override for max SERP results
        max_features: Optional override for max SERP features
        
    Returns:
        Tuple of (max_results, max_features)
    """
    if not is_testing_mode():
        return max_results or 20, max_features or 10
    
    limits = get_testing_limits()
    results = max_results or limits["max_serp_results"]
    features = max_features or limits["max_serp_features"]
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"🧪 TESTING MODE: SERP limits - {results} results, {features} features")
    
    return results, features


def get_trend_months() -> int:
    """
    Get trend data months limit for testing mode.
    
    Returns:
        Number of months for trend data
    """
    if not is_testing_mode():
        return 12
    
    limits = get_testing_limits()
    return limits["trend_months"]


def should_include_historical() -> bool:
    """
    Check if historical data should be included.
    
    Returns:
        False if testing mode, True otherwise
    """
    if not is_testing_mode():
        return True
    
    limits = get_testing_limits()
    return limits["include_historical"]


def apply_competitor_limits(max_competitors: Optional[int] = None) -> int:
    """
    Apply competitor limits for testing mode.
    
    Args:
        max_competitors: Optional override for max competitors
        
    Returns:
        Limited max competitors
    """
    if not is_testing_mode():
        return max_competitors or 10
    
    limits = get_testing_limits()
    limit = max_competitors or limits["max_competitors"]
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"🧪 TESTING MODE: Competitor limit - {limit} competitors")
    
    return limit


def apply_content_ideas_limit(max_ideas: Optional[int] = None) -> int:
    """
    Apply content ideas limit for testing mode.
    
    Args:
        max_ideas: Optional override for max content ideas
        
    Returns:
        Limited max content ideas
    """
    if not is_testing_mode():
        return max_ideas or 20
    
    limits = get_testing_limits()
    limit = max_ideas or limits["max_content_ideas"]
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"🧪 TESTING MODE: Content ideas limit - {limit} ideas")
    
    return limit

