"""
Keyword Categorization Module

Categorizes keywords into strategic buckets for content planning:
- Quick Wins: Low difficulty, good volume, manageable competition
- Authority Builders: High difficulty, high volume, competitive
- Emerging Topics: Growing trends, moderate difficulty
- Intent Signals: Clear search intent indicators
- Semantic Topics: Related semantic clusters
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class KeywordCategory(str, Enum):
    """Strategic keyword categories for content planning."""
    QUICK_WINS = "Quick Wins"
    AUTHORITY_BUILDERS = "Authority Builders"
    EMERGING_TOPICS = "Emerging Topics"
    INTENT_SIGNALS = "Intent Signals"
    SEMANTIC_TOPICS = "Semantic Topics"


@dataclass
class KeywordCategoryAssignment:
    """Assignment of a keyword to a strategic category."""
    keyword: str
    category: KeywordCategory
    confidence: float  # 0.0 to 1.0
    reasoning: str
    priority_score: float  # 0.0 to 1.0, higher = more important


@dataclass
class ClusterContentRecommendation:
    """Content recommendations for a keyword cluster."""
    cluster_name: str
    category: KeywordCategory
    pillar_title: Optional[str] = None
    pillar_description: Optional[str] = None
    pillar_url: Optional[str] = None
    sub_pages: List[Dict[str, str]] = None  # List of {title, description, url, keyword}
    priority: int = 3  # 1-5, higher = more important
    estimated_word_count: Optional[int] = None
    
    def __post_init__(self):
        if self.sub_pages is None:
            self.sub_pages = []


class KeywordCategorizer:
    """
    Categorizes keywords into strategic buckets for content planning.
    
    Uses keyword metrics (difficulty, search volume, competition, CPC, trends)
    to assign keywords to strategic categories that inform content strategy.
    """
    
    def __init__(self):
        """Initialize keyword categorizer."""
        # Intent signal words that indicate clear search intent
        self.intent_words = {
            'how', 'what', 'why', 'when', 'where', 'who', 'which',
            'best', 'top', 'guide', 'tutorial', 'tips', 'tricks',
            'buy', 'purchase', 'review', 'compare', 'vs', 'versus',
            'learn', 'understand', 'explain', 'definition', 'meaning'
        }
        
        # Commercial intent indicators
        self.commercial_signals = {
            'best', 'top', 'review', 'compare', 'vs', 'versus',
            'alternative', 'cheap', 'affordable', 'price', 'cost',
            'buy', 'purchase', 'deal', 'discount', 'sale'
        }
    
    def categorize_keyword(
        self,
        keyword: str,
        search_volume: int = 0,
        difficulty: float = 50.0,
        competition: float = 0.5,
        cpc: float = 0.0,
        trend_score: float = 0.0,
        keyword_ideas_count: int = 0
    ) -> KeywordCategoryAssignment:
        """
        Categorize a keyword based on metrics.
        
        Args:
            keyword: The keyword to categorize
            search_volume: Monthly search volume
            difficulty: Keyword difficulty score (0-100)
            competition: Competition index (0-1)
            cpc: Cost per click
            trend_score: Trend score (-1 to 1, positive = growing)
            keyword_ideas_count: Number of related keyword ideas found
            
        Returns:
            KeywordCategoryAssignment with category and reasoning
        """
        keyword_lower = keyword.lower()
        words = set(keyword_lower.split())
        
        # Calculate priority score (0.0 to 1.0)
        priority_score = self._calculate_priority_score(
            search_volume, difficulty, competition, cpc, trend_score
        )
        
        # Check for Intent Signals first (clear search intent)
        has_intent_signal = any(word in self.intent_words for word in words)
        if has_intent_signal and keyword_ideas_count > 5:
            return KeywordCategoryAssignment(
                keyword=keyword,
                category=KeywordCategory.INTENT_SIGNALS,
                confidence=0.8,
                reasoning=f"Contains clear search intent indicators ({', '.join(words.intersection(self.intent_words))}) with {keyword_ideas_count} related ideas",
                priority_score=priority_score
            )
        
        # Quick Wins: Low difficulty, decent volume, low competition
        if (difficulty < 40 and 
            search_volume >= 100 and 
            competition < 0.5 and
            search_volume < 5000):  # Not too competitive
            return KeywordCategoryAssignment(
                keyword=keyword,
                category=KeywordCategory.QUICK_WINS,
                confidence=0.85,
                reasoning=f"Low difficulty ({difficulty:.1f}), good volume ({search_volume}), manageable competition ({competition:.2f})",
                priority_score=priority_score
            )
        
        # Authority Builders: High difficulty, high volume, high competition
        if (difficulty >= 70 and 
            search_volume >= 1000 and 
            competition >= 0.7):
            return KeywordCategoryAssignment(
                keyword=keyword,
                category=KeywordCategory.AUTHORITY_BUILDERS,
                confidence=0.8,
                reasoning=f"High difficulty ({difficulty:.1f}), high volume ({search_volume}), competitive ({competition:.2f}) - authority-building opportunity",
                priority_score=priority_score
            )
        
        # Emerging Topics: Growing trend, moderate metrics
        if (trend_score > 0.3 and 
            30 <= difficulty <= 60 and 
            search_volume >= 200):
            return KeywordCategoryAssignment(
                keyword=keyword,
                category=KeywordCategory.EMERGING_TOPICS,
                confidence=0.75,
                reasoning=f"Growing trend (score: {trend_score:.2f}), moderate difficulty ({difficulty:.1f}), decent volume ({search_volume})",
                priority_score=priority_score
            )
        
        # High commercial value (high CPC) with reasonable difficulty
        if (cpc >= 1.0 and 
            difficulty <= 60 and 
            search_volume >= 200):
            return KeywordCategoryAssignment(
                keyword=keyword,
                category=KeywordCategory.QUICK_WINS,
                confidence=0.7,
                reasoning=f"High commercial value (CPC: ${cpc:.2f}) with reasonable difficulty ({difficulty:.1f})",
                priority_score=priority_score
            )
        
        # Intent Signals: Clear intent but lower volume
        if has_intent_signal:
            return KeywordCategoryAssignment(
                keyword=keyword,
                category=KeywordCategory.INTENT_SIGNALS,
                confidence=0.65,
                reasoning=f"Contains intent indicators but lower volume ({search_volume}) or higher difficulty ({difficulty:.1f})",
                priority_score=priority_score
            )
        
        # Default: Semantic Topics
        return KeywordCategoryAssignment(
            keyword=keyword,
            category=KeywordCategory.SEMANTIC_TOPICS,
            confidence=0.5,
            reasoning=f"Semantically related topic cluster (difficulty: {difficulty:.1f}, volume: {search_volume})",
            priority_score=priority_score
        )
    
    def _calculate_priority_score(
        self,
        search_volume: int,
        difficulty: float,
        competition: float,
        cpc: float,
        trend_score: float
    ) -> float:
        """
        Calculate priority score (0.0 to 1.0) for keyword prioritization.
        
        Higher score = more important/valuable keyword.
        """
        # Volume component (0-0.4)
        if search_volume >= 10000:
            volume_score = 0.4
        elif search_volume >= 1000:
            volume_score = 0.3
        elif search_volume >= 100:
            volume_score = 0.2
        elif search_volume >= 10:
            volume_score = 0.1
        else:
            volume_score = 0.0
        
        # Difficulty component (inverse - lower difficulty = higher score) (0-0.3)
        difficulty_score = max(0, (100 - difficulty) / 100) * 0.3
        
        # Competition component (inverse - lower competition = higher score) (0-0.2)
        competition_score = max(0, (1.0 - competition)) * 0.2
        
        # CPC component (higher CPC = higher value) (0-0.05)
        cpc_score = min(0.05, cpc / 20.0)  # Cap at $20 CPC
        
        # Trend component (growing trends = higher score) (0-0.05)
        trend_score_component = max(0, trend_score) * 0.05
        
        total = volume_score + difficulty_score + competition_score + cpc_score + trend_score_component
        
        # Normalize to 0.0-1.0
        return min(1.0, total)
    
    def categorize_cluster(
        self,
        cluster: Dict[str, Any],
        keywords_data: Dict[str, Dict[str, Any]]
    ) -> KeywordCategory:
        """
        Categorize an entire cluster based on its keywords.
        
        Args:
            cluster: Cluster object with keywords list
            keywords_data: Full keyword analysis data
            
        Returns:
            Dominant category for the cluster
        """
        cluster_keywords = cluster.get('keywords', [])
        if not cluster_keywords:
            return KeywordCategory.SEMANTIC_TOPICS
        
        # Get categories for all keywords in cluster
        categories = []
        for kw in cluster_keywords:
            kw_data = keywords_data.get(kw, {})
            assignment = self.categorize_keyword(
                keyword=kw,
                search_volume=kw_data.get('search_volume', 0),
                difficulty=kw_data.get('difficulty_score', 50.0),
                competition=kw_data.get('competition', 0.5),
                cpc=kw_data.get('cpc', 0.0),
                trend_score=kw_data.get('trend_score', 0.0),
                keyword_ideas_count=len(kw_data.get('keyword_ideas', []))
            )
            categories.append(assignment.category)
        
        # Return most common category, or highest priority if tied
        category_counts = {}
        for cat in categories:
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        if not category_counts:
            return KeywordCategory.SEMANTIC_TOPICS
        
        # Return most common category
        return max(category_counts.items(), key=lambda x: x[1])[0]
    
    def generate_cluster_priority(
        self,
        cluster: Dict[str, Any],
        keywords_data: Dict[str, Dict[str, Any]]
    ) -> int:
        """
        Generate priority score (1-5) for a cluster.
        
        Args:
            cluster: Cluster object
            keywords_data: Full keyword analysis data
            
        Returns:
            Priority integer (1-5, higher = more important)
        """
        cluster_keywords = cluster.get('keywords', [])
        if not cluster_keywords:
            return 3
        
        # Calculate average priority scores
        priority_scores = []
        for kw in cluster_keywords:
            kw_data = keywords_data.get(kw, {})
            assignment = self.categorize_keyword(
                keyword=kw,
                search_volume=kw_data.get('search_volume', 0),
                difficulty=kw_data.get('difficulty_score', 50.0),
                competition=kw_data.get('competition', 0.5),
                cpc=kw_data.get('cpc', 0.0),
                trend_score=kw_data.get('trend_score', 0.0),
                keyword_ideas_count=len(kw_data.get('keyword_ideas', []))
            )
            priority_scores.append(assignment.priority_score)
        
        if not priority_scores:
            return 3
        
        avg_priority = sum(priority_scores) / len(priority_scores)
        
        # Convert to 1-5 scale
        if avg_priority >= 0.8:
            return 5
        elif avg_priority >= 0.6:
            return 4
        elif avg_priority >= 0.4:
            return 3
        elif avg_priority >= 0.2:
            return 2
        else:
            return 1
