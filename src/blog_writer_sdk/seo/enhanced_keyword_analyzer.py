"""
Enhanced keyword analysis with DataForSEO integration.

This module provides comprehensive keyword analysis using both
content-based methods and external SEO data from DataForSEO.
"""

import asyncio
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .keyword_analyzer import KeywordAnalyzer
from ..models.blog_models import KeywordAnalysis, SEODifficulty
from ..integrations.dataforseo_integration import DataForSEOClient


class EnhancedKeywordAnalyzer(KeywordAnalyzer):
    """
    Enhanced keyword analyzer with DataForSEO integration.
    
    Combines content-based analysis with real SEO metrics from
    DataForSEO API for comprehensive keyword research.
    """
    
    def __init__(
        self,
        use_dataforseo: bool = True,
        location: str = "United States",
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        language_code: str = "en",
    ):
        """
        Initialize enhanced keyword analyzer.
        
        Args:
            use_dataforseo: Whether to use DataForSEO API for enhanced metrics
            location: Location for search volume data
        """
        super().__init__()
        self.use_dataforseo = use_dataforseo
        self.location = location
        self.language_code = language_code or "en"
        
        # Cache for API results to avoid repeated calls
        self._keyword_cache = {}
        self._cache_ttl = 3600  # 1 hour cache

        # Initialize direct DataForSEO client if credentials available
        api_key = api_key or os.getenv("DATAFORSEO_API_KEY")
        api_secret = api_secret or os.getenv("DATAFORSEO_API_SECRET")
        self._df_client: Optional[DataForSEOClient] = None
        if self.use_dataforseo and api_key and api_secret:
            try:
                self._df_client = DataForSEOClient(
                    api_key=api_key,
                    api_secret=api_secret,
                    location=self.location,
                    language_code=self.language_code,
                )
            except Exception as e:
                print(f"Warning: Failed to initialize DataForSEO client: {e}")
                self._df_client = None
    
    async def analyze_keyword_enhanced(self, keyword: str) -> KeywordAnalysis:
        """
        Perform enhanced keyword analysis with external data.
        
        Args:
            keyword: Keyword to analyze
            
        Returns:
            Enhanced KeywordAnalysis with real SEO metrics
        """
        # Start with basic analysis
        basic_analysis = await super().analyze_keyword(keyword)
        
        if not self.use_dataforseo:
            return basic_analysis
        
        # Check cache first
        cache_key = f"{keyword}_{self.location}_{self.language_code}"
        if cache_key in self._keyword_cache:
            cached_data = self._keyword_cache[cache_key]
            if datetime.now() - cached_data['timestamp'] < timedelta(seconds=self._cache_ttl):
                return self._merge_analyses(basic_analysis, cached_data['data'])
        
        try:
            # Get enhanced metrics from DataForSEO (direct API if available)
            enhanced_data = await self._get_dataforseo_metrics(keyword)
            
            # Cache the results
            self._keyword_cache[cache_key] = {
                'data': enhanced_data,
                'timestamp': datetime.now()
            }
            
            # Merge basic and enhanced analysis
            return self._merge_analyses(basic_analysis, enhanced_data)
            
        except Exception as e:
            print(f"Warning: DataForSEO analysis failed for '{keyword}': {e}")
            # Return basic analysis if external API fails
            return basic_analysis
    
    async def analyze_keywords_batch(self, keywords: List[str]) -> Dict[str, KeywordAnalysis]:
        """
        Analyze multiple keywords efficiently using batch operations.
        
        Args:
            keywords: List of keywords to analyze
            
        Returns:
            Dictionary mapping keywords to their analysis
        """
        results = {}
        
        if self.use_dataforseo and len(keywords) > 1:
            try:
                # Use DataForSEO batch operations for efficiency
                batch_data = await self._get_dataforseo_batch_metrics(keywords)
                
                for keyword in keywords:
                    basic_analysis = await super().analyze_keyword(keyword)
                    enhanced_data = batch_data.get(keyword, {})
                    results[keyword] = self._merge_analyses(basic_analysis, enhanced_data)
                
                return results
                
            except Exception as e:
                print(f"Warning: Batch analysis failed, falling back to individual analysis: {e}")
        
        # Fallback to individual analysis
        for keyword in keywords:
            results[keyword] = await self.analyze_keyword_enhanced(keyword)
        
        return results
    
    async def get_keyword_trends(self, keywords: List[str], days: int = 90) -> Dict[str, Any]:
        """
        Get keyword trend data from DataForSEO.
        
        Args:
            keywords: Keywords to analyze trends for
            days: Number of days to look back
            
        Returns:
            Trend data for keywords
        """
        if not self.use_dataforseo:
            return {}
        
        try:
            # Use DataForSEO trends API
            from datetime import date
            date_to = date.today().strftime("%Y-%m-%d")
            date_from = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            # This would use the MCP DataForSEO tools
            # For now, return placeholder structure
            return {
                "keywords": keywords,
                "date_range": {"from": date_from, "to": date_to},
                "trends": {keyword: {"trend_score": 0.0} for keyword in keywords}
            }
            
        except Exception as e:
            print(f"Warning: Trend analysis failed: {e}")
            return {}
    
    async def get_competitor_keywords(self, domain: str, limit: int = 50) -> List[str]:
        """
        Get keywords that competitors are ranking for.
        
        Args:
            domain: Competitor domain to analyze
            limit: Maximum keywords to return
            
        Returns:
            List of competitor keywords
        """
        if not self.use_dataforseo:
            return []
        
        try:
            # This would use DataForSEO ranked keywords API
            # Placeholder implementation
            return []
            
        except Exception as e:
            print(f"Warning: Competitor analysis failed: {e}")
            return []
    
    async def _get_dataforseo_metrics(self, keyword: str) -> Dict[str, Any]:
        """Get comprehensive keyword metrics from DataForSEO (direct API if available)."""
        if not (self.use_dataforseo and self._df_client):
            return {
                "search_volume": None,
                "cpc": None,
                "competition": 0.0,
                "trend_score": 0.0,
                "difficulty_score": None,
            }

        sv_data = await self._df_client.get_search_volume_data([keyword])
        diff_data = await self._df_client.get_keyword_difficulty([keyword])
        m = sv_data.get(keyword, {})
        return {
            "search_volume": m.get("search_volume"),
            "cpc": m.get("cpc"),
            "competition": m.get("competition", 0.0),
            "trend_score": m.get("trend", 0.0),
            "difficulty_score": diff_data.get(keyword),
        }
    
    async def _get_dataforseo_batch_metrics(self, keywords: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get metrics for multiple keywords in batch from DataForSEO (direct API)."""
        if not (self.use_dataforseo and self._df_client):
            return {kw: await self._get_dataforseo_metrics(kw) for kw in keywords}

        sv_data = await self._df_client.get_search_volume_data(keywords)
        diff_data = await self._df_client.get_keyword_difficulty(keywords)
        combined: Dict[str, Dict[str, Any]] = {}
        for kw in keywords:
            m = sv_data.get(kw, {})
            combined[kw] = {
                "search_volume": m.get("search_volume"),
                "cpc": m.get("cpc"),
                "competition": m.get("competition", 0.0),
                "trend_score": m.get("trend", 0.0),
                "difficulty_score": diff_data.get(kw),
            }
        return combined

    async def suggest_keyword_variations(self, keyword: str) -> List[str]:
        """Suggest keyword variations using DataForSEO if available, else fallback."""
        if self.use_dataforseo and self._df_client:
            try:
                suggestions = await self._df_client.get_keyword_suggestions(keyword, limit=20)
                return [s.get("keyword", "").strip() for s in suggestions if s.get("keyword")]
            except Exception as e:
                print(f"Warning: DataForSEO suggestions failed: {e}")
        return await super().suggest_keyword_variations(keyword)
    
    def _merge_analyses(self, basic: KeywordAnalysis, enhanced: Dict[str, Any]) -> KeywordAnalysis:
        """
        Merge basic content analysis with enhanced DataForSEO metrics.
        
        Args:
            basic: Basic keyword analysis
            enhanced: Enhanced metrics from DataForSEO
            
        Returns:
            Combined KeywordAnalysis with enhanced data
        """
        # Update with real data if available
        search_volume = enhanced.get("search_volume")
        cpc = enhanced.get("cpc")
        competition = enhanced.get("competition", basic.competition)
        trend_score = enhanced.get("trend_score", basic.trend_score)
        
        # Recalculate difficulty based on real metrics
        difficulty = self._calculate_enhanced_difficulty(
            basic.keyword,
            search_volume,
            competition,
            enhanced.get("difficulty_score")
        )
        
        # Update recommendation based on enhanced data
        recommended, reason = self._evaluate_enhanced_recommendation(
            basic.keyword,
            difficulty,
            search_volume,
            competition,
            cpc
        )
        
        return KeywordAnalysis(
            keyword=basic.keyword,
            search_volume=search_volume,
            difficulty=difficulty,
            competition=competition,
            related_keywords=basic.related_keywords,
            long_tail_keywords=basic.long_tail_keywords,
            cpc=cpc,
            trend_score=trend_score,
            recommended=recommended,
            reason=reason,
        )
    
    def _calculate_enhanced_difficulty(
        self,
        keyword: str,
        search_volume: Optional[int],
        competition: float,
        difficulty_score: Optional[float]
    ) -> SEODifficulty:
        """
        Calculate keyword difficulty using enhanced metrics.
        """
        if difficulty_score is not None:
            # Use DataForSEO difficulty score if available
            if difficulty_score <= 20:
                return SEODifficulty.VERY_EASY
            elif difficulty_score <= 40:
                return SEODifficulty.EASY
            elif difficulty_score <= 60:
                return SEODifficulty.MEDIUM
            elif difficulty_score <= 80:
                return SEODifficulty.HARD
            else:
                return SEODifficulty.VERY_HARD
        
        # Fallback to enhanced heuristic calculation
        word_count = len(keyword.split())
        
        # Factor in search volume and competition
        volume_factor = 0
        if search_volume:
            if search_volume > 10000:
                volume_factor = 2  # High volume = harder
            elif search_volume > 1000:
                volume_factor = 1
            else:
                volume_factor = -1  # Low volume = easier
        
        competition_factor = int(competition * 2)  # 0-2 scale
        
        total_score = word_count + volume_factor + competition_factor
        
        if total_score <= 2:
            return SEODifficulty.VERY_EASY
        elif total_score <= 4:
            return SEODifficulty.EASY
        elif total_score <= 6:
            return SEODifficulty.MEDIUM
        elif total_score <= 8:
            return SEODifficulty.HARD
        else:
            return SEODifficulty.VERY_HARD
    
    def _evaluate_enhanced_recommendation(
        self,
        keyword: str,
        difficulty: SEODifficulty,
        search_volume: Optional[int],
        competition: float,
        cpc: Optional[float]
    ) -> tuple[bool, str]:
        """
        Evaluate keyword recommendation using enhanced metrics.
        """
        word_count = len(keyword.split())
        
        # High-value long-tail keywords
        if word_count >= 3 and search_volume and search_volume >= 100:
            return True, "High-value long-tail keyword with good search volume"
        
        # Good search volume with manageable competition
        if search_volume and search_volume >= 500 and competition < 0.7:
            return True, "Good search volume with manageable competition"
        
        # Low competition opportunities
        if competition < 0.3 and difficulty in [SEODifficulty.VERY_EASY, SEODifficulty.EASY]:
            return True, "Low competition opportunity"
        
        # High commercial intent (high CPC but manageable difficulty)
        if cpc and cpc > 1.0 and difficulty in [SEODifficulty.EASY, SEODifficulty.MEDIUM]:
            return True, "High commercial value with reasonable difficulty"
        
        # Very competitive keywords
        if difficulty == SEODifficulty.VERY_HARD and competition > 0.8:
            return False, "Very competitive keyword - consider long-tail alternatives"
        
        # Low search volume
        if search_volume is not None and search_volume < 50:
            return False, "Low search volume - limited traffic potential"
        
        # Default recommendation
        return True, "Suitable keyword for targeting"


# Integration helper functions for MCP DataForSEO tools
class DataForSEOIntegration:
    """
    Helper class for integrating with DataForSEO MCP tools.
    """
    
    @staticmethod
    async def get_search_volume(keywords: List[str], location: str = "United States") -> Dict[str, int]:
        """
        Get search volume data using DataForSEO MCP tools.
        
        This would use: mcp_dataforseo_keywords_data_google_ads_search_volume
        """
        # Placeholder - would integrate with MCP tools
        return {keyword: 0 for keyword in keywords}
    
    @staticmethod
    async def get_keyword_difficulty(keywords: List[str], location: str = "United States") -> Dict[str, float]:
        """
        Get keyword difficulty using DataForSEO MCP tools.
        
        This would use: mcp_dataforseo_dataforseo_labs_bulk_keyword_difficulty
        """
        # Placeholder - would integrate with MCP tools
        return {keyword: 0.0 for keyword in keywords}
    
    @staticmethod
    async def get_serp_competitors(keywords: List[str], location: str = "United States") -> Dict[str, List[str]]:
        """
        Get SERP competitors using DataForSEO MCP tools.
        
        This would use: mcp_dataforseo_dataforseo_labs_google_serp_competitors
        """
        # Placeholder - would integrate with MCP tools
        return {keyword: [] for keyword in keywords}
