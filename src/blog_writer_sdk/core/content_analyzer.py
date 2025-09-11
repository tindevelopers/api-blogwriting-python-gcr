"""
Content analysis module for evaluating content quality and readability.

This module provides comprehensive analysis of blog content including
readability metrics, structure analysis, and quality scoring.
"""

import re
import statistics
from typing import Dict, List, Tuple
from collections import Counter

try:
    import textstat
except ImportError:
    textstat = None

from ..models.blog_models import ContentQuality


class ContentAnalyzer:
    """
    Analyzes content for quality, readability, and structure.
    
    This class provides comprehensive content analysis without relying
    on external AI services, focusing on measurable metrics.
    """
    
    def __init__(self):
        """Initialize the content analyzer."""
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'would', 'you', 'your', 'have', 'had',
            'this', 'these', 'they', 'were', 'been', 'their', 'said', 'each',
            'which', 'she', 'do', 'how', 'if', 'not', 'we', 'what', 'up', 'out',
            'many', 'then', 'them', 'can', 'about', 'get', 'go', 'her', 'him',
            'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who',
            'boy', 'did', 'its', 'let', 'put', 'say', 'too', 'use'
        }
    
    async def analyze_quality(self, content: str) -> ContentQuality:
        """
        Perform comprehensive quality analysis of content.
        
        Args:
            content: Content to analyze
            
        Returns:
            ContentQuality object with all metrics
        """
        # Clean content for analysis
        clean_content = self._clean_content(content)
        
        # Basic metrics
        sentences = self._extract_sentences(clean_content)
        paragraphs = self._extract_paragraphs(clean_content)
        words = self._extract_words(clean_content)
        
        # Calculate readability metrics
        readability_metrics = self._calculate_readability_metrics(clean_content)
        
        # Structure analysis
        structure_metrics = self._analyze_structure(sentences, paragraphs, words)
        
        # Vocabulary analysis
        vocab_metrics = self._analyze_vocabulary(words)
        
        # Calculate scores
        readability_score = self._calculate_readability_score(readability_metrics)
        engagement_score = self._calculate_engagement_score(structure_metrics, vocab_metrics)
        
        # Generate suggestions
        readability_suggestions = self._generate_readability_suggestions(
            readability_metrics, structure_metrics
        )
        structure_suggestions = self._generate_structure_suggestions(
            structure_metrics, len(paragraphs)
        )
        
        return ContentQuality(
            # Readability metrics
            flesch_kincaid_grade=readability_metrics.get('flesch_kincaid_grade', 0.0),
            flesch_reading_ease=readability_metrics.get('flesch_reading_ease', 0.0),
            gunning_fog_index=readability_metrics.get('gunning_fog_index', 0.0),
            
            # Structure metrics
            sentence_count=len(sentences),
            paragraph_count=len(paragraphs),
            avg_sentence_length=structure_metrics['avg_sentence_length'],
            avg_paragraph_length=structure_metrics['avg_paragraph_length'],
            
            # Vocabulary metrics
            unique_words=vocab_metrics['unique_words'],
            vocabulary_diversity=vocab_metrics['vocabulary_diversity'],
            complex_words_ratio=vocab_metrics['complex_words_ratio'],
            
            # Scores
            readability_score=readability_score,
            engagement_score=engagement_score,
            
            # Suggestions
            readability_suggestions=readability_suggestions,
            structure_suggestions=structure_suggestions,
        )
    
    def _clean_content(self, content: str) -> str:
        """Clean content for analysis by removing markdown and HTML."""
        # Remove markdown headers
        content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)
        
        # Remove markdown links but keep text
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
        
        # Remove markdown emphasis
        content = re.sub(r'\*\*([^\*]+)\*\*', r'\1', content)
        content = re.sub(r'\*([^\*]+)\*', r'\1', content)
        content = re.sub(r'__([^_]+)__', r'\1', content)
        content = re.sub(r'_([^_]+)_', r'\1', content)
        
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Clean up extra whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = re.sub(r' +', ' ', content)
        
        return content.strip()
    
    def _extract_sentences(self, content: str) -> List[str]:
        """Extract sentences from content."""
        # Split on sentence endings
        sentences = re.split(r'[.!?]+', content)
        
        # Clean and filter sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Minimum sentence length
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def _extract_paragraphs(self, content: str) -> List[str]:
        """Extract paragraphs from content."""
        paragraphs = content.split('\n\n')
        
        # Filter out empty paragraphs
        return [p.strip() for p in paragraphs if p.strip() and len(p.strip()) > 20]
    
    def _extract_words(self, content: str) -> List[str]:
        """Extract words from content."""
        # Remove punctuation and split
        words = re.findall(r'\b[a-zA-Z]+\b', content.lower())
        return words
    
    def _calculate_readability_metrics(self, content: str) -> Dict[str, float]:
        """Calculate readability metrics using textstat if available."""
        metrics = {}
        
        if textstat:
            try:
                metrics['flesch_kincaid_grade'] = textstat.flesch_kincaid().grade(content)
                metrics['flesch_reading_ease'] = textstat.flesch_reading_ease(content)
                metrics['gunning_fog_index'] = textstat.gunning_fog(content)
            except Exception:
                # Fallback to manual calculation
                metrics = self._manual_readability_calculation(content)
        else:
            metrics = self._manual_readability_calculation(content)
        
        return metrics
    
    def _manual_readability_calculation(self, content: str) -> Dict[str, float]:
        """Manual readability calculation as fallback."""
        sentences = self._extract_sentences(content)
        words = self._extract_words(content)
        
        if not sentences or not words:
            return {'flesch_kincaid_grade': 0.0, 'flesch_reading_ease': 0.0, 'gunning_fog_index': 0.0}
        
        # Count syllables (approximation)
        total_syllables = sum(self._count_syllables(word) for word in words)
        
        # Calculate metrics
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables_per_word = total_syllables / len(words)
        
        # Flesch-Kincaid Grade Level
        fk_grade = 0.39 * avg_sentence_length + 11.8 * avg_syllables_per_word - 15.59
        
        # Flesch Reading Ease
        flesch_ease = 206.835 - 1.015 * avg_sentence_length - 84.6 * avg_syllables_per_word
        
        # Gunning Fog Index (simplified)
        complex_words = sum(1 for word in words if self._count_syllables(word) >= 3)
        complex_word_ratio = complex_words / len(words) if words else 0
        gunning_fog = 0.4 * (avg_sentence_length + 100 * complex_word_ratio)
        
        return {
            'flesch_kincaid_grade': max(0.0, fk_grade),
            'flesch_reading_ease': max(0.0, min(100.0, flesch_ease)),
            'gunning_fog_index': max(0.0, gunning_fog),
        }
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (approximation)."""
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel
        
        # Handle silent 'e'
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    def _analyze_structure(
        self, sentences: List[str], paragraphs: List[str], words: List[str]
    ) -> Dict[str, float]:
        """Analyze content structure metrics."""
        if not sentences or not paragraphs:
            return {
                'avg_sentence_length': 0.0,
                'avg_paragraph_length': 0.0,
                'sentence_length_variance': 0.0,
            }
        
        # Sentence length analysis
        sentence_lengths = [len(sentence.split()) for sentence in sentences]
        avg_sentence_length = statistics.mean(sentence_lengths)
        sentence_length_variance = statistics.variance(sentence_lengths) if len(sentence_lengths) > 1 else 0.0
        
        # Paragraph length analysis
        paragraph_lengths = [len(paragraph.split()) for paragraph in paragraphs]
        avg_paragraph_length = statistics.mean(paragraph_lengths)
        
        return {
            'avg_sentence_length': avg_sentence_length,
            'avg_paragraph_length': avg_paragraph_length,
            'sentence_length_variance': sentence_length_variance,
        }
    
    def _analyze_vocabulary(self, words: List[str]) -> Dict[str, float]:
        """Analyze vocabulary diversity and complexity."""
        if not words:
            return {
                'unique_words': 0,
                'vocabulary_diversity': 0.0,
                'complex_words_ratio': 0.0,
            }
        
        # Remove stop words for analysis
        content_words = [word for word in words if word not in self.stop_words]
        
        # Unique words
        unique_words = len(set(content_words))
        
        # Vocabulary diversity (Type-Token Ratio)
        vocabulary_diversity = unique_words / len(content_words) if content_words else 0.0
        
        # Complex words (3+ syllables)
        complex_words = sum(1 for word in words if self._count_syllables(word) >= 3)
        complex_words_ratio = complex_words / len(words)
        
        return {
            'unique_words': unique_words,
            'vocabulary_diversity': vocabulary_diversity,
            'complex_words_ratio': complex_words_ratio,
        }
    
    def _calculate_readability_score(self, readability_metrics: Dict[str, float]) -> float:
        """Calculate overall readability score (0-100)."""
        flesch_ease = readability_metrics.get('flesch_reading_ease', 50.0)
        fk_grade = readability_metrics.get('flesch_kincaid_grade', 10.0)
        gunning_fog = readability_metrics.get('gunning_fog_index', 12.0)
        
        # Normalize scores
        flesch_score = max(0, min(100, flesch_ease))
        
        # Grade level scoring (lower is better for readability)
        grade_score = max(0, 100 - (fk_grade * 5))  # Penalize high grade levels
        fog_score = max(0, 100 - (gunning_fog * 4))  # Penalize high fog index
        
        # Weighted average
        overall_score = (flesch_score * 0.5 + grade_score * 0.3 + fog_score * 0.2)
        
        return min(100.0, max(0.0, overall_score))
    
    def _calculate_engagement_score(
        self, structure_metrics: Dict[str, float], vocab_metrics: Dict[str, float]
    ) -> float:
        """Calculate content engagement score (0-100)."""
        # Sentence length scoring (15-20 words is optimal)
        avg_sentence_length = structure_metrics.get('avg_sentence_length', 15.0)
        sentence_score = max(0, 100 - abs(avg_sentence_length - 17.5) * 3)
        
        # Paragraph length scoring (50-100 words is optimal)
        avg_paragraph_length = structure_metrics.get('avg_paragraph_length', 75.0)
        paragraph_score = max(0, 100 - abs(avg_paragraph_length - 75) * 1)
        
        # Vocabulary diversity scoring
        vocab_diversity = vocab_metrics.get('vocabulary_diversity', 0.5)
        vocab_score = vocab_diversity * 100
        
        # Complex words balance (some complexity is good, too much is bad)
        complex_ratio = vocab_metrics.get('complex_words_ratio', 0.15)
        complexity_score = max(0, 100 - abs(complex_ratio - 0.15) * 300)
        
        # Weighted average
        engagement_score = (
            sentence_score * 0.3 +
            paragraph_score * 0.3 +
            vocab_score * 0.2 +
            complexity_score * 0.2
        )
        
        return min(100.0, max(0.0, engagement_score))
    
    def _generate_readability_suggestions(
        self, readability_metrics: Dict[str, float], structure_metrics: Dict[str, float]
    ) -> List[str]:
        """Generate readability improvement suggestions."""
        suggestions = []
        
        # Flesch Reading Ease suggestions
        flesch_ease = readability_metrics.get('flesch_reading_ease', 50.0)
        if flesch_ease < 30:
            suggestions.append("Content is very difficult to read. Consider shorter sentences and simpler words.")
        elif flesch_ease < 50:
            suggestions.append("Content is fairly difficult to read. Try using shorter sentences and more common words.")
        
        # Grade level suggestions
        fk_grade = readability_metrics.get('flesch_kincaid_grade', 10.0)
        if fk_grade > 12:
            suggestions.append("Content requires college-level reading. Consider simplifying for broader audience.")
        elif fk_grade > 9:
            suggestions.append("Content is at high school level. Consider simplifying for general audience.")
        
        # Sentence length suggestions
        avg_sentence_length = structure_metrics.get('avg_sentence_length', 15.0)
        if avg_sentence_length > 25:
            suggestions.append("Sentences are too long. Aim for 15-20 words per sentence.")
        elif avg_sentence_length < 10:
            suggestions.append("Sentences are very short. Consider combining some for better flow.")
        
        return suggestions
    
    def _generate_structure_suggestions(
        self, structure_metrics: Dict[str, float], paragraph_count: int
    ) -> List[str]:
        """Generate structure improvement suggestions."""
        suggestions = []
        
        # Paragraph length suggestions
        avg_paragraph_length = structure_metrics.get('avg_paragraph_length', 75.0)
        if avg_paragraph_length > 150:
            suggestions.append("Paragraphs are too long. Break them into smaller chunks for better readability.")
        elif avg_paragraph_length < 30:
            suggestions.append("Paragraphs are very short. Consider combining related ideas.")
        
        # Paragraph count suggestions
        if paragraph_count < 3:
            suggestions.append("Content needs more paragraphs for better structure and readability.")
        elif paragraph_count > 20:
            suggestions.append("Consider organizing content with subheadings to improve structure.")
        
        # Sentence variety suggestions
        sentence_variance = structure_metrics.get('sentence_length_variance', 0.0)
        if sentence_variance < 5:
            suggestions.append("Add variety to sentence lengths for better flow and engagement.")
        
        return suggestions
