"""
Interlinking analyzer for matching keywords to existing content.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple, Set
from dateutil import parser as date_parser

from ..models.integration_models import ExistingContentItem, InterlinkOpportunity

logger = logging.getLogger(__name__)


class InterlinkingAnalyzer:
    """Analyzer for finding interlinking opportunities."""
    
    def __init__(self):
        """Initialize the interlinking analyzer."""
        pass
    
    def normalize_content(self, existing_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize existing content to a standard format for analysis.
        
        Args:
            existing_content: List of content items from provider
            
        Returns:
            List of normalized content items
        """
        normalized = []
        
        for item in existing_content:
            # Normalize keywords to lowercase
            keywords = item.get('keywords', [])
            keywords_normalized = [
                kw.lower().strip() 
                for kw in keywords if kw
            ]
            
            normalized.append({
                'id': item.get('id'),
                'title': item.get('title', ''),
                'url': item.get('url', ''),
                'slug': item.get('slug', ''),
                'keywords': keywords,
                'keywords_normalized': keywords_normalized,
                'categories': item.get('categories', []),
                'published_at': item.get('published_at'),
                'excerpt': item.get('excerpt', ''),
            })
        
        return normalized
    
    def match_keywords_to_content(
        self,
        keywords: List[str],
        existing_content: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Match keywords to existing content.
        
        Args:
            keywords: List of keywords to match
            existing_content: List of normalized content items
            
        Returns:
            Dictionary mapping keywords to list of matches
        """
        matches = {}
        
        for keyword in keywords:
            keyword_lower = keyword.lower().strip()
            keyword_words = keyword_lower.split()
            
            matches[keyword] = []
            
            for content in existing_content:
                # Check exact keyword match
                if keyword_lower in content['keywords_normalized']:
                    matches[keyword].append({
                        'content': content,
                        'match_type': 'exact',
                        'score': 1.0
                    })
                    continue
                
                # Check partial match (keyword contains content keyword or vice versa)
                matched = False
                for content_keyword in content['keywords_normalized']:
                    # Check if keyword contains content keyword
                    if content_keyword in keyword_lower:
                        matches[keyword].append({
                            'content': content,
                            'match_type': 'partial',
                            'score': 0.7
                        })
                        matched = True
                        break
                    
                    # Check if content keyword contains keyword
                    if keyword_lower in content_keyword:
                        matches[keyword].append({
                            'content': content,
                            'match_type': 'partial',
                            'score': 0.7
                        })
                        matched = True
                        break
                
                if matched:
                    continue
                
                # Check title match
                title_lower = content['title'].lower()
                if keyword_lower in title_lower:
                    matches[keyword].append({
                        'content': content,
                        'match_type': 'title',
                        'score': 0.8
                    })
                    continue
                
                # Check word overlap
                content_words = set(
                    ' '.join(content['keywords_normalized'] + [title_lower]).split()
                )
                keyword_words_set = set(keyword_words)
                overlap = len(keyword_words_set.intersection(content_words))
                
                if overlap > 0:
                    score = overlap / len(keyword_words_set)
                    if score >= 0.3:  # At least 30% word overlap
                        matches[keyword].append({
                            'content': content,
                            'match_type': 'word_overlap',
                            'score': score * 0.6  # Lower weight for word overlap
                        })
        
        return matches
    
    def calculate_relevance_score(
        self,
        keyword: str,
        content: Dict[str, Any],
        match_type: str,
        base_score: float
    ) -> float:
        """
        Calculate comprehensive relevance score.
        
        Args:
            keyword: The keyword being matched
            content: The content item
            match_type: Type of match (exact, partial, title, word_overlap)
            base_score: Base score from matching
            
        Returns:
            Final relevance score (0.0 to 1.0)
        """
        score = base_score
        
        # Boost score based on recency (newer content gets slight boost)
        if content.get('published_at'):
            try:
                published_date = date_parser.parse(content['published_at'])
                days_old = (datetime.now(published_date.tzinfo) - published_date).days
                
                # Content less than 30 days old gets 10% boost
                if days_old < 30:
                    score *= 1.1
                # Content less than 90 days old gets 5% boost
                elif days_old < 90:
                    score *= 1.05
            except (ValueError, TypeError) as e:
                logger.debug(f"Could not parse published_at date: {e}")
        
        # Boost score if keyword appears in title
        title_lower = content['title'].lower()
        keyword_lower = keyword.lower()
        if keyword_lower in title_lower:
            score *= 1.2
        
        # Boost score based on keyword count in content
        keyword_count = sum(
            1 for kw in content['keywords_normalized']
            if keyword_lower in kw or kw in keyword_lower
        )
        if keyword_count > 1:
            score *= (1 + keyword_count * 0.1)
        
        # Normalize score to 0-1 range
        return min(score, 1.0)
    
    def generate_anchor_text(
        self,
        keyword: str,
        content: Dict[str, Any]
    ) -> str:
        """
        Generate appropriate anchor text for interlink.
        
        Args:
            keyword: The keyword being linked
            content: The content item
            
        Returns:
            Suggested anchor text
        """
        title = content['title']
        keyword_lower = keyword.lower()
        title_lower = title.lower()
        
        # If keyword is in title, use the exact phrase from title
        if keyword_lower in title_lower:
            # Find the phrase in title that contains the keyword
            words = title.split()
            for i, word in enumerate(words):
                if keyword_lower in word.lower():
                    # Return 2-4 word phrase around the keyword
                    start = max(0, i - 1)
                    end = min(len(words), i + 3)
                    return ' '.join(words[start:end])
        
        # If keyword matches a content keyword, use that
        for content_keyword in content['keywords_normalized']:
            if keyword_lower in content_keyword or content_keyword in keyword_lower:
                return content_keyword.title()
        
        # Fallback: Use keyword as-is (capitalized)
        return keyword.title()
    
    def analyze_interlinking_opportunities(
        self,
        keywords: List[str],
        existing_content: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Complete interlinking analysis.
        
        Args:
            keywords: List of keywords to analyze
            existing_content: List of existing content items
            
        Returns:
            Dictionary with analysis results
        """
        # Normalize content
        normalized_content = self.normalize_content(existing_content)
        
        # Match keywords to content
        matches = self.match_keywords_to_content(keywords, normalized_content)
        
        # Process matches and calculate scores
        per_keyword_results = []
        
        for keyword in keywords:
            keyword_matches = matches.get(keyword, [])
            
            # Calculate relevance scores
            opportunities = []
            seen_content_ids: Set[str] = set()
            
            for match in keyword_matches:
                content = match['content']
                content_id = content['id']
                
                # Skip duplicates
                if content_id in seen_content_ids:
                    continue
                seen_content_ids.add(content_id)
                
                # Calculate final relevance score
                relevance_score = self.calculate_relevance_score(
                    keyword=keyword,
                    content=content,
                    match_type=match['match_type'],
                    base_score=match['score']
                )
                
                # Only include opportunities with score >= 0.4
                if relevance_score >= 0.4:
                    anchor_text = self.generate_anchor_text(keyword, content)
                    
                    opportunities.append({
                        'target_url': content['url'],
                        'target_title': content['title'],
                        'anchor_text': anchor_text,
                        'relevance_score': round(relevance_score, 2)
                    })
            
            # Sort by relevance score (descending)
            opportunities.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Limit to top 10 opportunities per keyword
            opportunities = opportunities[:10]
            
            per_keyword_results.append({
                'keyword': keyword,
                'suggested_interlinks': len(opportunities),
                'interlink_opportunities': opportunities
            })
        
        # Calculate total recommended interlinks
        total_interlinks = sum(
            result['suggested_interlinks']
            for result in per_keyword_results
        )
        
        return {
            'recommended_interlinks': total_interlinks,
            'per_keyword': per_keyword_results
        }

