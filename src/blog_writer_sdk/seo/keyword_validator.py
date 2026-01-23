"""
Keyword Validator Module

Validates keyword suggestions for semantic relevance, logical sense, and context awareness.
Filters out nonsensical combinations like "online parking garage waterproofing".
"""

import logging
import re
from typing import Dict, List, Optional, Any, Set, Tuple
from ..ai.base_provider import AIRequest, AIGenerationConfig, ContentType

logger = logging.getLogger(__name__)


class KeywordValidator:
    """
    Validates keyword suggestions for semantic relevance and logical sense.
    
    Filters out nonsensical combinations and ensures keywords make logical sense
    in the context of the seed keyword and service type.
    """
    
    def __init__(self, ai_generator=None):
        """
        Initialize keyword validator.
        
        Args:
            ai_generator: Optional AI generator for semantic validation
        """
        self.ai_generator = ai_generator
        
        # Context-aware invalid patterns
        self.invalid_patterns = {
            "physical_services": {
                "prefixes": ["online", "virtual", "digital", "app", "software", "web", "internet"],
                "suffixes": ["online", "virtual", "digital"],
                "keywords": ["waterproofing", "construction", "repair", "installation", 
                            "painting", "plumbing", "electrical", "roofing", "concrete",
                            "masonry", "carpentry", "flooring", "tiling", "landscaping"],
                "reason": "Physical services cannot be done online"
            },
            "location_services": {
                "prefixes": ["online", "virtual"],
                "suffixes": ["online", "virtual"],
                "keywords": ["near me", "local", "in person", "on site"],
                "reason": "Location-based services require physical presence"
            }
        }
        
        # Nonsensical modifier combinations
        self.nonsensical_modifiers = {
            "free": ["paid", "premium", "expensive", "cost"],
            "online": ["in-person", "local", "near me", "on site"],
            "learn": ["buy", "purchase", "hire", "contractor"],
            "virtual": ["physical", "in person", "on site"],
            "digital": ["physical", "concrete", "material"]
        }
        
        # Common low-quality prefixes that often create nonsensical combinations
        self.low_quality_prefixes = {
            "online", "virtual", "digital", "free", "learn", "study", 
            "download", "software", "app", "web", "internet"
        }
        
        # Service type detection patterns
        self.service_patterns = {
            "physical_service": [
                r"\b(waterproofing|construction|repair|installation|painting|plumbing|"
                r"electrical|roofing|concrete|masonry|carpentry|flooring|tiling|"
                r"landscaping|renovation|remodeling|maintenance|service|contractor)\b"
            ],
            "location_service": [
                r"\b(near me|local|in person|on site|at home|at office)\b"
            ]
        }
    
    def detect_service_type(self, keyword: str) -> Optional[str]:
        """
        Detect service type from keyword to apply appropriate validation rules.
        
        Args:
            keyword: Keyword to analyze
            
        Returns:
            Service type string or None
        """
        keyword_lower = keyword.lower()
        
        # Check for physical service keywords
        for pattern in self.service_patterns["physical_service"]:
            if re.search(pattern, keyword_lower, re.IGNORECASE):
                return "physical_service"
        
        # Check for location service keywords
        for pattern in self.service_patterns["location_service"]:
            if re.search(pattern, keyword_lower, re.IGNORECASE):
                return "location_service"
        
        return None
    
    def _has_invalid_pattern(self, keyword: str, seed_keyword: str) -> Tuple[bool, str]:
        """
        Check for invalid patterns based on context.
        
        Returns:
            (is_invalid, reason)
        """
        keyword_lower = keyword.lower()
        seed_lower = seed_keyword.lower()
        
        # Detect service type from seed keyword
        service_type = self.detect_service_type(seed_keyword)
        
        if service_type == "physical_service":
            # Check for physical service invalid patterns
            for prefix in self.invalid_patterns["physical_services"]["prefixes"]:
                if keyword_lower.startswith(prefix + " ") or f" {prefix} " in keyword_lower:
                    return True, f"'{prefix}' doesn't make sense for physical services"
            
            for suffix in self.invalid_patterns["physical_services"]["suffixes"]:
                if keyword_lower.endswith(" " + suffix) or f" {suffix}" in keyword_lower:
                    return True, f"'{suffix}' doesn't make sense for physical services"
        
        # Check for location service patterns
        if service_type == "location_service":
            for prefix in self.invalid_patterns["location_services"]["prefixes"]:
                if keyword_lower.startswith(prefix + " ") or f" {prefix} " in keyword_lower:
                    return True, f"'{prefix}' doesn't make sense for location-based services"
        
        return False, ""
    
    def _has_nonsensical_combination(self, keyword: str) -> Tuple[bool, str]:
        """
        Check for nonsensical modifier combinations.
        
        Returns:
            (is_nonsensical, reason)
        """
        keyword_lower = keyword.lower()
        words = set(keyword_lower.split())
        
        # Check for conflicting modifiers
        for modifier, conflicts in self.nonsensical_modifiers.items():
            if modifier in words:
                for conflict in conflicts:
                    if conflict in words:
                        return True, f"Conflicting modifiers: '{modifier}' and '{conflict}'"
        
        return False, ""
    
    def _has_low_quality_prefix(self, keyword: str, seed_keyword: str) -> Tuple[bool, str]:
        """
        Check if keyword has low-quality prefix that creates nonsensical combination.
        
        Returns:
            (is_low_quality, reason)
        """
        keyword_lower = keyword.lower()
        seed_lower = seed_keyword.lower()
        
        # Check if keyword just adds a low-quality prefix to seed
        for prefix in self.low_quality_prefixes:
            # Check if keyword is just "prefix + seed_keyword"
            if keyword_lower.startswith(prefix + " ") and keyword_lower.endswith(seed_lower):
                # Check if it's a physical service
                if self.detect_service_type(seed_keyword) == "physical_service":
                    return True, f"Low-quality prefix '{prefix}' added to physical service keyword"
        
        return False, ""
    
    async def _check_semantic_relevance(
        self,
        keyword: str,
        seed_keyword: str
    ) -> float:
        """
        Check semantic relevance using AI or similarity scoring.
        
        Returns:
            Relevance score (0.0 to 1.0)
        """
        if self.ai_generator:
            # Use AI to check if keyword makes sense
            prompt = f"""Does this keyword make logical sense in relation to the seed keyword?

Seed Keyword: {seed_keyword}
Suggested Keyword: {keyword}

Consider:
1. Does the suggested keyword make logical sense?
2. Is it semantically related to the seed keyword?
3. Would someone actually search for this combination?

Respond with ONLY a number between 0.0 and 1.0 representing relevance (1.0 = perfect match, 0.0 = nonsensical).

Examples:
- "parking garage waterproofing" + "free parking garage waterproofing" = 0.3 (free doesn't make sense for waterproofing)
- "parking garage waterproofing" + "parking garage waterproofing cost" = 0.9 (cost is relevant)
- "parking garage waterproofing" + "online parking garage waterproofing" = 0.1 (online doesn't make sense for physical service)
- "parking garage waterproofing" + "parking garage waterproofing membrane" = 0.95 (highly relevant)

Number only:"""

            try:
                # Use AI to validate
                response = await self.ai_generator.provider_manager.generate_content(
                    AIRequest(
                        prompt=prompt,
                        content_type=ContentType.TEXT,
                        config=AIGenerationConfig(max_tokens=10, temperature=0.1)
                    )
                )
                
                # Extract number from response
                content = response.content.strip()
                # Remove any non-numeric characters except decimal point
                content = re.sub(r'[^\d.]', '', content)
                
                if content:
                    score = float(content)
                    return max(0.0, min(1.0, score))
            except Exception as e:
                logger.debug(f"AI semantic check failed: {e}, using fallback")
        
        # Fallback: Simple word overlap similarity
        seed_words = set(seed_keyword.lower().split())
        keyword_words = set(keyword.lower().split())
        
        if not seed_words:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(seed_words.intersection(keyword_words))
        union = len(seed_words.union(keyword_words))
        
        if union == 0:
            return 0.0
        
        similarity = intersection / union
        
        # Penalize if keyword has many extra words that aren't in seed
        extra_words = keyword_words - seed_words
        if len(extra_words) > 3:  # Too many extra words might indicate low relevance
            similarity *= 0.7
        
        return similarity
    
    async def validate_keyword(
        self,
        keyword: str,
        seed_keyword: str,
        search_volume: int = 0,
        min_search_volume: int = 10,
        min_semantic_score: float = 0.3
    ) -> Dict[str, Any]:
        """
        Validate a keyword suggestion.
        
        Args:
            keyword: Keyword to validate
            seed_keyword: Original seed keyword
            search_volume: Search volume for the keyword
            min_search_volume: Minimum search volume threshold
            min_semantic_score: Minimum semantic relevance score (0.0-1.0)
            
        Returns:
            {
                "valid": bool,
                "reason": str,
                "confidence": float,
                "search_volume": int,
                "issues": List[str]
            }
        """
        issues = []
        
        # Check 1: Basic format
        if not keyword or len(keyword.strip()) < 3:
            return {
                "valid": False,
                "reason": "Too short or empty",
                "confidence": 0.0,
                "search_volume": search_volume,
                "issues": ["Keyword too short"]
            }
        
        keyword = keyword.strip()
        
        # Check 2: Invalid patterns for physical services
        is_invalid, invalid_reason = self._has_invalid_pattern(keyword, seed_keyword)
        if is_invalid:
            issues.append(invalid_reason)
            return {
                "valid": False,
                "reason": invalid_reason,
                "confidence": 0.0,
                "search_volume": search_volume,
                "issues": issues
            }
        
        # Check 3: Nonsensical modifier combinations
        is_nonsensical, nonsensical_reason = self._has_nonsensical_combination(keyword)
        if is_nonsensical:
            issues.append(nonsensical_reason)
            return {
                "valid": False,
                "reason": nonsensical_reason,
                "confidence": 0.1,
                "search_volume": search_volume,
                "issues": issues
            }
        
        # Check 4: Low-quality prefix
        is_low_quality, quality_reason = self._has_low_quality_prefix(keyword, seed_keyword)
        if is_low_quality:
            issues.append(quality_reason)
            # Don't reject immediately, but lower confidence
            min_semantic_score = max(min_semantic_score, 0.5)  # Require higher semantic score
        
        # Check 5: Minimum search volume
        if search_volume < min_search_volume:
            issues.append(f"Search volume {search_volume} below minimum {min_search_volume}")
            # Don't reject based on volume alone, but note it
        
        # Check 6: Semantic relevance
        semantic_score = await self._check_semantic_relevance(keyword, seed_keyword)
        if semantic_score < min_semantic_score:
            issues.append(f"Low semantic relevance: {semantic_score:.2f} < {min_semantic_score}")
            return {
                "valid": False,
                "reason": f"Low semantic relevance (score: {semantic_score:.2f})",
                "confidence": semantic_score,
                "search_volume": search_volume,
                "issues": issues
            }
        
        # All checks passed
        return {
            "valid": True,
            "reason": "Passed all validation checks",
            "confidence": semantic_score,
            "search_volume": search_volume,
            "issues": issues if issues else []
        }
    
    def filter_keywords(
        self,
        keywords: List[Dict[str, Any]],
        seed_keyword: str,
        min_search_volume: int = 10,
        min_semantic_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Filter a list of keyword suggestions synchronously (without AI).
        
        This is a faster, non-AI version for bulk filtering.
        
        Args:
            keywords: List of keyword dicts with 'keyword' and optionally 'search_volume'
            seed_keyword: Seed keyword
            min_search_volume: Minimum search volume
            min_semantic_score: Minimum semantic score (not used in sync version)
            
        Returns:
            Filtered list of valid keywords
        """
        valid_keywords = []
        
        for kw_data in keywords:
            if isinstance(kw_data, dict):
                keyword = kw_data.get("keyword", "")
                search_volume = kw_data.get("search_volume", 0)
            else:
                keyword = str(kw_data)
                search_volume = 0
            
            if not keyword:
                continue
            
            # Quick validation (synchronous checks only)
            is_invalid, _ = self._has_invalid_pattern(keyword, seed_keyword)
            if is_invalid:
                continue
            
            is_nonsensical, _ = self._has_nonsensical_combination(keyword)
            if is_nonsensical:
                continue
            
            is_low_quality, _ = self._has_low_quality_prefix(keyword, seed_keyword)
            if is_low_quality:
                continue
            
            # Check search volume
            if search_volume < min_search_volume:
                continue
            
            # Basic word overlap check
            seed_words = set(seed_keyword.lower().split())
            keyword_words = set(keyword.lower().split())
            overlap = len(seed_words.intersection(keyword_words))
            
            if overlap < len(seed_words) * 0.5:  # At least 50% word overlap
                continue
            
            valid_keywords.append(kw_data)
        
        return valid_keywords
