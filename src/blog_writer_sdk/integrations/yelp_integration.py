"""
Yelp Fusion API integration for local business data and reviews.

This module provides integration with Yelp Fusion API to fetch
business information, reviews, ratings, and other business details.
"""

import os
import logging
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

from ..monitoring.metrics import monitor_performance
from ..monitoring.cloud_logging import get_blog_logger

logger = get_blog_logger()


class YelpClient:
    """
    Yelp Fusion API client for business search and review fetching.
    
    Handles searching for businesses, fetching business details,
    and retrieving reviews from Yelp.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
    ):
        """
        Initialize Yelp client.
        
        Args:
            api_key: Yelp Fusion API key (or from YELP_API_KEY env)
        """
        self.api_key = api_key or os.getenv("YELP_API_KEY")
        self.base_url = "https://api.yelp.com/v3"
        
        if not self.api_key:
            logger.warning("Yelp API key not configured. Yelp features will be disabled.")
            self.is_configured = False
        else:
            self.is_configured = True
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        self.logger = logger
    
    @monitor_performance("yelp_search_businesses")
    async def search_businesses(
        self,
        term: str,
        location: str,
        limit: int = 20,
        sort_by: str = "rating",  # rating, distance, review_count
        price: Optional[str] = None,  # 1, 2, 3, 4
        categories: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Search for businesses on Yelp.
        
        Args:
            term: Search term (e.g., "plumbers", "restaurants")
            location: Location string (e.g., "Miami, FL", "33139")
            limit: Maximum number of results (default: 20, max: 50)
            sort_by: Sort order (rating, distance, review_count)
            price: Price range filter (1-4)
            categories: List of Yelp category aliases
            
        Returns:
            Dictionary with businesses list and metadata
        """
        if not self.is_configured:
            return {
                "businesses": [],
                "total": 0,
                "error": "Yelp API not configured"
            }
        
        try:
            params = {
                "term": term,
                "location": location,
                "limit": min(limit, 50),  # Yelp max is 50
                "sort_by": sort_by,
            }
            
            if price:
                params["price"] = price
            
            if categories:
                params["categories"] = ",".join(categories)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/businesses/search",
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                return {
                    "businesses": data.get("businesses", []),
                    "total": data.get("total", 0),
                    "region": data.get("region", {})
                }
        
        except httpx.HTTPStatusError as e:
            self.logger.error(f"Yelp API error: {e.response.status_code} - {e.response.text}")
            return {
                "businesses": [],
                "total": 0,
                "error": f"Yelp API error: {e.response.status_code}"
            }
        except Exception as e:
            self.logger.error(f"Yelp search failed: {e}")
            return {
                "businesses": [],
                "total": 0,
                "error": str(e)
            }
    
    @monitor_performance("yelp_get_business_details")
    async def get_business_details(
        self,
        business_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific business.
        
        Args:
            business_id: Yelp business ID
            
        Returns:
            Business details dictionary or None if error
        """
        if not self.is_configured:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/businesses/{business_id}",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()
        
        except httpx.HTTPStatusError as e:
            self.logger.error(f"Yelp API error getting business {business_id}: {e.response.status_code}")
            return None
        except Exception as e:
            self.logger.error(f"Yelp get business details failed: {e}")
            return None
    
    @monitor_performance("yelp_get_business_reviews")
    async def get_business_reviews(
        self,
        business_id: str,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Get reviews for a specific business.
        
        Args:
            business_id: Yelp business ID
            limit: Maximum number of reviews (default: 20, max: 50)
            
        Returns:
            Dictionary with reviews list and metadata
        """
        if not self.is_configured:
            return {
                "reviews": [],
                "total": 0,
                "error": "Yelp API not configured"
            }
        
        try:
            params = {
                "limit": min(limit, 50),  # Yelp max is 50
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/businesses/{business_id}/reviews",
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                return {
                    "reviews": data.get("reviews", []),
                    "total": data.get("total", 0),
                    "possible_languages": data.get("possible_languages", [])
                }
        
        except httpx.HTTPStatusError as e:
            self.logger.error(f"Yelp API error getting reviews for {business_id}: {e.response.status_code}")
            return {
                "reviews": [],
                "total": 0,
                "error": f"Yelp API error: {e.response.status_code}"
            }
        except Exception as e:
            self.logger.error(f"Yelp get reviews failed: {e}")
            return {
                "reviews": [],
                "total": 0,
                "error": str(e)
            }
    
    async def get_business_with_reviews(
        self,
        business_id: str,
        review_limit: int = 20,
    ) -> Optional[Dict[str, Any]]:
        """
        Get business details along with reviews in a single call.
        
        Args:
            business_id: Yelp business ID
            review_limit: Maximum number of reviews to fetch
            
        Returns:
            Combined business and reviews data
        """
        business_details, reviews_data = await asyncio.gather(
            self.get_business_details(business_id),
            self.get_business_reviews(business_id, review_limit),
            return_exceptions=True
        )
        
        if isinstance(business_details, Exception):
            self.logger.error(f"Failed to get business details: {business_details}")
            business_details = None
        
        if isinstance(reviews_data, Exception):
            self.logger.error(f"Failed to get reviews: {reviews_data}")
            reviews_data = {"reviews": [], "total": 0}
        
        if not business_details:
            return None
        
        return {
            **business_details,
            "yelp_reviews": reviews_data.get("reviews", []),
            "review_count_yelp": reviews_data.get("total", 0)
        }

