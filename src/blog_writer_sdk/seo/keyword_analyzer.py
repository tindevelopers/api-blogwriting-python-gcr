"""
Keyword analysis module for SEO research and optimization.

This module provides keyword analysis capabilities without relying
on external paid APIs, focusing on content-based analysis.
"""

import re
import math
from typing import Dict, List, Optional, Tuple
from collections import Counter

try:
    import yake
except ImportError:
    yake = None

from ..models.blog_models import KeywordAnalysis, SEODifficulty


class KeywordAnalyzer:
    """
    Analyzes keywords for SEO potential and competition.
    
    This class provides keyword analysis using content-based methods
    and statistical analysis rather than external APIs.
    """
    
    def __init__(self):
        """Initialize the keyword analyzer."""
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'would', 'you', 'your', 'have', 'had',
            'this', 'these', 'they', 'were', 'been', 'their', 'said', 'each',
            'which', 'she', 'do', 'how', 'if', 'not', 'we', 'what', 'up', 'out'
        }
    
    async def analyze_keyword(self, keyword: str) -> KeywordAnalysis:
        """
        Analyze a single keyword for SEO potential.
        
        Args:
            keyword: Keyword to analyze
            
        Returns:
            KeywordAnalysis object with metrics
        """
        # Basic keyword metrics
        word_count = len(keyword.split())
        character_count = len(keyword)
        
        # Estimate difficulty based on keyword characteristics
        difficulty = self._estimate_keyword_difficulty(keyword)
        
        # Generate related keywords
        related_keywords = self._generate_related_keywords(keyword)
        long_tail_keywords = self._generate_long_tail_keywords(keyword)
        
        # Calculate competition score (simplified)
        competition_score = self._calculate_competition_score(keyword)
        
        # Determine if keyword is recommended
        recommended, reason = self._evaluate_keyword_recommendation(
            keyword, difficulty, competition_score
        )
        
        return KeywordAnalysis(
            keyword=keyword,
            search_volume=None,  # Would require external API
            difficulty=difficulty,
            competition=competition_score,
            related_keywords=related_keywords,
            long_tail_keywords=long_tail_keywords,
            cpc=None,  # Would require external API
            trend_score=0.0,  # Would require historical data
            recommended=recommended,
            reason=reason,
        )
    
    async def extract_keywords_from_content(
        self,
        content: str,
        max_keywords: int = 20,
        max_ngram: int = 3,
        dedup_lim: float = 0.7
    ) -> List[str]:
        """
        Extract potential keywords from content.
        
        Args:
            content: Content to extract keywords from
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of extracted keywords
        """
        if yake:
            return self._extract_with_yake(content, max_keywords, max_ngram, dedup_lim)
        else:
            return self._extract_with_frequency(content, max_keywords)
    
    async def analyze_keyword_density(
        self, content: str, keywords: List[str]
    ) -> Dict[str, float]:
        """
        Analyze keyword density in content.
        
        Args:
            content: Content to analyze
            keywords: Keywords to check density for
            
        Returns:
            Dictionary mapping keywords to density percentages
        """
        # Clean content
        clean_content = self._clean_content(content)
        words = clean_content.lower().split()
        total_words = len(words)
        
        if total_words == 0:
            return {keyword: 0.0 for keyword in keywords}
        
        density_map = {}
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # Count exact phrase matches
            phrase_count = clean_content.lower().count(keyword_lower)
            
            # Count individual word matches if multi-word keyword
            keyword_words = keyword_lower.split()
            if len(keyword_words) > 1:
                # For multi-word keywords, count phrase occurrences
                density = (phrase_count / total_words) * 100
            else:
                # For single words, count word occurrences
                word_count = words.count(keyword_lower)
                density = (word_count / total_words) * 100
            
            density_map[keyword] = density
        
        return density_map
    
    async def suggest_keyword_variations(self, keyword: str, limit: int = 150) -> List[str]:
        """
        Suggest keyword variations and synonyms.
        
        Args:
            keyword: Base keyword
            limit: Maximum number of variations to return (default: 150)
            
        Returns:
            List of keyword variations (up to limit)
        """
        variations = []
        
        # Add plural/singular variations
        if keyword.endswith('s'):
            variations.append(keyword[:-1])  # Remove 's'
        else:
            variations.append(keyword + 's')  # Add 's'
        
        # Extended prefixes for comprehensive coverage
        prefixes = [
            'best', 'top', 'how to', 'what is', 'guide to', 'ultimate', 'complete',
            'professional', 'affordable', 'cheap', 'expensive', 'free', 'paid',
            'online', 'local', 'near me', 'nearby', 'in', 'for', 'with', 'without',
            'beginner', 'advanced', 'expert', 'essential', 'latest', 'new', 'popular',
            'trending', '2024', '2025', 'review', 'reviews', 'comparison', 'vs',
            'alternatives', 'buy', 'find', 'get', 'learn', 'discover', 'explore'
        ]
        
        # Extended suffixes
        suffixes = [
            'guide', 'tips', 'tutorial', 'examples', 'benefits', 'services',
            'company', 'provider', 'business', 'center', 'clinic', 'hospital',
            'near me', 'local', 'nearby', 'online', 'reviews', 'prices', 'cost',
            'costs', 'pricing', 'plans', 'options', 'solutions', 'software', 'tools'
        ]
        
        # Add prefix variations
        for prefix in prefixes:
            if len(variations) >= limit:
                break
            variations.append(f"{prefix} {keyword}")
        
        # Add suffix variations
        for suffix in suffixes:
            if len(variations) >= limit:
                break
            variations.append(f"{keyword} {suffix}")
        
        # Add question variations
        question_starters = ['how to', 'what is', 'why', 'when', 'where', 'who', 'which', 'can', 'should', 'will']
        for starter in question_starters:
            if len(variations) >= limit:
                break
            if starter not in keyword.lower():
                variations.append(f"{starter} {keyword}")
        
        # Add location-based variations
        locations = ['near me', 'local', 'nearby', 'in', 'for']
        for location in locations:
            if len(variations) >= limit:
                break
            variations.append(f"{keyword} {location}")
        
        # Remove duplicates and return up to limit
        unique_variations = list(dict.fromkeys(variations))  # Preserves order while removing duplicates
        return unique_variations[:limit]
    
    async def analyze_competitor_keywords(self, competitor_content: str) -> List[str]:
        """
        Analyze competitor content to extract potential keywords.
        
        Args:
            competitor_content: Competitor's content
            
        Returns:
            List of potential keywords found in competitor content
        """
        return await self.extract_keywords_from_content(competitor_content, max_keywords=30)
    
    def _estimate_keyword_difficulty(self, keyword: str) -> SEODifficulty:
        """
        Estimate keyword difficulty based on characteristics.
        
        This is a simplified estimation based on keyword structure
        and common patterns, not actual SERP analysis.
        """
        word_count = len(keyword.split())
        character_count = len(keyword)
        
        # Single word keywords are typically harder
        if word_count == 1:
            if character_count <= 4:
                return SEODifficulty.VERY_HARD  # Short, generic words
            elif character_count <= 8:
                return SEODifficulty.HARD
            else:
                return SEODifficulty.MEDIUM
        
        # Long-tail keywords (3+ words) are typically easier
        elif word_count >= 3:
            if word_count >= 5:
                return SEODifficulty.VERY_EASY  # Very specific long-tail
            else:
                return SEODifficulty.EASY
        
        # Two-word keywords are medium difficulty
        else:
            return SEODifficulty.MEDIUM
    
    def _generate_related_keywords(self, keyword: str) -> List[str]:
        """Generate related keywords based on the input keyword."""
        related = []
        
        # Add variations with common modifiers
        modifiers = [
            'best', 'top', 'free', 'online', 'professional', 'advanced',
            'beginner', 'complete', 'ultimate', 'essential'
        ]
        
        for modifier in modifiers[:5]:  # Limit to 5 modifiers
            related.append(f"{modifier} {keyword}")
        
        # Add action-based variations
        actions = ['learn', 'understand', 'master', 'improve', 'optimize']
        for action in actions[:3]:  # Limit to 3 actions
            related.append(f"{action} {keyword}")
        
        return related
    
    def _generate_long_tail_keywords(self, keyword: str) -> List[str]:
        """Generate long-tail keyword variations."""
        long_tail = []
        
        # Question-based long-tail keywords
        questions = [
            f"how to use {keyword}",
            f"what is {keyword}",
            f"why {keyword} is important",
            f"benefits of {keyword}",
            f"{keyword} for beginners",
        ]
        
        long_tail.extend(questions)
        
        # Problem-solving long-tail keywords
        problems = [
            f"{keyword} problems",
            f"{keyword} challenges",
            f"{keyword} solutions",
            f"common {keyword} mistakes",
        ]
        
        long_tail.extend(problems[:2])  # Limit to 2 problem keywords
        
        return long_tail
    
    def _calculate_competition_score(self, keyword: str) -> float:
        """
        Calculate a simplified competition score.
        
        This is based on keyword characteristics, not actual competition data.
        """
        word_count = len(keyword.split())
        
        # More words generally mean less competition
        if word_count == 1:
            return 0.8  # High competition for single words
        elif word_count == 2:
            return 0.6  # Medium-high competition
        elif word_count == 3:
            return 0.4  # Medium competition
        else:
            return 0.2  # Low competition for long-tail
    
    def _evaluate_keyword_recommendation(
        self, keyword: str, difficulty: SEODifficulty, competition: float
    ) -> Tuple[bool, str]:
        """Evaluate whether a keyword is recommended."""
        word_count = len(keyword.split())
        
        # Recommend long-tail keywords
        if word_count >= 3:
            return True, "Long-tail keyword with good potential"
        
        # Recommend medium difficulty keywords
        if difficulty in [SEODifficulty.EASY, SEODifficulty.MEDIUM]:
            return True, "Good balance of difficulty and potential"
        
        # Don't recommend very hard keywords for most users
        if difficulty == SEODifficulty.VERY_HARD:
            return False, "Very competitive keyword - consider alternatives"
        
        # Default recommendation
        return True, "Suitable keyword for targeting"
    
    def _clean_content(self, content: str) -> str:
        """Clean content for keyword analysis."""
        # Remove markdown formatting
        content = re.sub(r'#{1,6}\s+', '', content)
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
        content = re.sub(r'\*\*([^\*]+)\*\*', r'\1', content)
        content = re.sub(r'\*([^\*]+)\*', r'\1', content)
        
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Clean up whitespace
        content = re.sub(r'\s+', ' ', content)
        
        return content.strip()
    
    def _extract_with_yake(self, content: str, max_keywords: int, max_ngram: int, dedup_lim: float) -> List[str]:
        """Extract keywords using YAKE library."""
        try:
            # Configure YAKE
            kw_extractor = yake.KeywordExtractor(
                lan="en",
                n=max_ngram,  # Maximum number of words in keyphrase
                dedupLim=dedup_lim,  # Deduplication threshold
                top=max_keywords,  # Number of keywords to extract
            )
            
            # Extract keywords
            keywords = kw_extractor.extract_keywords(content)
            
            # Return just the keyword strings (not scores)
            return [keyword[1] for keyword in keywords]
            
        except Exception:
            # Fallback to frequency-based extraction
            return self._extract_with_frequency(content, max_keywords)
    
    def _extract_with_frequency(self, content: str, max_keywords: int) -> List[str]:
        """Extract keywords using frequency analysis."""
        # Clean content
        clean_content = self._clean_content(content).lower()
        
        # Extract words and phrases
        words = re.findall(r'\b[a-zA-Z]+\b', clean_content)
        
        # Filter out stop words and short words
        filtered_words = [
            word for word in words 
            if len(word) >= 3 and word not in self.stop_words
        ]
        
        # Count frequency
        word_counts = Counter(filtered_words)
        
        # Get most common words
        common_words = word_counts.most_common(max_keywords)
        
        # Extract 2-word phrases
        phrases = []
        for i in range(len(filtered_words) - 1):
            phrase = f"{filtered_words[i]} {filtered_words[i + 1]}"
            phrases.append(phrase)
        
        phrase_counts = Counter(phrases)
        common_phrases = phrase_counts.most_common(max_keywords // 2)
        
        # Combine words and phrases
        keywords = []
        
        # Add single words
        for word, count in common_words[:max_keywords // 2]:
            if count >= 2:  # Only include words that appear at least twice
                keywords.append(word)
        
        # Add phrases
        for phrase, count in common_phrases:
            if count >= 2:  # Only include phrases that appear at least twice
                keywords.append(phrase)
        
        return keywords[:max_keywords]
