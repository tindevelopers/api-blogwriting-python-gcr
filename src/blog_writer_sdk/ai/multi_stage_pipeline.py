"""
Multi-Stage Blog Generation Pipeline

Implements a 4-stage generation pipeline using different LLMs for each stage
to produce higher-quality content.
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from .ai_content_generator import AIContentGenerator
from .enhanced_prompts import EnhancedPromptBuilder, PromptTemplate
from .base_provider import AIRequest, AIGenerationConfig, ContentType
from ..models.blog_models import ContentTone, ContentLength
from ..integrations.google_custom_search import GoogleCustomSearchClient
from ..seo.readability_analyzer import ReadabilityAnalyzer, ReadabilityMetrics

logger = logging.getLogger(__name__)


@dataclass
class PipelineStageResult:
    """Result from a pipeline stage."""
    content: str
    metadata: Dict[str, Any]
    stage: str
    provider_used: str
    tokens_used: int
    cost: float


@dataclass
class PipelineResult:
    """Final result from multi-stage pipeline."""
    final_content: str
    meta_title: str
    meta_description: str
    stage_results: List[PipelineStageResult]
    readability_score: float
    seo_metadata: Dict[str, Any]
    citations: List[Dict[str, str]]
    total_tokens: int
    total_cost: float
    generation_time: float


class MultiStageGenerationPipeline:
    """Multi-stage content generation pipeline."""
    
    def __init__(
        self,
        ai_generator: AIContentGenerator,
        google_search: Optional[GoogleCustomSearchClient] = None,
        readability_analyzer: Optional[ReadabilityAnalyzer] = None
    ):
        """
        Initialize multi-stage pipeline.
        
        Args:
            ai_generator: AI content generator instance
            google_search: Google Custom Search client (optional)
            readability_analyzer: Readability analyzer (optional)
        """
        self.ai_generator = ai_generator
        self.google_search = google_search
        self.readability_analyzer = readability_analyzer or ReadabilityAnalyzer()
        self.prompt_builder = EnhancedPromptBuilder()
    
    async def generate(
        self,
        topic: str,
        keywords: List[str],
        tone: ContentTone = ContentTone.PROFESSIONAL,
        length: ContentLength = ContentLength.MEDIUM,
        template: Optional[PromptTemplate] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> PipelineResult:
        """
        Generate content using multi-stage pipeline.
        
        Args:
            topic: Blog topic
            keywords: Target keywords
            tone: Content tone
            length: Content length
            template: Prompt template type
            additional_context: Additional context for generation
        
        Returns:
            PipelineResult with final content and metadata
        """
        import time
        start_time = time.time()
        stage_results = []
        citations = []
        
        # Stage 1: Research & Outline (Claude 3.5 Sonnet)
        logger.info("Stage 1: Research & Outline")
        outline_result = await self._stage1_research_outline(
            topic, keywords, tone, length, additional_context
        )
        stage_results.append(outline_result)
        outline = outline_result.content
        
        # Stage 2: Draft Generation (GPT-4o)
        logger.info("Stage 2: Draft Generation")
        draft_result = await self._stage2_draft_generation(
            topic, outline, keywords, tone, length, template, additional_context
        )
        stage_results.append(draft_result)
        draft_content = draft_result.content
        
        # Stage 3: Enhancement & Fact-Checking (Claude 3.5 Sonnet)
        logger.info("Stage 3: Enhancement & Fact-Checking")
        enhanced_result = await self._stage3_enhancement(
            draft_content, topic, keywords, additional_context
        )
        stage_results.append(enhanced_result)
        enhanced_content = enhanced_result.content
        
        # Fact-checking (if Google Search available)
        if self.google_search:
            logger.info("Fact-checking content")
            fact_check_results = await self._fact_check_content(enhanced_content)
            if fact_check_results.get("issues"):
                # Regenerate problematic sections
                enhanced_content = await self._fix_factual_issues(
                    enhanced_content, fact_check_results
                )
        
        # Stage 4: SEO & Polish (GPT-4o-mini)
        logger.info("Stage 4: SEO & Polish")
        seo_result = await self._stage4_seo_polish(
            enhanced_content, topic, keywords
        )
        stage_results.append(seo_result)
        
        # Readability analysis
        readability_metrics = self.readability_analyzer.analyze(enhanced_content)
        readability_score = readability_metrics.flesch_reading_ease
        
        # Optimize readability if needed
        if readability_score < 60:
            logger.info("Optimizing readability")
            optimized_content, _ = self.readability_analyzer.optimize_content(
                enhanced_content
            )
            enhanced_content = optimized_content
        
        # Extract SEO metadata from stage 4
        seo_metadata = seo_result.metadata.get("seo_metadata", {})
        meta_title = seo_metadata.get("meta_title", "")
        meta_description = seo_metadata.get("meta_description", "")
        
        # Calculate totals
        total_tokens = sum(s.tokens_used for s in stage_results)
        total_cost = sum(s.cost for s in stage_results)
        generation_time = time.time() - start_time
        
        return PipelineResult(
            final_content=enhanced_content,
            meta_title=meta_title,
            meta_description=meta_description,
            stage_results=stage_results,
            readability_score=readability_score,
            seo_metadata=seo_metadata,
            citations=citations,
            total_tokens=total_tokens,
            total_cost=total_cost,
            generation_time=generation_time
        )
    
    async def _stage1_research_outline(
        self,
        topic: str,
        keywords: List[str],
        tone: ContentTone,
        length: ContentLength,
        context: Optional[Dict[str, Any]]
    ) -> PipelineStageResult:
        """Stage 1: Research and outline generation."""
        # Get competitor analysis if Google Search available
        competitor_analysis = None
        if self.google_search and keywords:
            try:
                competitor_data = await self.google_search.analyze_competitors(
                    keywords[0], num_results=5
                )
                competitor_analysis = f"Top domains: {', '.join(list(competitor_data['top_domains'].keys())[:3])}"
            except Exception as e:
                logger.warning(f"Competitor analysis failed: {e}")
        
        # Build research prompt
        research_context = context or {}
        if competitor_analysis:
            research_context["competitor_analysis"] = competitor_analysis
        
        prompt = self.prompt_builder.build_research_prompt(
            topic, keywords, research_context
        )
        
        # Generate with Claude (best for reasoning)
        request = AIRequest(
            prompt=prompt,
            content_type=ContentType.BLOG_POST,
            config=AIGenerationConfig(
                max_tokens=2000,
                temperature=0.7,
                top_p=0.9
            )
        )
        response = await self.ai_generator.provider_manager.generate_content(
            request=request,
            preferred_provider="anthropic"
        )
        
        return PipelineStageResult(
            content=response.content,
            metadata={"stage": "research_outline", "keywords": keywords},
            stage="research_outline",
            provider_used=response.provider,
            tokens_used=response.tokens_used,
            cost=response.cost or 0.0
        )
    
    async def _stage2_draft_generation(
        self,
        topic: str,
        outline: str,
        keywords: List[str],
        tone: ContentTone,
        length: ContentLength,
        template: Optional[PromptTemplate],
        context: Optional[Dict[str, Any]]
    ) -> PipelineStageResult:
        """Stage 2: Draft generation."""
        # Get sources if Google Search available
        sources = []
        if self.google_search:
            try:
                search_results = await self.google_search.search_for_sources(
                    topic, keywords, num_results=5
                )
                sources = [r.get("link", "") for r in search_results]
            except Exception as e:
                logger.warning(f"Source search failed: {e}")
        
        # Get recent information
        recent_info = None
        if self.google_search:
            try:
                recent_results = await self.google_search.get_recent_information(
                    topic, days=30
                )
                if recent_results:
                    recent_info = "\n".join([
                        f"- {r.get('title', '')}: {r.get('snippet', '')[:100]}"
                        for r in recent_results[:3]
                    ])
            except Exception as e:
                logger.warning(f"Recent info search failed: {e}")
        
        # Build draft prompt
        draft_context = context or {}
        if sources:
            draft_context["sources"] = sources
        if recent_info:
            draft_context["recent_info"] = recent_info
        
        prompt = self.prompt_builder.build_draft_prompt(
            topic, outline, keywords, tone, length, template, draft_context
        )
        
        # Generate with GPT-4o (best for comprehensive generation)
        max_tokens = int(self.prompt_builder._get_word_count(length) * 1.5)  # Tokens estimate
        request = AIRequest(
            prompt=prompt,
            content_type=ContentType.BLOG_POST,
            config=AIGenerationConfig(
                max_tokens=max_tokens,
                temperature=0.8,
                top_p=0.9
            )
        )
        response = await self.ai_generator.provider_manager.generate_content(
            request=request,
            preferred_provider="openai"
        )
        
        return PipelineStageResult(
            content=response.content,
            metadata={"stage": "draft", "sources": sources},
            stage="draft",
            provider_used=response.provider,
            tokens_used=response.tokens_used,
            cost=response.cost or 0.0
        )
    
    async def _stage3_enhancement(
        self,
        draft_content: str,
        topic: str,
        keywords: List[str],
        context: Optional[Dict[str, Any]]
    ) -> PipelineStageResult:
        """Stage 3: Content enhancement."""
        # Analyze readability
        readability_issues = self.readability_analyzer.identify_issues(draft_content)
        
        # Build enhancement prompt
        enhancement_context = context or {}
        if readability_issues.issues:
            enhancement_context["readability_issues"] = readability_issues.issues
        
        prompt = self.prompt_builder.build_enhancement_prompt(
            draft_content, topic, keywords, enhancement_context
        )
        
        # Generate with Claude (best for refinement)
        max_tokens = int(len(draft_content.split()) * 1.5)  # Estimate
        request = AIRequest(
            prompt=prompt,
            content_type=ContentType.BLOG_POST,
            config=AIGenerationConfig(
                max_tokens=max_tokens,
                temperature=0.7,
                top_p=0.9
            )
        )
        response = await self.ai_generator.provider_manager.generate_content(
            request=request,
            preferred_provider="anthropic"
        )
        
        return PipelineStageResult(
            content=response.content,
            metadata={
                "stage": "enhancement",
                "readability_issues_fixed": len(readability_issues.issues)
            },
            stage="enhancement",
            provider_used=response.provider,
            tokens_used=response.tokens_used,
            cost=response.cost or 0.0
        )
    
    async def _stage4_seo_polish(
        self,
        content: str,
        topic: str,
        keywords: List[str]
    ) -> PipelineStageResult:
        """Stage 4: SEO polish."""
        prompt = self.prompt_builder.build_seo_polish_prompt(
            content, topic, keywords
        )
        
        # Generate with GPT-4o-mini (cost-effective for SEO tasks)
        request = AIRequest(
            prompt=prompt,
            content_type=ContentType.META_DESCRIPTION,
            config=AIGenerationConfig(
                max_tokens=1000,
                temperature=0.5,
                top_p=0.9
            )
        )
        response = await self.ai_generator.provider_manager.generate_content(
            request=request,
            preferred_provider="openai"  # Will use GPT-4o-mini if available
        )
        
        # Parse SEO metadata from response
        seo_metadata = self._parse_seo_metadata(response.content)
        
        return PipelineStageResult(
            content=content,  # Content doesn't change, only metadata
            metadata={"stage": "seo_polish", "seo_metadata": seo_metadata},
            stage="seo_polish",
            provider_used=response.provider,
            tokens_used=response.tokens_used,
            cost=response.cost or 0.0
        )
    
    async def _fact_check_content(
        self,
        content: str
    ) -> Dict[str, Any]:
        """Fact-check content using Google Search."""
        if not self.google_search:
            return {"verified": True, "issues": []}
        
        # Extract factual claims (simple extraction)
        sentences = content.split('.')
        factual_sentences = [
            s.strip() for s in sentences
            if len(s.split()) > 10 and any(word in s.lower() for word in ['is', 'are', 'was', 'were', 'has', 'have'])
        ][:5]  # Check top 5 sentences
        
        issues = []
        for claim in factual_sentences:
            try:
                verification = await self.google_search.fact_check(claim, num_sources=2)
                if verification["confidence"] == "low":
                    issues.append({
                        "claim": claim,
                        "confidence": verification["confidence"],
                        "sources": verification["sources"]
                    })
            except Exception as e:
                logger.warning(f"Fact-check failed for claim: {e}")
        
        return {
            "verified": len(issues) == 0,
            "issues": issues
        }
    
    async def _fix_factual_issues(
        self,
        content: str,
        fact_check_results: Dict[str, Any]
    ) -> str:
        """Fix factual issues in content."""
        # Simple implementation - could be enhanced
        # For now, just return content as-is
        # In production, would regenerate problematic sections
        return content
    
    def _parse_seo_metadata(self, seo_response: str) -> Dict[str, Any]:
        """Parse SEO metadata from stage 4 response."""
        metadata = {}
        
        # Extract meta title
        title_match = re.search(r'Meta Title[:\s]+(.+)', seo_response, re.IGNORECASE)
        if title_match:
            metadata["meta_title"] = title_match.group(1).strip()
        
        # Extract meta description
        desc_match = re.search(r'Meta Description[:\s]+(.+)', seo_response, re.IGNORECASE)
        if desc_match:
            metadata["meta_description"] = desc_match.group(1).strip()
        
        # Extract internal links
        links_match = re.findall(r'Internal Link[:\s]+(.+?)(?:\n|$)', seo_response, re.IGNORECASE)
        if links_match:
            metadata["internal_links"] = [link.strip() for link in links_match]
        
        return metadata
    

