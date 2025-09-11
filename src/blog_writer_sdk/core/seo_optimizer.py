"""
SEO optimization module for analyzing and improving content SEO.

This module provides comprehensive SEO analysis and optimization
without relying on external AI services.
"""

import re
import math
from typing import Dict, List, Optional, Tuple
from collections import Counter
from urllib.parse import urlparse

from ..models.blog_models import SEOMetrics, MetaTags


class SEOOptimizer:
    """
    Handles SEO analysis and optimization of blog content.
    
    This class provides comprehensive SEO analysis focusing on
    measurable metrics and best practices.
    """
    
    def __init__(self):
        """Initialize the SEO optimizer."""
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'would', 'you', 'your', 'have', 'had',
            'this', 'these', 'they', 'were', 'been', 'their', 'said', 'each',
            'which', 'she', 'do', 'how', 'if', 'not', 'we', 'what', 'up', 'out'
        }
        
        # SEO best practice ranges
        self.optimal_ranges = {
            'title_length': (30, 60),
            'meta_description_length': (120, 160),
            'keyword_density': (0.5, 2.5),  # Percentage
            'word_count_min': 300,
            'reading_time_max': 15,  # Minutes
        }
    
    async def analyze_seo(
        self,
        content: str,
        title: str,
        meta_tags: MetaTags,
        keywords: Optional[List[str]] = None,
        focus_keyword: Optional[str] = None,
    ) -> SEOMetrics:
        """
        Perform comprehensive SEO analysis of content.
        
        Args:
            content: Content to analyze
            title: Page title
            meta_tags: Meta tags object
            keywords: Target keywords
            focus_keyword: Primary focus keyword
            
        Returns:
            SEOMetrics object with all SEO metrics
        """
        # Clean content for analysis
        clean_content = self._clean_content(content)
        words = self._extract_words(clean_content)
        
        # Keyword analysis
        keyword_metrics = self._analyze_keywords(clean_content, keywords or [], focus_keyword)
        
        # Title analysis
        title_score = self._analyze_title(title, focus_keyword)
        
        # Meta description analysis
        meta_description_score = self._analyze_meta_description(meta_tags.description, focus_keyword)
        
        # Heading structure analysis
        heading_score = self._analyze_heading_structure(content, focus_keyword)
        
        # Technical metrics
        word_count = len(words)
        reading_time = self._calculate_reading_time(word_count)
        link_metrics = self._analyze_links(content)
        
        # Calculate overall scores
        overall_seo_score = self._calculate_overall_seo_score(
            keyword_metrics, title_score, meta_description_score, heading_score, word_count
        )
        content_quality_score = self._calculate_content_quality_score(
            word_count, heading_score, link_metrics
        )
        
        # Generate recommendations
        recommendations = self._generate_seo_recommendations(
            keyword_metrics, title_score, meta_description_score, heading_score, 
            word_count, link_metrics
        )
        
        # Generate warnings
        warnings = self._generate_seo_warnings(
            keyword_metrics, title_score, meta_description_score, word_count
        )
        
        return SEOMetrics(
            keyword_density=keyword_metrics['density'],
            keyword_frequency=keyword_metrics['frequency'],
            focus_keyword_score=keyword_metrics['focus_score'],
            title_seo_score=title_score,
            meta_description_score=meta_description_score,
            heading_structure_score=heading_score,
            word_count=word_count,
            reading_time_minutes=reading_time,
            internal_links_count=link_metrics['internal_links'],
            external_links_count=link_metrics['external_links'],
            overall_seo_score=overall_seo_score,
            content_quality_score=content_quality_score,
            recommendations=recommendations,
            warnings=warnings,
        )
    
    async def optimize_keyword_distribution(
        self,
        content: str,
        keywords: List[str],
        focus_keyword: Optional[str] = None,
    ) -> str:
        """
        Optimize keyword distribution in content.
        
        Args:
            content: Original content
            keywords: Target keywords
            focus_keyword: Primary focus keyword
            
        Returns:
            Optimized content with better keyword distribution
        """
        if not keywords:
            return content
        
        # Analyze current keyword usage
        clean_content = self._clean_content(content)
        current_metrics = self._analyze_keywords(clean_content, keywords, focus_keyword)
        
        optimized_content = content
        
        # Optimize focus keyword if provided
        if focus_keyword:
            focus_density = current_metrics['density'].get(focus_keyword, 0.0)
            if focus_density < 0.5:  # Too low
                optimized_content = self._increase_keyword_usage(
                    optimized_content, focus_keyword, target_density=1.0
                )
            elif focus_density > 3.0:  # Too high
                optimized_content = self._decrease_keyword_usage(
                    optimized_content, focus_keyword, target_density=2.0
                )
        
        # Optimize secondary keywords
        for keyword in keywords[:3]:  # Focus on top 3 keywords
            if keyword == focus_keyword:
                continue
            
            density = current_metrics['density'].get(keyword, 0.0)
            if density < 0.3:  # Too low for secondary keyword
                optimized_content = self._increase_keyword_usage(
                    optimized_content, keyword, target_density=0.5
                )
        
        return optimized_content
    
    async def add_internal_linking_suggestions(self, content: str) -> str:
        """
        Add internal linking suggestions to content.
        
        Args:
            content: Original content
            
        Returns:
            Content with internal linking suggestions as comments
        """
        # Find potential internal linking opportunities
        sentences = content.split('.')
        enhanced_content = []
        
        for sentence in sentences:
            enhanced_sentence = sentence
            
            # Look for key phrases that could benefit from internal links
            link_opportunities = self._identify_link_opportunities(sentence)
            
            if link_opportunities:
                # Add comment suggesting internal links
                for opportunity in link_opportunities:
                    comment = f"<!-- Consider adding internal link for '{opportunity}' -->"
                    enhanced_sentence += f" {comment}"
            
            enhanced_content.append(enhanced_sentence)
        
        return '.'.join(enhanced_content)
    
    async def optimize_heading_structure(self, content: str) -> str:
        """
        Optimize heading structure for better SEO.
        
        Args:
            content: Original content
            
        Returns:
            Content with optimized heading structure
        """
        lines = content.split('\n')
        optimized_lines = []
        current_h2_count = 0
        
        for line in lines:
            # Check if line is a heading
            if line.startswith('#'):
                heading_level = len(line) - len(line.lstrip('#'))
                heading_text = line.lstrip('#').strip()
                
                # Ensure proper heading hierarchy
                if heading_level == 1:
                    # H1 should be unique and at the top
                    optimized_lines.append(line)
                elif heading_level == 2:
                    # H2 headings should be well-distributed
                    current_h2_count += 1
                    optimized_lines.append(line)
                elif heading_level > 2:
                    # Ensure H3+ headings follow H2
                    if current_h2_count == 0:
                        # Convert to H2 if no H2 exists yet
                        optimized_lines.append(f"## {heading_text}")
                    else:
                        optimized_lines.append(line)
                else:
                    optimized_lines.append(line)
            else:
                optimized_lines.append(line)
        
        return '\n'.join(optimized_lines)
    
    def _clean_content(self, content: str) -> str:
        """Clean content for SEO analysis."""
        # Remove markdown formatting
        content = re.sub(r'#{1,6}\s+', '', content)
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
        content = re.sub(r'\*\*([^\*]+)\*\*', r'\1', content)
        content = re.sub(r'\*([^\*]+)\*', r'\1', content)
        
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        return content.strip()
    
    def _extract_words(self, content: str) -> List[str]:
        """Extract words from content."""
        words = re.findall(r'\b[a-zA-Z]+\b', content.lower())
        return words
    
    def _analyze_keywords(
        self, content: str, keywords: List[str], focus_keyword: Optional[str]
    ) -> Dict:
        """Analyze keyword usage in content."""
        words = self._extract_words(content)
        total_words = len(words)
        
        if total_words == 0:
            return {
                'density': {},
                'frequency': {},
                'focus_score': 0.0,
            }
        
        # Calculate keyword density and frequency
        density = {}
        frequency = {}
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            # Count exact matches and partial matches
            exact_count = content.lower().count(keyword_lower)
            word_count = words.count(keyword_lower)
            
            frequency[keyword] = max(exact_count, word_count)
            density[keyword] = (frequency[keyword] / total_words) * 100
        
        # Calculate focus keyword score
        focus_score = 0.0
        if focus_keyword:
            focus_density = density.get(focus_keyword, 0.0)
            
            # Optimal density is 1-2%
            if 1.0 <= focus_density <= 2.0:
                focus_score = 100.0
            elif 0.5 <= focus_density < 1.0:
                focus_score = 80.0
            elif 2.0 < focus_density <= 3.0:
                focus_score = 70.0
            elif focus_density > 0:
                focus_score = 50.0
            else:
                focus_score = 0.0
        
        return {
            'density': density,
            'frequency': frequency,
            'focus_score': focus_score,
        }
    
    def _analyze_title(self, title: str, focus_keyword: Optional[str]) -> float:
        """Analyze title for SEO optimization."""
        if not title:
            return 0.0
        
        score = 0.0
        
        # Length check (30-60 characters is optimal)
        title_length = len(title)
        if 30 <= title_length <= 60:
            score += 40.0
        elif 20 <= title_length < 30 or 60 < title_length <= 70:
            score += 25.0
        elif title_length > 0:
            score += 10.0
        
        # Focus keyword in title
        if focus_keyword and focus_keyword.lower() in title.lower():
            score += 40.0
            
            # Bonus for keyword at the beginning
            if title.lower().startswith(focus_keyword.lower()):
                score += 20.0
        
        return min(100.0, score)
    
    def _analyze_meta_description(self, description: str, focus_keyword: Optional[str]) -> float:
        """Analyze meta description for SEO optimization."""
        if not description:
            return 0.0
        
        score = 0.0
        
        # Length check (120-160 characters is optimal)
        desc_length = len(description)
        if 120 <= desc_length <= 160:
            score += 50.0
        elif 100 <= desc_length < 120 or 160 < desc_length <= 180:
            score += 30.0
        elif desc_length > 0:
            score += 15.0
        
        # Focus keyword in description
        if focus_keyword and focus_keyword.lower() in description.lower():
            score += 30.0
        
        # Call-to-action or engaging language
        engaging_words = ['discover', 'learn', 'find out', 'explore', 'get', 'start', 'try']
        if any(word in description.lower() for word in engaging_words):
            score += 20.0
        
        return min(100.0, score)
    
    def _analyze_heading_structure(self, content: str, focus_keyword: Optional[str]) -> float:
        """Analyze heading structure for SEO."""
        headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        
        if not headings:
            return 0.0
        
        score = 0.0
        h1_count = 0
        h2_count = 0
        
        for heading_level, heading_text in headings:
            level = len(heading_level)
            
            if level == 1:
                h1_count += 1
                score += 20.0  # H1 present
                
                # Focus keyword in H1
                if focus_keyword and focus_keyword.lower() in heading_text.lower():
                    score += 20.0
            elif level == 2:
                h2_count += 1
                score += 10.0  # H2 present
        
        # Penalize multiple H1s
        if h1_count > 1:
            score -= 20.0
        
        # Bonus for good H2 distribution
        if 2 <= h2_count <= 6:
            score += 20.0
        
        # Proper hierarchy bonus
        if h1_count == 1 and h2_count >= 2:
            score += 30.0
        
        return min(100.0, max(0.0, score))
    
    def _analyze_links(self, content: str) -> Dict[str, int]:
        """Analyze internal and external links."""
        # Find markdown links
        links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content)
        
        internal_links = 0
        external_links = 0
        
        for link_text, link_url in links:
            if link_url.startswith('http'):
                # External link
                external_links += 1
            elif link_url.startswith('/') or not link_url.startswith('http'):
                # Internal link (relative path)
                internal_links += 1
        
        return {
            'internal_links': internal_links,
            'external_links': external_links,
        }
    
    def _calculate_reading_time(self, word_count: int) -> float:
        """Calculate estimated reading time in minutes."""
        # Average reading speed is 200-250 words per minute
        return word_count / 225.0
    
    def _calculate_overall_seo_score(
        self,
        keyword_metrics: Dict,
        title_score: float,
        meta_description_score: float,
        heading_score: float,
        word_count: int,
    ) -> float:
        """Calculate overall SEO score."""
        # Weight different factors
        weights = {
            'keywords': 0.25,
            'title': 0.20,
            'meta_description': 0.15,
            'headings': 0.20,
            'content_length': 0.10,
            'structure': 0.10,
        }
        
        # Keyword score
        keyword_score = keyword_metrics['focus_score']
        
        # Content length score
        if word_count >= 300:
            length_score = min(100.0, (word_count / 1000) * 100)
        else:
            length_score = (word_count / 300) * 50
        
        # Structure score (basic)
        structure_score = 70.0  # Base score for having content
        
        # Calculate weighted average
        overall_score = (
            keyword_score * weights['keywords'] +
            title_score * weights['title'] +
            meta_description_score * weights['meta_description'] +
            heading_score * weights['headings'] +
            length_score * weights['content_length'] +
            structure_score * weights['structure']
        )
        
        return min(100.0, max(0.0, overall_score))
    
    def _calculate_content_quality_score(
        self, word_count: int, heading_score: float, link_metrics: Dict
    ) -> float:
        """Calculate content quality score."""
        score = 0.0
        
        # Word count scoring
        if word_count >= 1000:
            score += 40.0
        elif word_count >= 500:
            score += 30.0
        elif word_count >= 300:
            score += 20.0
        else:
            score += 10.0
        
        # Heading structure
        score += heading_score * 0.3
        
        # Link diversity
        total_links = link_metrics['internal_links'] + link_metrics['external_links']
        if total_links >= 3:
            score += 20.0
        elif total_links >= 1:
            score += 10.0
        
        # Internal vs external link balance
        if link_metrics['internal_links'] > 0 and link_metrics['external_links'] > 0:
            score += 10.0
        
        return min(100.0, score)
    
    def _generate_seo_recommendations(
        self,
        keyword_metrics: Dict,
        title_score: float,
        meta_description_score: float,
        heading_score: float,
        word_count: int,
        link_metrics: Dict,
    ) -> List[str]:
        """Generate SEO improvement recommendations."""
        recommendations = []
        
        # Keyword recommendations
        if keyword_metrics['focus_score'] < 50:
            recommendations.append("Improve focus keyword usage in content (aim for 1-2% density)")
        
        # Title recommendations
        if title_score < 70:
            recommendations.append("Optimize title length (30-60 characters) and include focus keyword")
        
        # Meta description recommendations
        if meta_description_score < 70:
            recommendations.append("Improve meta description (120-160 characters with focus keyword)")
        
        # Heading recommendations
        if heading_score < 70:
            recommendations.append("Improve heading structure with proper H1 and H2 tags")
        
        # Content length recommendations
        if word_count < 300:
            recommendations.append("Increase content length to at least 300 words for better SEO")
        elif word_count < 500:
            recommendations.append("Consider expanding content to 500+ words for better ranking potential")
        
        # Link recommendations
        if link_metrics['internal_links'] == 0:
            recommendations.append("Add internal links to related content")
        
        if link_metrics['external_links'] == 0:
            recommendations.append("Add authoritative external links to support your content")
        
        return recommendations
    
    def _generate_seo_warnings(
        self,
        keyword_metrics: Dict,
        title_score: float,
        meta_description_score: float,
        word_count: int,
    ) -> List[str]:
        """Generate SEO warnings for critical issues."""
        warnings = []
        
        # Critical keyword issues
        for keyword, density in keyword_metrics['density'].items():
            if density > 4.0:
                warnings.append(f"Keyword '{keyword}' density too high ({density:.1f}%) - risk of keyword stuffing")
        
        # Critical title issues
        if title_score == 0:
            warnings.append("Missing title - critical for SEO")
        
        # Critical meta description issues
        if meta_description_score == 0:
            warnings.append("Missing meta description - important for search results")
        
        # Critical content length issues
        if word_count < 100:
            warnings.append("Content too short - may not rank well in search results")
        
        return warnings
    
    def _increase_keyword_usage(self, content: str, keyword: str, target_density: float) -> str:
        """Increase keyword usage in content to reach target density."""
        # This is a simplified implementation
        # In practice, you'd want more sophisticated natural language processing
        
        words = content.split()
        current_count = content.lower().count(keyword.lower())
        target_count = int((len(words) * target_density) / 100)
        
        if target_count <= current_count:
            return content
        
        # Add keyword naturally in a few places
        additions_needed = target_count - current_count
        
        # Simple approach: add keyword in strategic locations
        sentences = content.split('.')
        if len(sentences) > additions_needed:
            for i in range(min(additions_needed, len(sentences) - 1)):
                # Add keyword naturally to sentence
                sentence_idx = i * (len(sentences) // additions_needed)
                if sentence_idx < len(sentences):
                    sentences[sentence_idx] += f" {keyword}"
        
        return '.'.join(sentences)
    
    def _decrease_keyword_usage(self, content: str, keyword: str, target_density: float) -> str:
        """Decrease keyword usage to avoid over-optimization."""
        # This would involve more sophisticated text processing
        # For now, return content as-is with a comment
        return content + f"\n<!-- Note: Consider reducing usage of '{keyword}' -->"
    
    def _identify_link_opportunities(self, sentence: str) -> List[str]:
        """Identify potential internal linking opportunities."""
        # Simple keyword-based approach
        link_opportunities = []
        
        # Common topics that could benefit from internal links
        topics = [
            'seo', 'content marketing', 'blog writing', 'keyword research',
            'social media', 'email marketing', 'analytics', 'conversion',
            'user experience', 'web design', 'mobile optimization'
        ]
        
        for topic in topics:
            if topic in sentence.lower():
                link_opportunities.append(topic)
        
        return link_opportunities
