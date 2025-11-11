"""
Comprehensive Content Quality Scoring

Provides automated quality scoring across multiple dimensions:
readability, SEO, factual accuracy, structure, and uniqueness.
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from .readability_analyzer import ReadabilityAnalyzer, ReadabilityMetrics


class QualityDimension(str, Enum):
    """Quality scoring dimensions."""
    READABILITY = "readability"
    SEO = "seo"
    STRUCTURE = "structure"
    FACTUAL = "factual"
    UNIQUENESS = "uniqueness"
    ENGAGEMENT = "engagement"


@dataclass
class QualityScore:
    """Quality score for a specific dimension."""
    dimension: QualityDimension
    score: float  # 0-100
    weight: float  # 0-1, importance weight
    issues: List[str]
    recommendations: List[str]


@dataclass
class ContentQualityReport:
    """Comprehensive quality report."""
    overall_score: float  # 0-100
    dimension_scores: Dict[str, QualityScore]
    passed_threshold: bool
    critical_issues: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any]


class ContentQualityScorer:
    """Scores content quality across multiple dimensions."""
    
    def __init__(
        self,
        readability_analyzer: Optional[ReadabilityAnalyzer] = None,
        quality_threshold: float = 70.0
    ):
        """
        Initialize quality scorer.
        
        Args:
            readability_analyzer: Readability analyzer instance
            quality_threshold: Minimum quality score threshold
        """
        self.readability_analyzer = readability_analyzer or ReadabilityAnalyzer()
        self.quality_threshold = quality_threshold
        
        # Dimension weights (sum to 1.0)
        self.dimension_weights = {
            QualityDimension.READABILITY: 0.20,
            QualityDimension.SEO: 0.25,
            QualityDimension.STRUCTURE: 0.20,
            QualityDimension.FACTUAL: 0.15,
            QualityDimension.UNIQUENESS: 0.10,
            QualityDimension.ENGAGEMENT: 0.10
        }
    
    def score_content(
        self,
        content: str,
        title: str = "",
        keywords: List[str] = None,
        meta_description: str = "",
        citations: List[Dict[str, str]] = None
    ) -> ContentQualityReport:
        """
        Score content quality across all dimensions.
        
        Args:
            content: Content to score
            title: Content title
            keywords: Target keywords
            meta_description: Meta description
            citations: List of citations
        
        Returns:
            ContentQualityReport with comprehensive scores
        """
        keywords = keywords or []
        citations = citations or []
        
        # Score each dimension
        dimension_scores = {}
        
        # Readability score
        readability_score = self._score_readability(content)
        dimension_scores[QualityDimension.READABILITY.value] = readability_score
        
        # SEO score
        seo_score = self._score_seo(content, title, keywords, meta_description)
        dimension_scores[QualityDimension.SEO.value] = seo_score
        
        # Structure score
        structure_score = self._score_structure(content, title)
        dimension_scores[QualityDimension.STRUCTURE.value] = structure_score
        
        # Factual score
        factual_score = self._score_factual(content, citations)
        dimension_scores[QualityDimension.FACTUAL.value] = factual_score
        
        # Uniqueness score (simplified - would need comparison in production)
        uniqueness_score = self._score_uniqueness(content)
        dimension_scores[QualityDimension.UNIQUENESS.value] = uniqueness_score
        
        # Engagement score
        engagement_score = self._score_engagement(content)
        dimension_scores[QualityDimension.ENGAGEMENT.value] = engagement_score
        
        # Calculate weighted overall score
        overall_score = sum(
            score.score * self.dimension_weights.get(
                QualityDimension(score.dimension), 0
            )
            for score in dimension_scores.values()
        )
        
        # Collect all issues and recommendations
        all_issues = []
        all_recommendations = []
        critical_issues = []
        
        for score in dimension_scores.values():
            all_issues.extend(score.issues)
            all_recommendations.extend(score.recommendations)
            if score.score < 50:  # Critical if below 50
                critical_issues.extend(score.issues[:2])  # Top 2 issues
        
        return ContentQualityReport(
            overall_score=round(overall_score, 2),
            dimension_scores=dimension_scores,
            passed_threshold=overall_score >= self.quality_threshold,
            critical_issues=critical_issues[:5],  # Top 5 critical issues
            recommendations=list(set(all_recommendations))[:10],  # Unique, top 10
            metadata={
                "word_count": len(content.split()),
                "citation_count": len(citations),
                "keyword_count": len(keywords),
                "has_title": bool(title),
                "has_meta_description": bool(meta_description)
            }
        )
    
    def _score_readability(self, content: str) -> QualityScore:
        """Score readability dimension."""
        metrics = self.readability_analyzer.analyze(content)
        issues = self.readability_analyzer.identify_issues(content, metrics)
        
        # Score based on Flesch Reading Ease
        # Target: 60-70 (8th-9th grade)
        reading_ease = metrics.flesch_reading_ease
        
        if reading_ease >= 60:
            score = 100
        elif reading_ease >= 50:
            score = 80
        elif reading_ease >= 40:
            score = 60
        else:
            score = 40
        
        # Penalize for issues
        score -= len(issues.issues) * 5
        score = max(0, min(100, score))
        
        return QualityScore(
            dimension=QualityDimension.READABILITY,
            score=score,
            weight=self.dimension_weights[QualityDimension.READABILITY],
            issues=issues.issues,
            recommendations=issues.recommendations
        )
    
    def _score_seo(
        self,
        content: str,
        title: str,
        keywords: List[str],
        meta_description: str
    ) -> QualityScore:
        """Score SEO dimension."""
        issues = []
        recommendations = []
        score = 100
        
        # Title optimization
        if not title:
            issues.append("Missing title")
            score -= 20
        elif len(title) < 30 or len(title) > 60:
            issues.append(f"Title length ({len(title)} chars) not optimal (30-60)")
            score -= 10
            recommendations.append("Optimize title length to 30-60 characters")
        
        # Meta description
        if not meta_description:
            issues.append("Missing meta description")
            score -= 15
        elif len(meta_description) < 120 or len(meta_description) > 160:
            issues.append(f"Meta description length ({len(meta_description)} chars) not optimal (120-160)")
            score -= 10
            recommendations.append("Optimize meta description length to 120-160 characters")
        
        # Keyword optimization
        if keywords:
            primary_keyword = keywords[0].lower()
            content_lower = content.lower()
            
            # Check keyword density (target: 1-2%)
            keyword_count = content_lower.count(primary_keyword)
            word_count = len(content.split())
            density = (keyword_count / word_count * 100) if word_count > 0 else 0
            
            if density < 0.5:
                issues.append(f"Primary keyword density too low ({density:.2f}%)")
                score -= 15
                recommendations.append("Increase primary keyword usage naturally")
            elif density > 3:
                issues.append(f"Primary keyword density too high ({density:.2f}%) - keyword stuffing")
                score -= 20
                recommendations.append("Reduce keyword density to avoid stuffing")
            
            # Check keyword in title
            if primary_keyword not in title.lower():
                issues.append("Primary keyword not in title")
                score -= 10
                recommendations.append("Include primary keyword in title")
        
        # Heading structure
        h1_count = len(re.findall(r'<h1|^#\s+', content, re.MULTILINE))
        h2_count = len(re.findall(r'<h2|^##\s+', content, re.MULTILINE))
        
        if h1_count == 0:
            issues.append("Missing H1 heading")
            score -= 10
        if h2_count < 3:
            issues.append(f"Insufficient H2 headings ({h2_count})")
            score -= 10
            recommendations.append("Add more H2 headings for better structure")
        
        score = max(0, min(100, score))
        
        return QualityScore(
            dimension=QualityDimension.SEO,
            score=score,
            weight=self.dimension_weights[QualityDimension.SEO],
            issues=issues,
            recommendations=recommendations
        )
    
    def _score_structure(self, content: str, title: str) -> QualityScore:
        """Score content structure."""
        issues = []
        recommendations = []
        score = 100
        
        # Paragraph length
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        avg_para_length = sum(len(p.split('.')) for p in paragraphs) / len(paragraphs) if paragraphs else 0
        
        if avg_para_length > 4:
            issues.append(f"Average paragraph length ({avg_para_length:.1f} sentences) exceeds target (3-4)")
            score -= 15
            recommendations.append("Break long paragraphs into shorter ones")
        
        # List usage
        list_count = len(re.findall(r'<[uo]l>|^[\*\-\+]', content, re.MULTILINE))
        word_count = len(content.split())
        
        if word_count > 500 and list_count == 0:
            issues.append("No lists found in content")
            score -= 10
            recommendations.append("Add bulleted or numbered lists for scannability")
        
        # Heading hierarchy
        headings = re.findall(r'<h([1-6])|^(#{1,6})\s+', content, re.MULTILINE)
        if headings:
            heading_levels = [int(h[0] if h[0] else len(h[1])) for h in headings]
            # Check for proper hierarchy
            if heading_levels and heading_levels[0] != 1:
                issues.append("First heading should be H1")
                score -= 10
        
        score = max(0, min(100, score))
        
        return QualityScore(
            dimension=QualityDimension.STRUCTURE,
            score=score,
            weight=self.dimension_weights[QualityDimension.STRUCTURE],
            issues=issues,
            recommendations=recommendations
        )
    
    def _score_factual(self, content: str, citations: List[Dict[str, str]]) -> QualityScore:
        """Score factual accuracy."""
        issues = []
        recommendations = []
        score = 100
        
        # Check for citations
        if len(citations) == 0:
            issues.append("No citations or sources provided")
            score -= 20
            recommendations.append("Add citations to support factual claims")
        elif len(citations) < 3:
            issues.append(f"Few citations ({len(citations)}) for content length")
            score -= 10
            recommendations.append("Add more citations to support claims")
        
        # Check for factual claims (simple heuristic)
        factual_indicators = [
            "according to", "research shows", "studies indicate",
            "data suggests", "statistics show", "reports indicate"
        ]
        
        factual_claims = sum(1 for indicator in factual_indicators if indicator in content.lower())
        
        if factual_claims > len(citations):
            issues.append(f"More factual claims ({factual_claims}) than citations ({len(citations)})")
            score -= 15
            recommendations.append("Add citations for all factual claims")
        
        score = max(0, min(100, score))
        
        return QualityScore(
            dimension=QualityDimension.FACTUAL,
            score=score,
            weight=self.dimension_weights[QualityDimension.FACTUAL],
            issues=issues,
            recommendations=recommendations
        )
    
    def _score_uniqueness(self, content: str) -> QualityScore:
        """Score content uniqueness (simplified)."""
        # In production, would compare against existing content
        # For now, use heuristics
        
        issues = []
        recommendations = []
        score = 80  # Default assumption
        
        # Check for generic phrases
        generic_phrases = [
            "in today's world", "it is important to", "as we all know",
            "in conclusion", "last but not least"
        ]
        
        generic_count = sum(1 for phrase in generic_phrases if phrase in content.lower())
        if generic_count > 3:
            issues.append("Too many generic phrases detected")
            score -= 15
            recommendations.append("Replace generic phrases with specific, unique content")
        
        # Check for repetition
        sentences = content.split('.')
        unique_sentences = len(set(s.strip().lower() for s in sentences))
        repetition_ratio = unique_sentences / len(sentences) if sentences else 1.0
        
        if repetition_ratio < 0.8:
            issues.append("High sentence repetition detected")
            score -= 20
            recommendations.append("Reduce repetitive content")
        
        score = max(0, min(100, score))
        
        return QualityScore(
            dimension=QualityDimension.UNIQUENESS,
            score=score,
            weight=self.dimension_weights[QualityDimension.UNIQUENESS],
            issues=issues,
            recommendations=recommendations
        )
    
    def _score_engagement(self, content: str) -> QualityScore:
        """Score engagement potential."""
        issues = []
        recommendations = []
        score = 100
        
        # Check for questions
        question_count = len(re.findall(r'\?', content))
        if question_count == 0:
            issues.append("No questions to engage readers")
            score -= 10
            recommendations.append("Add rhetorical questions to engage readers")
        
        # Check for call-to-action
        cta_indicators = [
            "learn more", "get started", "try now", "discover",
            "explore", "find out", "check out"
        ]
        
        has_cta = any(indicator in content.lower() for indicator in cta_indicators)
        if not has_cta:
            issues.append("No call-to-action found")
            score -= 10
            recommendations.append("Add a call-to-action to guide readers")
        
        # Check for examples
        example_indicators = ["for example", "for instance", "such as", "like"]
        example_count = sum(1 for indicator in example_indicators if indicator in content.lower())
        
        if example_count < 2:
            issues.append("Insufficient examples")
            score -= 10
            recommendations.append("Add more examples to illustrate points")
        
        score = max(0, min(100, score))
        
        return QualityScore(
            dimension=QualityDimension.ENGAGEMENT,
            score=score,
            weight=self.dimension_weights[QualityDimension.ENGAGEMENT],
            issues=issues,
            recommendations=recommendations
        )

