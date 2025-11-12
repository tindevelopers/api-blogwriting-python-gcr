"""
Search Intent Analysis and Intent-Based Content Generation

Analyzes search intent and optimizes content generation accordingly.
"""

import logging
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class SearchIntent(str, Enum):
    """Search intent types."""
    INFORMATIONAL = "informational"  # How-to guides, explanations, tutorials
    NAVIGATIONAL = "navigational"    # Brand or site-specific queries
    COMMERCIAL = "commercial"        # Comparison, reviews, best-of lists
    TRANSACTIONAL = "transactional"  # Purchase intent, pricing information


@dataclass
class IntentAnalysis:
    """Search intent analysis result."""
    primary_intent: SearchIntent
    intent_probabilities: Dict[str, float]  # intent -> probability
    confidence: float  # 0-1
    recommendations: List[str]


class IntentAnalyzer:
    """Analyzes search intent and provides content generation recommendations."""
    
    def __init__(self, dataforseo_client=None):
        """
        Initialize intent analyzer.
        
        Args:
            dataforseo_client: DataForSEO client for intent analysis (optional)
        """
        self.dataforseo_client = dataforseo_client
    
    async def analyze_intent(
        self,
        keywords: List[str],
        language_code: str = "en"
    ) -> IntentAnalysis:
        """
        Analyze search intent for keywords.
        
        Args:
            keywords: Target keywords
            language_code: Language code
        
        Returns:
            IntentAnalysis with primary intent and recommendations
        """
        intent_probabilities = {}
        primary_intent = SearchIntent.INFORMATIONAL
        confidence = 0.5
        
        # Use DataForSEO if available
        if self.dataforseo_client:
            try:
                intent_data = await self.dataforseo_client.get_search_intent(
                    keywords=keywords,
                    language_code=language_code,
                    tenant_id="default"
                )
                
                # Parse intent data from DataForSEO response
                if isinstance(intent_data, dict) and "tasks" in intent_data:
                    for task in intent_data.get("tasks", []):
                        for item in task.get("result", []):
                            keyword_data = item.get("keyword_data", {})
                            intent_info = keyword_data.get("search_intent", {})
                            
                            if intent_info:
                                # Extract intent probabilities
                                for intent_type, prob in intent_info.items():
                                    if intent_type.lower() in ["informational", "navigational", "commercial", "transactional"]:
                                        intent_probabilities[intent_type.lower()] = prob
                                
                                # Find primary intent
                                if intent_probabilities:
                                    primary_intent_str = max(
                                        intent_probabilities.items(),
                                        key=lambda x: x[1]
                                    )[0]
                                    primary_intent = SearchIntent(primary_intent_str)
                                    confidence = intent_probabilities[primary_intent_str]
            except Exception as e:
                logger.warning(f"DataForSEO intent analysis failed: {e}")
        
        # Fallback: Analyze keywords for intent signals
        if not intent_probabilities:
            intent_probabilities = self._analyze_keyword_signals(keywords)
            primary_intent = max(intent_probabilities.items(), key=lambda x: x[1])[0]
            confidence = intent_probabilities[primary_intent]
        
        # Generate recommendations based on intent
        recommendations = self._get_intent_recommendations(primary_intent)
        
        return IntentAnalysis(
            primary_intent=primary_intent,
            intent_probabilities=intent_probabilities,
            confidence=confidence,
            recommendations=recommendations
        )
    
    def _analyze_keyword_signals(self, keywords: List[str]) -> Dict[str, float]:
        """Analyze keywords for intent signals (fallback method)."""
        keyword_text = " ".join(keywords).lower()
        
        # Intent signals
        informational_signals = [
            "how", "what", "why", "when", "where", "guide", "tutorial",
            "explain", "learn", "understand", "tips", "best practices"
        ]
        commercial_signals = [
            "best", "top", "review", "compare", "vs", "versus", "alternative",
            "cheap", "affordable", "price", "cost", "buy", "purchase"
        ]
        transactional_signals = [
            "buy", "purchase", "order", "price", "cost", "deal", "discount",
            "coupon", "sale", "shop", "store"
        ]
        navigational_signals = [
            "login", "sign in", "account", "official", "website", "site"
        ]
        
        # Count signals
        info_score = sum(1 for signal in informational_signals if signal in keyword_text)
        commercial_score = sum(1 for signal in commercial_signals if signal in keyword_text)
        transactional_score = sum(1 for signal in transactional_signals if signal in keyword_text)
        nav_score = sum(1 for signal in navigational_signals if signal in keyword_text)
        
        total_score = info_score + commercial_score + transactional_score + nav_score
        
        if total_score == 0:
            # Default to informational
            return {
                SearchIntent.INFORMATIONAL.value: 0.6,
                SearchIntent.COMMERCIAL.value: 0.2,
                SearchIntent.TRANSACTIONAL.value: 0.1,
                SearchIntent.NAVIGATIONAL.value: 0.1
            }
        
        return {
            SearchIntent.INFORMATIONAL.value: info_score / total_score,
            SearchIntent.COMMERCIAL.value: commercial_score / total_score,
            SearchIntent.TRANSACTIONAL.value: transactional_score / total_score,
            SearchIntent.NAVIGATIONAL.value: nav_score / total_score
        }
    
    def _get_intent_recommendations(self, intent: SearchIntent) -> List[str]:
        """Get content generation recommendations based on intent."""
        recommendations = {
            SearchIntent.INFORMATIONAL: [
                "Use step-by-step instructions",
                "Include definitions and explanations",
                "Add examples and use cases",
                "Create tutorial-style content",
                "Focus on education and learning"
            ],
            SearchIntent.COMMERCIAL: [
                "Include comparison tables",
                "List pros and cons",
                "Provide recommendations",
                "Include pricing information",
                "Focus on helping users make decisions"
            ],
            SearchIntent.TRANSACTIONAL: [
                "Include clear pricing",
                "Add purchase links or CTAs",
                "Highlight product features",
                "Include availability information",
                "Focus on conversion"
            ],
            SearchIntent.NAVIGATIONAL: [
                "Include brand name prominently",
                "Provide direct links",
                "Focus on specific site information",
                "Include login/access information",
                "Keep content concise and direct"
            ]
        }
        
        return recommendations.get(intent, recommendations[SearchIntent.INFORMATIONAL])
    
    def get_intent_optimized_template(self, intent: SearchIntent) -> str:
        """Get recommended prompt template for intent."""
        template_map = {
            SearchIntent.INFORMATIONAL: "how_to_guide",
            SearchIntent.COMMERCIAL: "comparison",
            SearchIntent.TRANSACTIONAL: "review",
            SearchIntent.NAVIGATIONAL: "expert_authority"
        }
        return template_map.get(intent, "expert_authority")

