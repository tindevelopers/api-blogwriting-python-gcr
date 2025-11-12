"""
Keyword clustering and parent topic extraction module.

This module groups keywords by semantic similarity and extracts
meaningful parent topics for better organization and content strategy.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from collections import Counter, defaultdict
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class KeywordCluster:
    """Represents a cluster of related keywords."""
    parent_topic: str
    keywords: List[str]
    cluster_score: float  # 0-1, higher = more cohesive
    dominant_words: List[str]  # Most common words in cluster
    category_type: str  # e.g., "question", "action", "entity", "topic"


@dataclass
class ClusteringResult:
    """Result of keyword clustering operation."""
    clusters: List[KeywordCluster]
    unclustered: List[str]  # Keywords that didn't fit into any cluster
    total_keywords: int
    cluster_count: int


class KeywordClustering:
    """
    Clusters keywords by semantic similarity and extracts parent topics.
    
    Uses multiple strategies:
    1. Question word grouping (why, what, how, when, where)
    2. Common word extraction (most frequent meaningful words)
    3. Semantic similarity (word overlap and shared concepts)
    4. Entity-based grouping (using Google Knowledge Graph if available)
    """
    
    def __init__(self, knowledge_graph_client=None):
        """
        Initialize keyword clustering.
        
        Args:
            knowledge_graph_client: Optional Google Knowledge Graph client
                for entity-based clustering
        """
        self.knowledge_graph_client = knowledge_graph_client
        
        # Question words that indicate intent types
        self.question_words = {
            'why': 'Why',
            'what': 'What',
            'how': 'How',
            'when': 'When',
            'where': 'Where',
            'who': 'Who',
            'which': 'Which',
            'can': 'Can',
            'should': 'Should',
            'will': 'Will'
        }
        
        # Common stop words to ignore when extracting parent topics
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might',
            'this', 'that', 'these', 'those', 'it', 'its', 'they', 'them', 'their'
        }
        
        # Action words that might indicate content type
        self.action_words = {
            'guide', 'tutorial', 'tips', 'tricks', 'best', 'top', 'review',
            'compare', 'vs', 'versus', 'buy', 'purchase', 'learn', 'understand'
        }
    
    def cluster_keywords(
        self,
        keywords: List[str],
        min_cluster_size: int = 2,
        max_clusters: Optional[int] = None,
        max_keywords_per_cluster: Optional[int] = None
    ) -> ClusteringResult:
        """
        Cluster keywords into groups with parent topics.
        
        Args:
            keywords: List of keywords to cluster
            min_cluster_size: Minimum keywords per cluster
            max_clusters: Maximum number of clusters (None = unlimited)
            max_keywords_per_cluster: Maximum keywords per cluster (None = unlimited)
        
        Returns:
            ClusteringResult with clusters and parent topics
        """
        if not keywords:
            return ClusteringResult(
                clusters=[],
                unclustered=[],
                total_keywords=0,
                cluster_count=0
            )
        
        # Normalize keywords
        normalized_keywords = [self._normalize_keyword(kw) for kw in keywords]
        
        # Limit keywords if too many (for performance)
        if len(normalized_keywords) > 500:
            logger.warning(f"Too many keywords ({len(normalized_keywords)}), limiting to 500 for performance")
            normalized_keywords = normalized_keywords[:500]
        
        # Strategy 1: Group by question words
        question_clusters = self._cluster_by_question_words(normalized_keywords)
        
        # Strategy 2: Group by common words/phrases
        semantic_clusters = self._cluster_by_semantic_similarity(normalized_keywords)
        
        # Strategy 3: Group by action words
        action_clusters = self._cluster_by_action_words(normalized_keywords)
        
        # Merge clusters (question clusters take priority)
        merged_clusters = self._merge_clusters(
            question_clusters + semantic_clusters + action_clusters,
            min_cluster_size
        )
        
        # Limit clusters if specified
        if max_clusters and len(merged_clusters) > max_clusters:
            # Sort by size and keep largest
            merged_clusters.sort(key=lambda c: len(c.keywords), reverse=True)
            merged_clusters = merged_clusters[:max_clusters]
        
        # Find unclustered keywords
        clustered_keywords = set()
        for cluster in merged_clusters:
            clustered_keywords.update(cluster.keywords)
        
        unclustered = [
            kw for kw in normalized_keywords
            if kw not in clustered_keywords
        ]
        
        # Create single-keyword clusters for unclustered if they're meaningful
        if unclustered:
            for kw in unclustered:
                parent_topic = self._extract_parent_topic_from_keyword(kw)
                merged_clusters.append(KeywordCluster(
                    parent_topic=parent_topic,
                    keywords=[kw],
                    cluster_score=0.5,
                    dominant_words=self._extract_dominant_words(kw),
                    category_type=self._classify_keyword_type(kw)
                ))
        
        return ClusteringResult(
            clusters=merged_clusters,
            unclustered=[],
            total_keywords=len(keywords),
            cluster_count=len(merged_clusters)
        )
    
    def _normalize_keyword(self, keyword: str) -> str:
        """Normalize keyword for clustering."""
        # Lowercase and strip
        keyword = keyword.lower().strip()
        # Remove extra whitespace
        keyword = re.sub(r'\s+', ' ', keyword)
        return keyword
    
    def _cluster_by_question_words(self, keywords: List[str]) -> List[KeywordCluster]:
        """Group keywords by question words."""
        clusters = defaultdict(list)
        
        for kw in keywords:
            words = kw.split()
            if words:
                first_word = words[0]
                if first_word in self.question_words:
                    clusters[first_word].append(kw)
        
        result = []
        for question_word, kw_list in clusters.items():
            if len(kw_list) >= 2:  # Only create cluster if 2+ keywords
                parent_topic = self.question_words[question_word]
                result.append(KeywordCluster(
                    parent_topic=parent_topic,
                    keywords=kw_list,
                    cluster_score=0.8,  # High score for question-based clusters
                    dominant_words=[question_word],
                    category_type="question"
                ))
        
        return result
    
    def _cluster_by_action_words(self, keywords: List[str]) -> List[KeywordCluster]:
        """Group keywords by action words."""
        clusters = defaultdict(list)
        
        for kw in keywords:
            words = kw.split()
            for word in words:
                if word in self.action_words:
                    clusters[word].append(kw)
                    break
        
        result = []
        for action_word, kw_list in clusters.items():
            if len(kw_list) >= 2:
                # Extract the main topic (words that aren't the action word)
                parent_topic = self._extract_parent_topic_from_keyword_list(kw_list)
                result.append(KeywordCluster(
                    parent_topic=parent_topic or action_word.title(),
                    keywords=kw_list,
                    cluster_score=0.7,
                    dominant_words=[action_word],
                    category_type="action"
                ))
        
        return result
    
    def _cluster_by_semantic_similarity(self, keywords: List[str]) -> List[KeywordCluster]:
        """Group keywords by semantic similarity (word overlap)."""
        if len(keywords) < 2:
            return []
        
        # Extract meaningful words from each keyword
        keyword_words = {}
        for kw in keywords:
            words = self._extract_meaningful_words(kw)
            keyword_words[kw] = words
        
        # Build similarity matrix
        clusters = []
        processed = set()
        
        for kw1 in keywords:
            if kw1 in processed:
                continue
            
            words1 = keyword_words[kw1]
            if not words1:
                continue
            
            cluster_keywords = [kw1]
            processed.add(kw1)
            
            # Find similar keywords
            for kw2 in keywords:
                if kw2 in processed or kw2 == kw1:
                    continue
                
                words2 = keyword_words[kw2]
                if not words2:
                    continue
                
                # Calculate similarity (Jaccard similarity)
                similarity = self._jaccard_similarity(words1, words2)
                
                # If similarity is high enough, add to cluster
                if similarity >= 0.3:  # Threshold for semantic similarity
                    cluster_keywords.append(kw2)
                    processed.add(kw2)
                    # Update words1 to include words from kw2 (for better clustering)
                    words1 = words1.union(words2)
            
            if len(cluster_keywords) >= 2:
                # Extract parent topic from cluster
                parent_topic = self._extract_parent_topic_from_keyword_list(cluster_keywords)
                if not parent_topic:
                    parent_topic = self._extract_parent_topic_from_keyword(cluster_keywords[0])
                
                clusters.append(KeywordCluster(
                    parent_topic=parent_topic,
                    keywords=cluster_keywords,
                    cluster_score=min(0.9, 0.5 + (len(cluster_keywords) * 0.1)),
                    dominant_words=list(words1)[:5],  # Top 5 most common words
                    category_type="semantic"
                ))
        
        return clusters
    
    def _merge_clusters(
        self,
        clusters: List[KeywordCluster],
        min_cluster_size: int
    ) -> List[KeywordCluster]:
        """Merge overlapping clusters."""
        if not clusters:
            return []
        
        # Filter by minimum size
        filtered = [c for c in clusters if len(c.keywords) >= min_cluster_size]
        
        # Merge clusters with significant overlap
        merged = []
        processed_keywords = set()
        
        for cluster in filtered:
            # Check if cluster keywords are already in a merged cluster
            if any(kw in processed_keywords for kw in cluster.keywords):
                continue
            
            # Find clusters to merge with
            to_merge = [cluster]
            cluster_keywords = set(cluster.keywords)
            
            for other_cluster in filtered:
                if other_cluster == cluster:
                    continue
                
                other_keywords = set(other_cluster.keywords)
                overlap = len(cluster_keywords.intersection(other_keywords))
                
                # Merge if significant overlap
                if overlap > 0 and overlap / max(len(cluster_keywords), len(other_keywords)) > 0.3:
                    to_merge.append(other_cluster)
                    cluster_keywords.update(other_keywords)
            
            # Combine merged clusters
            if len(to_merge) > 1:
                all_keywords = []
                for c in to_merge:
                    all_keywords.extend(c.keywords)
                all_keywords = list(set(all_keywords))  # Remove duplicates
                
                parent_topic = self._extract_parent_topic_from_keyword_list(all_keywords)
                if not parent_topic:
                    parent_topic = to_merge[0].parent_topic
                
                merged.append(KeywordCluster(
                    parent_topic=parent_topic,
                    keywords=all_keywords,
                    cluster_score=max(c.cluster_score for c in to_merge),
                    dominant_words=self._get_most_common_words(all_keywords),
                    category_type=to_merge[0].category_type
                ))
            else:
                merged.append(cluster)
            
            processed_keywords.update(cluster_keywords)
        
        return merged
    
    def _extract_parent_topic_from_keyword_list(self, keywords: List[str]) -> Optional[str]:
        """Extract parent topic from a list of keywords."""
        if not keywords:
            return None
        
        # Find common words across all keywords
        all_words = []
        for kw in keywords:
            words = self._extract_meaningful_words(kw)
            all_words.extend(words)
        
        if not all_words:
            return None
        
        # Count word frequency
        word_counts = Counter(all_words)
        
        # Get most common words (excluding question/action words)
        meaningful_words = [
            word for word, count in word_counts.most_common(10)
            if word not in self.question_words
            and word not in self.action_words
            and count >= 2  # Must appear in at least 2 keywords
        ]
        
        if meaningful_words:
            # Use top 2-3 words as parent topic
            parent_words = meaningful_words[:3]
            return ' '.join(word.title() for word in parent_words)
        
        # Fallback: use most common word
        if word_counts:
            most_common = word_counts.most_common(1)[0][0]
            return most_common.title()
        
        return None
    
    def _extract_parent_topic_from_keyword(self, keyword: str) -> str:
        """Extract parent topic from a single keyword."""
        words = self._extract_meaningful_words(keyword)
        
        if not words:
            # Fallback: use first word
            first_word = keyword.split()[0] if keyword.split() else keyword
            return first_word.title()
        
        # Remove question/action words
        meaningful = [w for w in words if w not in self.question_words and w not in self.action_words]
        
        if meaningful:
            # Use first 2-3 meaningful words
            parent_words = meaningful[:3]
            return ' '.join(word.title() for word in parent_words)
        
        # Fallback: use first meaningful word
        return words[0].title() if words else keyword.title()
    
    def _extract_meaningful_words(self, keyword: str) -> List[str]:
        """Extract meaningful words from a keyword."""
        words = keyword.lower().split()
        meaningful = [
            w for w in words
            if w not in self.stop_words
            and len(w) >= 3  # At least 3 characters
        ]
        return meaningful
    
    def _extract_dominant_words(self, keyword: str) -> List[str]:
        """Extract dominant words from a keyword."""
        return self._extract_meaningful_words(keyword)[:3]
    
    def _get_most_common_words(self, keywords: List[str]) -> List[str]:
        """Get most common words across a list of keywords."""
        all_words = []
        for kw in keywords:
            all_words.extend(self._extract_meaningful_words(kw))
        
        word_counts = Counter(all_words)
        return [word for word, count in word_counts.most_common(5)]
    
    def _classify_keyword_type(self, keyword: str) -> str:
        """Classify keyword type."""
        words = keyword.lower().split()
        
        if words and words[0] in self.question_words:
            return "question"
        
        if any(word in self.action_words for word in words):
            return "action"
        
        # Check if it's an entity (proper noun, capitalized)
        if keyword and keyword[0].isupper():
            return "entity"
        
        return "topic"
    
    def _jaccard_similarity(self, set1: set, set2: set) -> float:
        """Calculate Jaccard similarity between two sets."""
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 0.0
        
        return intersection / union


def create_keyword_clustering(knowledge_graph_client=None) -> KeywordClustering:
    """Factory function to create KeywordClustering instance."""
    return KeywordClustering(knowledge_graph_client=knowledge_graph_client)

