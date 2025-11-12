"""
Content Readability Analysis and Optimization

Analyzes and optimizes content for readability using various metrics.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ReadabilityMetrics:
    """Readability metrics for content."""
    flesch_reading_ease: float
    average_sentence_length: float
    average_words_per_sentence: float
    average_syllables_per_word: float
    paragraph_count: int
    average_paragraph_length: float
    heading_count: int
    list_count: int
    grade_level: float


@dataclass
class ReadabilityIssues:
    """Identified readability issues."""
    issues: List[str]
    recommendations: List[str]
    score: float  # 0-100, higher is better


class ReadabilityAnalyzer:
    """Analyzes and optimizes content readability."""
    
    def __init__(self):
        """Initialize readability analyzer."""
        self.target_reading_ease = 60.0  # 8th-9th grade level
        self.max_sentence_length = 20  # words
        self.max_paragraph_length = 4  # sentences
        self.min_heading_frequency = 300  # words per heading
    
    def analyze(self, content: str) -> ReadabilityMetrics:
        """
        Analyze content readability.
        
        Args:
            content: Content to analyze
        
        Returns:
            ReadabilityMetrics object
        """
        # Extract text content (remove HTML if present)
        text = self._extract_text(content)
        
        # Count sentences
        sentences = self._split_sentences(text)
        sentence_count = len(sentences)
        
        # Count words
        words = self._split_words(text)
        word_count = len(words)
        
        # Count syllables
        total_syllables = sum(self._count_syllables(word) for word in words)
        
        # Count paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)
        
        # Count headings
        heading_count = len(re.findall(r'<h[1-6]|^#+\s', content, re.MULTILINE))
        
        # Count lists
        list_count = len(re.findall(r'<[uo]l>|^[\*\-\+]', content, re.MULTILINE))
        
        # Calculate metrics
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        avg_words_per_sentence = avg_sentence_length
        avg_syllables_per_word = total_syllables / word_count if word_count > 0 else 0
        avg_paragraph_length = sentence_count / paragraph_count if paragraph_count > 0 else 0
        
        # Calculate Flesch Reading Ease
        flesch_reading_ease = self._calculate_flesch_reading_ease(
            avg_sentence_length,
            avg_syllables_per_word
        )
        
        # Calculate grade level
        grade_level = self._calculate_grade_level(flesch_reading_ease)
        
        return ReadabilityMetrics(
            flesch_reading_ease=flesch_reading_ease,
            average_sentence_length=avg_sentence_length,
            average_words_per_sentence=avg_words_per_sentence,
            average_syllables_per_word=avg_syllables_per_word,
            paragraph_count=paragraph_count,
            average_paragraph_length=avg_paragraph_length,
            heading_count=heading_count,
            list_count=list_count,
            grade_level=grade_level
        )
    
    def identify_issues(self, content: str, metrics: Optional[ReadabilityMetrics] = None) -> ReadabilityIssues:
        """
        Identify readability issues and provide recommendations.
        
        Args:
            content: Content to analyze
            metrics: Pre-calculated metrics (optional)
        
        Returns:
            ReadabilityIssues object
        """
        if metrics is None:
            metrics = self.analyze(content)
        
        issues = []
        recommendations = []
        score = 100.0
        
        # Check Flesch Reading Ease
        if metrics.flesch_reading_ease < self.target_reading_ease:
            diff = self.target_reading_ease - metrics.flesch_reading_ease
            issues.append(f"Reading ease ({metrics.flesch_reading_ease:.1f}) is below target ({self.target_reading_ease})")
            recommendations.append("Simplify sentence structure and use shorter words")
            score -= min(20, diff / 2)
        
        # Check sentence length
        if metrics.average_words_per_sentence > self.max_sentence_length:
            issues.append(f"Average sentence length ({metrics.average_words_per_sentence:.1f} words) exceeds target ({self.max_sentence_length})")
            recommendations.append("Break long sentences into shorter ones")
            score -= 15
        
        # Check paragraph length
        if metrics.average_paragraph_length > self.max_paragraph_length:
            issues.append(f"Average paragraph length ({metrics.average_paragraph_length:.1f} sentences) exceeds target ({self.max_paragraph_length})")
            recommendations.append("Split long paragraphs into shorter ones (3-4 sentences max)")
            score -= 10
        
        # Check heading frequency
        word_count = len(self._split_words(self._extract_text(content)))
        headings_per_300_words = (metrics.heading_count / word_count) * 300 if word_count > 0 else 0
        if headings_per_300_words < 1:
            issues.append("Insufficient headings for content length")
            recommendations.append("Add more H2/H3 headings to improve scannability")
            score -= 10
        
        # Check list usage
        if metrics.list_count == 0 and word_count > 500:
            issues.append("No lists found in content")
            recommendations.append("Add bulleted or numbered lists to improve scannability")
            score -= 5
        
        # Check paragraph count
        if metrics.paragraph_count < 5 and word_count > 1000:
            issues.append("Too few paragraphs for content length")
            recommendations.append("Break content into more paragraphs")
            score -= 5
        
        return ReadabilityIssues(
            issues=issues,
            recommendations=recommendations,
            score=max(0, score)
        )
    
    def optimize_content(
        self,
        content: str,
        target_reading_ease: Optional[float] = None
    ) -> Tuple[str, List[str]]:
        """
        Optimize content for readability.
        
        Args:
            content: Content to optimize
            target_reading_ease: Target reading ease score
        
        Returns:
            Tuple of (optimized_content, changes_made)
        """
        if target_reading_ease is None:
            target_reading_ease = self.target_reading_ease
        
        metrics = self.analyze(content)
        issues = self.identify_issues(content, metrics)
        
        optimized = content
        changes = []
        
        # Split long sentences
        if metrics.average_words_per_sentence > self.max_sentence_length:
            optimized = self._split_long_sentences(optimized)
            changes.append("Split long sentences into shorter ones")
        
        # Split long paragraphs
        if metrics.average_paragraph_length > self.max_paragraph_length:
            optimized = self._split_long_paragraphs(optimized)
            changes.append("Split long paragraphs into shorter ones")
        
        return optimized, changes
    
    def _extract_text(self, content: str) -> str:
        """Extract plain text from HTML/Markdown content."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', content)
        # Remove markdown headers
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        # Remove markdown links
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # Remove markdown formatting
        text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^\*]+)\*', r'\1', text)
        return text.strip()
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting (can be improved)
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _split_words(self, text: str) -> List[str]:
        """Split text into words."""
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        return words
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (approximation)."""
        word = word.lower()
        if len(word) <= 3:
            return 1
        
        vowels = 'aeiouy'
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel
        
        # Handle silent e
        if word.endswith('e'):
            syllable_count -= 1
        
        # Minimum 1 syllable
        return max(1, syllable_count)
    
    def _calculate_flesch_reading_ease(
        self,
        avg_sentence_length: float,
        avg_syllables_per_word: float
    ) -> float:
        """Calculate Flesch Reading Ease score."""
        # Flesch Reading Ease formula
        score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        return max(0, min(100, score))
    
    def _calculate_grade_level(self, flesch_reading_ease: float) -> float:
        """Calculate approximate grade level from Flesch Reading Ease."""
        if flesch_reading_ease >= 90:
            return 5.0
        elif flesch_reading_ease >= 80:
            return 6.0
        elif flesch_reading_ease >= 70:
            return 7.0
        elif flesch_reading_ease >= 60:
            return 8.0
        elif flesch_reading_ease >= 50:
            return 9.0
        elif flesch_reading_ease >= 30:
            return 10.0
        else:
            return 12.0
    
    def _split_long_sentences(self, content: str) -> str:
        """Split long sentences into shorter ones."""
        sentences = self._split_sentences(self._extract_text(content))
        optimized_sentences = []
        
        for sentence in sentences:
            words = sentence.split()
            if len(words) > self.max_sentence_length:
                # Split at conjunctions or commas
                parts = re.split(r'[,;]\s+|and\s+|or\s+|but\s+', sentence)
                optimized_sentences.extend(parts)
            else:
                optimized_sentences.append(sentence)
        
        return '. '.join(optimized_sentences) + '.'
    
    def _split_long_paragraphs(self, content: str) -> str:
        """Split long paragraphs into shorter ones."""
        paragraphs = content.split('\n\n')
        optimized_paragraphs = []
        
        for para in paragraphs:
            sentences = self._split_sentences(self._extract_text(para))
            if len(sentences) > self.max_paragraph_length:
                # Split into chunks
                chunk_size = self.max_paragraph_length
                for i in range(0, len(sentences), chunk_size):
                    chunk = sentences[i:i + chunk_size]
                    optimized_paragraphs.append(' '.join(chunk))
            else:
                optimized_paragraphs.append(para)
        
        return '\n\n'.join(optimized_paragraphs)

