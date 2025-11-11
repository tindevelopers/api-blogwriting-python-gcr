"""
Few-Shot Learning with Top-Ranking Content Examples

Fetches top-ranking content examples from SERP and uses them
to guide LLM output for better quality and ranking alignment.
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ContentExample:
    """Example content from top-ranking page."""
    title: str
    url: str
    snippet: str
    structure_elements: List[str]  # Headings, sections identified
    key_points: List[str]  # Main points extracted
    tone: str  # Detected tone


@dataclass
class FewShotContext:
    """Few-shot learning context."""
    examples: List[ContentExample]
    common_structure: List[str]
    common_themes: List[str]
    quality_patterns: List[str]


class FewShotLearningExtractor:
    """Extracts examples from top-ranking content for few-shot learning."""
    
    def __init__(self, google_search_client=None, dataforseo_client=None):
        """
        Initialize few-shot learning extractor.
        
        Args:
            google_search_client: Google Custom Search client (optional)
            dataforseo_client: DataForSEO client for SERP data (optional)
        """
        self.google_search = google_search_client
        self.dataforseo_client = dataforseo_client
    
    async def extract_top_ranking_examples(
        self,
        keyword: str,
        num_examples: int = 3,
        location: str = "United States",
        language: str = "en"
    ) -> FewShotContext:
        """
        Extract top-ranking content examples for few-shot learning.
        
        Args:
            keyword: Target keyword
            num_examples: Number of examples to extract
            location: Location for search
            language: Language code
        
        Returns:
            FewShotContext with examples and patterns
        """
        examples = []
        
        # Fetch top-ranking results
        if self.google_search:
            try:
                search_results = await self.google_search.search(
                    query=keyword,
                    num_results=num_examples * 2,  # Get more to filter
                    language=language,
                    country=location.split(",")[-1].strip() if "," in location else location
                )
                
                # Extract examples from top results
                for result in search_results[:num_examples]:
                    example = ContentExample(
                        title=result.get("title", ""),
                        url=result.get("link", ""),
                        snippet=result.get("snippet", ""),
                        structure_elements=self._extract_structure_hints(result.get("snippet", "")),
                        key_points=self._extract_key_points(result.get("snippet", "")),
                        tone=self._detect_tone(result.get("snippet", ""))
                    )
                    examples.append(example)
            except Exception as e:
                logger.warning(f"Failed to extract examples from Google Search: {e}")
        
        # Analyze common patterns
        common_structure = self._analyze_common_structure(examples)
        common_themes = self._analyze_common_themes(examples)
        quality_patterns = self._identify_quality_patterns(examples)
        
        return FewShotContext(
            examples=examples,
            common_structure=common_structure,
            common_themes=common_themes,
            quality_patterns=quality_patterns
        )
    
    def _extract_structure_hints(self, snippet: str) -> List[str]:
        """Extract structure hints from snippet."""
        hints = []
        
        # Look for list indicators
        if any(word in snippet.lower() for word in ["steps", "ways", "tips", "reasons"]):
            hints.append("list_format")
        
        # Look for question format
        if "?" in snippet:
            hints.append("question_based")
        
        # Look for comparison
        if any(word in snippet.lower() for word in ["vs", "versus", "compare", "better"]):
            hints.append("comparison_format")
        
        # Look for how-to
        if snippet.lower().startswith("how to") or "how to" in snippet.lower():
            hints.append("how_to_format")
        
        return hints
    
    def _extract_key_points(self, snippet: str) -> List[str]:
        """Extract key points from snippet."""
        # Simple extraction - split by sentences and take first few
        sentences = snippet.split('.')[:3]
        return [s.strip() for s in sentences if len(s.strip()) > 20]
    
    def _detect_tone(self, snippet: str) -> str:
        """Detect tone from snippet."""
        snippet_lower = snippet.lower()
        
        if any(word in snippet_lower for word in ["best", "top", "recommended"]):
            return "recommendatory"
        elif any(word in snippet_lower for word in ["guide", "tutorial", "learn"]):
            return "instructional"
        elif any(word in snippet_lower for word in ["review", "compare", "vs"]):
            return "comparative"
        else:
            return "informational"
    
    def _analyze_common_structure(self, examples: List[ContentExample]) -> List[str]:
        """Analyze common structure patterns across examples."""
        structure_counts = {}
        
        for example in examples:
            for structure in example.structure_elements:
                structure_counts[structure] = structure_counts.get(structure, 0) + 1
        
        # Return most common structures
        sorted_structures = sorted(
            structure_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [struct for struct, count in sorted_structures[:3]]
    
    def _analyze_common_themes(self, examples: List[ContentExample]) -> List[str]:
        """Analyze common themes across examples."""
        # Extract themes from key points
        all_points = []
        for example in examples:
            all_points.extend(example.key_points)
        
        # Simple theme extraction (could be enhanced)
        themes = []
        if len(all_points) > 0:
            # Look for common words
            word_counts = {}
            for point in all_points:
                words = point.lower().split()
                for word in words:
                    if len(word) > 4:  # Skip short words
                        word_counts[word] = word_counts.get(word, 0) + 1
            
            # Get top themes
            sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
            themes = [word for word, count in sorted_words[:5]]
        
        return themes
    
    def _identify_quality_patterns(self, examples: List[ContentExample]) -> List[str]:
        """Identify quality patterns from examples."""
        patterns = []
        
        # Check for specific patterns
        has_lists = any("list_format" in ex.structure_elements for ex in examples)
        has_questions = any("question_based" in ex.structure_elements for ex in examples)
        has_examples = any(len(ex.key_points) > 2 for ex in examples)
        
        if has_lists:
            patterns.append("Use bulleted or numbered lists")
        if has_questions:
            patterns.append("Include questions to engage readers")
        if has_examples:
            patterns.append("Provide specific examples and use cases")
        
        return patterns
    
    def build_few_shot_prompt_context(
        self,
        context: FewShotContext,
        max_examples: int = 3
    ) -> str:
        """
        Build few-shot learning context for prompts.
        
        Args:
            context: FewShotContext with examples
            max_examples: Maximum number of examples to include
        
        Returns:
            Formatted prompt context string
        """
        if not context.examples:
            return ""
        
        prompt_parts = ["\n\nTOP-RANKING CONTENT EXAMPLES (Learn from these successful patterns):\n"]
        
        for i, example in enumerate(context.examples[:max_examples], 1):
            prompt_parts.append(f"\nExample {i}:")
            prompt_parts.append(f"Title: {example.title}")
            prompt_parts.append(f"Key Points: {'; '.join(example.key_points[:2])}")
            prompt_parts.append(f"Structure: {', '.join(example.structure_elements)}")
            prompt_parts.append(f"Tone: {example.tone}")
        
        if context.common_structure:
            prompt_parts.append(f"\n\nCommon Structure Patterns: {', '.join(context.common_structure)}")
        
        if context.quality_patterns:
            prompt_parts.append(f"\nQuality Patterns to Emulate: {'; '.join(context.quality_patterns)}")
        
        prompt_parts.append("\n\nUse these examples as inspiration for structure, tone, and approach, but create original content that provides unique value.")
        
        return "\n".join(prompt_parts)

