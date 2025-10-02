"""
Core BlogWriter class - the main interface for the SDK.

This module provides the primary BlogWriter class that orchestrates
content generation, SEO optimization, and quality analysis.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime

from ..models.blog_models import (
    BlogRequest,
    BlogPost,
    BlogGenerationResult,
    MetaTags,
    ContentTone,
    ContentLength,
)
from .content_analyzer import ContentAnalyzer
from .seo_optimizer import SEOOptimizer
from .content_generator import ContentGenerator
from ..seo.keyword_analyzer import KeywordAnalyzer
from ..integrations.dataforseo_integration import EnhancedKeywordAnalyzer
from ..ai.ai_content_generator import AIContentGenerator
from ..seo.meta_generator import MetaTagGenerator
from ..formatters.markdown_formatter import MarkdownFormatter
from ..utils.text_utils import create_slug, extract_excerpt


logger = logging.getLogger(__name__)


class BlogWriter:
    """
    Main BlogWriter class for generating SEO-optimized blog content.
    
    This class orchestrates the entire blog writing process, from content
    generation to SEO optimization and quality analysis.
    """
    
    def __init__(
        self,
        default_tone: ContentTone = ContentTone.PROFESSIONAL,
        default_length: ContentLength = ContentLength.MEDIUM,
        enable_seo_optimization: bool = True,
        enable_quality_analysis: bool = True,
        enhanced_keyword_analyzer: Optional[EnhancedKeywordAnalyzer] = None,
        ai_content_generator: Optional[AIContentGenerator] = None,
        enable_ai_enhancement: bool = False,
    ):
        """
        Initialize the BlogWriter.
        
        Args:
            default_tone: Default writing tone for content
            default_length: Default content length
            enable_seo_optimization: Whether to perform SEO optimization
            enable_quality_analysis: Whether to perform quality analysis
            enhanced_keyword_analyzer: Optional enhanced keyword analyzer with external API support
            ai_content_generator: Optional AI content generator for enhanced content creation
            enable_ai_enhancement: Whether to use AI for content enhancement
        """
        self.default_tone = default_tone
        self.default_length = default_length
        self.enable_seo_optimization = enable_seo_optimization
        self.enable_quality_analysis = enable_quality_analysis
        self.enable_ai_enhancement = enable_ai_enhancement
        
        # Initialize components
        self.content_generator = ContentGenerator()
        self.content_analyzer = ContentAnalyzer()
        self.seo_optimizer = SEOOptimizer()
        self.keyword_analyzer = enhanced_keyword_analyzer or KeywordAnalyzer()
        self.meta_generator = MetaTagGenerator()
        self.formatter = MarkdownFormatter()
        self.ai_generator = ai_content_generator
    
    async def generate(self, request: BlogRequest) -> BlogGenerationResult:
        """
        Generate a complete blog post based on the request.
        
        Args:
            request: Blog generation request with all parameters
            
        Returns:
            BlogGenerationResult with the generated content and metrics
        """
        start_time = time.time()
        
        try:
            # Step 1: Analyze keywords and competition
            if request.keywords:
                keyword_analysis = await self._analyze_keywords(request.keywords)
                if request.focus_keyword:
                    focus_analysis = await self.keyword_analyzer.analyze_keyword(
                        request.focus_keyword
                    )
            
            # Step 2: Generate content structure
            content_outline = await self._create_content_outline(request)
            
            # Step 3: Generate main content
            content = await self._generate_content(request, content_outline)
            
            # Step 4: Optimize for SEO
            if self.enable_seo_optimization:
                content = await self._optimize_content_for_seo(content, request)
            
            # Step 5: Generate title and meta tags
            title = await self._generate_title(request, content)
            meta_tags = await self._generate_meta_tags(title, content, request)
            
            # Step 6: Create final blog post
            blog_post = await self._create_blog_post(
                title=title,
                content=content,
                meta_tags=meta_tags,
                request=request,
            )
            
            # Step 7: Analyze quality and SEO
            if self.enable_quality_analysis:
                blog_post.content_quality = await self.content_analyzer.analyze_quality(
                    blog_post.content
                )
            
            if self.enable_seo_optimization:
                blog_post.seo_metrics = await self.seo_optimizer.analyze_seo(
                    content=blog_post.content,
                    title=blog_post.title,
                    meta_tags=blog_post.meta_tags,
                    keywords=request.keywords,
                    focus_keyword=request.focus_keyword,
                )
            
            # Calculate generation time
            generation_time = time.time() - start_time
            
            # Create result
            result = BlogGenerationResult(
                success=True,
                blog_post=blog_post,
                generation_time_seconds=generation_time,
                word_count=len(blog_post.content.split()),
                seo_score=blog_post.seo_metrics.overall_seo_score if blog_post.seo_metrics else 0.0,
                readability_score=blog_post.content_quality.readability_score if blog_post.content_quality else 0.0,
                suggestions=await self._generate_suggestions(blog_post),
            )
            
            return result
            
        except Exception as e:
            return BlogGenerationResult(
                success=False,
                generation_time_seconds=time.time() - start_time,
                error_message=str(e),
                error_code="GENERATION_ERROR",
            )
    
    async def _analyze_keywords(self, keywords: List[str]) -> Dict:
        """Analyze provided keywords for SEO potential."""
        analysis_results = {}
        
        for keyword in keywords:
            try:
                analysis = await self.keyword_analyzer.analyze_keyword(keyword)
                analysis_results[keyword] = analysis
            except Exception as e:
                analysis_results[keyword] = {"error": str(e)}
        
        return analysis_results
    
    async def _create_content_outline(self, request: BlogRequest) -> Dict:
        """Create a structured outline for the content."""
        outline = {
            "title": request.topic,
            "sections": [],
            "include_introduction": request.include_introduction,
            "include_conclusion": request.include_conclusion,
            "include_faq": request.include_faq,
            "include_toc": request.include_toc,
        }
        
        # Generate section headings based on topic and keywords
        if request.keywords:
            # Create sections around main keywords
            for i, keyword in enumerate(request.keywords[:5]):  # Limit to 5 main sections
                section = {
                    "heading": f"Understanding {keyword.title()}",
                    "keyword_focus": keyword,
                    "estimated_words": self._estimate_section_words(request.length, len(request.keywords)),
                }
                outline["sections"].append(section)
        else:
            # Create generic sections based on topic
            outline["sections"] = [
                {"heading": f"Introduction to {request.topic}", "estimated_words": 200},
                {"heading": f"Key Aspects of {request.topic}", "estimated_words": 300},
                {"heading": f"Benefits and Applications", "estimated_words": 250},
                {"heading": f"Best Practices", "estimated_words": 200},
            ]
        
        return outline
    
    def _estimate_section_words(self, length: ContentLength, num_sections: int) -> int:
        """Estimate words per section based on total length."""
        total_words = {
            ContentLength.SHORT: 500,
            ContentLength.MEDIUM: 1000,
            ContentLength.LONG: 2000,
            ContentLength.EXTENDED: 3500,
        }[length]
        
        # Reserve words for intro/conclusion
        content_words = int(total_words * 0.8)
        return max(100, content_words // max(1, num_sections))
    
    async def _generate_content(self, request: BlogRequest, outline: Dict) -> str:
        """Generate the main content based on outline."""
        # Use AI-enhanced generation if available and enabled
        if self.enable_ai_enhancement and self.ai_generator:
            return await self._generate_ai_enhanced_content(request, outline)
        
        # Fallback to traditional generation
        content_parts = []
        
        # Introduction
        if outline["include_introduction"]:
            intro = await self.content_generator.generate_introduction(
                topic=request.topic,
                tone=request.tone,
                keywords=request.keywords[:3],  # Use top 3 keywords
            )
            content_parts.append(intro)
        
        # Main sections
        for section in outline["sections"]:
            section_content = await self.content_generator.generate_section(
                heading=section["heading"],
                topic=request.topic,
                keyword_focus=section.get("keyword_focus"),
                tone=request.tone,
                target_words=section["estimated_words"],
            )
            content_parts.append(f"## {section['heading']}\n\n{section_content}")
        
        # FAQ section
        if outline["include_faq"]:
            faq_content = await self.content_generator.generate_faq(
                topic=request.topic,
                keywords=request.keywords,
            )
            content_parts.append(f"## Frequently Asked Questions\n\n{faq_content}")
        
        # Conclusion
        if outline["include_conclusion"]:
            conclusion = await self.content_generator.generate_conclusion(
                topic=request.topic,
                tone=request.tone,
                key_points=request.keywords[:3],
            )
            content_parts.append(f"## Conclusion\n\n{conclusion}")
        
        return "\n\n".join(content_parts)
    
    async def _generate_ai_enhanced_content(self, request: BlogRequest, outline: Dict) -> str:
        """Generate AI-enhanced content using the AI content generator."""
        try:
            # Prepare additional context
            additional_context = {
                "audience": request.target_audience,
                "word_count": request.word_count_target,
                "additional_instructions": request.custom_instructions,
                "include_introduction": outline["include_introduction"],
                "include_conclusion": outline["include_conclusion"],
                "include_faq": outline["include_faq"],
                "include_toc": outline["include_toc"],
            }
            
            # Generate full blog content using AI
            ai_response = await self.ai_generator.generate_blog_content(
                topic=request.topic,
                keywords=request.keywords or [],
                tone=request.tone or self.default_tone,
                length=request.length or self.default_length,
                additional_context=additional_context
            )
            
            return ai_response.content
            
        except Exception as e:
            # Fallback to traditional generation if AI fails
            logger.warning(f"AI content generation failed, falling back to traditional method: {e}")
            return await self._generate_traditional_content(request, outline)
    
    async def _generate_traditional_content(self, request: BlogRequest, outline: Dict) -> str:
        """Generate content using traditional methods (fallback)."""
        content_parts = []
        
        # Introduction
        if outline["include_introduction"]:
            intro = await self.content_generator.generate_introduction(
                topic=request.topic,
                tone=request.tone,
                keywords=request.keywords[:3] if request.keywords else [],
            )
            content_parts.append(intro)
        
        # Main sections
        for section in outline["sections"]:
            section_content = await self.content_generator.generate_section(
                heading=section["heading"],
                topic=request.topic,
                keyword_focus=section.get("keyword_focus"),
                tone=request.tone,
                target_words=section["estimated_words"],
            )
            content_parts.append(f"## {section['heading']}\n\n{section_content}")
        
        # FAQ section
        if outline["include_faq"]:
            faq_content = await self.content_generator.generate_faq(
                topic=request.topic,
                keywords=request.keywords or [],
            )
            content_parts.append(f"## Frequently Asked Questions\n\n{faq_content}")
        
        # Conclusion
        if outline["include_conclusion"]:
            conclusion = await self.content_generator.generate_conclusion(
                topic=request.topic,
                tone=request.tone,
                key_points=request.keywords[:3] if request.keywords else [],
            )
            content_parts.append(f"## Conclusion\n\n{conclusion}")
        
        return "\n\n".join(content_parts)
    
    async def _optimize_content_for_seo(self, content: str, request: BlogRequest) -> str:
        """Optimize content for SEO based on keywords and best practices."""
        if not request.keywords:
            return content
        
        # Optimize keyword distribution
        optimized_content = await self.seo_optimizer.optimize_keyword_distribution(
            content=content,
            keywords=request.keywords,
            focus_keyword=request.focus_keyword,
        )
        
        # Add internal linking opportunities
        optimized_content = await self.seo_optimizer.add_internal_linking_suggestions(
            optimized_content
        )
        
        # Optimize heading structure
        optimized_content = await self.seo_optimizer.optimize_heading_structure(
            optimized_content
        )
        
        return optimized_content
    
    async def _generate_title(self, request: BlogRequest, content: str) -> str:
        """Generate an SEO-optimized title."""
        return await self.content_generator.generate_title(
            topic=request.topic,
            content=content,
            keywords=request.keywords,
            focus_keyword=request.focus_keyword,
            tone=request.tone,
        )
    
    async def _generate_meta_tags(
        self, title: str, content: str, request: BlogRequest
    ) -> MetaTags:
        """Generate SEO meta tags."""
        return await self.meta_generator.generate_meta_tags(
            title=title,
            content=content,
            keywords=request.keywords,
            focus_keyword=request.focus_keyword,
        )
    
    async def _create_blog_post(
        self,
        title: str,
        content: str,
        meta_tags: MetaTags,
        request: BlogRequest,
    ) -> BlogPost:
        """Create the final BlogPost object."""
        slug = create_slug(title)
        excerpt = extract_excerpt(content, max_length=250)
        
        return BlogPost(
            title=title,
            content=content,
            excerpt=excerpt,
            meta_tags=meta_tags,
            slug=slug,
            categories=request.keywords[:3] if request.keywords else [],
            tags=request.keywords if request.keywords else [],
            created_at=datetime.now().astimezone(),
        )
    
    async def _generate_suggestions(self, blog_post: BlogPost) -> List[str]:
        """Generate improvement suggestions based on analysis."""
        suggestions = []
        
        if blog_post.seo_metrics:
            if blog_post.seo_metrics.overall_seo_score < 70:
                suggestions.extend(blog_post.seo_metrics.recommendations)
        
        if blog_post.content_quality:
            if blog_post.content_quality.readability_score < 60:
                suggestions.extend(blog_post.content_quality.readability_suggestions)
        
        # Add general suggestions
        word_count = len(blog_post.content.split())
        if word_count < 300:
            suggestions.append("Consider expanding the content to at least 300 words for better SEO.")
        
        if not blog_post.meta_tags.description:
            suggestions.append("Add a meta description for better search engine visibility.")
        
        return suggestions
    
    def set_defaults(
        self,
        tone: Optional[ContentTone] = None,
        length: Optional[ContentLength] = None,
    ) -> None:
        """Update default settings for content generation."""
        if tone:
            self.default_tone = tone
        if length:
            self.default_length = length
    
    async def analyze_existing_content(self, content: str, title: str = "") -> BlogGenerationResult:
        """
        Analyze existing content for SEO and quality metrics.
        
        Args:
            content: Existing content to analyze
            title: Optional title for the content
            
        Returns:
            BlogGenerationResult with analysis metrics
        """
        start_time = time.time()
        
        try:
            # Create a basic blog post for analysis
            meta_tags = MetaTags(
                title=title or "Untitled",
                description="Analysis of existing content for SEO and quality metrics evaluation",
                keywords=[],
            )
            
            blog_post = BlogPost(
                title=title or "Untitled",
                content=content,
                meta_tags=meta_tags,
                slug=create_slug(title) if title else "untitled",
            )
            
            # Perform analysis
            if self.enable_quality_analysis:
                blog_post.content_quality = await self.content_analyzer.analyze_quality(content)
            
            if self.enable_seo_optimization:
                blog_post.seo_metrics = await self.seo_optimizer.analyze_seo(
                    content=content,
                    title=title,
                    meta_tags=meta_tags,
                    keywords=[],
                    focus_keyword=None,
                )
            
            return BlogGenerationResult(
                success=True,
                blog_post=blog_post,
                generation_time_seconds=time.time() - start_time,
                word_count=len(content.split()),
                seo_score=blog_post.seo_metrics.overall_seo_score if blog_post.seo_metrics else 0.0,
                readability_score=blog_post.content_quality.readability_score if blog_post.content_quality else 0.0,
                suggestions=await self._generate_suggestions(blog_post),
            )
            
        except Exception as e:
            return BlogGenerationResult(
                success=False,
                generation_time_seconds=time.time() - start_time,
                error_message=str(e),
                error_code="ANALYSIS_ERROR",
            )
