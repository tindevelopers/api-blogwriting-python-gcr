"""
Interlinking analyzer for matching keywords to existing content.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple, Set, Optional
from dateutil import parser as date_parser

from ..models.integration_models import ExistingContentItem, InterlinkOpportunity, InterlinkingSettings

logger = logging.getLogger(__name__)

# Priority weighting for strategic page types and collections
PAGE_TYPE_WEIGHTS = {
    'solution': 1.5,
    'case-study': 1.3,
    'project': 1.2,
    'blog': 1.0,
    'static': 0.9,
}

COLLECTION_WEIGHTS = {
    'solutions': 1.5,
    'case-studies': 1.3,
    'projects': 1.2,
    'blog-posts': 1.0,
}

# Simple semantic mappings to catch near-matches
SEMANTIC_MAPPINGS = {
    'customer service': ['support', 'help desk', 'customer support', 'service'],
    'marketing': ['advertising', 'promotion', 'campaigns', 'content marketing'],
    'ai': ['artificial intelligence', 'machine learning', 'automation'],
}

DEFAULT_STRATEGIC_PRIORITY = 1.0


class InterlinkingAnalyzer:
    """Analyzer for finding interlinking opportunities."""
    
    def __init__(self):
        """Initialize the interlinking analyzer."""
        pass
    
    def calculate_strategic_priority(self, content: Dict[str, Any]) -> float:
        """
        Calculate strategic importance multiplier for a content item.
        Higher values indicate higher business value for linking.
        """
        priority = content.get('strategic_priority', DEFAULT_STRATEGIC_PRIORITY) or DEFAULT_STRATEGIC_PRIORITY
        
        # Page type boost
        page_type = (content.get('page_type') or '').lower()
        priority *= PAGE_TYPE_WEIGHTS.get(page_type, 1.0)
        
        # Collection boost
        collection_slug = (content.get('collection_slug') or '').lower()
        priority *= COLLECTION_WEIGHTS.get(collection_slug, 1.0)
        
        # SEO metadata presence boost
        if content.get('meta_description'):
            priority *= 1.05
        
        return min(priority, 2.0)
    
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
            meta_description = item.get('meta_description', '') or ''
            short_description = item.get('short_description', '') or ''
            collection_slug = item.get('collection_slug', '') or ''
            page_type = item.get('page_type', '') or ''
            strategic_priority = item.get('strategic_priority', DEFAULT_STRATEGIC_PRIORITY)
            
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
                'meta_description': meta_description,
                'title_tag': item.get('title_tag', ''),
                'short_description': short_description,
                'collection_slug': collection_slug,
                'collection_name': item.get('collection_name', ''),
                'page_type': page_type,
                'strategic_priority': strategic_priority,
                'searchable_text': ' '.join([
                    item.get('title', ''),
                    meta_description,
                    short_description,
                    ' '.join(keywords)
                ]).lower()
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
            semantic_terms = []
            for pivot, related_terms in SEMANTIC_MAPPINGS.items():
                if pivot in keyword_lower:
                    semantic_terms.extend(related_terms)
            
            matches[keyword] = []
            
            for content in existing_content:
                meta_description = (content.get('meta_description') or '').lower()
                short_description = (content.get('short_description') or '').lower()
                searchable_text = content.get('searchable_text', '')
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
                
                # Check meta description match
                if keyword_lower and keyword_lower in meta_description:
                    matches[keyword].append({
                        'content': content,
                        'match_type': 'meta_description',
                        'score': 0.85
                    })
                    continue
                
                # Check short description match
                if keyword_lower and keyword_lower in short_description:
                    matches[keyword].append({
                        'content': content,
                        'match_type': 'short_description',
                        'score': 0.8
                    })
                    continue
                
                # Check multi-word phrase match against combined searchable text
                if ' ' in keyword_lower and keyword_lower in searchable_text:
                    matches[keyword].append({
                        'content': content,
                        'match_type': 'phrase',
                        'score': 0.75
                    })
                    continue
                
                # Semantic related terms
                if semantic_terms:
                    for term in semantic_terms:
                        if term in searchable_text:
                            matches[keyword].append({
                                'content': content,
                                'match_type': 'semantic',
                                'score': 0.65
                            })
                            break
                    if matches[keyword] and matches[keyword][-1].get('match_type') == 'semantic':
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
        base_score: float,
        authority_weight: float = 0.3
    ) -> float:
        """
        Calculate comprehensive relevance score.
        
        Args:
            keyword: The keyword being matched
            content: The content item
            match_type: Type of match (exact, partial, title, word_overlap)
            base_score: Base score from matching
            authority_weight: Weight for authority score (0.0 to 1.0)
            
        Returns:
            Final relevance score (0.0 to 1.0)
        """
        match_score = base_score
        authority_score = 1.0
        
        # Boost score based on recency (newer content gets slight boost)
        if content.get('published_at'):
            try:
                published_date = date_parser.parse(content['published_at'])
                days_old = (datetime.now(published_date.tzinfo) - published_date).days
                
                # Content less than 30 days old gets 10% boost
                if days_old < 30:
                    authority_score = 1.1
                # Content less than 90 days old gets 5% boost
                elif days_old < 90:
                    authority_score = 1.05
            except (ValueError, TypeError) as e:
                logger.debug(f"Could not parse published_at date: {e}")
        
        # Boost score if keyword appears in title
        title_lower = content['title'].lower()
        keyword_lower = keyword.lower()
        if keyword_lower in title_lower:
            match_score *= 1.2
        
        # Boost score based on keyword count in content
        keyword_count = sum(
            1 for kw in content['keywords_normalized']
            if keyword_lower in kw or kw in keyword_lower
        )
        if keyword_count > 1:
            match_score *= (1 + keyword_count * 0.1)
        
        match_score = min(match_score, 1.0)
        authority_score = min(authority_score, 1.2)
        strategic_priority = self.calculate_strategic_priority(content)
        
        # Calculate weights dynamically based on authority_weight
        # Base weights: match=0.5, authority=0.3, strategic=0.2
        # User can adjust authority_weight (0.0 to 1.0)
        # Adjust other weights proportionally to ensure they sum to 1.0
        
        base_match_weight = 0.5
        base_strategic_weight = 0.2
        base_total = base_match_weight + base_strategic_weight  # 0.7
        
        # If authority_weight is provided, adjust the remaining 1.0 - authority_weight
        # proportionally between match and strategic
        remaining_weight = 1.0 - authority_weight
        
        if remaining_weight <= 0:
            # Edge case: authority_weight is 1.0, use only authority
            match_weight = 0.0
            strategic_weight = 0.0
        else:
            # Distribute remaining weight proportionally
            match_weight = (base_match_weight / base_total) * remaining_weight
            strategic_weight = (base_strategic_weight / base_total) * remaining_weight
        
        final_score = (
            match_score * match_weight +
            authority_score * authority_weight +
            strategic_priority * strategic_weight
        )
        
        # Normalize score to 0-1 range
        return min(final_score, 1.0)
    
    def _extract_phrase_from_title(self, title: str, keyword: str) -> str:
        """Extract a short phrase from the title that includes the keyword."""
        words = title.split()
        keyword_lower = keyword.lower()
        for i, word in enumerate(words):
            if keyword_lower in word.lower():
                start = max(0, i - 1)
                end = min(len(words), i + 3)
                return ' '.join(words[start:end])
        return title[:60] if len(title) > 60 else title
    
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
        short_description = content.get('short_description') or ''
        
        # Strategy 1: concise short description if available
        if short_description and len(short_description) < 60:
            return short_description
        
        # Strategy 2: extract natural phrase from title when keyword present
        if keyword_lower in title_lower:
            return self._extract_phrase_from_title(title, keyword)
        
        # Strategy 3: use related keyword phrase when available
        for content_keyword in content['keywords_normalized']:
            if keyword_lower in content_keyword or content_keyword in keyword_lower:
                return content_keyword.title()
        
        # Strategy 4: contextual anchor by page type
        page_type = (content.get('page_type') or '').lower()
        if page_type == 'solution':
            return f"{keyword} services"
        if page_type == 'case-study':
            return f"{keyword} case study"
        if page_type == 'project':
            return f"{keyword} implementation"
        
        # Fallback: Use keyword as-is (capitalized)
        return keyword.title() if len(keyword) <= 60 else keyword[:57] + '...'
    
    def analyze_interlinking_opportunities(
        self,
        keywords: List[str],
        existing_content: List[Dict[str, Any]],
        settings: Optional[InterlinkingSettings] = None
    ) -> Dict[str, Any]:
        """
        Complete interlinking analysis.
        
        Args:
            keywords: List of keywords to analyze
            existing_content: List of existing content items
            settings: Optional interlinking settings to control analysis behavior
            
        Returns:
            Dictionary with analysis results
        """
        # Use default settings if none provided
        if settings is None:
            settings = InterlinkingSettings()
        
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
                
                # Calculate final relevance score with custom authority weight
                relevance_score = self.calculate_relevance_score(
                    keyword=keyword,
                    content=content,
                    match_type=match['match_type'],
                    base_score=match['score'],
                    authority_weight=settings.authority_weight
                )
                
                # Filter based on relevance threshold and allow_low_value_links setting
                should_include = False
                if settings.allow_low_value_links:
                    # Include all links if low-value links are allowed
                    should_include = True
                else:
                    # Only include links above the threshold
                    should_include = relevance_score >= settings.relevance_threshold
                
                if should_include:
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

