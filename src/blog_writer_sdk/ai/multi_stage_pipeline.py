"""
Multi-Stage Blog Generation Pipeline

Implements a 4-stage generation pipeline using different LLMs for each stage
to produce higher-quality content.
"""

import asyncio
import logging
import re
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from .ai_content_generator import AIContentGenerator
from .enhanced_prompts import EnhancedPromptBuilder, PromptTemplate
from .base_provider import AIRequest, AIGenerationConfig, ContentType
from .consensus_generator import ConsensusGenerator
from ..models.blog_models import ContentTone, ContentLength
from ..models.progress_models import ProgressUpdate, ProgressCallback, PipelineStage
from ..integrations.google_custom_search import GoogleCustomSearchClient
from ..integrations.google_knowledge_graph import GoogleKnowledgeGraphClient
from ..integrations.dataforseo_integration import DataForSEOClient
from ..seo.readability_analyzer import ReadabilityAnalyzer, ReadabilityMetrics
from ..seo.semantic_keyword_integrator import SemanticKeywordIntegrator
from ..seo.content_quality_scorer import ContentQualityScorer
from ..seo.intent_analyzer import IntentAnalyzer, SearchIntent
from enum import Enum
import time

logger = logging.getLogger(__name__)


def _safe_enum_to_str(value) -> str:
    """
    Safely convert an enum or string to a string value.
    
    Args:
        value: Either an Enum instance or a string
        
    Returns:
        String representation of the value
    """
    if isinstance(value, Enum):
        return value.value
    elif isinstance(value, str):
        return value
    else:
        # Try to get .value attribute, fallback to str()
        try:
            return value.value
        except AttributeError:
            return str(value)


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
    quality_score: Optional[float] = None
    structured_data: Optional[Dict[str, Any]] = None


class MultiStageGenerationPipeline:
    """Multi-stage content generation pipeline."""
    
    def __init__(
        self,
        ai_generator: AIContentGenerator,
        google_search: Optional[GoogleCustomSearchClient] = None,
        readability_analyzer: Optional[ReadabilityAnalyzer] = None,
        knowledge_graph: Optional[GoogleKnowledgeGraphClient] = None,
        semantic_integrator: Optional[SemanticKeywordIntegrator] = None,
        quality_scorer: Optional[ContentQualityScorer] = None,
        intent_analyzer: Optional["IntentAnalyzer"] = None,
        few_shot_extractor: Optional["FewShotLearningExtractor"] = None,
        length_optimizer: Optional["ContentLengthOptimizer"] = None,
        use_consensus: bool = False,
        dataforseo_client: Optional[DataForSEOClient] = None,
        progress_callback: Optional[ProgressCallback] = None
    ):
        """
        Initialize multi-stage pipeline.
        
        Args:
            ai_generator: AI content generator instance
            google_search: Google Custom Search client (optional)
            readability_analyzer: Readability analyzer (optional)
            knowledge_graph: Google Knowledge Graph client (optional)
            semantic_integrator: Semantic keyword integrator (optional)
            quality_scorer: Content quality scorer (optional)
            intent_analyzer: Intent analyzer for intent-based generation (optional)
            few_shot_extractor: Few-shot learning extractor (optional)
            length_optimizer: Content length optimizer (optional)
            use_consensus: Whether to use consensus generation (Phase 3)
        """
        self.ai_generator = ai_generator
        self.google_search = google_search
        self.readability_analyzer = readability_analyzer or ReadabilityAnalyzer()
        self.knowledge_graph = knowledge_graph
        self.semantic_integrator = semantic_integrator
        self.quality_scorer = quality_scorer or ContentQualityScorer(readability_analyzer=self.readability_analyzer)
        self.intent_analyzer = intent_analyzer
        self.few_shot_extractor = few_shot_extractor
        self.length_optimizer = length_optimizer
        self.use_consensus = use_consensus
        self.consensus_generator = ConsensusGenerator(ai_generator) if use_consensus else None
        self.prompt_builder = EnhancedPromptBuilder()
        self.dataforseo_client = dataforseo_client
        self.progress_callback = progress_callback
    
    async def _emit_progress(
        self,
        stage: PipelineStage,
        stage_number: int,
        total_stages: int,
        status: str,
        details: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Emit progress update if callback is available."""
        if self.progress_callback:
            progress = ProgressUpdate(
                stage=stage.value,
                stage_number=stage_number,
                total_stages=total_stages,
                progress_percentage=(stage_number / total_stages) * 100,
                status=status,
                details=details,
                metadata=metadata or {},
                timestamp=time.time()
            )
            try:
                await self.progress_callback(progress)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")
    
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
        citations = []  # Will be populated during processing
        
        # Calculate total stages dynamically
        # Base stages: initialization, research, draft, enhancement, seo, finalization = 6
        # Optional stages: keyword_analysis, competitor_analysis, intent, length, semantic, quality = up to 6 more
        total_stages = 6  # Base stages
        if self.dataforseo_client and self.dataforseo_client.is_configured and keywords:
            total_stages += 2  # keyword_analysis, competitor_analysis
        if self.intent_analyzer and keywords:
            total_stages += 1  # intent_analysis
        if self.length_optimizer and keywords:
            total_stages += 1  # length_optimization
        if self.semantic_integrator:
            total_stages += 1  # semantic_integration
        if self.quality_scorer:
            total_stages += 1  # quality_scoring
        
        current_stage = 0
        
        # Stage 0: Initialization
        await self._emit_progress(
            PipelineStage.INITIALIZATION,
            current_stage := current_stage + 1,
            total_stages,
            "Initializing blog generation pipeline",
            f"Topic: {topic}, Keywords: {', '.join(keywords[:3])}"
        )
        
        # DataForSEO Labs: Keyword Analysis (if available)
        keyword_analysis_data = {}
        if self.dataforseo_client and self.dataforseo_client.is_configured and keywords:
            await self._emit_progress(
                PipelineStage.KEYWORD_ANALYSIS,
                current_stage := current_stage + 1,
                total_stages,
                "Analyzing keywords with DataForSEO Labs",
                f"Analyzing {len(keywords)} keywords for difficulty, search volume, and competition"
            )
            try:
                tenant_id = os.getenv("TENANT_ID", "default")
                location = additional_context.get("location", "United States") if additional_context else "United States"
                language = additional_context.get("language", "en") if additional_context else "en"
                
                # Get keyword difficulty
                difficulty_data = await self.dataforseo_client.get_keyword_difficulty(
                    keywords=keywords,
                    location_name=location,
                    language_code=language,
                    tenant_id=tenant_id
                )
                keyword_analysis_data["difficulty"] = difficulty_data
                
                # Get keyword overview (search volume, CPC, competition)
                overview_data = await self.dataforseo_client.get_keyword_overview(
                    keywords=keywords,
                    location_name=location,
                    language_code=language,
                    tenant_id=tenant_id
                )
                keyword_analysis_data["overview"] = overview_data
                
                # Add to context
                if additional_context is None:
                    additional_context = {}
                additional_context["keyword_analysis"] = keyword_analysis_data
                
                await self._emit_progress(
                    PipelineStage.KEYWORD_ANALYSIS,
                    current_stage,
                    total_stages,
                    "Keyword analysis complete",
                    f"Analyzed {len(keywords)} keywords. Average difficulty: {sum(difficulty_data.values()) / len(difficulty_data) if difficulty_data else 0:.1f}/100"
                )
            except Exception as e:
                logger.warning(f"DataForSEO keyword analysis failed: {e}")
                await self._emit_progress(
                    PipelineStage.KEYWORD_ANALYSIS,
                    current_stage,
                    total_stages,
                    "Keyword analysis skipped",
                    "DataForSEO analysis unavailable, using fallback methods"
                )
        
        # DataForSEO Labs: Competitor Analysis (if available and keywords provided)
        competitor_data = {}
        if self.dataforseo_client and self.dataforseo_client.is_configured and keywords:
            await self._emit_progress(
                PipelineStage.COMPETITOR_ANALYSIS,
                current_stage := current_stage + 1,
                total_stages,
                "Analyzing competitors with DataForSEO Labs",
                f"Identifying top competitors for keyword: {keywords[0]}"
            )
            try:
                tenant_id = os.getenv("TENANT_ID", "default")
                location = additional_context.get("location", "United States") if additional_context else "United States"
                language = additional_context.get("language", "en") if additional_context else "en"
                
                # Get SERP analysis to find top-ranking domains
                serp_analysis = await self.dataforseo_client.get_serp_analysis(
                    keyword=keywords[0],
                    location_name=location,
                    language_code=language,
                    tenant_id=tenant_id,
                    depth=10
                )
                
                # Extract top domains from SERP results
                top_domains = serp_analysis.get("top_domains", [])[:5] if serp_analysis else []
                competitor_data["top_rankers"] = top_domains
                competitor_data["serp_features"] = serp_analysis.get("serp_features", {})
                competitor_data["organic_results"] = serp_analysis.get("organic_results", [])[:5]
                
                if additional_context is None:
                    additional_context = {}
                additional_context["competitor_analysis"] = competitor_data
                
                competitor_count = len(top_domains)
                await self._emit_progress(
                    PipelineStage.COMPETITOR_ANALYSIS,
                    current_stage,
                    total_stages,
                    "Competitor analysis complete",
                    f"Identified {competitor_count} top-ranking competitors from SERP"
                )
            except Exception as e:
                logger.warning(f"DataForSEO competitor analysis failed: {e}")
                await self._emit_progress(
                    PipelineStage.COMPETITOR_ANALYSIS,
                    current_stage,
                    total_stages,
                    "Competitor analysis skipped",
                    "DataForSEO competitor analysis unavailable"
                )
        
        # Analyze search intent (if analyzer available)
        intent_analysis = None
        if self.intent_analyzer and keywords:
            await self._emit_progress(
                PipelineStage.INTENT_ANALYSIS,
                current_stage := current_stage + 1,
                total_stages,
                "Analyzing search intent",
                f"Determining user intent for keywords: {', '.join(keywords[:2])}"
            )
            logger.info("Analyzing search intent")
            try:
                intent_analysis = await self.intent_analyzer.analyze_intent(
                    keywords=keywords,
                    language_code="en"
                )
                # Add intent to context
                if additional_context is None:
                    additional_context = {}
                # Handle both enum and string types for primary_intent
                intent_value = _safe_enum_to_str(intent_analysis.primary_intent)
                additional_context["search_intent"] = intent_value
                additional_context["intent_recommendations"] = intent_analysis.recommendations
                logger.info(f"Detected intent: {intent_value} (confidence: {intent_analysis.confidence:.2f})")
                
                await self._emit_progress(
                    PipelineStage.INTENT_ANALYSIS,
                    current_stage,
                    total_stages,
                    "Search intent analysis complete",
                    f"Detected intent: {intent_value} ({intent_analysis.confidence*100:.0f}% confidence)"
                )
            except Exception as e:
                logger.warning(f"Intent analysis failed: {e}")
                await self._emit_progress(
                    PipelineStage.INTENT_ANALYSIS,
                    current_stage,
                    total_stages,
                    "Intent analysis skipped",
                    "Intent analysis unavailable"
                )
        
        # Extract few-shot learning examples (if extractor available)
        few_shot_context = None
        if self.few_shot_extractor and keywords:
            logger.info("Extracting top-ranking content examples")
            try:
                few_shot_context = await self.few_shot_extractor.extract_top_ranking_examples(
                    keyword=keywords[0],
                    num_examples=3
                )
                # Add few-shot context to additional_context
                if additional_context is None:
                    additional_context = {}
                additional_context["few_shot_examples"] = self.few_shot_extractor.build_few_shot_prompt_context(few_shot_context)
                logger.info(f"Extracted {len(few_shot_context.examples)} content examples")
            except Exception as e:
                logger.warning(f"Few-shot extraction failed: {e}")
        
        # Optimize content length based on competition (if optimizer available)
        length_analysis = None
        if self.length_optimizer and keywords:
            await self._emit_progress(
                PipelineStage.LENGTH_OPTIMIZATION,
                current_stage := current_stage + 1,
                total_stages,
                "Optimizing content length",
                f"Analyzing optimal word count for keyword: {keywords[0]}"
            )
            logger.info("Analyzing optimal content length")
            try:
                length_analysis = await self.length_optimizer.analyze_optimal_length(
                    keyword=keywords[0]
                )
                # Adjust length target if needed
                original_word_count = self.prompt_builder._get_word_count(length)
                adjusted_word_count = self.length_optimizer.adjust_word_count_target(
                    original_word_count,
                    length_analysis
                )
                if adjusted_word_count != original_word_count:
                    logger.info(f"Adjusted word count target: {original_word_count} -> {adjusted_word_count}")
                    # Update length in context
                    if additional_context is None:
                        additional_context = {}
                    additional_context["adjusted_word_count"] = adjusted_word_count
                    additional_context["depth_score"] = length_analysis.depth_score
                    
                    await self._emit_progress(
                        PipelineStage.LENGTH_OPTIMIZATION,
                        current_stage,
                        total_stages,
                        "Content length optimized",
                        f"Adjusted target: {original_word_count} → {adjusted_word_count} words"
                    )
                else:
                    await self._emit_progress(
                        PipelineStage.LENGTH_OPTIMIZATION,
                        current_stage,
                        total_stages,
                        "Content length analysis complete",
                        f"Optimal length: {original_word_count} words"
                    )
            except Exception as e:
                logger.warning(f"Length optimization failed: {e}")
                await self._emit_progress(
                    PipelineStage.LENGTH_OPTIMIZATION,
                    current_stage,
                    total_stages,
                    "Length optimization skipped",
                    "Length optimizer unavailable"
                )
        
        # Stage 1: Research & Outline (Claude 3.5 Sonnet)
        await self._emit_progress(
            PipelineStage.RESEARCH_OUTLINE,
            current_stage := current_stage + 1,
            total_stages,
            "Stage 1: Research & Outline",
            f"Conducting research and creating content outline for: {topic}"
        )
        logger.info("Stage 1: Research & Outline")
        outline_result = await self._stage1_research_outline(
            topic, keywords, tone, length, additional_context
        )
        stage_results.append(outline_result)
        outline = outline_result.content
        
        outline_sections = len(outline.split('\n'))
        await self._emit_progress(
            PipelineStage.RESEARCH_OUTLINE,
            current_stage,
            total_stages,
            "Stage 1 Complete: Research & Outline",
            f"Generated comprehensive outline with {outline_sections} sections"
        )
        
        # Stage 2: Draft Generation (GPT-4o or Consensus)
        await self._emit_progress(
            PipelineStage.DRAFT_GENERATION,
            current_stage := current_stage + 1,
            total_stages,
            "Stage 2: Draft Generation",
            f"Generating initial draft content based on outline"
        )
        logger.info("Stage 2: Draft Generation")
        if self.use_consensus and self.consensus_generator:
            # Use consensus generation (Phase 3)
            logger.info("Using consensus generation for Stage 2")
            consensus_result = await self.consensus_generator.generate_with_consensus(
                topic=topic,
                outline=outline_result.content,
                keywords=keywords,
                tone=_safe_enum_to_str(tone),
                length=_safe_enum_to_str(length),
                additional_context=additional_context
            )
            draft_content = consensus_result.final_content
            draft_result = PipelineStageResult(
                content=draft_content,
                metadata={
                    "stage": "draft_consensus",
                    "variations": len(consensus_result.draft_variations),
                    "best_sections": list(consensus_result.best_sections.keys())
                },
                stage="draft_consensus",
                provider_used="multi-model",
                tokens_used=consensus_result.total_tokens,
                cost=consensus_result.total_cost
            )
        else:
            # Standard single-model generation
            draft_result = await self._stage2_draft_generation(
                topic, outline, keywords, tone, length, template, additional_context
            )
            draft_content = draft_result.content
        stage_results.append(draft_result)
        
        await self._emit_progress(
            PipelineStage.DRAFT_GENERATION,
            current_stage,
            total_stages,
            "Stage 2 Complete: Draft Generation",
            f"Generated draft with {len(draft_content.split())} words"
        )
        
        # Stage 3: Enhancement & Fact-Checking (Claude 3.5 Sonnet)
        await self._emit_progress(
            PipelineStage.ENHANCEMENT,
            current_stage := current_stage + 1,
            total_stages,
            "Stage 3: Enhancement & Fact-Checking",
            "Enhancing content quality, improving readability, and fact-checking"
        )
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
        
        await self._emit_progress(
            PipelineStage.ENHANCEMENT,
            current_stage,
            total_stages,
            "Stage 3 Complete: Enhancement & Fact-Checking",
            "Content enhanced and fact-checked"
        )
        
        # Stage 4: SEO & Polish (GPT-4o-mini)
        await self._emit_progress(
            PipelineStage.SEO_POLISH,
            current_stage := current_stage + 1,
            total_stages,
            "Stage 4: SEO & Polish",
            "Optimizing content for SEO, generating meta tags, and final polish"
        )
        logger.info("Stage 4: SEO & Polish")
        seo_result = await self._stage4_seo_polish(
            enhanced_content, topic, keywords
        )
        stage_results.append(seo_result)
        
        await self._emit_progress(
            PipelineStage.SEO_POLISH,
            current_stage,
            total_stages,
            "Stage 4 Complete: SEO & Polish",
            "SEO optimization and meta tags generated"
        )
        
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
        
        # Add intent analysis to metadata
        if intent_analysis:
            intent_value = _safe_enum_to_str(intent_analysis.primary_intent)
            seo_metadata["search_intent"] = {
                "primary_intent": intent_value,
                "confidence": intent_analysis.confidence,
                "probabilities": intent_analysis.intent_probabilities
            }
        
        # Add freshness signal to content
        from datetime import datetime
        current_year = datetime.now().year
        # Add "Last updated" note if not already present
        if "last updated" not in enhanced_content.lower() and "updated" not in enhanced_content.lower():
            enhanced_content += f"\n\n*Last updated: {datetime.now().strftime('%B %Y')}*"
        
        # Phase 3: Semantic keyword integration
        if self.semantic_integrator:
            await self._emit_progress(
                PipelineStage.SEMANTIC_INTEGRATION,
                current_stage := current_stage + 1,
                total_stages,
                "Integrating semantic keywords",
                f"Adding semantically related keywords for topical authority"
            )
            logger.info("Integrating semantic keywords (Phase 3)")
            try:
                semantic_result = await self.semantic_integrator.integrate_semantic_keywords(
                    enhanced_content,
                    keywords,
                    max_related=10
                )
                enhanced_content = semantic_result.integrated_content
                # Add semantic metadata
                seo_metadata["semantic_keywords"] = semantic_result.keywords_used
                seo_metadata["keyword_clusters"] = len(semantic_result.keyword_clusters)
                
                await self._emit_progress(
                    PipelineStage.SEMANTIC_INTEGRATION,
                    current_stage,
                    total_stages,
                    "Semantic keyword integration complete",
                    f"Integrated {len(semantic_result.keywords_used)} semantic keywords"
                )
            except Exception as e:
                logger.warning(f"Semantic keyword integration failed: {e}")
                await self._emit_progress(
                    PipelineStage.SEMANTIC_INTEGRATION,
                    current_stage,
                    total_stages,
                    "Semantic integration skipped",
                    "Semantic integrator unavailable"
                )
        
        # Phase 3: Knowledge Graph integration
        structured_data = None
        if self.knowledge_graph:
            logger.info("Integrating Knowledge Graph entities (Phase 3)")
            try:
                # Extract entities and generate structured data
                entities = await self.knowledge_graph.extract_entities_from_content(
                    enhanced_content,
                    limit=5
                )
                if entities:
                    structured_data = await self.knowledge_graph.generate_structured_data(
                        topic,
                        enhanced_content,
                        keywords
                    )
                    seo_metadata["structured_data"] = structured_data
                    seo_metadata["entities_found"] = len(entities)
            except Exception as e:
                logger.warning(f"Knowledge Graph integration failed: {e}")
        
        # Phase 3: Content quality scoring
        quality_report = None
        if self.quality_scorer:
            await self._emit_progress(
                PipelineStage.QUALITY_SCORING,
                current_stage := current_stage + 1,
                total_stages,
                "Scoring content quality",
                "Evaluating content across multiple quality dimensions"
            )
            logger.info("Scoring content quality (Phase 3)")
            try:
                quality_report = self.quality_scorer.score_content(
                    content=enhanced_content,
                    title=meta_title,
                    keywords=keywords,
                    meta_description=meta_description,
                    citations=[{"url": "", "title": ""}]  # Citations will be added later
                )
                seo_metadata["quality_report"] = {
                    "overall_score": quality_report.overall_score,
                    "dimension_scores": {
                        dim: score.score
                        for dim, score in quality_report.dimension_scores.items()
                    },
                    "passed_threshold": quality_report.passed_threshold,
                    "critical_issues": quality_report.critical_issues[:3]
                }
                
                await self._emit_progress(
                    PipelineStage.QUALITY_SCORING,
                    current_stage,
                    total_stages,
                    "Quality scoring complete",
                    f"Overall quality score: {quality_report.overall_score:.1f}/100"
                )
            except Exception as e:
                logger.warning(f"Quality scoring failed: {e}")
                await self._emit_progress(
                    PipelineStage.QUALITY_SCORING,
                    current_stage,
                    total_stages,
                    "Quality scoring skipped",
                    "Quality scorer unavailable"
                )
        
        # Finalization
        await self._emit_progress(
            PipelineStage.FINALIZATION,
            current_stage := current_stage + 1,
            total_stages,
            "Finalizing blog generation",
            "Compiling final content and metadata"
        )
        
        # Add DataForSEO results to seo_metadata if available
        if additional_context:
            if "keyword_analysis" in additional_context:
                seo_metadata["keyword_analysis"] = additional_context["keyword_analysis"]
            if "competitor_analysis" in additional_context:
                seo_metadata["competitor_analysis"] = additional_context["competitor_analysis"]
        
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
            generation_time=generation_time,
            quality_score=quality_report.overall_score if quality_report else None,
            structured_data=structured_data
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
        
        # Extract product brands if this is a product-related topic
        brand_recommendations = None
        if self.google_search and keywords:
            try:
                # Check if topic/keywords suggest product research
                product_indicators = ["best", "top", "review", "compare", "buy", "product"]
                is_product_topic = any(indicator in topic.lower() or any(indicator in kw.lower() for kw in keywords) for indicator in product_indicators)
                
                if is_product_topic:
                    logger.info("Detected product topic, searching for brand recommendations")
                    brands = await self.google_search.search_product_brands(
                        product_query=f"{topic} {keywords[0]}",
                        num_results=10
                    )
                    if brands:
                        brand_list = [b["brand"] for b in brands[:8]]  # Top 8 brands
                        brand_recommendations = {
                            "brands": brand_list,
                            "sources": [{"brand": b["brand"], "source": b["source_title"], "url": b["source_url"]} for b in brands[:5]]
                        }
                        logger.info(f"Found {len(brand_list)} brand recommendations: {', '.join(brand_list[:5])}")
            except Exception as e:
                logger.warning(f"Brand extraction failed: {e}")
        
        # Build research prompt
        research_context = context or {}
        if competitor_analysis:
            research_context["competitor_analysis"] = competitor_analysis
        if brand_recommendations:
            research_context["brand_recommendations"] = brand_recommendations
        
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
    

