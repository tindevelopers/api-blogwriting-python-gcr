"""
Google Custom Search API Integration

Provides real-time content research, fact-checking, and source discovery
using Google Custom Search API.
"""

import os
import asyncio
import aiohttp
from typing import List, Dict, Optional, Any
from urllib.parse import quote_plus
import logging

logger = logging.getLogger(__name__)


class GoogleCustomSearchClient:
    """Client for Google Custom Search API."""
    
    def __init__(self, api_key: Optional[str] = None, search_engine_id: Optional[str] = None):
        """
        Initialize Google Custom Search client.
        
        Args:
            api_key: Google Custom Search API key (or from GOOGLE_CUSTOM_SEARCH_API_KEY env)
            search_engine_id: Custom Search Engine ID (or from GOOGLE_CUSTOM_SEARCH_ENGINE_ID env)
        """
        self.api_key = api_key or os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY")
        self.search_engine_id = search_engine_id or os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self.session: Optional[aiohttp.ClientSession] = None
        
        if not self.api_key or not self.search_engine_id:
            logger.warning("Google Custom Search API credentials not configured")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def search(
        self,
        query: str,
        num_results: int = 10,
        language: str = "en",
        country: str = "us",
        date_restrict: Optional[str] = None,
        safe: str = "active"
    ) -> List[Dict[str, Any]]:
        """
        Perform a Google Custom Search.
        
        Args:
            query: Search query
            num_results: Number of results to return (max 10 per request)
            language: Language code (e.g., 'en')
            country: Country code (e.g., 'us')
            date_restrict: Date restriction (e.g., 'd7' for past week, 'm1' for past month)
            safe: Safe search level ('active', 'off')
        
        Returns:
            List of search results with title, link, snippet, etc.
        """
        if not self.api_key or not self.search_engine_id:
            logger.warning("Google Custom Search not configured, returning empty results")
            return []
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        results = []
        start_index = 1
        
        # Handle pagination if more than 10 results needed
        while len(results) < num_results:
            remaining = num_results - len(results)
            current_num = min(10, remaining)  # Max 10 per request
            
            params = {
                "key": self.api_key,
                "cx": self.search_engine_id,
                "q": query,
                "num": current_num,
                "start": start_index,
                "lr": f"lang_{language}",
                "cr": f"country{country}",
                "safe": safe
            }
            
            if date_restrict:
                params["dateRestrict"] = date_restrict
            
            try:
                async with self.session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get("items", [])
                        
                        for item in items:
                            results.append({
                                "title": item.get("title", ""),
                                "link": item.get("link", ""),
                                "snippet": item.get("snippet", ""),
                                "display_link": item.get("displayLink", ""),
                                "formatted_url": item.get("formattedUrl", "")
                            })
                        
                        # Check if there are more results
                        if len(items) < current_num or len(results) >= num_results:
                            break
                        
                        start_index += current_num
                    else:
                        error_text = await response.text()
                        logger.error(f"Google Custom Search API error: {response.status} - {error_text}")
                        break
                        
            except Exception as e:
                logger.error(f"Error performing Google Custom Search: {e}")
                break
        
        return results[:num_results]
    
    async def search_for_sources(
        self,
        topic: str,
        keywords: List[str],
        num_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for authoritative sources on a topic.
        
        Args:
            topic: Main topic
            keywords: Related keywords
            num_results: Number of sources to find
        
        Returns:
            List of authoritative sources
        """
        query = f"{topic} {' '.join(keywords[:3])}"
        results = await self.search(query, num_results=num_results)
        
        # Filter for authoritative domains (can be customized)
        authoritative_domains = [
            "edu", "gov", "org", "wikipedia.org", "medium.com",
            "forbes.com", "techcrunch.com", "wired.com"
        ]
        
        filtered_results = []
        for result in results:
            domain = result.get("display_link", "").lower()
            if any(auth_domain in domain for auth_domain in authoritative_domains):
                filtered_results.append(result)
        
        return filtered_results[:num_results] if filtered_results else results[:num_results]
    
    async def fact_check(
        self,
        claim: str,
        num_sources: int = 3
    ) -> Dict[str, Any]:
        """
        Fact-check a claim by searching for verification.
        
        Args:
            claim: The claim to verify
            num_sources: Number of sources to check
        
        Returns:
            Dictionary with verification results
        """
        query = f'"{claim}"'
        results = await self.search(query, num_results=num_sources)
        
        verification = {
            "claim": claim,
            "sources_found": len(results),
            "sources": results,
            "verified": len(results) > 0,
            "confidence": "high" if len(results) >= 2 else "medium" if len(results) == 1 else "low"
        }
        
        return verification
    
    async def get_recent_information(
        self,
        topic: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get recent information on a topic.
        
        Args:
            topic: Topic to search
            days: Number of days to look back
        
        Returns:
            List of recent articles/information
        """
        date_restrict = f"d{days}" if days <= 30 else "m1"
        results = await self.search(
            topic,
            num_results=10,
            date_restrict=date_restrict
        )
        
        return results
    
    async def analyze_competitors(
        self,
        keyword: str,
        num_results: int = 10
    ) -> Dict[str, Any]:
        """
        Analyze top-ranking content for a keyword.
        
        Args:
            keyword: Target keyword
            num_results: Number of results to analyze
        
        Returns:
            Analysis of competitor content
        """
        results = await self.search(keyword, num_results=num_results)
        
        analysis = {
            "keyword": keyword,
            "total_results": len(results),
            "top_domains": {},
            "common_themes": [],
            "content_length_estimate": [],
            "serp_features": []
        }
        
        # Analyze domains
        for result in results:
            domain = result.get("display_link", "")
            analysis["top_domains"][domain] = analysis["top_domains"].get(domain, 0) + 1
        
        # Extract snippets for theme analysis
        snippets = [r.get("snippet", "") for r in results]
        analysis["common_themes"] = snippets[:5]  # Top 5 snippets
        
        return analysis
    
    async def search_product_brands(
        self,
        product_query: str,
        num_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for specific product brands and models.
        
        Args:
            product_query: Product search query (e.g., "best blow dryers for dogs")
            num_results: Number of results to return
        
        Returns:
            List of brand/product recommendations with details
        """
        # Search for product reviews and comparisons
        query = f"{product_query} brands models review comparison"
        results = await self.search(query, num_results=num_results)
        
        # Extract brand names from results
        brands = []
        seen_brands = set()
        
        for result in results:
            title = result.get("title", "").lower()
            snippet = result.get("snippet", "").lower()
            combined_text = f"{title} {snippet}"
            
            # Common brand indicators
            brand_patterns = [
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:blow\s+dryer|dryer|hair\s+dryer)',
                r'(?:best|top|review|compare)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:professional|commercial|industrial)',
            ]
            
            import re
            for pattern in brand_patterns:
                matches = re.findall(pattern, combined_text, re.IGNORECASE)
                for match in matches:
                    brand_name = match.strip() if isinstance(match, str) else match[0].strip() if match else ""
                    if brand_name and len(brand_name) > 2 and brand_name not in seen_brands:
                        seen_brands.add(brand_name)
                        brands.append({
                            "brand": brand_name,
                            "source_title": result.get("title", ""),
                            "source_url": result.get("link", ""),
                            "snippet": result.get("snippet", ""),
                            "relevance_score": 1.0
                        })
        
        # Also search Knowledge Graph for product entities if available
        # This would require Knowledge Graph client integration
        
        return brands[:num_results]

