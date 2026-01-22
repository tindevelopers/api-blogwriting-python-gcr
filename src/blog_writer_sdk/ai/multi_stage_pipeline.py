"""
Multi-Stage Blog Generation Pipeline

Implements a 4-stage generation pipeline using different LLMs for each stage
to produce higher-quality content.
"""

import asyncio
import logging
import re
import os
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass

from .ai_content_generator import AIContentGenerator
from .enhanced_prompts import EnhancedPromptBuilder, PromptTemplate
from .base_provider import AIRequest, AIGenerationConfig, ContentType
from .consensus_generator import ConsensusGenerator
from .content_enhancement import ContentEnhancer
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
    warnings: List[str] = None  # API warnings and notices
    
    def __post_init__(self):
        """Initialize warnings list if None."""
        if self.warnings is None:
            self.warnings = []


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
        few_shot_extractor: Optional[Any] = None,  # FewShotLearningExtractor
        length_optimizer: Optional[Any] = None,  # ContentLengthOptimizer
        use_consensus: bool = False,
        dataforseo_client: Optional[DataForSEOClient] = None,
        search_console: Optional[Any] = None,  # GoogleSearchConsoleClient
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
            dataforseo_client: DataForSEO client (optional)
            search_console: Google Search Console client (optional, for multi-site support)
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
        self.search_console = search_console
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
        
        # Extract citation patterns and LLM responses from research stage metadata
        if outline_result.metadata:
            if outline_result.metadata.get("citation_patterns"):
                if additional_context is None:
                    additional_context = {}
                additional_context["citation_patterns"] = outline_result.metadata["citation_patterns"]
            if outline_result.metadata.get("llm_responses"):
                if additional_context is None:
                    additional_context = {}
                additional_context["llm_responses"] = outline_result.metadata["llm_responses"]
        
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
        
        # Validate word count after draft generation
        word_count_target = self.prompt_builder._get_word_count(length)
        actual_word_count = len(draft_content.split())
        if actual_word_count < word_count_target * 0.8:  # 80% threshold
            logger.warning(
                f"Content too short after draft generation: {actual_word_count} words "
                f"(target: {word_count_target}, {actual_word_count/word_count_target*100:.1f}%)"
            )
        else:
            logger.info(
                f"Draft word count: {actual_word_count} words (target: {word_count_target}, "
                f"{actual_word_count/word_count_target*100:.1f}%)"
            )
        
        await self._emit_progress(
            PipelineStage.DRAFT_GENERATION,
            current_stage,
            total_stages,
            "Stage 2 Complete: Draft Generation",
            f"Generated draft with {actual_word_count} words (target: {word_count_target})"
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
        
        # Phase 2: AI-powered readability optimization (if below target)
        if readability_score < 60:
            logger.info(f"Reading ease ({readability_score:.1f}) below target (60), applying AI-powered simplification")
            await self._emit_progress(
                PipelineStage.ENHANCEMENT,
                current_stage,
                total_stages,
                "AI Readability Optimization",
                f"Simplifying content to improve reading ease from {readability_score:.1f} to 60-70"
            )
            
            # Use AI-powered readability enhancement
            content_enhancer = ContentEnhancer(ai_generator=self.ai_generator)
            readability_result = await content_enhancer.enhance_readability_with_ai(
                content=enhanced_content,
                target_reading_ease=65.0,
                current_reading_ease=readability_score
            )
            
            if readability_result.changes_made:
                enhanced_content = readability_result.content
                logger.info(f"AI readability enhancement applied: {', '.join(readability_result.changes_made)}")
            else:
                # Fallback to simple optimization
                logger.info("Falling back to simple readability optimization")
                optimized_content, _ = self.readability_analyzer.optimize_content(
                    enhanced_content
                )
                enhanced_content = optimized_content
        
        # Phase 2: Engagement element injection
        logger.info("Injecting engagement elements")
        content_enhancer = ContentEnhancer(ai_generator=self.ai_generator)
        
        # Calculate word count for engagement targets
        word_count = len(enhanced_content.split())
        engagement_result = content_enhancer.inject_engagement_elements(
            content=enhanced_content,
            target_questions=max(3, int(word_count / 500)),  # ~1 question per 500 words
            target_examples=max(5, int(word_count / 200)),  # ~1 example per 200 words
            target_ctas=max(2, int(word_count / 1000))  # ~1 CTA per 1000 words
        )
        
        if engagement_result.changes_made:
            enhanced_content = engagement_result.content
            logger.info(f"Engagement elements injected: {', '.join(engagement_result.changes_made)}")
        
        # Phase 2: Experience indicator injection (only if enabled)
        include_eeat = additional_context.get('include_eeat', False) if additional_context else False
        if include_eeat:
            logger.info("Injecting experience indicators")
            experience_result = content_enhancer.inject_experience_indicators(
                content=enhanced_content,
                target_count=3,  # 3 per 1000 words
                word_count=word_count
            )
            
            if experience_result.changes_made:
                enhanced_content = experience_result.content
                logger.info(f"Experience indicators injected: {', '.join(experience_result.changes_made)}")
        else:
            logger.info("E-E-A-T disabled, skipping experience indicator injection")
        
        # Extract SEO metadata from stage 4
        seo_metadata = seo_result.metadata.get("seo_metadata", {})
        meta_title = seo_metadata.get("meta_title", "")
        meta_description = seo_metadata.get("meta_description", "")
        
        # Validate and fix title if invalid
        if not meta_title or meta_title == "**" or len(meta_title) < 5:
            # Extract title from H1 in content as fallback
            h1_match = re.search(r'^#\s+(.+)$', enhanced_content, re.MULTILINE)
            if h1_match:
                meta_title = h1_match.group(1).strip()
                logger.info(f"Using H1 as title fallback: {meta_title}")
            else:
                # Last resort: use topic
                meta_title = topic
                logger.warning(f"Using topic as title fallback: {meta_title}")
        
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
                include_eeat = additional_context.get('include_eeat', False) if additional_context else True
                quality_report = self.quality_scorer.score_content(
                    content=enhanced_content,
                    title=meta_title,
                    keywords=keywords,
                    meta_description=meta_description,
                    citations=[{"url": "", "title": ""}],  # Citations will be added later
                    include_eeat=include_eeat
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
        
        # Validate and enforce content structure
        enhanced_content = self._validate_and_fix_content_structure(
            enhanced_content,
            topic,
            keywords,
            length
        )
        
        # Generate and insert internal links
        # Get link targets from additional_context if provided by frontend
        internal_link_targets = additional_context.get("internal_link_targets") if additional_context else None
        site_domain = additional_context.get("site_domain") if additional_context else None
        max_internal_links = additional_context.get("max_internal_links", 5) if additional_context else 5
        
        enhanced_content, internal_links_list, internal_links_metadata = await self._generate_and_insert_internal_links(
            enhanced_content,
            keywords,
            topic,
            internal_link_targets=internal_link_targets,
            site_domain=site_domain,
            max_links=max_internal_links
        )
        
        # Store internal links in seo_metadata for response (legacy format)
        seo_metadata["internal_links"] = internal_links_list
        # Store enhanced metadata
        seo_metadata["internal_links_metadata"] = internal_links_metadata
        
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
        
        # Final word count validation
        final_word_count = len(enhanced_content.split())
        word_count_target = self.prompt_builder._get_word_count(length)
        if final_word_count < word_count_target * 0.8:  # 80% threshold
            logger.warning(
                f"Final content too short: {final_word_count} words "
                f"(target: {word_count_target}, {final_word_count/word_count_target*100:.1f}%)"
            )
        else:
            logger.info(
                f"Final word count: {final_word_count} words (target: {word_count_target}, "
                f"{final_word_count/word_count_target*100:.1f}%)"
            )
        
        # Calculate totals
        total_tokens = sum(s.tokens_used for s in stage_results)
        total_cost = sum(s.cost for s in stage_results)
        generation_time = time.time() - start_time
        
        # Collect API warnings from all stages
        all_warnings = []
        for stage_result in stage_results:
            if stage_result.metadata and stage_result.metadata.get("api_warnings"):
                all_warnings.extend(stage_result.metadata["api_warnings"])
        
        # Add word count warning if below threshold
        if final_word_count < word_count_target * 0.8:
            all_warnings.append(
                f"Content word count ({final_word_count}) is below target ({word_count_target}). "
                f"Consider expanding sections or adding more detail."
            )
        
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
            structured_data=structured_data,
            warnings=all_warnings
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
        
        # Priority 1: Analyze LLM Mentions for citation patterns
        llm_mentions_data = None
        citation_patterns = None
        api_warnings = []  # Collect API warnings
        
        if self.dataforseo_client and self.dataforseo_client.is_configured and keywords:
            try:
                tenant_id = os.getenv("TENANT_ID", "default")
                location = context.get("location", "United States") if context else "United States"
                language = context.get("language", "en") if context else "en"
                
                logger.info(f"Analyzing LLM mentions for keyword: {keywords[0]}")
                # Get LLM mentions for primary keyword
                mentions = await self.dataforseo_client.get_llm_mentions_search(
                    target=keywords[0],
                    target_type="keyword",
                    location_name=location,
                    language_code=language,
                    tenant_id=tenant_id,
                    platform="auto",  # Auto tries chat_gpt first, then google
                    limit=20
                )
                
                if mentions and mentions.get("top_pages"):
                    llm_mentions_data = mentions
                    top_pages = mentions.get("top_pages", [])[:10]
                    
                    # Analyze citation patterns
                    citation_patterns = {
                        "top_cited_pages": top_pages[:5],
                        "common_domains": [],
                        "avg_mentions": 0,
                        "content_structure_insights": []
                    }
                    
                    # Extract common domains
                    domains = {}
                    for page in top_pages:
                        domain = page.get("domain", "")
                        if domain:
                            domains[domain] = domains.get(domain, 0) + 1
                    citation_patterns["common_domains"] = sorted(domains.items(), key=lambda x: x[1], reverse=True)[:5]
                    
                    # Calculate average mentions
                    total_mentions = sum(page.get("mentions", 0) for page in top_pages)
                    citation_patterns["avg_mentions"] = total_mentions / len(top_pages) if top_pages else 0
                    
                    # Extract content structure insights from top-cited pages
                    structure_insights = []
                    for page in top_pages[:5]:
                        title = page.get("title", "")
                        if title:
                            # Analyze heading patterns (question-based, etc.)
                            if "?" in title:
                                structure_insights.append("Question-based headings")
                            if len(title.split()) <= 10:
                                structure_insights.append("Concise titles")
                    citation_patterns["content_structure_insights"] = list(set(structure_insights))
                    
                    logger.info(f"Found {len(top_pages)} top-cited pages with citation patterns")
            except Exception as e:
                error_msg = f"DataForSEO LLM Mentions API unavailable: {str(e)}"
                logger.error(f"LLM mentions analysis failed: {error_msg}", exc_info=True)
                api_warnings.append(f"AI citation optimization unavailable: LLM Mentions API error. Content generated without AI citation pattern analysis.")
                logger.warning(f"API_UNAVAILABLE: DataForSEO LLM Mentions API failed for keyword '{keywords[0]}'. Error: {type(e).__name__}: {str(e)}")
        else:
            if not self.dataforseo_client or not self.dataforseo_client.is_configured:
                warning_msg = "DataForSEO client not configured - LLM Mentions analysis skipped"
                logger.warning(warning_msg)
                api_warnings.append("AI citation optimization unavailable: DataForSEO client not configured.")
        
        # Google Search Console: Content opportunities and gaps (if available)
        gsc_opportunities = None
        gsc_content_gaps = None
        if self.search_console and keywords:
            try:
                logger.info(f"Analyzing Google Search Console data for keywords: {keywords[:3]}")
                
                # Get content opportunities (high impressions, low CTR)
                opportunities = await self.search_console.identify_content_opportunities(
                    min_impressions=50,
                    max_position=20.0,
                    min_ctr_threshold=0.02
                )
                if opportunities:
                    gsc_opportunities = opportunities[:10]  # Top 10 opportunities
                    logger.info(f"Found {len(gsc_opportunities)} content opportunities from Search Console")
                
                # Get content gaps for target keywords
                gaps = await self.search_console.get_content_gaps(target_keywords=keywords)
                if gaps and gaps.get("gaps"):
                    gsc_content_gaps = gaps
                    logger.info(f"Found {gaps.get('gaps_found', 0)} content gaps for target keywords")
                
            except Exception as e:
                error_msg = f"Google Search Console API unavailable: {str(e)}"
                logger.warning(f"GSC analysis failed: {error_msg}")
                api_warnings.append(f"Search Console optimization unavailable: GSC API error. Content generated without site-specific performance data.")
                logger.warning(f"API_UNAVAILABLE: Google Search Console API failed. Error: {type(e).__name__}: {str(e)}")
        
        # Priority 3: Query LLM Responses for research
        llm_responses_data = None
        if self.dataforseo_client and self.dataforseo_client.is_configured:
            try:
                tenant_id = os.getenv("TENANT_ID", "default")
                
                # Query multiple LLMs about the topic
                research_prompt = f"What are the key points, questions, and important aspects to cover when writing about '{topic}'? Focus on what readers need to know and what makes content authoritative on this topic."
                
                logger.info(f"Querying LLMs for research: {topic}")
                llm_responses = await self.dataforseo_client.get_llm_responses(
                    prompt=research_prompt,
                    llms=["chatgpt", "claude"],  # Query ChatGPT and Claude
                    max_tokens=500,
                    tenant_id=tenant_id
                )
                
                if llm_responses and llm_responses.get("responses"):
                    llm_responses_data = llm_responses
                    
                    # Extract key points from responses
                    key_points = []
                    for llm_name, response_data in llm_responses.get("responses", {}).items():
                        text = response_data.get("text", "")
                        if text:
                            # Extract bullet points or key sentences
                            lines = text.split('\n')
                            for line in lines[:10]:  # Top 10 lines
                                line = line.strip()
                                if line and (line.startswith('-') or line.startswith('•') or len(line) > 50):
                                    key_points.append(f"{llm_name.upper()}: {line}")
                    
                    if key_points:
                        llm_responses_data["extracted_key_points"] = key_points[:10]
                        logger.info(f"Extracted {len(key_points)} key points from LLM responses")
            except Exception as e:
                error_msg = f"DataForSEO LLM Responses API unavailable: {str(e)}"
                logger.error(f"LLM responses research failed: {error_msg}", exc_info=True)
                api_warnings.append(f"AI research optimization unavailable: LLM Responses API error. Content generated without AI agent research insights.")
                logger.warning(f"API_UNAVAILABLE: DataForSEO LLM Responses API failed for topic '{topic}'. Error: {type(e).__name__}: {str(e)}")
        
        # Build research prompt
        research_context = context or {}
        if competitor_analysis:
            research_context["competitor_analysis"] = competitor_analysis
        if brand_recommendations:
            research_context["brand_recommendations"] = brand_recommendations
        if citation_patterns:
            research_context["citation_patterns"] = citation_patterns
            research_context["llm_mentions"] = llm_mentions_data
        if llm_responses_data:
            research_context["llm_responses"] = llm_responses_data
        if gsc_opportunities:
            research_context["gsc_opportunities"] = gsc_opportunities
        if gsc_content_gaps:
            research_context["gsc_content_gaps"] = gsc_content_gaps
        
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
        
        # Store citation patterns and LLM responses in metadata for use in draft stage
        metadata = {"stage": "research_outline", "keywords": keywords, "api_warnings": api_warnings}
        if citation_patterns:
            metadata["citation_patterns"] = citation_patterns
        if llm_responses_data:
            metadata["llm_responses"] = llm_responses_data
        
        return PipelineStageResult(
            content=response.content,
            metadata=metadata,
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
        # Increase max_tokens to ensure we can generate long content
        word_count_target = self.prompt_builder._get_word_count(length)
        max_tokens = int(word_count_target * 2.5)  # Increased multiplier to 2.5x to ensure enough tokens for long content
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
        
        # Extract meta title with validation
        title_match = re.search(r'Meta Title[:\s]+(.+)', seo_response, re.IGNORECASE)
        if title_match:
            extracted_title = title_match.group(1).strip()
            # Validate title - reject if it's just "**" or too short
            if extracted_title and extracted_title != "**" and len(extracted_title) > 3:
                metadata["meta_title"] = extracted_title
            else:
                logger.warning(f"Invalid title extracted: '{extracted_title}', will use fallback")
        
        # Extract meta description
        desc_match = re.search(r'Meta Description[:\s]+(.+)', seo_response, re.IGNORECASE)
        if desc_match:
            metadata["meta_description"] = desc_match.group(1).strip()
        
        # Extract internal links - but don't set here as they're generated properly in _generate_and_insert_internal_links
        # The internal_links will be set from the actual link generation method
        # links_match = re.findall(r'Internal Link[:\s]+(.+?)(?:\n|$)', seo_response, re.IGNORECASE)
        # if links_match:
        #     metadata["internal_links"] = [link.strip() for link in links_match]
        
        return metadata
    
    def _validate_and_fix_content_structure(
        self,
        content: str,
        topic: str,
        keywords: List[str],
        length: Union[ContentLength, str]
    ) -> str:
        """
        Validate and fix content structure (H2 count, length, etc.).
        
        Args:
            content: Content to validate
            topic: Blog topic
            keywords: Keywords list
            length: Target content length
            
        Returns:
            Fixed content
        """
        lines = content.split('\n')
        h1_count = sum(1 for line in lines if line.strip().startswith('# ') and not line.strip().startswith('##'))
        h2_count = sum(1 for line in lines if line.strip().startswith('## ') and not line.strip().startswith('###'))
        word_count = len(content.split())
        target_word_count = self.prompt_builder._get_word_count(length)
        
        issues = []
        
        # Check H1 count
        if h1_count == 0:
            issues.append("Missing H1 heading")
            # Add H1 at the beginning
            content = f"# {topic}\n\n{content}"
        elif h1_count > 1:
            issues.append(f"Multiple H1 headings found ({h1_count}), should be exactly 1")
        
        # Check H2 count (should be 3-5 minimum)
        if h2_count < 3:
            issues.append(f"Insufficient H2 headings ({h2_count}), minimum 3 required")
            logger.warning(f"Content has only {h2_count} H2 headings, minimum 3 required")
            # Try to identify sections that should be H2
            # This is a basic fix - in production, might want to regenerate sections
            content = self._promote_headings_to_h2(content, keywords)
        
        # Check content length
        if word_count < target_word_count * 0.7:  # Allow 30% tolerance
            issues.append(f"Content too short ({word_count} words, target: {target_word_count})")
            logger.warning(f"Content length ({word_count} words) is below target ({target_word_count} words)")
            # Note: We can't easily expand content here, but we log the issue
        
        if issues:
            logger.warning(f"Content structure issues found: {', '.join(issues)}")
        
        return content
    
    def _promote_headings_to_h2(self, content: str, keywords: List[str]) -> str:
        """
        Promote some H3 headings to H2 if H2 count is insufficient.
        
        Args:
            content: Content to fix
            keywords: Keywords for context
            
        Returns:
            Fixed content
        """
        lines = content.split('\n')
        fixed_lines = []
        h2_count = 0
        h3_promoted = 0
        
        for i, line in enumerate(lines):
            # Count current H2
            if line.strip().startswith('## ') and not line.strip().startswith('###'):
                h2_count += 1
                fixed_lines.append(line)
            # Promote first few H3s to H2 if needed
            elif line.strip().startswith('### ') and h2_count < 3 and h3_promoted < 2:
                # Promote to H2
                fixed_lines.append(line.replace('###', '##', 1))
                h2_count += 1
                h3_promoted += 1
            else:
                fixed_lines.append(line)
        
        if h3_promoted > 0:
            logger.info(f"Promoted {h3_promoted} H3 headings to H2 to meet minimum requirement")
        
        return '\n'.join(fixed_lines)
    
    async def _generate_and_insert_internal_links(
        self,
        content: str,
        keywords: List[str],
        topic: str,
        internal_link_targets: Optional[List[Dict[str, Any]]] = None,
        site_domain: Optional[str] = None,
        max_links: int = 5
    ) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Generate and insert internal links into content.
        
        If internal_link_targets are provided by frontend, use those.
        Otherwise, fall back to generating placeholder links from keywords.
        
        Args:
            content: Content to add links to
            keywords: Keywords for link generation (fallback)
            topic: Blog topic
            internal_link_targets: Optional list of actual link targets from frontend/database
            site_domain: Site domain for URL generation
            max_links: Maximum number of links to insert
            
        Returns:
            Tuple of (content with links, inserted_links_list, internal_links_metadata)
        """
        # Determine link sources
        if internal_link_targets and len(internal_link_targets) > 0:
            # Use provided link targets (preferred)
            logger.info(f"Using {len(internal_link_targets)} provided internal link targets")
            link_sources = []
            for target in internal_link_targets:
                # Handle both dict and model formats
                if hasattr(target, 'dict'):
                    target = target.dict()
                
                url = target.get('url', '')
                # Ensure full URL if site_domain provided and URL is relative
                if site_domain and url.startswith('/'):
                    url = site_domain.rstrip('/') + url
                
                link_sources.append({
                    'anchor_text': target.get('title', ''),
                    'url': url,
                    'target_title': target.get('title', ''),
                    'keywords': target.get('keywords', []),
                    'type': target.get('type', 'cms'),
                })
            available_count = len(internal_link_targets)
        else:
            # Fallback: Generate placeholder links from keywords
            logger.warning("No internal link targets provided, generating placeholder links from keywords")
            link_sources = []
            for keyword in keywords[:max_links]:
                slug = keyword.lower().replace(' ', '-').replace(',', '').replace('.', '')
                url = f"/{slug}" if not site_domain else f"{site_domain.rstrip('/')}/{slug}"
                link_sources.append({
                    'anchor_text': keyword,
                    'url': url,
                    'target_title': keyword.title(),
                    'keywords': [keyword],
                    'type': 'generated',
                })
            available_count = len(link_sources)
        
        # First, check if content already has placeholder links from AI generation
        placeholder_link_pattern = r'\[([^\]]+)\]\(/([^\)]+)\)'
        existing_placeholder_links = re.findall(placeholder_link_pattern, content)
        
        # If placeholder links exist and we have site_domain or internal_link_targets, replace them
        if existing_placeholder_links and (site_domain or (internal_link_targets and len(internal_link_targets) > 0)):
            logger.info(f"Found {len(existing_placeholder_links)} placeholder links, replacing with real URLs")
            lines = content.split('\n')
            fixed_lines = []
            links_inserted = 0
            inserted_links = []
            used_urls = set()
            
            # Track content position for metadata
            current_section = "introduction"
            h2_count = 0
            total_lines = len(lines)
            
            for i, line in enumerate(lines):
                # Track position in content
                if line.strip().startswith('## '):
                    h2_count += 1
                    if h2_count == 1:
                        current_section = "body"
                    elif 'conclusion' in line.lower() or i > total_lines * 0.8:
                        current_section = "conclusion"
                
                # Replace placeholder links with real URLs
                for anchor_text, slug in existing_placeholder_links:
                    if links_inserted >= max_links:
                        break
                    
                    # Skip if in conclusion or resources section
                    if current_section == "conclusion" or 'resources' in line.lower():
                        continue
                    
                    placeholder_pattern = f'\\[{re.escape(anchor_text)}\\]\\(/{re.escape(slug)}\\)'
                    if re.search(placeholder_pattern, line):
                        # Try to find matching link target
                        matched = False
                        for link_info in link_sources:
                            if link_info['url'] in used_urls:
                                continue
                            
                            # Match by slug or anchor text similarity
                            link_slug = link_info['url'].split('/')[-1] if '/' in link_info['url'] else link_info['url']
                            if slug.lower() in link_slug.lower() or anchor_text.lower() in link_info['anchor_text'].lower():
                                # Replace placeholder with real URL
                                real_url = link_info['url']
                                if site_domain and not real_url.startswith('http'):
                                    if real_url.startswith('/'):
                                        real_url = site_domain.rstrip('/') + real_url
                                    else:
                                        real_url = f"{site_domain.rstrip('/')}/{real_url}"
                                
                                line = re.sub(placeholder_pattern, f'[{anchor_text}]({real_url})', line)
                                links_inserted += 1
                                used_urls.add(link_info['url'])
                                inserted_links.append({
                                    'anchor_text': anchor_text,
                                    'url': real_url,
                                    'target_title': link_info.get('target_title', ''),
                                    'position': current_section,
                                    'relevance_score': 0.7,
                                    'text': anchor_text,
                                })
                                matched = True
                                logger.info(f"Replaced placeholder link: {anchor_text} -> {real_url} ({current_section})")
                                break
                        
                        if not matched and site_domain:
                            # No match found, but we have site_domain - convert to absolute URL
                            real_url = f"{site_domain.rstrip('/')}/{slug}"
                            line = re.sub(placeholder_pattern, f'[{anchor_text}]({real_url})', line)
                            links_inserted += 1
                            inserted_links.append({
                                'anchor_text': anchor_text,
                                'url': real_url,
                                'target_title': slug.replace('-', ' ').title(),
                                'position': current_section,
                                'relevance_score': 0.5,
                                'text': anchor_text,
                            })
                            logger.info(f"Converted placeholder to absolute URL: {anchor_text} -> {real_url}")
                
                fixed_lines.append(line)
        else:
            # No placeholder links found, use existing insertion logic
            # Find natural insertion points in content
            lines = content.split('\n')
            fixed_lines = []
            links_inserted = 0
            target_link_count = min(max_links, len(link_sources))
            inserted_links = []
            used_urls = set()  # Avoid duplicate links
            
            # Track content position for metadata
            current_section = "introduction"
            h2_count = 0
            total_lines = len(lines)
            
            for i, line in enumerate(lines):
                fixed_lines.append(line)
                
                # Track position in content
                if line.strip().startswith('## '):
                    h2_count += 1
                    if h2_count == 1:
                        current_section = "body"
                    elif 'conclusion' in line.lower() or i > total_lines * 0.8:
                        current_section = "conclusion"
                
                # Skip conclusion and resources sections
                if current_section == "conclusion" or 'resources' in line.lower():
                    continue
                
                # Insert links in paragraphs (not in headings or code blocks)
                if (links_inserted < target_link_count and 
                    line.strip() and 
                    not line.strip().startswith('#') and
                    not line.strip().startswith('```') and
                    not line.strip().startswith('![') and
                    not line.strip().startswith('|') and  # Skip table rows
                    len(line.strip()) > 50):
                    
                    # Check if any link source matches this line
                    for link_info in link_sources:
                        if link_info['url'] in used_urls:
                            continue
                        
                        # Try to find anchor text in line
                        anchor_text = link_info['anchor_text']
                        anchor_lower = anchor_text.lower()
                        line_lower = line.lower()
                        
                        # Also check keywords associated with this link
                        keywords_to_check = [anchor_lower] + [k.lower() for k in link_info.get('keywords', [])]
                        
                        for keyword in keywords_to_check:
                            if keyword in line_lower and links_inserted < target_link_count:
                                idx = line_lower.find(keyword)
                                if idx != -1:
                                    before = line[:idx]
                                    # Check if already linked
                                    if '[' not in before[-20:] and '](' not in before[-20:]:
                                        keyword_text = line[idx:idx+len(keyword)]
                                        after = line[idx+len(keyword):]
                                        
                                        # Use real URL if available, otherwise placeholder
                                        url_to_use = link_info['url']
                                        if site_domain and not url_to_use.startswith('http'):
                                            if url_to_use.startswith('/'):
                                                url_to_use = site_domain.rstrip('/') + url_to_use
                                            else:
                                                url_to_use = f"{site_domain.rstrip('/')}/{url_to_use}"
                                        
                                        linked_keyword = f"[{keyword_text}]({url_to_use})"
                                        fixed_lines[-1] = before + linked_keyword + after
                                        links_inserted += 1
                                        used_urls.add(link_info['url'])
                                        
                                        # Calculate simple relevance score based on keyword match
                                        relevance = 0.8 if keyword == anchor_lower else 0.6
                                        
                                        inserted_links.append({
                                            'anchor_text': keyword_text,
                                            'url': url_to_use,
                                            'target_title': link_info.get('target_title', ''),
                                            'position': current_section,
                                            'relevance_score': relevance,
                                            # Legacy format fields for backwards compatibility
                                            'text': keyword_text,
                                        })
                                        logger.info(f"Inserted internal link: {keyword_text} -> {url_to_use} ({current_section})")
                                        break
                            if links_inserted >= target_link_count:
                                break
                        if links_inserted >= target_link_count:
                            break
        
        if links_inserted > 0:
            logger.info(f"Inserted {links_inserted} internal links into content")
        else:
            logger.warning("No internal links were inserted - content may need manual review")
        
        # Build metadata for response
        internal_links_metadata = {
            'inserted': inserted_links,
            'available_count': available_count,
            'inserted_count': links_inserted,
            'max_allowed': max_links,
        }
        
        # Legacy format for backwards compatibility
        legacy_links = [{'text': link['anchor_text'], 'url': link['url']} for link in inserted_links]
        
        return '\n'.join(fixed_lines), legacy_links, internal_links_metadata
    

