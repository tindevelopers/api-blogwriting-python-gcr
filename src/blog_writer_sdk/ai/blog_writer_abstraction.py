"""
Blog Writer Abstraction Layer

This module provides a high-level abstraction layer for the Blog Writer SDK,
offering intelligent content generation strategies, provider management,
and advanced features like content optimization and quality assurance.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

from .base_provider import (
    AIProviderManager, 
    AIRequest, 
    AIResponse, 
    ContentType, 
    AIGenerationConfig,
    AIProviderError,
    AIProviderType
)
from .ai_content_generator import AIContentGenerator, ContentTemplate
from ..models.blog_models import ContentTone, ContentLength, ContentFormat
from ..seo.enhanced_keyword_analyzer import EnhancedKeywordAnalyzer
from ..core.content_analyzer import ContentAnalyzer


logger = logging.getLogger(__name__)


class ContentStrategy(str, Enum):
    """Content generation strategies."""
    SEO_OPTIMIZED = "seo_optimized"
    ENGAGEMENT_FOCUSED = "engagement_focused"
    CONVERSION_OPTIMIZED = "conversion_optimized"
    EDUCATIONAL = "educational"
    PROMOTIONAL = "promotional"
    TECHNICAL = "technical"
    CREATIVE = "creative"


class ContentQuality(str, Enum):
    """Content quality levels."""
    DRAFT = "draft"
    GOOD = "good"
    EXCELLENT = "excellent"
    PUBLICATION_READY = "publication_ready"


@dataclass
class BlogGenerationRequest:
    """Request model for blog generation."""
    topic: str
    keywords: List[str]
    target_audience: Optional[str] = None
    content_strategy: ContentStrategy = ContentStrategy.SEO_OPTIMIZED
    tone: ContentTone = ContentTone.PROFESSIONAL
    length: ContentLength = ContentLength.MEDIUM
    format: ContentFormat = ContentFormat.HTML
    template: Optional[ContentTemplate] = None
    quality_target: ContentQuality = ContentQuality.GOOD
    preferred_provider: Optional[str] = None
    additional_context: Optional[Dict[str, Any]] = None
    seo_requirements: Optional[Dict[str, Any]] = None


@dataclass
class BlogGenerationResult:
    """Result model for blog generation."""
    title: str
    content: str
    meta_description: str
    introduction: str
    conclusion: str
    faq_section: Optional[str] = None
    seo_score: Optional[float] = None
    readability_score: Optional[float] = None
    quality_score: Optional[float] = None
    provider_used: str = ""
    generation_time: Optional[float] = None
    cost: Optional[float] = None
    tokens_used: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class ContentOptimizationStrategy(ABC):
    """Abstract base class for content optimization strategies."""
    
    @abstractmethod
    async def optimize_content(
        self, 
        content: str, 
        keywords: List[str], 
        target_audience: Optional[str] = None
    ) -> str:
        """Optimize content based on strategy."""
        pass


class SEOOptimizationStrategy(ContentOptimizationStrategy):
    """SEO-focused content optimization."""
    
    def __init__(self, keyword_analyzer: Optional[EnhancedKeywordAnalyzer] = None):
        self.keyword_analyzer = keyword_analyzer
    
    async def optimize_content(
        self, 
        content: str, 
        keywords: List[str], 
        target_audience: Optional[str] = None
    ) -> str:
        """Optimize content for SEO."""
        # Add keyword density optimization
        # Add heading structure optimization
        # Add internal linking suggestions
        # Add meta tag optimization
        return content


class EngagementOptimizationStrategy(ContentOptimizationStrategy):
    """Engagement-focused content optimization."""
    
    async def optimize_content(
        self, 
        content: str, 
        keywords: List[str], 
        target_audience: Optional[str] = None
    ) -> str:
        """Optimize content for engagement."""
        # Add emotional triggers
        # Add storytelling elements
        # Add interactive elements
        # Add social proof elements
        return content


class ConversionOptimizationStrategy(ContentOptimizationStrategy):
    """Conversion-focused content optimization."""
    
    async def optimize_content(
        self, 
        content: str, 
        keywords: List[str], 
        target_audience: Optional[str] = None
    ) -> str:
        """Optimize content for conversions."""
        # Add call-to-action optimization
        # Add urgency elements
        # Add benefit-focused language
        # Add trust signals
        return content


class ContentQualityAssurance:
    """Content quality assurance and validation."""
    
    def __init__(self, content_analyzer: Optional[ContentAnalyzer] = None):
        self.content_analyzer = content_analyzer
    
    async def assess_content_quality(
        self, 
        content: str, 
        keywords: List[str],
        target_quality: ContentQuality = ContentQuality.GOOD
    ) -> Dict[str, Any]:
        """Assess content quality and provide recommendations."""
        quality_metrics = {
            "readability_score": 0.0,
            "seo_score": 0.0,
            "engagement_score": 0.0,
            "overall_quality": 0.0,
            "recommendations": []
        }
        
        # Implement quality assessment logic
        # - Readability analysis
        # - SEO optimization check
        # - Engagement factor analysis
        # - Content structure validation
        
        return quality_metrics
    
    async def improve_content_quality(
        self, 
        content: str, 
        quality_metrics: Dict[str, Any]
    ) -> str:
        """Improve content based on quality metrics."""
        improved_content = content
        
        # Implement content improvement logic based on metrics
        # - Fix readability issues
        # - Improve SEO elements
        # - Enhance engagement factors
        
        return improved_content


class BlogWriterAbstraction:
    """
    High-level abstraction layer for the Blog Writer SDK.
    
    This class provides intelligent content generation with advanced features
    like strategy-based optimization, quality assurance, and provider management.
    """
    
    def __init__(
        self,
        ai_generator: Optional[AIContentGenerator] = None,
        keyword_analyzer: Optional[EnhancedKeywordAnalyzer] = None,
        content_analyzer: Optional[ContentAnalyzer] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the Blog Writer abstraction layer.
        
        Args:
            ai_generator: AI content generator instance
            keyword_analyzer: Enhanced keyword analyzer instance
            content_analyzer: Content analyzer instance
            config: Configuration dictionary
        """
        self.config = config or {}
        self.ai_generator = ai_generator or AIContentGenerator(config)
        self.keyword_analyzer = keyword_analyzer
        self.content_analyzer = content_analyzer
        
        # Initialize optimization strategies
        self.optimization_strategies = {
            ContentStrategy.SEO_OPTIMIZED: SEOOptimizationStrategy(keyword_analyzer),
            ContentStrategy.ENGAGEMENT_FOCUSED: EngagementOptimizationStrategy(),
            ContentStrategy.CONVERSION_OPTIMIZED: ConversionOptimizationStrategy(),
            ContentStrategy.EDUCATIONAL: SEOOptimizationStrategy(keyword_analyzer),
            ContentStrategy.PROMOTIONAL: ConversionOptimizationStrategy(),
            ContentStrategy.TECHNICAL: SEOOptimizationStrategy(keyword_analyzer),
            ContentStrategy.CREATIVE: EngagementOptimizationStrategy()
        }
        
        # Initialize quality assurance
        self.quality_assurance = ContentQualityAssurance(content_analyzer)
        
        # Generation statistics
        self.generation_stats = {
            "total_blogs_generated": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "average_quality_score": 0.0,
            "strategy_usage": {},
            "provider_usage": {},
            "total_cost": 0.0,
            "total_tokens": 0
        }
    
    async def generate_blog(
        self, 
        request: BlogGenerationRequest
    ) -> BlogGenerationResult:
        """
        Generate a complete blog post with advanced features.
        
        Args:
            request: Blog generation request
            
        Returns:
            Complete blog generation result
        """
        start_time = asyncio.get_event_loop().time()
        self.generation_stats["total_blogs_generated"] += 1
        
        try:
            # Step 1: Analyze and enhance keywords if analyzer is available
            enhanced_keywords = await self._enhance_keywords(request.keywords, request.topic)
            
            # Step 2: Generate main content
            content_response = await self.ai_generator.generate_blog_content(
                topic=request.topic,
                keywords=enhanced_keywords,
                tone=request.tone,
                length=request.length,
                template=request.template,
                additional_context=request.additional_context,
                preferred_provider=request.preferred_provider
            )
            
            # Step 3: Generate supporting content
            title_response = await self.ai_generator.generate_title(
                topic=request.topic,
                content=content_response.content,
                keywords=enhanced_keywords,
                tone=request.tone,
                preferred_provider=request.preferred_provider
            )
            
            meta_description_response = await self.ai_generator.generate_meta_description(
                title=title_response.content,
                content=content_response.content,
                keywords=enhanced_keywords,
                preferred_provider=request.preferred_provider
            )
            
            introduction_response = await self.ai_generator.generate_introduction(
                topic=request.topic,
                keywords=enhanced_keywords,
                tone=request.tone,
                preferred_provider=request.preferred_provider
            )
            
            # Extract key points for conclusion
            key_points = self._extract_key_points(content_response.content)
            conclusion_response = await self.ai_generator.generate_conclusion(
                topic=request.topic,
                key_points=key_points,
                tone=request.tone,
                preferred_provider=request.preferred_provider
            )
            
            # Step 4: Generate FAQ section if requested
            faq_response = None
            if request.content_strategy in [ContentStrategy.EDUCATIONAL, ContentStrategy.SEO_OPTIMIZED]:
                faq_response = await self.ai_generator.generate_faq_section(
                    topic=request.topic,
                    keywords=enhanced_keywords,
                    num_questions=5,
                    preferred_provider=request.preferred_provider
                )
            
            # Step 5: Apply content optimization strategy
            optimized_content = await self._apply_optimization_strategy(
                content_response.content,
                enhanced_keywords,
                request.content_strategy,
                request.target_audience
            )
            
            # Step 6: Quality assurance and improvement
            quality_metrics = await self.quality_assurance.assess_content_quality(
                optimized_content,
                enhanced_keywords,
                request.quality_target
            )
            
            if quality_metrics["overall_quality"] < self._get_quality_threshold(request.quality_target):
                optimized_content = await self.quality_assurance.improve_content_quality(
                    optimized_content,
                    quality_metrics
                )
            
            # Step 7: Calculate final metrics
            generation_time = asyncio.get_event_loop().time() - start_time
            total_cost = (
                content_response.cost or 0 +
                title_response.cost or 0 +
                meta_description_response.cost or 0 +
                introduction_response.cost or 0 +
                conclusion_response.cost or 0 +
                (faq_response.cost or 0 if faq_response else 0)
            )
            total_tokens = (
                content_response.tokens_used or 0 +
                title_response.tokens_used or 0 +
                meta_description_response.tokens_used or 0 +
                introduction_response.tokens_used or 0 +
                conclusion_response.tokens_used or 0 +
                (faq_response.tokens_used or 0 if faq_response else 0)
            )
            
            # Step 8: Create result
            result = BlogGenerationResult(
                title=title_response.content,
                content=optimized_content,
                meta_description=meta_description_response.content,
                introduction=introduction_response.content,
                conclusion=conclusion_response.content,
                faq_section=faq_response.content if faq_response else None,
                seo_score=quality_metrics.get("seo_score"),
                readability_score=quality_metrics.get("readability_score"),
                quality_score=quality_metrics.get("overall_quality"),
                provider_used=content_response.provider,
                generation_time=generation_time,
                cost=total_cost,
                tokens_used=total_tokens,
                metadata={
                    "strategy_used": request.content_strategy.value,
                    "quality_metrics": quality_metrics,
                    "enhanced_keywords": enhanced_keywords,
                    "original_keywords": request.keywords
                }
            )
            
            # Step 9: Update statistics
            self._update_generation_stats(result, request, success=True)
            
            return result
            
        except Exception as e:
            self.generation_stats["failed_generations"] += 1
            logger.error(f"Blog generation failed: {e}")
            raise AIProviderError(f"Failed to generate blog: {str(e)}", "blog_writer_abstraction")
    
    async def generate_blog_batch(
        self, 
        requests: List[BlogGenerationRequest],
        max_concurrent: int = 3
    ) -> List[BlogGenerationResult]:
        """
        Generate multiple blog posts concurrently.
        
        Args:
            requests: List of blog generation requests
            max_concurrent: Maximum concurrent generations
            
        Returns:
            List of blog generation results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_with_semaphore(request: BlogGenerationRequest) -> BlogGenerationResult:
            async with semaphore:
                return await self.generate_blog(request)
        
        tasks = [generate_with_semaphore(request) for request in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log them
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch generation failed for request {i}: {result}")
                self.generation_stats["failed_generations"] += 1
            else:
                successful_results.append(result)
        
        return successful_results
    
    async def optimize_existing_content(
        self,
        content: str,
        keywords: List[str],
        strategy: ContentStrategy = ContentStrategy.SEO_OPTIMIZED,
        target_audience: Optional[str] = None
    ) -> str:
        """
        Optimize existing content using specified strategy.
        
        Args:
            content: Existing content to optimize
            keywords: Target keywords
            strategy: Optimization strategy
            target_audience: Target audience
            
        Returns:
            Optimized content
        """
        optimization_strategy = self.optimization_strategies.get(strategy)
        if not optimization_strategy:
            raise ValueError(f"Unknown optimization strategy: {strategy}")
        
        return await optimization_strategy.optimize_content(
            content, keywords, target_audience
        )
    
    async def assess_content_quality(
        self,
        content: str,
        keywords: List[str],
        target_quality: ContentQuality = ContentQuality.GOOD
    ) -> Dict[str, Any]:
        """
        Assess the quality of existing content.
        
        Args:
            content: Content to assess
            keywords: Target keywords
            target_quality: Target quality level
            
        Returns:
            Quality assessment metrics
        """
        return await self.quality_assurance.assess_content_quality(
            content, keywords, target_quality
        )
    
    async def get_ai_provider_status(self) -> Dict[str, Any]:
        """Get status of all AI providers."""
        return await self.ai_generator.get_provider_health()
    
    def get_generation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive generation statistics."""
        stats = self.generation_stats.copy()
        
        if stats["total_blogs_generated"] > 0:
            stats["success_rate"] = stats["successful_generations"] / stats["total_blogs_generated"]
            stats["average_cost_per_blog"] = stats["total_cost"] / stats["total_blogs_generated"]
            stats["average_tokens_per_blog"] = stats["total_tokens"] / stats["total_blogs_generated"]
        else:
            stats["success_rate"] = 0.0
            stats["average_cost_per_blog"] = 0.0
            stats["average_tokens_per_blog"] = 0.0
        
        return stats
    
    async def _enhance_keywords(
        self, 
        keywords: List[str], 
        topic: str
    ) -> List[str]:
        """Enhance keywords using keyword analyzer if available."""
        if not self.keyword_analyzer:
            return keywords
        
        try:
            # Use keyword analyzer to enhance keywords
            enhanced = await self.keyword_analyzer.analyze_keywords(keywords)
            return enhanced.get("enhanced_keywords", keywords)
        except Exception as e:
            logger.warning(f"Keyword enhancement failed: {e}")
            return keywords
    
    async def _apply_optimization_strategy(
        self,
        content: str,
        keywords: List[str],
        strategy: ContentStrategy,
        target_audience: Optional[str] = None
    ) -> str:
        """Apply content optimization strategy."""
        optimization_strategy = self.optimization_strategies.get(strategy)
        if not optimization_strategy:
            return content
        
        return await optimization_strategy.optimize_content(
            content, keywords, target_audience
        )
    
    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from content for conclusion generation."""
        # Simple implementation - can be enhanced with NLP
        lines = content.split('\n')
        key_points = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('##') or line.startswith('###'):
                key_points.append(line.replace('#', '').strip())
            elif len(line) > 50 and any(word in line.lower() for word in ['important', 'key', 'main', 'primary']):
                key_points.append(line)
        
        return key_points[:5]  # Limit to 5 key points
    
    def _get_quality_threshold(self, quality_target: ContentQuality) -> float:
        """Get quality threshold for target quality level."""
        thresholds = {
            ContentQuality.DRAFT: 0.3,
            ContentQuality.GOOD: 0.6,
            ContentQuality.EXCELLENT: 0.8,
            ContentQuality.PUBLICATION_READY: 0.9
        }
        return thresholds.get(quality_target, 0.6)
    
    def _update_generation_stats(
        self, 
        result: BlogGenerationResult, 
        request: BlogGenerationRequest,
        success: bool
    ):
        """Update generation statistics."""
        if success:
            self.generation_stats["successful_generations"] += 1
            
            # Update strategy usage
            strategy = request.content_strategy.value
            if strategy not in self.generation_stats["strategy_usage"]:
                self.generation_stats["strategy_usage"][strategy] = 0
            self.generation_stats["strategy_usage"][strategy] += 1
            
            # Update provider usage
            provider = result.provider_used
            if provider not in self.generation_stats["provider_usage"]:
                self.generation_stats["provider_usage"][provider] = 0
            self.generation_stats["provider_usage"][provider] += 1
            
            # Update cost and tokens
            if result.cost:
                self.generation_stats["total_cost"] += result.cost
            if result.tokens_used:
                self.generation_stats["total_tokens"] += result.tokens_used
            
            # Update average quality score
            if result.quality_score:
                current_avg = self.generation_stats["average_quality_score"]
                total_successful = self.generation_stats["successful_generations"]
                self.generation_stats["average_quality_score"] = (
                    (current_avg * (total_successful - 1) + result.quality_score) / total_successful
                )
