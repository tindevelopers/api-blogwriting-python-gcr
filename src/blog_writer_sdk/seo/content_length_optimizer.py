"""
Content Length & Depth Optimization

Analyzes top-ranking content length and optimizes content depth
based on competition and keyword difficulty.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ContentLengthAnalysis:
    """Analysis of optimal content length."""
    average_length: int
    median_length: int
    min_length: int
    max_length: int
    recommended_length: int
    depth_score: float  # 0-1, how deep content should be


class ContentLengthOptimizer:
    """Optimizes content length based on SERP competition."""
    
    def __init__(self, google_search_client=None, dataforseo_client=None):
        """
        Initialize content length optimizer.
        
        Args:
            google_search_client: Google Custom Search client (optional)
            dataforseo_client: DataForSEO client for SERP data (optional)
        """
        self.google_search = google_search_client
        self.dataforseo_client = dataforseo_client
    
    async def analyze_optimal_length(
        self,
        keyword: str,
        location: str = "United States",
        language: str = "en"
    ) -> ContentLengthAnalysis:
        """
        Analyze optimal content length based on top-ranking content.
        
        Args:
            keyword: Target keyword
            location: Location for search
            language: Language code
        
        Returns:
            ContentLengthAnalysis with recommended length
        """
        # Fetch top-ranking results
        top_results = []
        
        if self.google_search:
            try:
                search_results = await self.google_search.search(
                    query=keyword,
                    num_results=10,
                    language=language
                )
                top_results = search_results
            except Exception as e:
                logger.warning(f"Failed to fetch SERP results for length analysis: {e}")
        
        # Estimate content lengths from snippets and titles
        # In production, could fetch full pages, but snippets give good estimates
        estimated_lengths = []
        
        for result in top_results:
            snippet = result.get("snippet", "")
            title = result.get("title", "")
            
            # Estimate word count from snippet (snippets are typically 150-200 words)
            # Full articles are typically 10-50x snippet length
            snippet_words = len(snippet.split())
            # Conservative estimate: assume snippet is ~5% of article
            estimated_length = snippet_words * 20 if snippet_words > 0 else 1000
            estimated_lengths.append(estimated_length)
        
        if not estimated_lengths:
            # Default recommendation
            return ContentLengthAnalysis(
                average_length=1500,
                median_length=1500,
                min_length=1000,
                max_length=2500,
                recommended_length=1800,  # Aim to exceed average
                depth_score=0.7
            )
        
        # Calculate statistics
        estimated_lengths.sort()
        avg_length = sum(estimated_lengths) / len(estimated_lengths)
        median_length = estimated_lengths[len(estimated_lengths) // 2]
        min_length = min(estimated_lengths)
        max_length = max(estimated_lengths)
        
        # Recommended length: exceed average by 20-30%
        recommended_length = int(avg_length * 1.25)
        
        # Depth score: based on how much content is needed
        # Higher score = need more depth
        if avg_length > 2000:
            depth_score = 0.9
        elif avg_length > 1500:
            depth_score = 0.8
        elif avg_length > 1000:
            depth_score = 0.7
        else:
            depth_score = 0.6
        
        return ContentLengthAnalysis(
            average_length=int(avg_length),
            median_length=int(median_length),
            min_length=int(min_length),
            max_length=int(max_length),
            recommended_length=recommended_length,
            depth_score=depth_score
        )
    
    def adjust_word_count_target(
        self,
        original_target: int,
        analysis: ContentLengthAnalysis
    ) -> int:
        """
        Adjust word count target based on competition analysis.
        
        Args:
            original_target: Original word count target
            analysis: Content length analysis
        
        Returns:
            Adjusted word count target
        """
        # If recommended length is significantly higher, adjust
        if analysis.recommended_length > original_target * 1.2:
            # Increase target but cap at reasonable maximum
            adjusted = min(analysis.recommended_length, original_target * 1.5)
            return int(adjusted)
        
        # If recommended is close, use it
        if analysis.recommended_length >= original_target * 0.9:
            return analysis.recommended_length
        
        # Otherwise keep original
        return original_target

