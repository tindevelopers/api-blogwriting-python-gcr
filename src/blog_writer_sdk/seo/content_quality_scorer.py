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
    EEAT = "eeat"  # Experience, Expertise, Authoritativeness, Trustworthiness
    ACCESSIBILITY = "accessibility"  # WCAG compliance


@dataclass
class QualityScore:
    """Quality score for a specific dimension."""
    dimension: QualityDimension
    score: float  # 0-100
    weight: float  # 0-1, importance weight
    issues: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any] = None  # Optional metadata (e.g., E-E-A-T breakdown)
    
    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}


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
            QualityDimension.READABILITY: 0.12,
            QualityDimension.SEO: 0.18,
            QualityDimension.STRUCTURE: 0.15,
            QualityDimension.FACTUAL: 0.15,
            QualityDimension.UNIQUENESS: 0.10,
            QualityDimension.ENGAGEMENT: 0.10,
            QualityDimension.EEAT: 0.12,  # E-E-A-T scoring
            QualityDimension.ACCESSIBILITY: 0.08  # Accessibility scoring
        }
    
    def score_content(
        self,
        content: str,
        title: str = "",
        keywords: List[str] = None,
        meta_description: str = "",
        citations: List[Dict[str, str]] = None,
        include_eeat: bool = True
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
        
        # E-E-A-T score
        eeat_score = self._score_eeat(content, citations, title, keywords, include_eeat=include_eeat)
        dimension_scores[QualityDimension.EEAT.value] = eeat_score
        
        # Accessibility score
        accessibility_score = self._score_accessibility(content)
        dimension_scores[QualityDimension.ACCESSIBILITY.value] = accessibility_score
        
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
        """
        Score content structure with detailed recommendations.
        
        Enhanced to provide:
        - Specific heading recommendations
        - Image placement suggestions
        - CTA placement optimization
        - Internal linking structure
        """
        issues = []
        recommendations = []
        score = 100
        structure_metadata = {
            "recommended_headings": [],
            "image_recommendations": [],
            "cta_placements": [],
            "internal_links": []
        }
        
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
        
        # Heading hierarchy and recommendations
        headings = re.findall(r'<h([1-6])|^(#{1,6})\s+', content, re.MULTILINE)
        heading_positions = []
        
        if headings:
            heading_levels = [int(h[0] if h[0] else len(h[1])) for h in headings]
            
            # Check for proper hierarchy
            if heading_levels and heading_levels[0] != 1:
                issues.append("First heading should be H1")
                score -= 10
                structure_metadata["recommended_headings"].append({
                    "level": 1,
                    "position": 0,
                    "suggested_text": title or "Main Heading",
                    "reason": "First heading should be H1"
                })
            
            # Recommend H2 headings at optimal positions
            # Optimal: H2 every 300-500 words
            optimal_h2_positions = list(range(300, word_count, 400))
            current_h2_positions = []
            
            # Find existing H2 positions (simplified - would parse actual positions)
            for i, level in enumerate(heading_levels):
                if level == 2:
                    # Estimate position (simplified)
                    estimated_pos = i * 200
                    current_h2_positions.append(estimated_pos)
            
            # Recommend missing H2s
            for pos in optimal_h2_positions:
                if not any(abs(pos - existing) < 100 for existing in current_h2_positions):
                    structure_metadata["recommended_headings"].append({
                        "level": 2,
                        "position": pos,
                        "suggested_text": f"Section Heading at ~{pos} words",
                        "reason": "Optimal H2 placement for content structure"
                    })
        
        # Image placement recommendations
        images = re.findall(r'<img[^>]*>', content, re.IGNORECASE)
        image_count = len(images)
        
        # Optimal: Image every 300-500 words
        optimal_image_positions = list(range(300, word_count, 400))
        for pos in optimal_image_positions[:3]:  # Recommend top 3 positions
            structure_metadata["image_recommendations"].append({
                "position": pos,
                "suggested_alt_text": "Descriptive alt text for image",
                "type": "content_image",
                "reason": "Optimal image placement for engagement"
            })
        
        if image_count == 0 and word_count > 500:
            recommendations.append("Add images to break up text and improve engagement")
        
        # CTA placement recommendations
        # Optimal: CTA at 60-70% of content and at the end
        cta_positions = [
            int(word_count * 0.65),
            word_count - 100  # Near end
        ]
        
        for pos in cta_positions:
            if pos > 0:
                structure_metadata["cta_placements"].append({
                    "position": pos,
                    "type": "related_content" if pos < word_count * 0.7 else "newsletter",
                    "suggested_text": "Want more insights? Subscribe to our newsletter" if pos > word_count * 0.7 else "Related: Check out our other articles",
                    "reason": "Optimal CTA placement for conversion"
                })
        
        # Internal linking recommendations (simplified)
        # Would analyze content for keyword opportunities
        if word_count > 1000:
            structure_metadata["internal_links"].append({
                "position": int(word_count * 0.3),
                "anchor_text": "related topic",
                "target_keyword": "related keyword",
                "relevance_score": 0.85,
                "reason": "Internal link opportunity for SEO"
            })
        
        score = max(0, min(100, score))
        
        return QualityScore(
            dimension=QualityDimension.STRUCTURE,
            score=score,
            weight=self.dimension_weights[QualityDimension.STRUCTURE],
            issues=issues,
            recommendations=recommendations,
            metadata=structure_metadata
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
    
    def _score_accessibility(self, content: str) -> QualityScore:
        """
        Score accessibility compliance (WCAG guidelines).
        
        Checks for:
        - Alt text for images
        - Proper heading hierarchy
        - Table of contents for long content
        - Sufficient color contrast (simplified)
        - ARIA labels where needed
        """
        issues = []
        recommendations = []
        score = 100
        wcag_level = "A"  # Default
        
        # Check for images without alt text
        # Look for img tags without alt attribute
        img_pattern = r'<img[^>]*>'
        images = re.findall(img_pattern, content, re.IGNORECASE)
        images_without_alt = [
            img for img in images
            if 'alt=' not in img.lower() or 'alt=""' in img.lower()
        ]
        
        if images_without_alt:
            issues.append(f"Found {len(images_without_alt)} image(s) without alt text")
            score -= len(images_without_alt) * 10
            recommendations.append("Add descriptive alt text to all images")
        
        # Check heading hierarchy
        headings = re.findall(r'<h([1-6])|^(#{1,6})\s+', content, re.MULTILINE)
        if headings:
            heading_levels = [int(h[0] if h[0] else len(h[1])) for h in headings]
            
            # Check for skipped levels (e.g., H1 -> H3 without H2)
            for i in range(len(heading_levels) - 1):
                if heading_levels[i+1] > heading_levels[i] + 1:
                    issues.append("Skipped heading level detected (e.g., H1 -> H3)")
                    score -= 15
                    recommendations.append("Maintain proper heading hierarchy (H1 -> H2 -> H3)")
                    break
            
            # Check for multiple H1s (should only have one)
            h1_count = sum(1 for level in heading_levels if level == 1)
            if h1_count > 1:
                issues.append(f"Multiple H1 headings found ({h1_count})")
                score -= 10
                recommendations.append("Use only one H1 heading per page")
        
        # Check for table of contents (for long content)
        word_count = len(content.split())
        toc_indicators = [
            "table of contents", "contents", "toc",
            "in this article", "article outline"
        ]
        
        has_toc = any(indicator in content.lower()[:500] for indicator in toc_indicators)
        if word_count > 2000 and not has_toc:
            issues.append("Long content missing table of contents")
            score -= 10
            recommendations.append("Add table of contents for content over 2000 words")
        
        # Check for lists (improves scannability)
        list_count = len(re.findall(r'<[uo]l>|^[\*\-\+]', content, re.MULTILINE))
        if word_count > 1000 and list_count < 2:
            issues.append("Insufficient lists for scannability")
            score -= 5
            recommendations.append("Add more bulleted or numbered lists")
        
        # Check for link accessibility (simplified)
        # Check for descriptive link text
        generic_link_texts = ["click here", "read more", "here", "link"]
        generic_links = sum(
            1 for text in generic_link_texts
            if text in content.lower()
        )
        
        if generic_links > 2:
            issues.append("Generic link text detected")
            score -= 5
            recommendations.append("Use descriptive link text instead of 'click here' or 'read more'")
        
        # Determine WCAG level
        if score >= 90:
            wcag_level = "AAA"
        elif score >= 80:
            wcag_level = "AA"
        elif score >= 70:
            wcag_level = "A"
        else:
            wcag_level = "Not compliant"
        
        score = max(0, min(100, score))
        
        return QualityScore(
            dimension=QualityDimension.ACCESSIBILITY,
            score=score,
            weight=self.dimension_weights[QualityDimension.ACCESSIBILITY],
            issues=issues,
            recommendations=recommendations,
            metadata={
                "wcag_level": wcag_level,
                "images_without_alt": len(images_without_alt),
                "heading_issues": len([i for i in issues if "heading" in i.lower()]),
                "has_table_of_contents": has_toc,
                "list_count": list_count
            }
        )
    
    def _score_eeat(
        self,
        content: str,
        citations: List[Dict[str, str]],
        title: str = "",
        keywords: List[str] = None,
        include_eeat: bool = True
    ) -> QualityScore:
        """
        Score E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness).
        
        Google's quality rater guidelines focus on:
        - Experience: First-hand experience signals
        - Expertise: Author credentials, qualifications
        - Authoritativeness: Domain authority, citations from authoritative sources
        - Trustworthiness: Fact-checking, source quality, transparency
        
        Args:
            include_eeat: If False, returns neutral scores and no issues
        """
        # If E-E-A-T is disabled, return neutral scores
        if not include_eeat:
            return QualityScore(
                dimension=QualityDimension.EEAT,
                score=50.0,  # Neutral score
                weight=self.dimension_weights[QualityDimension.EEAT],
                issues=[],
                recommendations=[],
                metadata={
                    "experience_score": 50.0,
                    "expertise_score": 50.0,
                    "authoritativeness_score": 50.0,
                    "trustworthiness_score": 50.0,
                    "overall_eeat": 0.5,
                    "yyml_topic": False,
                    "yyml_compliant": True,
                    "eeat_disabled": True
                }
            )
        
        issues = []
        recommendations = []
        scores = {
            'experience': 0.0,
            'expertise': 0.0,
            'authoritativeness': 0.0,
            'trustworthiness': 0.0
        }
        
        keywords = keywords or []
        
        # 1. EXPERIENCE Scoring (0-1.0)
        # Check for first-hand experience indicators
        experience_indicators = [
            "i've", "i have", "i experienced", "in my experience",
            "when i", "i found", "i noticed", "i learned",
            "based on my", "from my", "my own", "personally"
        ]
        
        experience_count = sum(1 for indicator in experience_indicators if indicator in content.lower())
        if experience_count > 0:
            scores['experience'] = min(1.0, experience_count * 0.2)
        else:
            issues.append("No first-hand experience indicators found")
            recommendations.append("Add personal experience or case studies")
            scores['experience'] = 0.3  # Default low score
        
        # 2. EXPERTISE Scoring (0-1.0)
        # Check for author credentials, qualifications, expertise signals
        expertise_indicators = [
            "years of experience", "certified", "licensed", "degree",
            "expert", "specialist", "professional", "qualified",
            "credentials", "background in", "training in"
        ]
        
        expertise_count = sum(1 for indicator in expertise_indicators if indicator in content.lower())
        
        # Check for citations from authoritative sources (academic, industry)
        authoritative_domains = [
            ".edu", ".gov", ".org", "research", "study", "journal",
            "academic", "university", "institute", "association"
        ]
        
        authoritative_citations = sum(
            1 for citation in citations
            if any(domain in citation.get("url", "").lower() for domain in authoritative_domains)
        )
        
        if expertise_count > 0 or authoritative_citations > 0:
            scores['expertise'] = min(1.0, (expertise_count * 0.15) + (authoritative_citations * 0.3))
        else:
            issues.append("Missing expertise indicators or author credentials")
            recommendations.append("Add author bio with credentials and qualifications")
            recommendations.append("Cite authoritative sources (academic, industry reports)")
            scores['expertise'] = 0.4
        
        # 3. AUTHORITATIVENESS Scoring (0-1.0)
        # Domain authority signals, citation quality, source diversity
        citation_count = len(citations)
        unique_domains = len(set(
            citation.get("url", "").split("/")[2] if "/" in citation.get("url", "") else ""
            for citation in citations
        ))
        
        # Check citation quality
        high_quality_domains = [
            "wikipedia.org", "nih.gov", "edu", "gov", "who.int",
            "mayo.edu", "harvard.edu", "stanford.edu", "mit.edu"
        ]
        
        high_quality_citations = sum(
            1 for citation in citations
            if any(domain in citation.get("url", "").lower() for domain in high_quality_domains)
        )
        
        if citation_count >= 5:
            scores['authoritativeness'] = min(1.0, 0.5 + (unique_domains * 0.1) + (high_quality_citations * 0.15))
        elif citation_count >= 3:
            scores['authoritativeness'] = 0.6 + (high_quality_citations * 0.2)
        elif citation_count > 0:
            scores['authoritativeness'] = 0.4
            issues.append("Insufficient citations for authoritative content")
            recommendations.append("Add more citations from authoritative sources")
        else:
            issues.append("No citations provided")
            recommendations.append("Add citations from authoritative sources (academic, government, industry)")
            scores['authoritativeness'] = 0.2
        
        # 4. TRUSTWORTHINESS Scoring (0-1.0)
        # Fact-checking, source quality, transparency, accuracy signals
        trust_score = 0.5  # Base score
        
        # Check for fact-checking indicators
        fact_check_indicators = [
            "verified", "confirmed", "according to", "research shows",
            "studies indicate", "data from", "statistics from"
        ]
        
        fact_check_count = sum(1 for indicator in fact_check_indicators if indicator in content.lower())
        trust_score += min(0.3, fact_check_count * 0.1)
        
        # Check for transparency signals
        transparency_indicators = [
            "last updated", "published", "reviewed", "updated",
            "as of", "current as of", "date"
        ]
        
        transparency_count = sum(1 for indicator in transparency_indicators if indicator in content.lower())
        trust_score += min(0.2, transparency_count * 0.1)
        
        # Penalize for unverified claims
        unverified_claims = [
            "guaranteed", "always", "never", "proven to",
            "scientifically proven"  # Without citation
        ]
        
        unverified_count = 0
        for claim in unverified_claims:
            if claim in content.lower():
                # Check if there's a citation nearby (simplified check)
                claim_pos = content.lower().find(claim)
                nearby_text = content[max(0, claim_pos-100):claim_pos+100]
                if not any(indicator in nearby_text for indicator in fact_check_indicators):
                    unverified_count += 1
        
        trust_score -= min(0.3, unverified_count * 0.1)
        
        scores['trustworthiness'] = max(0.0, min(1.0, trust_score))
        
        if scores['trustworthiness'] < 0.6:
            issues.append("Low trustworthiness signals")
            recommendations.append("Add fact-checking and verification")
            recommendations.append("Include 'Last updated' date")
            recommendations.append("Cite sources for all claims")
        
        # Calculate overall E-E-A-T score (weighted average)
        overall_eeat = (
            scores['experience'] * 0.25 +
            scores['expertise'] * 0.25 +
            scores['authoritativeness'] * 0.25 +
            scores['trustworthiness'] * 0.25
        )
        
        # Convert to 0-100 scale
        eeat_score = overall_eeat * 100
        
        # YMYL (Your Money Your Life) compliance check
        yyml_keywords = [
            "medical", "health", "financial", "legal", "advice",
            "treatment", "cure", "investment", "money", "law"
        ]
        
        is_yyml = any(kw in content.lower() or kw in title.lower() for kw in yyml_keywords)
        yyml_compliant = overall_eeat >= 0.75 if is_yyml else True
        
        if is_yyml and not yyml_compliant:
            issues.append("YMYL topic requires higher E-E-A-T score (≥75)")
            recommendations.append("Add author credentials and qualifications")
            recommendations.append("Cite authoritative medical/financial sources")
            recommendations.append("Include disclaimers and transparency")
        
        return QualityScore(
            dimension=QualityDimension.EEAT,
            score=round(eeat_score, 2),
            weight=self.dimension_weights[QualityDimension.EEAT],
            issues=issues,
            recommendations=recommendations,
            metadata={
                "experience_score": round(scores['experience'] * 100, 2),
                "expertise_score": round(scores['expertise'] * 100, 2),
                "authoritativeness_score": round(scores['authoritativeness'] * 100, 2),
                "trustworthiness_score": round(scores['trustworthiness'] * 100, 2),
                "overall_eeat": round(overall_eeat, 3),
                "yyml_topic": is_yyml,
                "yyml_compliant": yyml_compliant
            }
        )

