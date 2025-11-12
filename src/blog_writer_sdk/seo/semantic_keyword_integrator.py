"""
Advanced Semantic Keyword Integration

Uses DataForSEO and semantic analysis to naturally integrate related keywords
and create topic clusters for better topical authority.
"""

import logging
from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


@dataclass
class KeywordCluster:
    """Keyword cluster for topic authority."""
    primary_keyword: str
    related_keywords: List[str]
    semantic_relationships: Dict[str, float]  # keyword -> similarity score
    usage_suggestions: Dict[str, str]  # keyword -> suggested usage context


@dataclass
class SemanticIntegrationResult:
    """Result of semantic keyword integration."""
    integrated_content: str
    keywords_used: List[str]
    keyword_clusters: List[KeywordCluster]
    integration_metadata: Dict[str, Any]


class SemanticKeywordIntegrator:
    """Integrates semantic keywords naturally into content."""
    
    def __init__(self, dataforseo_client=None):
        """
        Initialize semantic keyword integrator.
        
        Args:
            dataforseo_client: DataForSEO client for keyword data (optional)
        """
        self.dataforseo_client = dataforseo_client
    
    async def integrate_semantic_keywords(
        self,
        content: str,
        primary_keywords: List[str],
        max_related: int = 10
    ) -> SemanticIntegrationResult:
        """
        Integrate semantic keywords naturally into content.
        
        Args:
            content: Original content
            primary_keywords: Primary target keywords
            max_related: Maximum number of related keywords to integrate
        
        Returns:
            SemanticIntegrationResult with integrated content
        """
        # Get related keywords from DataForSEO if available
        related_keywords_map = {}
        if self.dataforseo_client and primary_keywords:
            try:
                for keyword in primary_keywords[:3]:  # Limit to top 3
                    related = await self._get_related_keywords(keyword, max_related)
                    related_keywords_map[keyword] = related
            except Exception as e:
                logger.warning(f"Failed to get related keywords from DataForSEO: {e}")
        
        # Create keyword clusters
        clusters = self._create_keyword_clusters(primary_keywords, related_keywords_map)
        
        # Analyze content for natural integration points
        integration_points = self._identify_integration_points(content, clusters)
        
        # Integrate keywords naturally
        integrated_content = self._integrate_keywords_naturally(
            content,
            integration_points,
            clusters
        )
        
        # Track which keywords were used
        keywords_used = self._extract_used_keywords(integrated_content, clusters)
        
        return SemanticIntegrationResult(
            integrated_content=integrated_content,
            keywords_used=keywords_used,
            keyword_clusters=clusters,
            integration_metadata={
                "integration_points": len(integration_points),
                "keywords_integrated": len(keywords_used),
                "natural_integration": True
            }
        )
    
    async def _get_related_keywords(
        self,
        keyword: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get related keywords from DataForSEO."""
        if not self.dataforseo_client:
            return []
        
        try:
            # Use DataForSEO related keywords endpoint
            result = await self.dataforseo_client.get_related_keywords(
                keyword=keyword,
                location="United States",
                language="en",
                limit=limit
            )
            
            # Extract keyword data
            related = []
            if isinstance(result, dict) and "tasks" in result:
                for task in result.get("tasks", []):
                    for item in task.get("result", []):
                        keyword_data = item.get("keyword_data", {})
                        keyword_info = keyword_data.get("keyword_info", {})
                        related.append({
                            "keyword": keyword_info.get("keyword", ""),
                            "search_volume": keyword_info.get("search_volume", 0),
                            "difficulty": keyword_info.get("keyword_difficulty", 0),
                            "cpc": keyword_info.get("cpc", 0)
                        })
            
            return related
        except Exception as e:
            logger.warning(f"DataForSEO related keywords failed: {e}")
            return []
    
    def _create_keyword_clusters(
        self,
        primary_keywords: List[str],
        related_keywords_map: Dict[str, List[Dict[str, Any]]]
    ) -> List[KeywordCluster]:
        """Create keyword clusters for semantic integration."""
        clusters = []
        
        for primary in primary_keywords:
            related = related_keywords_map.get(primary, [])
            related_keyword_list = [
                r.get("keyword", "") for r in related
                if r.get("keyword") and r.get("keyword") != primary
            ]
            
            # Calculate semantic relationships (simplified)
            relationships = {}
            for rel_keyword in related_keyword_list:
                # Simple similarity based on word overlap
                similarity = self._calculate_similarity(primary, rel_keyword)
                relationships[rel_keyword] = similarity
            
            # Sort by similarity
            sorted_related = sorted(
                related_keyword_list,
                key=lambda k: relationships.get(k, 0),
                reverse=True
            )
            
            # Generate usage suggestions
            usage_suggestions = {}
            for keyword in sorted_related[:5]:
                usage_suggestions[keyword] = self._suggest_usage_context(keyword, primary)
            
            clusters.append(KeywordCluster(
                primary_keyword=primary,
                related_keywords=sorted_related[:10],
                semantic_relationships=relationships,
                usage_suggestions=usage_suggestions
            ))
        
        return clusters
    
    def _calculate_similarity(self, keyword1: str, keyword2: str) -> float:
        """Calculate semantic similarity between keywords."""
        words1 = set(keyword1.lower().split())
        words2 = set(keyword2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _suggest_usage_context(
        self,
        keyword: str,
        primary_keyword: str
    ) -> str:
        """Suggest natural usage context for a keyword."""
        # Simple heuristics for usage suggestions
        if "how" in keyword.lower() or "what" in keyword.lower():
            return "Use in explanatory sections or FAQ"
        elif "best" in keyword.lower() or "top" in keyword.lower():
            return "Use in comparison or recommendation sections"
        elif "guide" in keyword.lower() or "tutorial" in keyword.lower():
            return "Use in instructional sections"
        else:
            return "Use naturally in relevant sections"
    
    def _identify_integration_points(
        self,
        content: str,
        clusters: List[KeywordCluster]
    ) -> List[Dict[str, Any]]:
        """Identify natural points in content for keyword integration."""
        integration_points = []
        
        # Split content into sentences
        sentences = re.split(r'[.!?]+\s+', content)
        
        for i, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()
            
            # Check if sentence could naturally include related keywords
            for cluster in clusters:
                for related_keyword in cluster.related_keywords[:5]:
                    related_lower = related_keyword.lower()
                    
                    # Check if related keyword is semantically relevant to sentence
                    if self._is_semantically_relevant(sentence, related_keyword, cluster.primary_keyword):
                        integration_points.append({
                            "position": i,
                            "sentence": sentence,
                            "keyword": related_keyword,
                            "cluster": cluster.primary_keyword,
                            "suggestion": cluster.usage_suggestions.get(related_keyword, "")
                        })
                        break  # One keyword per sentence max
        
        return integration_points
    
    def _is_semantically_relevant(
        self,
        sentence: str,
        keyword: str,
        primary_keyword: str
    ) -> bool:
        """Check if keyword is semantically relevant to sentence."""
        sentence_words = set(sentence.lower().split())
        keyword_words = set(keyword.lower().split())
        primary_words = set(primary_keyword.lower().split())
        
        # Check for word overlap
        keyword_overlap = len(sentence_words & keyword_words)
        primary_overlap = len(sentence_words & primary_words)
        
        # Relevant if there's some overlap with primary keyword
        return primary_overlap > 0 and keyword_overlap > 0
    
    def _integrate_keywords_naturally(
        self,
        content: str,
        integration_points: List[Dict[str, Any]],
        clusters: List[KeywordCluster]
    ) -> str:
        """Integrate keywords naturally into content."""
        if not integration_points:
            return content
        
        # Sort integration points by position (reverse for safe insertion)
        sorted_points = sorted(integration_points, key=lambda x: x["position"], reverse=True)
        
        result = content
        sentences = re.split(r'([.!?]+\s+)', result)
        
        for point in sorted_points[:10]:  # Limit integrations
            pos = point["position"]
            keyword = point["keyword"]
            
            if pos < len(sentences):
                sentence = sentences[pos]
                
                # Check if keyword already in sentence
                if keyword.lower() not in sentence.lower():
                    # Try to integrate naturally
                    integrated = self._natural_integration(sentence, keyword)
                    if integrated != sentence:
                        sentences[pos] = integrated
        
        return ''.join(sentences)
    
    def _natural_integration(self, sentence: str, keyword: str) -> str:
        """Integrate keyword naturally into sentence."""
        # Simple integration: add keyword in a natural way
        # In production, could use LLM for better integration
        
        # Try to add keyword after a relevant word
        words = sentence.split()
        keyword_words = keyword.split()
        
        # Find insertion point
        for i, word in enumerate(words):
            if len(keyword_words) == 1:
                # Single word keyword - add after relevant context
                if word.lower() in ["the", "a", "an", "this", "that"]:
                    if i + 1 < len(words):
                        words.insert(i + 1, keyword)
                        return ' '.join(words)
            else:
                # Multi-word keyword - try to find natural insertion
                if i < len(words) - 1:
                    # Check if we can replace or add
                    pass
        
        # Fallback: add at end before punctuation
        if sentence.rstrip()[-1] in '.!?':
            return sentence.rstrip()[:-1] + f" ({keyword})."
        return sentence
    
    def _extract_used_keywords(
        self,
        content: str,
        clusters: List[KeywordCluster]
    ) -> List[str]:
        """Extract which keywords were actually used in content."""
        content_lower = content.lower()
        used = []
        
        for cluster in clusters:
            if cluster.primary_keyword.lower() in content_lower:
                used.append(cluster.primary_keyword)
            
            for related in cluster.related_keywords:
                if related.lower() in content_lower:
                    used.append(related)
        
        return list(set(used))  # Remove duplicates

