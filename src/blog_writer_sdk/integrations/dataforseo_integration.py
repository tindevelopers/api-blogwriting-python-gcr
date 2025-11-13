"""
DataForSEO integration for real keyword analysis.

This module integrates directly with DataForSEO API to provide
real search volume, competition, and SEO metrics.
"""

import asyncio
import httpx
import base64
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os
import logging
from contextlib import asynccontextmanager
import time

from src.blog_writer_sdk.monitoring.metrics import metrics_collector, monitor_performance
from src.blog_writer_sdk.monitoring.cloud_logging import get_blog_logger, log_api_request
# DataForSEOCredentialService import removed - service not implemented yet

from ..models.blog_models import KeywordAnalysis, SEODifficulty

logger = get_blog_logger()

class DataForSEOClient:
    """
    Client for direct DataForSEO API integration.
    
    This class provides methods to get real SEO data including
    search volume, keyword difficulty, and competitor analysis.
    """
    
    def __init__(self, credential_service: Any = None, api_key: Optional[str] = None, api_secret: Optional[str] = None, location: Optional[str] = None, language_code: Optional[str] = None):
        """
        Initialize DataForSEO client.
        
        Args:
            credential_service: Optional credential service for multi-tenant support
            api_key: DataForSEO API key (optional, can also use env vars)
            api_secret: DataForSEO API secret (optional, can also use env vars)
            location: Location for search data (e.g., "United States", "United Kingdom")
            language_code: Language code for search data (e.g., "en", "es")
        """
        self.base_url = "https://api.dataforseo.com/v3"
        self.credential_service = credential_service
        # Accept credentials directly or from env vars
        self.api_key = api_key or os.getenv("DATAFORSEO_API_KEY")
        self.api_secret = api_secret or os.getenv("DATAFORSEO_API_SECRET")
        self.location = location or os.getenv("DATAFORSEO_LOCATION", "United States")
        self.language_code = language_code or os.getenv("DATAFORSEO_LANGUAGE", "en")
        self.is_configured = bool(self.api_key and self.api_secret)
        self._cache = {}
        self._cache_ttl = 3600  # 1 hour cache
    
    async def initialize_credentials(self, tenant_id: str):
        # If already configured from constructor, skip re-initialization
        if self.is_configured and self.api_key and self.api_secret:
            logger.debug(f"DataforSEO credentials already configured, skipping initialization for tenant {tenant_id}")
            return
            
        if self.credential_service:
            credentials = await self.credential_service.get_credentials(tenant_id, "dataforseo")
            if credentials:
                self.api_key = credentials.get("api_key")
                self.api_secret = credentials.get("api_secret")
                self.is_configured = True
                logger.info(f"DataforSEO credentials loaded for tenant {tenant_id} from credential service.")
                return
        
        # Fallback to environment variables if credential service is not used or no credentials found
        # Prefer KEY/SECRET, fallback to LOGIN/PASSWORD for legacy environments
        if not self.api_key:
            self.api_key = os.getenv("DATAFORSEO_API_KEY") or os.getenv("DATAFORSEO_API_LOGIN")
        if not self.api_secret:
            self.api_secret = os.getenv("DATAFORSEO_API_SECRET") or os.getenv("DATAFORSEO_API_PASSWORD")
        if self.api_key and self.api_secret:
            self.is_configured = True
            logger.warning("DataforSEO credentials loaded from environment variables. Consider using credential service.")
        else:
            self.is_configured = False
            logger.error("DataforSEO API credentials not found.")

    @monitor_performance("dataforseo_get_keyword_overview")
    async def get_keyword_overview(self, keywords: List[str], location_name: str, language_code: str, tenant_id: str) -> Dict[str, Any]:
        """Keyword overview with rich metrics (intent, monthly searches, SERP features)."""
        try:
            cache_key = f"kw_overview_{hash(tuple(keywords))}"
            if cache_key in self._cache:
                data, ts = self._cache[cache_key]
                if datetime.now().timestamp() - ts < self._cache_ttl:
                    return data
            payload = [{
                "keywords": keywords,
                "location_name": location_name,
                "language_code": language_code
            }]
            data = await self._make_request("dataforseo_labs/google/keyword_overview/live", payload, tenant_id)
            self._cache[cache_key] = (data, datetime.now().timestamp())
            return data
        except Exception as e:
            logger.error(f"Error getting keyword overview: {e}")
            return {}

    @monitor_performance("dataforseo_get_related_keywords")
    async def get_related_keywords(self, keyword: str, location_name: str, language_code: str, tenant_id: str, depth: int = 2, limit: int = 100) -> Dict[str, Any]:
        """Related keywords (graph/depth-first)."""
        try:
            cache_key = f"related_{keyword}_{depth}_{limit}"
            if cache_key in self._cache:
                data, ts = self._cache[cache_key]
                if datetime.now().timestamp() - ts < self._cache_ttl:
                    return data
            payload = [{
                "keyword": keyword,
                "depth": depth,
                "location_name": location_name,
                "language_code": language_code,
                "limit": limit
            }]
            data = await self._make_request("dataforseo_labs/google/related_keywords/live", payload, tenant_id)
            self._cache[cache_key] = (data, datetime.now().timestamp())
            return data
        except Exception as e:
            logger.error(f"Error getting related keywords: {e}")
            return {}

    @monitor_performance("dataforseo_get_top_searches")
    async def get_top_searches(self, location_name: str, language_code: str, tenant_id: str, limit: int = 100) -> Dict[str, Any]:
        """Top searches discovery in the target market."""
        try:
            cache_key = f"top_searches_{location_name}_{language_code}_{limit}"
            if cache_key in self._cache:
                data, ts = self._cache[cache_key]
                if datetime.now().timestamp() - ts < self._cache_ttl:
                    return data
            payload = [{
                "location_name": location_name,
                "language_code": language_code,
                "limit": limit
            }]
            data = await self._make_request("dataforseo_labs/google/top_searches/live", payload, tenant_id)
            self._cache[cache_key] = (data, datetime.now().timestamp())
            return data
        except Exception as e:
            logger.error(f"Error getting top searches: {e}")
            return {}

    @monitor_performance("dataforseo_get_search_intent")
    async def get_search_intent(self, keywords: List[str], language_code: str, tenant_id: str) -> Dict[str, Any]:
        """Search intent probabilities per keyword."""
        try:
            cache_key = f"intent_{hash(tuple(keywords))}_{language_code}"
            if cache_key in self._cache:
                data, ts = self._cache[cache_key]
                if datetime.now().timestamp() - ts < self._cache_ttl:
                    return data
            payload = [{
                "keywords": keywords,
                "language_code": language_code
            }]
            data = await self._make_request("dataforseo_labs/search_intent/live", payload, tenant_id)
            self._cache[cache_key] = (data, datetime.now().timestamp())
            return data
        except Exception as e:
            logger.error(f"Error getting search intent: {e}")
            return {}
    
    async def _make_request(self, endpoint: str, payload: List[Dict[str, Any]], tenant_id: str) -> Dict[str, Any]:
        if not self.is_configured or not self.api_key or not self.api_secret:
            logger.error(f"DataforSEO API not configured. Returning fallback data for endpoint: {endpoint}")
            log_api_request("dataforseo", endpoint, 0, 0.0, message="API not configured", tenant_id=tenant_id)
            return self._fallback_data(endpoint, payload)

        url = f"{self.base_url}/{endpoint}"
        credentials = f"{self.api_key}:{self.api_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        }

        try:
            start_time = time.perf_counter()
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload, timeout=30.0)
                response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
            end_time = time.perf_counter()
            duration = end_time - start_time
            log_api_request("dataforseo", endpoint, response.status_code, duration, message="Success", tenant_id=tenant_id)
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"DataForSEO API request failed due to HTTP error for {endpoint}: {e.response.status_code} - {e.response.text}")
            log_api_request("dataforseo", endpoint, e.response.status_code, 0.0, message=f"HTTP Error: {e.response.status_code}", tenant_id=tenant_id)
            return self._fallback_data(endpoint, payload)
        except httpx.RequestError as e:
            logger.error(f"DataForSEO API request failed due to network error for {endpoint}: {e}")
            log_api_request("dataforseo", endpoint, 0, 0.0, message=f"Network Error: {e}", tenant_id=tenant_id)
            return self._fallback_data(endpoint, payload)
        except Exception as e:
            logger.error(f"An unexpected error occurred during DataforSEO API request for {endpoint}: {e}")
            log_api_request("dataforseo", endpoint, 0, 0.0, message=f"Unexpected Error: {e}", tenant_id=tenant_id)
            return self._fallback_data(endpoint, payload)

    @monitor_performance("dataforseo_get_search_volume")
    async def get_search_volume_data(self, keywords: List[str], location_name: str, language_code: str, tenant_id: str) -> Dict[str, Any]:
        """
        Get search volume data for keywords using DataForSEO API.
        
        Args:
            keywords: List of keywords to analyze
            
        Returns:
            Dictionary with search volume data for each keyword
        """
        try:
            # Check cache first
            cache_key = f"search_volume_{hash(tuple(keywords))}"
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if datetime.now().timestamp() - timestamp < self._cache_ttl:
                    return cached_data
            
            # Prepare API request
            payload = [{
                "keywords": keywords,
                "location_name": location_name,
                "language_code": language_code
            }]
            
            data = await self._make_request("keywords_data/google_ads/search_volume/live", payload, tenant_id)
            
            # Process response
            results = {}
            if data.get("tasks") and data["tasks"][0].get("result"):
                for item in data["tasks"][0]["result"]:
                    keyword = item.get("keyword", "")
                    results[keyword] = {
                        "search_volume": item.get("search_volume", 0),
                        "competition": item.get("competition", 0.0),
                        "cpc": item.get("cpc", 0.0),
                        "trend": item.get("trends", [{}])[0].get("value", 0.0) if item.get("trends") else 0.0,
                        "competition_level": item.get("competition_level", "medium"),
                        "monthly_searches": item.get("monthly_searches", [])
                    }
            
            # Cache the results
            self._cache[cache_key] = (results, datetime.now().timestamp())
            
            return results
            
        except Exception as e:
            print(f"Error getting search volume data: {e}")
            # Return fallback data
            return {
                keyword: {
                    "search_volume": self._estimate_search_volume(keyword),
                    "competition": self._estimate_competition(keyword),
                    "cpc": self._estimate_cpc(keyword),
                    "trend": 0.0,
                    "competition_level": "medium",
                    "monthly_searches": []
                }
                for keyword in keywords
            }
    
    @monitor_performance("dataforseo_get_keyword_difficulty")
    async def get_keyword_difficulty(self, keywords: List[str], location_name: str, language_code: str, tenant_id: str) -> Dict[str, float]:
        """
        Get keyword difficulty scores using DataForSEO API.
        
        Args:
            keywords: List of keywords to analyze
            
        Returns:
            Dictionary mapping keywords to difficulty scores (0-100)
        """
        try:
            # Check cache first
            cache_key = f"difficulty_{hash(tuple(keywords))}"
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if datetime.now().timestamp() - timestamp < self._cache_ttl:
                    return cached_data
            
            # Prepare API request
            payload = [{
                "keywords": keywords,
                "location_name": location_name,
                "language_code": language_code
            }]
            
            data = await self._make_request("dataforseo_labs/bulk_keyword_difficulty/live", payload, tenant_id)
            
            # Process response
            results = {}
            if data.get("tasks") and data["tasks"][0].get("result"):
                for item in data["tasks"][0]["result"]:
                    keyword = item.get("keyword", "")
                    difficulty_score = item.get("keyword_difficulty", 50.0)
                    results[keyword] = difficulty_score
            
            # Cache the results
            self._cache[cache_key] = (results, datetime.now().timestamp())
            
            return results
            
        except Exception as e:
            print(f"Error getting keyword difficulty: {e}")
            # Return fallback data
            return {
                keyword: self._estimate_difficulty_score(keyword)
                for keyword in keywords
            }
    
    @monitor_performance("dataforseo_get_keyword_suggestions")
    async def get_keyword_suggestions(self, seed_keyword: str, location_name: str, language_code: str, tenant_id: str, limit: int = 150) -> List[Dict[str, Any]]:
        """
        Get keyword suggestions using DataForSEO keyword ideas API.
        
        Args:
            seed_keyword: Base keyword to get suggestions for
            location_name: Location for keyword data
            language_code: Language code
            tenant_id: Tenant ID for credentials
            limit: Maximum number of suggestions to return (default: 150, max: 1000)
            
        Returns:
            List of keyword suggestions with metrics
        """
        try:
            # Ensure limit is within API constraints
            limit = min(limit, 1000)  # DataForSEO API max limit
            
            # Check cache first
            cache_key = f"suggestions_{seed_keyword}_{limit}"
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if datetime.now().timestamp() - timestamp < self._cache_ttl:
                    return cached_data
            
            # Prepare API request
            payload = [{
                "keyword": seed_keyword,
                "location_name": location_name,
                "language_code": language_code,
                "limit": limit,
                # Explicitly request all monetization and difficulty metrics
                "include_search_volume": True,
                "include_difficulty": True,
                "include_competition": True,
                "include_cpc": True,
            }]
            
            data = await self._make_request("dataforseo_labs/google/keyword_suggestions/live", payload, tenant_id)
            
            # Process response
            suggestions = []
            if data.get("tasks") and data["tasks"][0].get("result"):
                for item in data["tasks"][0]["result"]:
                    suggestion = {
                        "keyword": item.get("keyword", ""),
                        "search_volume": item.get("search_volume", 0),
                        "competition": item.get("competition", 0.0),
                        "cpc": item.get("cpc", 0.0),
                        "keyword_difficulty": item.get("keyword_difficulty", 50.0),
                        "keyword_info": item.get("keyword_info", {}),
                        "keyword_properties": item.get("keyword_properties", {}),
                        "impressions_info": item.get("impressions_info", {}),
                        "serp_info": item.get("serp_info", {})
                    }
                    suggestions.append(suggestion)
            
            # Cache the results
            self._cache[cache_key] = (suggestions, datetime.now().timestamp())
            
            return suggestions[:limit]  # Ensure we don't exceed limit
            
        except Exception as e:
            logger.warning(f"Error getting keyword suggestions from DataForSEO: {e}")
            # Return fallback suggestions
            return self._generate_fallback_suggestions(seed_keyword, limit)
    
    @monitor_performance("dataforseo_get_ai_search_volume")
    async def get_ai_search_volume(self, keywords: List[str], location_name: str, language_code: str, tenant_id: str) -> Dict[str, Any]:
        """
        Get AI optimization search volume data for keywords using DataForSEO API.
        
        This endpoint provides data on how keywords appear in AI LLM queries/responses,
        which is critical for AI-optimized content strategy.
        
        Args:
            keywords: List of keywords to analyze
            location_name: Location for keyword data (e.g., "United States")
            language_code: Language code (e.g., "en")
            tenant_id: Tenant ID for credentials
            
        Returns:
            Dictionary with AI search volume data for each keyword including:
            - ai_search_volume: Current month's estimated volume in AI queries
            - ai_monthly_searches: Historical trend over past 12 months
        """
        try:
            # Check cache first
            cache_key = f"ai_search_volume_{hash(tuple(keywords))}"
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if datetime.now().timestamp() - timestamp < self._cache_ttl:
                    return cached_data
            
            # Prepare API request for AI optimization endpoint
            payload = [{
                "keywords": keywords,
                "location_name": location_name,
                "language_code": language_code
            }]
            
            data = await self._make_request("keywords_data/ai_optimization/search_volume/live", payload, tenant_id)
            
            # Debug: Log response structure for troubleshooting
            if data.get("tasks") and data["tasks"][0].get("result"):
                sample_result = data["tasks"][0]["result"][0] if data["tasks"][0]["result"] else {}
                logger.debug(f"DataForSEO AI optimization response structure: {list(sample_result.keys())}")
            
            # Process response
            results = {}
            if data.get("tasks") and data["tasks"][0].get("result"):
                for item in data["tasks"][0]["result"]:
                    keyword = item.get("keyword", "")
                    
                    # Extract AI search volume metrics - check multiple possible response structures
                    ai_search_volume = 0
                    ai_monthly_searches = []
                    
                    # Try different response formats
                    if "ai_search_volume" in item:
                        ai_data = item.get("ai_search_volume", {})
                        if isinstance(ai_data, dict):
                            ai_search_volume = ai_data.get("search_volume", 0) or 0
                        elif isinstance(ai_data, (int, float)):
                            ai_search_volume = int(ai_data)
                    
                    # Also check for direct search_volume field (some APIs return it directly)
                    if ai_search_volume == 0 and "search_volume" in item:
                        ai_search_volume = item.get("search_volume", 0) or 0
                    
                    # Get monthly searches
                    ai_monthly_searches = item.get("ai_monthly_searches", [])
                    if not ai_monthly_searches and "monthly_searches" in item:
                        ai_monthly_searches = item.get("monthly_searches", [])
                    
                    # Ensure numeric types
                    try:
                        ai_search_volume = int(float(ai_search_volume)) if ai_search_volume else 0
                    except (ValueError, TypeError):
                        ai_search_volume = 0
                    
                    results[keyword] = {
                        "ai_search_volume": ai_search_volume,
                        "ai_monthly_searches": ai_monthly_searches,
                        "ai_trend": self._calculate_ai_trend(ai_monthly_searches) if ai_monthly_searches else 0.0
                    }
            
            # Cache the results
            self._cache[cache_key] = (results, datetime.now().timestamp())
            
            return results
            
        except Exception as e:
            logger.warning(f"Error getting AI search volume data from DataForSEO: {e}")
            # Return fallback data with zeros
            return {
                keyword: {
                    "ai_search_volume": 0,
                    "ai_monthly_searches": [],
                    "ai_trend": 0.0
                }
                for keyword in keywords
            }
    
    def _calculate_ai_trend(self, monthly_searches: List[Dict[str, Any]]) -> float:
        """
        Calculate AI search trend from monthly searches data.
        
        Returns a trend score (-1.0 to 1.0) indicating if AI volume is increasing or decreasing.
        """
        if not monthly_searches or len(monthly_searches) < 2:
            return 0.0
        
        try:
            # Get first and last month's values
            first_month = monthly_searches[0].get("search_volume", 0) or 0
            last_month = monthly_searches[-1].get("search_volume", 0) or 0
            
            if first_month == 0:
                return 1.0 if last_month > 0 else 0.0
            
            # Calculate percentage change
            trend = (last_month - first_month) / first_month
            # Normalize to -1.0 to 1.0 range
            return max(-1.0, min(1.0, trend))
        except Exception:
            return 0.0
    
    @monitor_performance("dataforseo_get_serp_analysis")
    async def get_serp_analysis(self, keyword: str, location_name: str, language_code: str, tenant_id: str, depth: int = 10) -> Dict[str, Any]:
        """
        Get SERP analysis for a keyword using DataForSEO.
        
        Args:
            keyword: Keyword to analyze
            depth: Number of SERP results to analyze
            
        Returns:
            SERP analysis data
        """
        try:
            # This would use the MCP DataForSEO tool:
            # result = await mcp_dataforseo_serp_organic_live_advanced(
            #     keyword=keyword,
            #     language_code=self.language_code,
            #     location_name=self.location,
            #     depth=depth
            # )
            
            payload = [{
                "keyword": keyword,
                "location_name": location_name,
                "language_code": language_code,
                "depth": depth
            }]
            data = await self._make_request("serp/google/organic/live/advanced", payload, tenant_id)

            return {
                "keyword": keyword,
                "serp_results": [],
                "competition_level": "medium",
                "top_domains": [],
                "content_gaps": []
            }
            
        except Exception as e:
            print(f"Error getting SERP analysis: {e}")
            return {}
    
    @monitor_performance("dataforseo_get_competitor_keywords")
    async def get_competitor_keywords(self, domain: str, location_name: str, language_code: str, tenant_id: str) -> List[Dict[str, Any]]:
        """
        Get keywords that a competitor domain ranks for.
        
        Args:
            domain: Competitor domain to analyze
            limit: Maximum keywords to return
            
        Returns:
            List of competitor keywords with metrics
        """
        try:
            # This would use the MCP DataForSEO tool:
            # result = await mcp_dataforseo_dataforseo_labs_google_ranked_keywords(
            #     target=domain,
            #     language_code=self.language_code,
            #     location_name=self.location,
            #     limit=limit
            # )
            
            payload = [{
                "target": domain,
                "location_name": location_name,
                "language_code": language_code
            }]
            data = await self._make_request("dataforseo_labs/google/competitors_domain/live", payload, tenant_id)

            return []
            
        except Exception as e:
            print(f"Error getting competitor keywords: {e}")
            return []
    
    @monitor_performance("dataforseo_get_keyword_trends")
    async def get_keyword_trends(self, keywords: List[str], location_name: str, language_code: str, tenant_id: str) -> Dict[str, Any]:
        """
        Get keyword trend data using DataForSEO.
        
        Args:
            keywords: Keywords to analyze trends for
            time_range: Time range for trends (e.g., "past_12_months", "past_30_days")
            
        Returns:
            Trend data for keywords
        """
        try:
            # This would use the MCP DataForSEO tool:
            # result = await mcp_dataforseo_keywords_data_google_trends_explore(
            #     keywords=keywords,
            #     time_range=time_range,
            #     location_name=self.location
            # )
            
            payload = [{
                "keywords": keywords,
                "location_name": location_name,
                "language_code": language_code
            }]
            data = await self._make_request("dataforseo_labs/google/historical_serp/live", payload, tenant_id)

            return {
                "keywords": keywords,
                "time_range": "past_12_months", # Placeholder, actual time_range would be passed
                "trends": {keyword: {"trend_score": 0.0} for keyword in keywords}
            }
            
        except Exception as e:
            print(f"Error getting keyword trends: {e}")
            return {}
    
    @monitor_performance("dataforseo_analyze_content_gaps")
    async def analyze_content_gaps(self, primary_keyword: str, competitor_domains: List[str], location_name: str, language_code: str, tenant_id: str) -> Dict[str, Any]:
        """
        Analyze content gaps compared to competitors.
        
        Args:
            primary_keyword: Main keyword to analyze
            competitor_domains: List of competitor domains
            
        Returns:
            Content gap analysis
        """
        try:
            gaps = {
                "missing_keywords": [],
                "weak_content_areas": [],
                "opportunities": [],
                "competitor_strengths": {}
            }
            
            # Analyze each competitor
            for domain in competitor_domains:
                competitor_keywords = await self.get_competitor_keywords(domain, location_name, language_code, tenant_id)
                # Process competitor data to identify gaps
                # This would involve more complex analysis
            
            return gaps
            
        except Exception as e:
            print(f"Error analyzing content gaps: {e}")
            return {}
    
    def _estimate_search_volume(self, keyword: str) -> int:
        """
        Estimate search volume based on keyword characteristics.
        This is a fallback when real data isn't available.
        """
        word_count = len(keyword.split())
        keyword_length = len(keyword)
        
        # Heuristic estimation
        if word_count == 1 and keyword_length <= 5:
            return 10000  # Short, generic terms
        elif word_count == 1:
            return 5000   # Longer single words
        elif word_count == 2:
            return 2000   # Two-word phrases
        elif word_count == 3:
            return 800    # Three-word phrases
        else:
            return 200    # Long-tail keywords
    
    def _estimate_competition(self, keyword: str) -> float:
        """
        Estimate competition level based on keyword characteristics.
        """
        word_count = len(keyword.split())
        
        if word_count == 1:
            return 0.8    # High competition for single words
        elif word_count == 2:
            return 0.6    # Medium-high competition
        elif word_count == 3:
            return 0.4    # Medium competition
        else:
            return 0.2    # Low competition for long-tail
    
    def _estimate_cpc(self, keyword: str) -> float:
        """
        Estimate cost-per-click based on keyword characteristics.
        """
        # Commercial intent keywords
        commercial_terms = ['buy', 'price', 'cost', 'review', 'best', 'top', 'compare']
        
        if any(term in keyword.lower() for term in commercial_terms):
            return 2.50   # Higher CPC for commercial intent
        else:
            return 0.75   # Lower CPC for informational keywords
    
    def _estimate_difficulty_score(self, keyword: str) -> float:
        """
        Estimate keyword difficulty score (0-100).
        """
        word_count = len(keyword.split())
        competition = self._estimate_competition(keyword)
        
        # Base difficulty on word count and competition
        base_score = (5 - word_count) * 15  # Fewer words = higher difficulty
        competition_score = competition * 50
        
        difficulty = max(0, min(100, base_score + competition_score))
        return difficulty
    
    def _generate_fallback_suggestions(self, seed_keyword: str, limit: int) -> List[Dict[str, Any]]:
        """Generate fallback keyword suggestions when API fails."""
        modifiers = [
            "best", "top", "how to", "guide", "tips", "benefits", "reviews",
            "comparison", "vs", "alternatives", "free", "paid", "online",
            "2024", "2025", "latest", "new", "popular", "trending"
        ]
        
        suggestions = []
        for i, modifier in enumerate(modifiers[:limit]):
            keyword = f"{modifier} {seed_keyword}" if i % 2 == 0 else f"{seed_keyword} {modifier}"
            suggestions.append({
                "keyword": keyword,
                "search_volume": self._estimate_search_volume(keyword),
                "competition": self._estimate_competition(keyword),
                "cpc": self._estimate_cpc(keyword),
                "keyword_difficulty": self._estimate_difficulty_score(keyword),
                "keyword_info": {},
                "keyword_properties": {},
                "impressions_info": {},
                "serp_info": {}
            })
        
        return suggestions

    def _fallback_data(self, endpoint: str, payload: List[Dict[str, Any]]) -> Dict[str, Any]:
        # In a real application, you might have more sophisticated fallback logic
        # or return a specific error structure.
        logger.warning(f"Returning fallback data for {endpoint} with payload {payload}")
        return {"status": "error", "message": "API not configured or request failed. Returning fallback data.", "data": []}


class EnhancedKeywordAnalyzer:
    """
    Enhanced keyword analyzer that combines content analysis with DataForSEO data.
    """
    
    def __init__(self, use_dataforseo: bool = True, credential_service: Any = None):
        """
        Initialize enhanced keyword analyzer.
        
        Args:
            use_dataforseo: Whether to use DataForSEO for enhanced metrics
            credential_service: The DataForSEOCredentialService instance
        """
        self.use_dataforseo = use_dataforseo
        if use_dataforseo and credential_service:
            self.dataforseo_client = DataForSEOClient(credential_service=credential_service)
        else:
            self.dataforseo_client = None
    
    async def analyze_keywords_comprehensive(self, keywords: List[str], tenant_id: str) -> Dict[str, KeywordAnalysis]:
        """
        Perform comprehensive keyword analysis with real SEO data.
        
        Args:
            keywords: List of keywords to analyze
            tenant_id: The ID of the tenant making the request
            
        Returns:
            Dictionary mapping keywords to their comprehensive analysis
        """
        results = {}
        
        if self.use_dataforseo and self.dataforseo_client:
            try:
                await self.dataforseo_client.initialize_credentials(tenant_id)
                # Get real SEO data
                search_data = await self.dataforseo_client.get_search_volume_data(keywords, "United States", "en", tenant_id)
                difficulty_data = await self.dataforseo_client.get_keyword_difficulty(keywords, "United States", "en", tenant_id)
                
                for keyword in keywords:
                    seo_data = search_data.get(keyword, {})
                    difficulty_score = difficulty_data.get(keyword, 50.0)
                    
                    # Ensure search_volume and cpc are always numeric (never None)
                    search_volume = seo_data.get("search_volume", 0) or 0
                    cpc_value = seo_data.get("cpc", 0.0) or 0.0
                    competition_value = seo_data.get("competition", 0.5) or 0.5
                    trend_value = seo_data.get("trend", 0.0) or 0.0
                    
                    # Create comprehensive analysis
                    analysis = KeywordAnalysis(
                        keyword=keyword,
                        search_volume=search_volume,  # Always numeric
                        difficulty=self._score_to_difficulty(difficulty_score),
                        competition=competition_value,
                        related_keywords=self._generate_related_keywords(keyword),
                        long_tail_keywords=self._generate_long_tail_keywords(keyword),
                        cpc=cpc_value,  # Always numeric
                        trend_score=trend_value,
                        recommended=self._evaluate_recommendation(keyword, seo_data, difficulty_score),
                        reason=self._get_recommendation_reason(keyword, seo_data, difficulty_score),
                    )
                    
                    results[keyword] = analysis
                
                return results
                
            except Exception as e:
                print(f"Error in comprehensive analysis: {e}")
        
        # Fallback to basic analysis
        for keyword in keywords:
            results[keyword] = self._basic_keyword_analysis(keyword)
        
        return results
    
    async def get_content_strategy(self, primary_keywords: List[str], competitor_domains: List[str] = None, tenant_id: str = "default_tenant") -> Dict[str, Any]:
        """
        Generate a comprehensive content strategy based on keyword analysis.
        
        Args:
            primary_keywords: Main keywords to target
            competitor_domains: Optional competitor domains to analyze
            tenant_id: The ID of the tenant making the request
            
        Returns:
            Content strategy recommendations
        """
        strategy = {
            "primary_keywords": [],
            "supporting_keywords": [],
            "content_clusters": [],
            "competitor_gaps": [],
            "recommended_content": []
        }
        
        if self.use_dataforseo and self.dataforseo_client:
            await self.dataforseo_client.initialize_credentials(tenant_id)
            # Analyze primary keywords
            keyword_analyses = await self.analyze_keywords_comprehensive(primary_keywords, tenant_id)
            
            # Categorize keywords by difficulty and opportunity
            for keyword, analysis in keyword_analyses.items():
                if analysis.recommended:
                    if analysis.difficulty in [SEODifficulty.VERY_EASY, SEODifficulty.EASY]:
                        strategy["primary_keywords"].append({
                            "keyword": keyword,
                            "priority": "high",
                            "reason": "Low competition opportunity"
                        })
                    else:
                        strategy["supporting_keywords"].append({
                            "keyword": keyword,
                            "priority": "medium",
                            "reason": analysis.reason
                        })
            
            # Analyze competitor gaps if domains provided
            if competitor_domains:
                for domain in competitor_domains:
                    gaps = await self.dataforseo_client.analyze_content_gaps(
                        primary_keywords[0], [domain], "United States", "en", tenant_id
                    )
                    strategy["competitor_gaps"].extend(gaps.get("opportunities", []))
        
        return strategy
    
    def _score_to_difficulty(self, score: float) -> SEODifficulty:
        """Convert numeric difficulty score to SEODifficulty enum."""
        if score <= 20:
            return SEODifficulty.VERY_EASY
        elif score <= 40:
            return SEODifficulty.EASY
        elif score <= 60:
            return SEODifficulty.MEDIUM
        elif score <= 80:
            return SEODifficulty.HARD
        else:
            return SEODifficulty.VERY_HARD
    
    def _evaluate_recommendation(self, keyword: str, seo_data: Dict[str, Any], difficulty: float) -> bool:
        """Evaluate whether a keyword is recommended based on comprehensive data."""
        search_volume = seo_data.get("search_volume", 0)
        competition = seo_data.get("competition", 0.5)
        cpc = seo_data.get("cpc", 0.0)
        
        # High-value opportunities
        if search_volume >= 1000 and difficulty <= 40:
            return True
        
        # Long-tail opportunities
        if len(keyword.split()) >= 3 and search_volume >= 100:
            return True
        
        # Commercial opportunities
        if cpc >= 1.0 and difficulty <= 60:
            return True
        
        # Low competition
        if competition <= 0.3:
            return True
        
        # Avoid very competitive or low-volume keywords
        if difficulty >= 80 or (search_volume and search_volume < 50):
            return False
        
        return True
    
    def _get_recommendation_reason(self, keyword: str, seo_data: Dict[str, Any], difficulty: float) -> str:
        """Get explanation for keyword recommendation."""
        search_volume = seo_data.get("search_volume", 0)
        competition = seo_data.get("competition", 0.5)
        cpc = seo_data.get("cpc", 0.0)
        
        if search_volume >= 1000 and difficulty <= 40:
            return f"High search volume ({search_volume:,}) with manageable difficulty"
        elif len(keyword.split()) >= 3 and search_volume >= 100:
            return f"Long-tail keyword with decent volume ({search_volume:,})"
        elif cpc >= 1.0 and difficulty <= 60:
            return f"High commercial value (${cpc:.2f} CPC)"
        elif competition <= 0.3:
            return "Low competition opportunity"
        elif difficulty >= 80:
            return "Very competitive - consider alternatives"
        elif search_volume and search_volume < 50:
            return "Low search volume - limited traffic potential"
        else:
            return "Suitable for content strategy"
    
    def _generate_related_keywords(self, keyword: str) -> List[str]:
        """Generate related keywords (basic implementation)."""
        modifiers = ["best", "top", "how to", "guide", "tips", "benefits"]
        return [f"{modifier} {keyword}" for modifier in modifiers[:3]]
    
    def _generate_long_tail_keywords(self, keyword: str) -> List[str]:
        """Generate long-tail keyword variations."""
        variations = [
            f"how to {keyword}",
            f"{keyword} for beginners",
            f"{keyword} guide",
            f"best {keyword} practices",
            f"{keyword} tips and tricks"
        ]
        return variations[:3]
    
    def _basic_keyword_analysis(self, keyword: str) -> KeywordAnalysis:
        """Basic keyword analysis without external APIs."""
        word_count = len(keyword.split())
        
        if word_count >= 3:
            difficulty = SEODifficulty.EASY
            recommended = True
            reason = "Long-tail keyword with good potential"
        elif word_count == 2:
            difficulty = SEODifficulty.MEDIUM
            recommended = True
            reason = "Moderate difficulty, good for content strategy"
        else:
            difficulty = SEODifficulty.HARD
            recommended = False
            reason = "Single word - very competitive"
        
        return KeywordAnalysis(
            keyword=keyword,
            search_volume=None,
            difficulty=difficulty,
            competition=0.5,
            related_keywords=self._generate_related_keywords(keyword),
            long_tail_keywords=self._generate_long_tail_keywords(keyword),
            cpc=None,
            trend_score=0.0,
            recommended=recommended,
            reason=reason,
        )
