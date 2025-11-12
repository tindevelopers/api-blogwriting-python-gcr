"""
Google Search Console API Integration

Provides access to Search Console data for content strategy and performance tracking.
"""

import os
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GSC_AVAILABLE = True
except ImportError:
    GSC_AVAILABLE = False
    logging.warning("Google Search Console API libraries not available")

logger = logging.getLogger(__name__)


class GoogleSearchConsoleClient:
    """Client for Google Search Console API."""
    
    def __init__(
        self,
        credentials_path: Optional[str] = None,
        site_url: Optional[str] = None
    ):
        """
        Initialize Google Search Console client.
        
        Args:
            credentials_path: Path to service account credentials JSON
            site_url: Site URL (e.g., 'https://example.com' or 'sc-domain:example.com')
        """
        if not GSC_AVAILABLE:
            logger.warning("Google Search Console API not available - install google-api-python-client")
            self.service = None
            self.site_url = site_url or os.getenv("GSC_SITE_URL")
            return
        
        self.site_url = site_url or os.getenv("GSC_SITE_URL")
        self.service = None
        
        try:
            # Try to use service account credentials
            if credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                creds_path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
                credentials = service_account.Credentials.from_service_account_file(
                    creds_path,
                    scopes=['https://www.googleapis.com/auth/webmasters.readonly']
                )
                self.service = build('searchconsole', 'v1', credentials=credentials)
                logger.info("Google Search Console client initialized")
            else:
                logger.warning("Google Search Console credentials not configured")
        except Exception as e:
            logger.error(f"Failed to initialize Google Search Console client: {e}")
            self.service = None
    
    async def get_query_performance(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        dimensions: List[str] = None,
        row_limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get query performance data from Search Console.
        
        Args:
            start_date: Start date in YYYY-MM-DD format (default: 30 days ago)
            end_date: End date in YYYY-MM-DD format (default: today)
            dimensions: Dimensions to group by (['query'], ['page'], ['query', 'page'])
            row_limit: Maximum number of rows to return
        
        Returns:
            List of query performance data
        """
        if not self.service or not self.site_url:
            logger.warning("Google Search Console not configured")
            return []
        
        if dimensions is None:
            dimensions = ['query']
        
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        try:
            request = {
                'startDate': start_date,
                'endDate': end_date,
                'dimensions': dimensions,
                'rowLimit': row_limit
            }
            
            response = self.service.searchanalytics().query(
                siteUrl=self.site_url,
                body=request
            ).execute()
            
            rows = response.get('rows', [])
            return [
                {
                    'query': row.get('keys', [''])[0] if 'query' in dimensions else '',
                    'clicks': row.get('clicks', 0),
                    'impressions': row.get('impressions', 0),
                    'ctr': row.get('ctr', 0),
                    'position': row.get('position', 0)
                }
                for row in rows
            ]
        except HttpError as e:
            logger.error(f"Google Search Console API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching query performance: {e}")
            return []
    
    async def identify_content_opportunities(
        self,
        min_impressions: int = 100,
        max_position: float = 20.0,
        min_ctr_threshold: float = 0.02
    ) -> List[Dict[str, Any]]:
        """
        Identify content opportunities from Search Console data.
        
        Args:
            min_impressions: Minimum impressions to consider
            max_position: Maximum average position
            min_ctr_threshold: Minimum CTR threshold for opportunity
        
        Returns:
            List of content opportunities
        """
        queries = await self.get_query_performance()
        
        opportunities = []
        for query_data in queries:
            impressions = query_data.get('impressions', 0)
            position = query_data.get('position', 0)
            ctr = query_data.get('ctr', 0)
            
            # Identify opportunities: high impressions, low CTR, decent position
            if (impressions >= min_impressions and 
                position <= max_position and 
                ctr < min_ctr_threshold):
                opportunities.append({
                    'keyword': query_data.get('query', ''),
                    'impressions': impressions,
                    'position': position,
                    'ctr': ctr,
                    'opportunity_score': impressions * (1 - ctr) / position,
                    'recommendation': 'Improve title and meta description to increase CTR'
                })
        
        # Sort by opportunity score
        opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)
        return opportunities[:20]  # Top 20 opportunities
    
    async def get_top_queries(
        self,
        days: int = 30,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get top performing queries.
        
        Args:
            days: Number of days to look back
            limit: Maximum number of queries to return
        
        Returns:
            List of top queries
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        queries = await self.get_query_performance(
            start_date=start_date,
            end_date=end_date,
            row_limit=limit
        )
        
        # Sort by clicks
        queries.sort(key=lambda x: x.get('clicks', 0), reverse=True)
        return queries[:limit]
    
    async def get_content_gaps(
        self,
        target_keywords: List[str]
    ) -> Dict[str, Any]:
        """
        Identify content gaps for target keywords.
        
        Args:
            target_keywords: List of target keywords to analyze
        
        Returns:
            Dictionary with gap analysis
        """
        all_queries = await self.get_query_performance(row_limit=5000)
        existing_queries = {q.get('query', '').lower() for q in all_queries}
        
        gaps = []
        for keyword in target_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower not in existing_queries:
                gaps.append({
                    'keyword': keyword,
                    'status': 'not_ranking',
                    'recommendation': 'Create content targeting this keyword'
                })
            else:
                # Check performance
                query_data = next(
                    (q for q in all_queries if q.get('query', '').lower() == keyword_lower),
                    None
                )
                if query_data:
                    if query_data.get('position', 0) > 10:
                        gaps.append({
                            'keyword': keyword,
                            'status': 'ranking_low',
                            'position': query_data.get('position', 0),
                            'recommendation': 'Improve content to rank higher'
                        })
        
        return {
            'total_keywords': len(target_keywords),
            'gaps_found': len(gaps),
            'gaps': gaps
        }

