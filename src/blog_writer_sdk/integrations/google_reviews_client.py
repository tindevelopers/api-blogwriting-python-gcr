"""
Google Places API integration for business information and reviews.

This module provides integration with Google Places API to fetch
business information, reviews, ratings, and other business details.

Note: Google Places API has limited review access in the public API.
For full review access, businesses need to use Google Business Profile API
(requires business owner authentication).
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


class GoogleReviewsClient:
    """
    Google Places API client for business search and information.
    
    Handles searching for businesses, fetching business details,
    and retrieving limited review information from Google Places.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
    ):
        """
        Initialize Google Places API client.
        
        Args:
            api_key: Google Places API key (or from GOOGLE_PLACES_API_KEY env)
        """
        self.api_key = api_key or os.getenv("GOOGLE_PLACES_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")
        self.base_url = "https://maps.googleapis.com/maps/api/place"
        
        if not self.api_key:
            logger.warning("Google Places API key not configured. Google Reviews features will be disabled.")
            self.is_configured = False
        else:
            self.is_configured = True
        
        self.logger = logger
    
    @monitor_performance("google_places_search_businesses")
    async def search_businesses(
        self,
        query: str,
        location: Optional[str] = None,  # "latitude,longitude" or "city, state"
        radius: Optional[int] = None,  # meters
        type: Optional[str] = None,  # e.g., "plumber", "restaurant"
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Search for businesses using Google Places Text Search.
        
        Args:
            query: Search query (e.g., "plumbers in Miami")
            location: Location bias (lat,lng or city, state)
            radius: Search radius in meters
            type: Business type filter
            limit: Maximum number of results (default: 20)
            
        Returns:
            Dictionary with places list and metadata
        """
        if not self.is_configured:
            return {
                "places": [],
                "total": 0,
                "error": "Google Places API not configured"
            }
        
        try:
            params = {
                "query": query,
                "key": self.api_key,
            }
            
            if location:
                params["location"] = location
            
            if radius:
                params["radius"] = radius
            
            if type:
                params["type"] = type
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/textsearch/json",
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") != "OK":
                    error_msg = data.get("error_message", "Unknown error")
                    self.logger.warning(f"Google Places API error: {data.get('status')} - {error_msg}")
                    return {
                        "places": [],
                        "total": 0,
                        "error": f"Google Places API error: {data.get('status')}"
                    }
                
                places = data.get("results", [])[:limit]
                
                return {
                    "places": places,
                    "total": len(places),
                    "next_page_token": data.get("next_page_token")
                }
        
        except httpx.HTTPStatusError as e:
            self.logger.error(f"Google Places API error: {e.response.status_code} - {e.response.text}")
            return {
                "places": [],
                "total": 0,
                "error": f"Google Places API error: {e.response.status_code}"
            }
        except Exception as e:
            self.logger.error(f"Google Places search failed: {e}")
            return {
                "places": [],
                "total": 0,
                "error": str(e)
            }
    
    @monitor_performance("google_places_get_place_details")
    async def get_place_details(
        self,
        place_id: str,
        fields: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific place.
        
        Args:
            place_id: Google Places place_id
            fields: List of fields to return (default: all common fields)
            
        Returns:
            Place details dictionary or None if error
        """
        if not self.is_configured:
            return None
        
        try:
            # Default fields for business information
            default_fields = [
                "name",
                "rating",
                "user_ratings_total",
                "formatted_address",
                "formatted_phone_number",
                "website",
                "opening_hours",
                "types",
                "geometry",
                "photos",
                "reviews",  # Limited reviews available
                "price_level",
                "business_status"
            ]
            
            fields_to_request = fields or default_fields
            
            params = {
                "place_id": place_id,
                "fields": ",".join(fields_to_request),
                "key": self.api_key,
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/details/json",
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") != "OK":
                    error_msg = data.get("error_message", "Unknown error")
                    self.logger.warning(f"Google Places API error: {data.get('status')} - {error_msg}")
                    return None
                
                return data.get("result")
        
        except httpx.HTTPStatusError as e:
            self.logger.error(f"Google Places API error getting place {place_id}: {e.response.status_code}")
            return None
        except Exception as e:
            self.logger.error(f"Google Places get place details failed: {e}")
            return None
    
    @monitor_performance("google_places_get_reviews")
    async def get_place_reviews(
        self,
        place_id: str,
    ) -> Dict[str, Any]:
        """
        Get reviews for a specific place.
        
        Note: Google Places API returns limited reviews (usually 5) in the
        place details response. For full review access, use Google Business
        Profile API (requires business owner authentication).
        
        Args:
            place_id: Google Places place_id
            
        Returns:
            Dictionary with reviews list and metadata
        """
        if not self.is_configured:
            return {
                "reviews": [],
                "total": 0,
                "error": "Google Places API not configured"
            }
        
        try:
            # Get place details with reviews field
            place_details = await self.get_place_details(
                place_id,
                fields=["reviews", "rating", "user_ratings_total"]
            )
            
            if not place_details:
                return {
                    "reviews": [],
                    "total": 0,
                    "error": "Failed to fetch place details"
                }
            
            reviews = place_details.get("reviews", [])
            rating = place_details.get("rating", 0)
            total_ratings = place_details.get("user_ratings_total", 0)
            
            return {
                "reviews": reviews,
                "total": len(reviews),
                "rating": rating,
                "total_ratings": total_ratings,
                "note": "Google Places API returns limited reviews. For full access, use Google Business Profile API."
            }
        
        except Exception as e:
            self.logger.error(f"Google Places get reviews failed: {e}")
            return {
                "reviews": [],
                "total": 0,
                "error": str(e)
            }
    
    async def get_place_with_reviews(
        self,
        place_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get place details along with reviews in a single call.
        
        Args:
            place_id: Google Places place_id
            
        Returns:
            Combined place and reviews data
        """
        place_details = await self.get_place_details(place_id)
        
        if not place_details:
            return None
        
        reviews_data = await self.get_place_reviews(place_id)
        
        return {
            **place_details,
            "google_reviews": reviews_data.get("reviews", []),
            "review_count_google": reviews_data.get("total", 0),
            "rating_google": reviews_data.get("rating", 0),
            "total_ratings_google": reviews_data.get("total_ratings", 0)
        }

