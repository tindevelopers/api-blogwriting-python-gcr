"""
Review aggregation service for combining reviews from Google Places.

This module aggregates reviews from Google Places API,
providing a unified interface for review data processing and analysis.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from .google_reviews_client import GoogleReviewsClient
from ..monitoring.cloud_logging import get_blog_logger

logger = get_blog_logger()


class ReviewSource(str, Enum):
    """Review source enumeration."""
    GOOGLE = "google"
    UNKNOWN = "unknown"


@dataclass
class Review:
    """Unified review data structure."""
    text: str
    rating: float
    author: str
    date: Optional[datetime] = None
    source: ReviewSource = ReviewSource.UNKNOWN
    source_id: Optional[str] = None
    url: Optional[str] = None
    helpful_count: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BusinessReviewSummary:
    """Summary of reviews for a business."""
    business_name: str
    business_id: Optional[str] = None
    total_reviews: int = 0
    average_rating: float = 0.0
    rating_distribution: Dict[int, int] = field(default_factory=dict)
    reviews: List[Review] = field(default_factory=list)
    sources: List[ReviewSource] = field(default_factory=list)
    last_updated: Optional[datetime] = None


class ReviewAggregationService:
    """
    Service for aggregating reviews from Google Places.
    
    Combines reviews from Google Places API
    into a unified format for content generation.
    """
    
    def __init__(
        self,
        google_client: Optional[GoogleReviewsClient] = None,
    ):
        """
        Initialize review aggregation service.
        
        Args:
            google_client: Optional Google Reviews client instance
        """
        self.google_client = google_client or GoogleReviewsClient()
        self.logger = logger
    
    def _parse_google_review(self, google_review: Dict[str, Any]) -> Review:
        """Parse a Google review into unified format."""
        try:
            # Parse date
            date_timestamp = google_review.get("time")
            review_date = None
            if date_timestamp:
                try:
                    review_date = datetime.fromtimestamp(date_timestamp)
                except:
                    pass
            
            return Review(
                text=google_review.get("text", ""),
                rating=google_review.get("rating", 0),
                author=google_review.get("author_name", "Anonymous"),
                date=review_date,
                source=ReviewSource.GOOGLE,
                source_id=google_review.get("author_url"),
                url=google_review.get("author_url"),
                helpful_count=None,
                metadata={
                    "google_review_id": google_review.get("author_url"),
                    "relative_time": google_review.get("relative_time_description"),
                }
            )
        except Exception as e:
            self.logger.error(f"Error parsing Google review: {e}")
            return Review(
                text="",
                rating=0,
                author="Unknown",
                source=ReviewSource.GOOGLE
            )
    
    async def aggregate_business_reviews(
        self,
        business_name: str,
        google_place_id: Optional[str] = None,
        max_reviews_per_source: int = 20,
    ) -> BusinessReviewSummary:
        """
        Aggregate reviews from Google Places for a business.
        
        Args:
            business_name: Name of the business
            google_place_id: Optional Google Places place_id
            max_reviews_per_source: Maximum reviews to fetch
            
        Returns:
            BusinessReviewSummary with aggregated reviews
        """
        summary = BusinessReviewSummary(business_name=business_name)
        all_reviews: List[Review] = []
        sources_used: List[ReviewSource] = []
        
        # Fetch Google reviews
        if google_place_id and self.google_client.is_configured:
            try:
                google_data = await self.google_client.get_place_reviews(google_place_id)
                
                google_reviews = google_data.get("reviews", [])
                for google_review in google_reviews:
                    review = self._parse_google_review(google_review)
                    if review.text:  # Only add reviews with text
                        all_reviews.append(review)
                
                if google_reviews:
                    sources_used.append(ReviewSource.GOOGLE)
                    self.logger.info(f"Fetched {len(google_reviews)} Google reviews for {business_name}")
            
            except Exception as e:
                self.logger.error(f"Error fetching Google reviews: {e}")
        
        # Calculate summary statistics
        if all_reviews:
            ratings = [r.rating for r in all_reviews if r.rating > 0]
            if ratings:
                summary.average_rating = sum(ratings) / len(ratings)
                
                # Rating distribution
                for rating in ratings:
                    rating_int = int(rating)
                    summary.rating_distribution[rating_int] = summary.rating_distribution.get(rating_int, 0) + 1
        
        summary.total_reviews = len(all_reviews)
        summary.reviews = all_reviews
        summary.sources = sources_used
        summary.last_updated = datetime.now()
        
        return summary
    
    async def aggregate_multiple_businesses(
        self,
        businesses: List[Dict[str, Any]],
        max_reviews_per_business: int = 20,
    ) -> List[BusinessReviewSummary]:
        """
        Aggregate reviews for multiple businesses.
        
        Args:
            businesses: List of business dictionaries with:
                - name: Business name
                - google_place_id: Optional Google Places place_id
            max_reviews_per_business: Maximum reviews per business
            
        Returns:
            List of BusinessReviewSummary objects
        """
        import asyncio
        
        tasks = []
        for business in businesses:
            task = self.aggregate_business_reviews(
                business_name=business.get("name", "Unknown"),
                google_place_id=business.get("google_place_id"),
                max_reviews_per_source=max_reviews_per_business,
            )
            tasks.append(task)
        
        summaries = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_summaries = []
        for summary in summaries:
            if isinstance(summary, Exception):
                self.logger.error(f"Error aggregating reviews: {summary}")
            else:
                valid_summaries.append(summary)
        
        return valid_summaries
    
    def get_top_reviews(
        self,
        summary: BusinessReviewSummary,
        limit: int = 10,
        min_rating: Optional[float] = None,
    ) -> List[Review]:
        """
        Get top reviews from a business summary.
        
        Args:
            summary: BusinessReviewSummary object
            limit: Maximum number of reviews to return
            min_rating: Minimum rating filter (optional)
            
        Returns:
            List of top reviews
        """
        reviews = summary.reviews
        
        # Filter by minimum rating if specified
        if min_rating:
            reviews = [r for r in reviews if r.rating >= min_rating]
        
        # Sort by rating (descending), then by helpful count if available
        reviews.sort(
            key=lambda r: (r.rating, r.helpful_count or 0),
            reverse=True
        )
        
        return reviews[:limit]
    
    def get_review_sentiment_summary(
        self,
        summary: BusinessReviewSummary,
    ) -> Dict[str, Any]:
        """
        Get sentiment summary from reviews.
        
        This is a basic implementation. For Phase 3, this can be enhanced
        with actual sentiment analysis using NLP libraries.
        
        Args:
            summary: BusinessReviewSummary object
            
        Returns:
            Dictionary with sentiment metrics
        """
        if not summary.reviews:
            return {
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "positive_percentage": 0,
                "negative_percentage": 0,
            }
        
        positive = sum(1 for r in summary.reviews if r.rating >= 4)
        negative = sum(1 for r in summary.reviews if r.rating <= 2)
        neutral = len(summary.reviews) - positive - negative
        
        total = len(summary.reviews)
        
        return {
            "positive_count": positive,
            "negative_count": negative,
            "neutral_count": neutral,
            "positive_percentage": (positive / total * 100) if total > 0 else 0,
            "negative_percentage": (negative / total * 100) if total > 0 else 0,
            "average_rating": summary.average_rating,
        }

