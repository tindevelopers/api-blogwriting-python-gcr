"""
FastAPI application for the Blog Writer SDK.

This module provides a REST API wrapper around the Blog Writer SDK,
enabling web-based access to all blog generation and optimization features.
"""

import os
import time
import logging
import asyncio
import uuid
import math
import json
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from contextlib import asynccontextmanager
import jwt

# Track startup time for uptime calculation
startup_time = time.time()

# Deployment trigger - updated timestamp
deployment_version = "2025-11-15-001"
APP_VERSION = os.getenv("APP_VERSION", "1.3.5")

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from enum import Enum

from src.blog_writer_sdk import BlogWriter
from src.blog_writer_sdk.models.blog_models import (
    BlogRequest,
    BlogGenerationResult,
    ContentTone,
    ContentLength,
    ContentFormat,
)
from src.blog_writer_sdk.seo.enhanced_keyword_analyzer import EnhancedKeywordAnalyzer
from src.blog_writer_sdk.seo.keyword_clustering import KeywordClustering
from src.blog_writer_sdk.ai.ai_content_generator import AIContentGenerator
from src.blog_writer_sdk.config.testing_limits import (
    is_testing_mode,
    apply_keyword_limits,
    apply_suggestions_limit,
    apply_clustering_limits,
    get_testing_limits
)
from src.blog_writer_sdk.ai import (
    BlogWriterAbstraction,
    BlogWriterFactory,
    BlogWriterPreset,
    BlogGenerationRequest as AbstractionBlogRequest,
    ContentStrategy,
    ContentQuality
)
# LiteLLM router removed - using direct AI provider integrations
from src.blog_writer_sdk.middleware.rate_limiter import rate_limit_middleware
from src.blog_writer_sdk.cache.redis_cache import initialize_cache, get_cache_manager
from src.blog_writer_sdk.monitoring.metrics import initialize_metrics, get_metrics_collector, monitor_performance
from src.blog_writer_sdk.monitoring.cloud_logging import initialize_cloud_logging, get_blog_logger, log_blog_generation, log_api_request

# Initialize logger
logger = get_blog_logger()

# Credential services not implemented yet - using direct environment variables
# from src.blog_writer_sdk.services.credential_service import TenantCredentialService
# from src.blog_writer_sdk.services.dataforseo_credential_service import DataForSEOCredentialService
# from src.blog_writer_sdk.models.credential_models import DataForSEOCredentials, TenantCredentialStatus
from src.blog_writer_sdk.integrations.dataforseo_integration import DataForSEOClient

# Global DataForSEO client for Phase 3 semantic integration
dataforseo_client_global = None

from src.blog_writer_sdk.integrations import (
    WebflowClient, WebflowPublisher,
    ShopifyClient, ShopifyPublisher,
    CloudinaryStorage, CloudflareR2Storage, MediaStorageManager,
    GoogleReviewsClient, ReviewAggregationService
)
try:
    # Optional: WordPress not installed in this repo currently
    from src.blog_writer_sdk.integrations.wordpress_integration import WordPressClient, WordPressPublisher  # type: ignore
    WORDPRESS_AVAILABLE = True
except Exception:
    WORDPRESS_AVAILABLE = False

from google.cloud import secretmanager
from supabase import create_client, Client
from src.blog_writer_sdk.integrations.supabase_client import SupabaseClient
from src.blog_writer_sdk.batch.batch_processor import BatchProcessor
from src.blog_writer_sdk.api.ai_provider_management import router as ai_provider_router, initialize_from_env
from src.blog_writer_sdk.api.image_generation import router as image_generation_router, initialize_image_providers_from_env
from src.blog_writer_sdk.api.integration_management import router as integrations_router
from src.blog_writer_sdk.api.user_management import router as user_management_router
from src.blog_writer_sdk.api.keyword_streaming import (
    KeywordSearchStage,
    create_stage_update,
    stream_stage_update
)
from src.blog_writer_sdk.models.enhanced_blog_models import (
    EnhancedBlogGenerationRequest,
    EnhancedBlogGenerationResponse
)
from src.blog_writer_sdk.models.job_models import (
    BlogGenerationJob,
    JobStatus,
    JobStatusResponse,
    CreateJobResponse
)
from src.blog_writer_sdk.services.cloud_tasks_service import get_cloud_tasks_service

# In-memory job storage (can be upgraded to Supabase/database later)
blog_generation_jobs: Dict[str, BlogGenerationJob] = {}
from src.blog_writer_sdk.ai.multi_stage_pipeline import MultiStageGenerationPipeline
from src.blog_writer_sdk.ai.enhanced_prompts import PromptTemplate
from src.blog_writer_sdk.integrations.google_custom_search import GoogleCustomSearchClient
from src.blog_writer_sdk.integrations.google_knowledge_graph import GoogleKnowledgeGraphClient
from src.blog_writer_sdk.seo.readability_analyzer import ReadabilityAnalyzer
from src.blog_writer_sdk.seo.citation_generator import CitationGenerator
from src.blog_writer_sdk.seo.serp_analyzer import SERPAnalyzer
from src.blog_writer_sdk.seo.semantic_keyword_integrator import SemanticKeywordIntegrator
from src.blog_writer_sdk.seo.content_quality_scorer import ContentQualityScorer
from src.blog_writer_sdk.seo.intent_analyzer import IntentAnalyzer
from src.blog_writer_sdk.seo.few_shot_learning import FewShotLearningExtractor
from src.blog_writer_sdk.seo.content_length_optimizer import ContentLengthOptimizer
from src.blog_writer_sdk.seo.topic_recommender import TopicRecommendationEngine
from src.blog_writer_sdk.integrations.google_search_console import GoogleSearchConsoleClient
from src.blog_writer_sdk.seo.keyword_difficulty_analyzer import KeywordDifficultyAnalyzer
from src.blog_writer_sdk.services.quota_manager import QuotaManager
from src.blog_writer_sdk.middleware.rate_limiter import RateLimitTier
from src.blog_writer_sdk.utils.content_metadata import extract_content_metadata


# API Request/Response Models
class BlogGenerationRequest(BaseModel):
    """Request model for blog generation API."""
    topic: str = Field(..., min_length=3, max_length=200, description="Main topic for the blog post")
    keywords: List[str] = Field(default_factory=list, max_items=20, description="Target SEO keywords")
    tone: ContentTone = Field(default=ContentTone.PROFESSIONAL, description="Writing tone")
    length: ContentLength = Field(default=ContentLength.MEDIUM, description="Target content length")
    format: ContentFormat = Field(default=ContentFormat.MARKDOWN, description="Output format")
    
    # SEO Configuration
    target_audience: Optional[str] = Field(None, max_length=200, description="Target audience description")
    focus_keyword: Optional[str] = Field(None, max_length=100, description="Primary focus keyword")
    
    # Content Structure
    include_introduction: bool = Field(default=True, description="Include introduction section")
    include_conclusion: bool = Field(default=True, description="Include conclusion section")
    include_faq: bool = Field(default=False, description="Include FAQ section")
    include_toc: bool = Field(default=True, description="Include table of contents")
    
    # Advanced Options
    word_count_target: Optional[int] = Field(None, ge=100, le=10000, description="Specific word count target")
    custom_instructions: Optional[str] = Field(None, max_length=1000, description="Additional instructions")


class ContentAnalysisRequest(BaseModel):
    """Request model for content analysis API."""
    content: str = Field(..., min_length=50, description="Content to analyze")
    title: Optional[str] = Field(None, max_length=200, description="Content title")
    keywords: List[str] = Field(default_factory=list, max_length=20, description="Keywords to analyze for")


class KeywordAnalysisRequest(BaseModel):
    """Request model for keyword analysis."""
    keywords: List[str] = Field(..., max_length=200, description="Keywords to analyze (up to 200)")
    location: Optional[str] = Field("United States", description="Location for keyword analysis")
    language: Optional[str] = Field("en", description="Language code for analysis")
    search_type: Optional[str] = Field("keyword_analysis", description="Keyword search type (e.g., keyword_analysis, competitor)")
    text: Optional[str] = Field(None, description="Optional text content (ignored if keywords provided)")
    max_suggestions_per_keyword: Optional[int] = Field(None, description="Optional: if provided, routes to enhanced analysis")
    
    class Config:
        extra = "ignore"  # Ignore extra fields to be more flexible with frontend requests

class EnhancedKeywordAnalysisRequest(BaseModel):
    """Request model for enhanced keyword analysis with DataForSEO."""
    keywords: List[str] = Field(..., max_length=200, description="Keywords to analyze (up to 200 for comprehensive research)")
    location: Optional[str] = Field("United States", description="Location for keyword analysis")
    language: Optional[str] = Field("en", description="Language code for analysis")
    search_type: Optional[str] = Field("enhanced_keyword_analysis", description="Keyword search type (e.g., keyword_analysis, competitor, enhanced_keyword_analysis)")
    include_serp: bool = Field(default=False, description="Include SERP scrape preview (slower)")
    max_suggestions_per_keyword: int = Field(default=20, ge=5, le=150, description="Maximum keyword suggestions per seed keyword (up to 150 for comprehensive research)")

class TopicRecommendationRequest(BaseModel):
    """Request model for topic recommendations."""
    seed_keywords: List[str] = Field(..., min_items=1, max_length=10, description="Seed keywords to base recommendations on")
    location: Optional[str] = Field("United States", description="Location for search volume analysis")
    language: Optional[str] = Field("en", description="Language code")
    max_topics: int = Field(default=20, ge=5, le=50, description="Maximum number of topics to return")
    min_search_volume: int = Field(default=100, ge=0, description="Minimum monthly search volume")
    max_difficulty: float = Field(default=70.0, ge=0, le=100, description="Maximum keyword difficulty (0-100)")
    include_ai_suggestions: bool = Field(default=True, description="Use Claude AI for intelligent topic generation")


class KeywordDifficultyRequest(BaseModel):
    """Request model for keyword difficulty analysis."""
    keyword: str = Field(..., min_length=1, description="Keyword to analyze")
    search_volume: int = Field(default=0, ge=0, description="Monthly search volume")
    difficulty: float = Field(default=50.0, ge=0, le=100, description="Basic difficulty score")
    competition: float = Field(default=0.5, ge=0, le=1, description="Competition index")
    location: str = Field(default="United States", description="Location for analysis")
    language: str = Field(default="en", description="Language code")


class SetQuotaLimitsRequest(BaseModel):
    """Request model for setting quota limits."""
    monthly_limit: Optional[int] = Field(None, ge=1, description="Monthly quota limit")
    daily_limit: Optional[int] = Field(None, ge=1, description="Daily quota limit")
    hourly_limit: Optional[int] = Field(None, ge=1, description="Hourly quota limit")


class PlatformPublishRequest(BaseModel):
    """Request model for platform publishing."""
    blog_result: BlogGenerationResult = Field(..., description="Generated blog content to publish")
    platform: str = Field(..., description="Target platform (webflow, shopify, wordpress)")
    publish: bool = Field(default=True, description="Whether to publish immediately")
    categories: Optional[List[str]] = Field(default_factory=list, description="Categories for the content")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags for the content")
    media_files: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Media files to upload")


class MediaUploadRequest(BaseModel):
    """Request model for media upload."""
    media_data: str = Field(..., description="Base64 encoded media data")
    filename: str = Field(..., description="Original filename")
    folder: Optional[str] = Field(None, description="Upload folder")
    alt_text: Optional[str] = Field(None, description="Alt text for images")
    caption: Optional[str] = Field(None, description="Caption for media")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class KeywordExtractionRequest(BaseModel):
    """Request model for keyword extraction API."""
    content: str = Field(..., min_length=100, description="Content to extract keywords from")
    max_keywords: int = Field(default=20, ge=5, le=200, description="Maximum keywords to extract (up to 200 for comprehensive research)")
    max_ngram: int = Field(default=3, ge=1, le=5, description="Maximum words per keyphrase (phrase mode)")
    dedup_lim: float = Field(default=0.7, ge=0.1, le=0.99, description="Deduplication threshold for phrases")


class KeywordSuggestionRequest(BaseModel):
    """Request model for keyword suggestions."""
    keyword: str = Field(..., min_length=2, max_length=100, description="Base keyword for suggestions")
    limit: int = Field(default=20, ge=5, le=150, description="Maximum number of keyword suggestions to return (up to 150 for comprehensive research)")


class ContentOptimizationRequest(BaseModel):
    """Request model for content optimization."""
    content: str = Field(..., min_length=100, description="Content to optimize")
    keywords: List[str] = Field(default_factory=list, max_length=20, description="Target keywords")
    focus_keyword: Optional[str] = Field(None, description="Primary focus keyword")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: float
    version: str


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str
    timestamp: float


class BlogType(str, Enum):
    """Blog generation type enumeration."""
    STANDARD = "standard"
    ENHANCED = "enhanced"
    LOCAL_BUSINESS = "local_business"
    ABSTRACTION = "abstraction"


class UnifiedBlogRequest(BaseModel):
    """
    Unified blog generation request model.
    
    This model supports all blog types through a single endpoint.
    Type-specific fields are optional and only used when relevant.
    """
    # Required
    blog_type: BlogType = Field(..., description="Type of blog to generate")
    topic: str = Field(..., min_length=3, max_length=200, description="Main topic for the blog post")
    
    # Common fields (used by all blog types)
    keywords: List[str] = Field(default_factory=list, max_items=20, description="Target SEO keywords")
    tone: ContentTone = Field(default=ContentTone.PROFESSIONAL, description="Writing tone")
    length: ContentLength = Field(default=ContentLength.MEDIUM, description="Target content length")
    format: ContentFormat = Field(default=ContentFormat.MARKDOWN, description="Output format")
    target_audience: Optional[str] = Field(None, max_length=200, description="Target audience description")
    custom_instructions: Optional[str] = Field(None, max_length=1000, description="Additional instructions")
    
    # Standard & Enhanced fields
    include_introduction: bool = Field(default=True, description="Include introduction section (standard/enhanced)")
    include_conclusion: bool = Field(default=True, description="Include conclusion section (standard/enhanced)")
    include_faq: bool = Field(default=False, description="Include FAQ section (standard/enhanced)")
    include_toc: bool = Field(default=True, description="Include table of contents (standard/enhanced)")
    focus_keyword: Optional[str] = Field(None, max_length=100, description="Primary focus keyword (standard/enhanced)")
    word_count_target: Optional[int] = Field(None, ge=100, le=10000, description="Specific word count target (standard/enhanced)")
    
    # Enhanced-specific fields
    use_google_search: bool = Field(default=True, description="Use Google Custom Search for research (enhanced)")
    use_fact_checking: bool = Field(default=True, description="Enable fact-checking (enhanced)")
    use_citations: bool = Field(default=True, description="Include citations and sources (enhanced)")
    use_serp_optimization: bool = Field(default=True, description="Optimize for SERP features (enhanced)")
    use_consensus_generation: bool = Field(default=False, description="Use multi-model consensus generation (enhanced)")
    use_knowledge_graph: bool = Field(default=True, description="Use Google Knowledge Graph for entities (enhanced)")
    use_semantic_keywords: bool = Field(default=True, description="Use semantic keyword integration (enhanced)")
    use_quality_scoring: bool = Field(default=True, description="Enable comprehensive quality scoring (enhanced)")
    template_type: Optional[str] = Field(None, description="Prompt template type (enhanced)")
    async_mode: bool = Field(default=False, description="Create async job via Cloud Tasks (enhanced)")
    
    # Local Business-specific fields
    location: Optional[str] = Field(None, min_length=2, description="Location for local business blogs (required for local_business)")
    max_businesses: int = Field(default=10, ge=1, le=20, description="Maximum number of businesses to include (local_business)")
    max_reviews_per_business: int = Field(default=20, ge=5, le=50, description="Maximum reviews per business (local_business)")
    include_business_details: bool = Field(default=True, description="Include business details (local_business)")
    include_review_sentiment: bool = Field(default=True, description="Include review sentiment analysis (local_business)")
    use_google: bool = Field(default=True, description="Fetch reviews from Google Places (local_business)")
    
    # Abstraction-specific fields
    content_strategy: Optional[str] = Field(None, description="Content strategy (abstraction)")
    quality_target: Optional[str] = Field(None, description="Quality target (abstraction)")
    preferred_provider: Optional[str] = Field(None, description="Preferred AI provider (abstraction)")
    seo_requirements: Optional[Dict[str, Any]] = Field(None, description="SEO requirements (abstraction)")
    
    class Config:
        use_enum_values = True


class LocalBusinessBlogRequest(BaseModel):
    """Request model for local business blog generation."""
    topic: str = Field(..., min_length=3, max_length=200, description="Main topic (e.g., 'best plumbers in Miami')")
    location: str = Field(..., min_length=2, description="Location (e.g., 'Miami, FL', '33139')")
    max_businesses: int = Field(default=10, ge=1, le=20, description="Maximum number of businesses to include")
    max_reviews_per_business: int = Field(default=20, ge=5, le=50, description="Maximum reviews per business")
    tone: ContentTone = Field(default=ContentTone.PROFESSIONAL, description="Writing tone")
    length: ContentLength = Field(default=ContentLength.LONG, description="Target content length")
    format: ContentFormat = Field(default=ContentFormat.MARKDOWN, description="Output format")
    include_business_details: bool = Field(default=True, description="Include business details (hours, contact, services)")
    include_review_sentiment: bool = Field(default=True, description="Include review sentiment analysis")
    use_google: bool = Field(default=True, description="Fetch reviews from Google Places")
    custom_instructions: Optional[str] = Field(None, max_length=1000, description="Additional instructions")


class BusinessInfo(BaseModel):
    """Business information model."""
    name: str
    google_place_id: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    categories: List[str] = Field(default_factory=list)
    hours: Optional[Dict[str, Any]] = None


class LocalBusinessBlogResponse(BaseModel):
    """Response model for local business blog generation."""
    title: str
    content: str
    businesses: List[BusinessInfo]
    total_reviews_aggregated: int
    generation_time_seconds: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Application lifespan management
def load_env_from_secrets():
    """Load environment variables from mounted secrets file.
    
    Note: Individual secrets (set via --update-secrets) take precedence over
    values in the mounted secret file to avoid placeholder values overriding real credentials.
    """
    secrets_file = "/secrets/env"
    if os.path.exists(secrets_file):
        print("📁 Loading environment variables from mounted secrets...")
        loaded_count = 0
        skipped_count = 0
        with open(secrets_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Only set if not already set (individual secrets take precedence)
                    # Also skip placeholder values
                    if key not in os.environ:
                        # Skip placeholder values that look like templates
                        if not (value.startswith('your_') or value.startswith('YOUR_') or 
                                'placeholder' in value.lower() or value == ''):
                            os.environ[key] = value
                            loaded_count += 1
                        else:
                            skipped_count += 1
                    else:
                        skipped_count += 1
        print(f"✅ Environment variables loaded from secrets: {loaded_count} set, {skipped_count} skipped (already set or placeholders)")
    else:
        print("⚠️ No secrets file found at /secrets/env, using system environment variables")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    # Startup
    print("🚀 Blog Writer SDK API starting up...")
    
    # Initialize user management default data
    try:
        from src.blog_writer_sdk.api.user_management import initialize_default_data
        initialize_default_data()
        print("✅ User management initialized with default roles and system admin")
    except Exception as e:
        print(f"⚠️ Failed to initialize user management: {e}")
    
    # Load environment variables from mounted secrets
    load_env_from_secrets()
    
    # Initialize cache manager
    redis_url = os.getenv("REDIS_URL")
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_password = os.getenv("REDIS_PASSWORD")
    
    cache_manager = initialize_cache(
        redis_url=redis_url,
        redis_host=redis_host,
        redis_port=redis_port,
        redis_password=redis_password
    )
    print(f"✅ Cache manager initialized: {cache_manager}")
    
    # Initialize metrics collector
    metrics_collector = initialize_metrics(retention_hours=24)
    print(f"✅ Metrics collector initialized: {metrics_collector}")
    
    # Initialize cloud logging
    cloud_logger = initialize_cloud_logging(
        name="blog_writer_api",
        use_cloud_logging=os.getenv("GOOGLE_CLOUD_PROJECT") is not None
    )
    print(f"✅ Cloud logging initialized: {cloud_logger}")
    
    # Initialize batch processor
    global batch_processor
    blog_writer = get_blog_writer()
    batch_processor = BatchProcessor(
        blog_writer=blog_writer,
        max_concurrent=int(os.getenv("BATCH_MAX_CONCURRENT", "5")),
        max_retries=int(os.getenv("BATCH_MAX_RETRIES", "2"))
    )
    print("✅ Batch processor initialized")
    
    # Initialize AI providers from environment variables
    try:
        await initialize_from_env()
        print("✅ AI providers initialized from environment")
    except Exception as e:
        print(f"⚠️ Failed to initialize AI providers from environment: {e}")
    
    # Initialize image providers from environment variables
    try:
        await initialize_image_providers_from_env()
        print("✅ Image providers initialized from environment")
    except Exception as e:
        print(f"⚠️ Failed to initialize image providers from environment: {e}")
    
    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    if supabase_url and supabase_key:
        global supabase_client, supabase_server_client
        supabase_client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client initialized.")
        try:
            supabase_server_client = SupabaseClient(
                supabase_url=supabase_url,
                supabase_key=supabase_key,
                environment=os.getenv("ENVIRONMENT", "dev"),
            )
            print("✅ Supabase server client initialized.")
        except Exception as supabase_exc:
            supabase_server_client = None
            print(f"⚠️ Supabase server client not initialized: {supabase_exc}")
    else:
        print("⚠️ Supabase credentials not found. Supabase client not initialized.")

    # Initialize Google Secret Manager client
    global secret_manager_client
    secret_manager_client = secretmanager.SecretManagerServiceClient()
    print("✅ Google Secret Manager client initialized.")

    # Initialize DataforSEO Credential Service (not implemented yet)
    global dataforseo_credential_service
    dataforseo_credential_service = None  # Service not implemented yet
    print("⚠️ DataforSEO Credential Service not implemented yet. Using direct environment variables.")

    # Initialize EnhancedKeywordAnalyzer
    global enhanced_keyword_analyzer, dataforseo_client_global
    # Get DataForSEO credentials from environment (loaded from secrets)
    dataforseo_api_key = os.getenv("DATAFORSEO_API_KEY")
    dataforseo_api_secret = os.getenv("DATAFORSEO_API_SECRET")
    if dataforseo_api_key and dataforseo_api_secret:
        enhanced_keyword_analyzer = EnhancedKeywordAnalyzer(
            use_dataforseo=True,
            api_key=dataforseo_api_key,
            api_secret=dataforseo_api_secret,
            location=os.getenv("DATAFORSEO_LOCATION", "United States"),
            language_code=os.getenv("DATAFORSEO_LANGUAGE", "en"),
        )
    else:
        enhanced_keyword_analyzer = EnhancedKeywordAnalyzer(
            use_dataforseo=False  # Disable if credentials not available
        )
    
    # Initialize DataForSEO client for semantic integration (Phase 3)
    if dataforseo_api_key and dataforseo_api_secret:
        dataforseo_client_global = DataForSEOClient(
            api_key=dataforseo_api_key,
            api_secret=dataforseo_api_secret,
            location=os.getenv("DATAFORSEO_LOCATION", "United States"),
            language_code=os.getenv("DATAFORSEO_LANGUAGE", "en"),
        )
        print("✅ DataForSEO Labs client initialized.")
    else:
        dataforseo_client_global = None
        print("⚠️ DataForSEO Labs not configured (DATAFORSEO_API_KEY and DATAFORSEO_API_SECRET)")
    
    print("✅ EnhancedKeywordAnalyzer initialized.")
    
    # Initialize Google Custom Search client (Phase 1)
    global google_custom_search_client
    google_api_key = os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY")
    google_engine_id = os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")
    if google_api_key and google_engine_id:
        google_custom_search_client = GoogleCustomSearchClient(
            api_key=google_api_key,
            search_engine_id=google_engine_id
        )
        print("✅ Google Custom Search client initialized.")
    else:
        google_custom_search_client = None
        print("⚠️ Google Custom Search not configured (GOOGLE_CUSTOM_SEARCH_API_KEY and GOOGLE_CUSTOM_SEARCH_ENGINE_ID)")
    
    # Initialize Google Search Console client (Phase 2)
    global google_search_console_client
    gsc_site_url = os.getenv("GSC_SITE_URL")
    if gsc_site_url:
        google_search_console_client = GoogleSearchConsoleClient(site_url=gsc_site_url)
        print("✅ Google Search Console client initialized.")
    else:
        google_search_console_client = None
        print("⚠️ Google Search Console not configured (GSC_SITE_URL)")
    
    # Initialize multi-stage pipeline components
    global readability_analyzer, citation_generator, serp_analyzer
    global google_knowledge_graph_client, semantic_integrator, quality_scorer
    global intent_analyzer, few_shot_extractor, length_optimizer
    readability_analyzer = ReadabilityAnalyzer()
    citation_generator = CitationGenerator(google_search_client=google_custom_search_client)
    serp_analyzer = SERPAnalyzer(dataforseo_client=None)  # Will use DataForSEO if available
    
    # Phase 3: Google Knowledge Graph
    kg_api_key = os.getenv("GOOGLE_KNOWLEDGE_GRAPH_API_KEY")
    if kg_api_key:
        google_knowledge_graph_client = GoogleKnowledgeGraphClient(api_key=kg_api_key)
        print("✅ Google Knowledge Graph client initialized.")
    else:
        google_knowledge_graph_client = None
        print("⚠️ Google Knowledge Graph not configured (GOOGLE_KNOWLEDGE_GRAPH_API_KEY)")
    
    # Phase 3: Semantic keyword integrator (uses DataForSEO if available)
    semantic_integrator = SemanticKeywordIntegrator(dataforseo_client=dataforseo_client_global)
    quality_scorer = ContentQualityScorer(readability_analyzer=readability_analyzer)
    
    # Additional enhancements: Intent analysis, few-shot learning, length optimization
    intent_analyzer = IntentAnalyzer(dataforseo_client=dataforseo_client_global)
    few_shot_extractor = FewShotLearningExtractor(
        google_search_client=google_custom_search_client,
        dataforseo_client=dataforseo_client_global
    )
    length_optimizer = ContentLengthOptimizer(
        google_search_client=google_custom_search_client,
        dataforseo_client=dataforseo_client_global
    )
    print("✅ Phase 3 components initialized.")
    print("✅ Additional enhancements initialized (intent analysis, few-shot learning, length optimization).")
    
    # Initialize Topic Recommendation Engine
    global topic_recommender
    from src.blog_writer_sdk.seo.keyword_clustering import KeywordClustering
    keyword_clustering = KeywordClustering(knowledge_graph_client=google_knowledge_graph_client)
    topic_recommender = TopicRecommendationEngine(
        dataforseo_client=dataforseo_client_global,
        google_search_client=google_custom_search_client,
        ai_generator=ai_generator,
        keyword_clustering=keyword_clustering
    )
    print("✅ Topic Recommendation Engine initialized.")
    
    # Initialize Phase 1-3 services
    global quota_manager, keyword_difficulty_analyzer
    quota_manager = QuotaManager()  # In-memory for now, can be extended with database backend
    keyword_difficulty_analyzer = KeywordDifficultyAnalyzer(dataforseo_client=dataforseo_client_global)
    print("✅ Quota Manager initialized.")
    print("✅ Keyword Difficulty Analyzer initialized.")

    yield
    
    # Shutdown
    print("📝 Blog Writer SDK API shutting down...")
    
    # Cleanup tasks
    if hasattr(metrics_collector, '_cleanup_task') and metrics_collector._cleanup_task:
        metrics_collector._cleanup_task.cancel()
    
    print("✅ Cleanup completed")


# Create FastAPI application
app = FastAPI(
    title="Blog Writer SDK API",
    description="""
    A powerful REST API for AI-driven blog writing with advanced SEO optimization, intelligent routing, and enterprise features.
    
    ## Key Features
    
    ### 🚀 Enhanced Blog Generation (v1.2.0) - NEW
    - **Multi-Stage Pipeline**: 4-stage generation (Research → Draft → Enhancement → SEO)
    - **Intent-Based Optimization**: Automatic search intent detection and content optimization
    - **Few-Shot Learning**: Learns from top-ranking content examples
    - **Content Length Optimization**: Dynamically adjusts based on SERP competition
    - **Multi-Model Consensus**: Optional GPT-4o + Claude synthesis for higher quality
    - **Knowledge Graph Integration**: Entity recognition and structured data
    - **Semantic Keywords**: Natural integration of related keywords
    - **Quality Scoring**: 6-dimensional quality assessment (readability, SEO, structure, factual, uniqueness, engagement)
    
    ### 🤖 AI Provider Management
    - **Dynamic Provider Configuration**: Add, update, and remove AI providers without service restarts
    - **Multi-Provider Support**: OpenAI and Anthropic with automatic fallback
    - **Real-time Health Monitoring**: Live status checks and usage statistics
    - **Secure API Key Management**: Encrypted storage and validation
    - **Provider Switching**: Dynamic switching between providers based on performance
    
    ### 🎨 Image Generation
    - **Multi-Provider Image Generation**: Stability AI with extensible architecture for more providers
    - **Text-to-Image**: Generate images from text prompts with customizable styles and quality
    - **Image Variations**: Create variations of existing images with adjustable strength
    - **Image Upscaling**: Enhance image resolution while preserving quality
    - **Image Editing**: Inpainting and outpainting capabilities for image modification
    - **Asynchronous Processing**: Background job processing for batch operations
    
    ### 📝 Content Generation
    - **AI-Powered Blog Writing**: Generate high-quality blog posts with multiple AI providers
    - **SEO Optimization**: Built-in keyword analysis and content optimization
    - **Multiple Content Types**: Blog posts, introductions, conclusions, FAQs, and more
    - **Quality Assurance**: Content analysis and improvement suggestions
    
    ### 🌐 Platform Publishing
    - **Multi-Platform Support**: Publish directly to Webflow, Shopify, and WordPress
    - **Webflow Integration**: CMS publishing with collection management and media uploads
    - **Shopify Integration**: Blog publishing with automatic product recommendations
    - **WordPress Integration**: REST API publishing with category and tag management
    - **Media Storage**: Cloudinary and Cloudflare R2 support for image and video assets
    
    ### 🔍 SEO & Analytics
    - **DataForSEO Integration**: Real-time keyword research and analysis
    - **Content Optimization**: SEO scoring and improvement recommendations
    - **Competitor Analysis**: Analyze competitor content and strategies
    - **Performance Metrics**: Track content performance and engagement
    
    ### ⚡ Enterprise Features
    - **Batch Processing**: Handle multiple content generation requests
    - **Rate Limiting**: Configurable rate limits and quotas
    - **Caching**: Redis-based caching for improved performance
    - **Monitoring**: Comprehensive metrics and health monitoring
    - **Multi-Environment**: Support for dev, staging, and production environments
    
    ## API Endpoints
    
    ### Enhanced Blog Generation (v1.2.0)
    - `POST /api/v1/blog/generate-enhanced` - High-quality multi-stage blog generation with advanced optimizations
    
    ### Standard Endpoints
    - `POST /api/v1/generate` - Standard blog generation
    - `POST /api/v1/keywords/enhanced` - Enhanced keyword analysis with DataForSEO
    - `POST /api/v1/integrations/connect-and-recommend` - Backlink/interlink recommendations
    
    ## Quick Start
    
    1. **Configure AI Providers**: Use `/api/v1/ai/providers/configure` to add your AI provider credentials
    2. **Generate Enhanced Content**: Use `/api/v1/blog/generate-enhanced` for high-quality blog posts
    3. **Generate Images**: Use `/api/v1/images/generate` to create images from text prompts
    4. **Publish Content**: Use `/api/v1/publish/{platform}` to publish to Webflow, Shopify, or WordPress
    5. **Analyze Keywords**: Use `/api/v1/keywords/enhanced` for comprehensive keyword research
    
    ## Documentation
    
    - 📚 **Enhanced Blog Generation Guide**: See [ENHANCED_BLOG_GENERATION_GUIDE.md](https://github.com/tindevelopers/api-blogwriting-python-gcr/blob/develop/ENHANCED_BLOG_GENERATION_GUIDE.md)
    - 🔧 **Health Checks**: Monitor service health at `/health`
    - 📊 **Metrics**: View usage statistics at `/api/v1/metrics`
    """,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
# Note: FastAPI CORSMiddleware doesn't support wildcard patterns
# Use allow_origin_regex for pattern matching or list exact origins
import re
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js development
        "http://localhost:3001",  # Alternative Next.js port
        "https://blogwriter.develop.tinconnect.com",  # Development frontend
        # Add your production domains here
    ],
    allow_origin_regex=r"https://.*\.(vercel\.app|netlify\.app|tinconnect\.com)$",  # Pattern matching for subdomains
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include AI provider management router
app.include_router(ai_provider_router)

# Include image generation router
app.include_router(image_generation_router)

# Include integrations router
app.include_router(integrations_router)
# Include user management router
app.include_router(user_management_router)
# Add rate limiting middleware (disabled for development)
# app.middleware("http")(rate_limit_middleware)

# Global variables
batch_processor: Optional[BatchProcessor] = None

# Initialize enhanced keyword analyzer if DataForSEO credentials are available
def create_enhanced_keyword_analyzer() -> Optional[EnhancedKeywordAnalyzer]:
    """Create enhanced keyword analyzer with DataForSEO integration if configured."""
    dataforseo_api_key = os.getenv("DATAFORSEO_API_KEY")
    dataforseo_api_secret = os.getenv("DATAFORSEO_API_SECRET")
    
    if dataforseo_api_key and dataforseo_api_secret:
        try:
            # Use the enhanced keyword analyzer with direct DataForSEO integration
            return EnhancedKeywordAnalyzer(
                use_dataforseo=True,
                api_key=dataforseo_api_key,
                api_secret=dataforseo_api_secret,
                location=os.getenv("DATAFORSEO_LOCATION", "United States"),
                language_code=os.getenv("DATAFORSEO_LANGUAGE", "en"),
            )
        except Exception as e:
            print(f"⚠️ Failed to initialize DataForSEO integration: {e}")
            print("📝 Falling back to built-in keyword analysis")
    
    return None

# Initialize AI content generator if AI provider credentials are available
def create_ai_content_generator() -> Optional[AIContentGenerator]:
    """Create AI content generator with configured providers."""
    ai_config = {
        'providers': {}
    }
    
    # Check for OpenAI configuration
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        ai_config['providers']['openai'] = {
            'api_key': openai_api_key,
            'organization': os.getenv("OPENAI_ORGANIZATION"),
            'default_model': os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini"),
            'enabled': True,
            'priority': 1
        }
    
    # Check for Anthropic configuration
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_api_key:
        ai_config['providers']['anthropic'] = {
            'api_key': anthropic_api_key,
            'default_model': os.getenv("ANTHROPIC_DEFAULT_MODEL", "claude-3-5-haiku-20241022"),
            'enabled': True,
            'priority': 3
        }
    
    # Only create AI generator if at least one provider is configured
    if ai_config['providers']:
        try:
            ai_generator = AIContentGenerator(config=ai_config)
            print(f"🤖 AI Content Generator initialized with providers: {list(ai_config['providers'].keys())}")
            return ai_generator
        except Exception as e:
            print(f"⚠️ Failed to initialize AI Content Generator: {e}")
            print("📝 AI-enhanced content generation will be disabled")
    else:
        print("ℹ️ No AI provider credentials found. AI-enhanced content generation disabled.")
    
    return None


# LiteLLM router removed - using direct AI provider integrations


# Global instances
enhanced_analyzer = create_enhanced_keyword_analyzer()
ai_generator = create_ai_content_generator()
# LiteLLM router removed
blog_writer = BlogWriter(
    enable_seo_optimization=True,
    enable_quality_analysis=True,
    enhanced_keyword_analyzer=enhanced_analyzer,
    ai_content_generator=ai_generator,
    enable_ai_enhancement=ai_generator is not None,
)

# Phase 1-3 global services (initialized in lifespan)
quota_manager = None
keyword_difficulty_analyzer = None
supabase_client: Optional[Client] = None
supabase_server_client: Optional[SupabaseClient] = None


# Dependency to get blog writer instance
def get_blog_writer() -> BlogWriter:
    """Get blog writer instance."""
    return blog_writer


# Health check endpoint - optimized for Cloud Run
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint optimized for Cloud Run.
    
    This endpoint is used by Cloud Run for:
    - Liveness probes
    - Readiness probes  
    - Startup probes
    """
    return HealthResponse(
        status="healthy",
        timestamp=time.time(),
        version=f"{APP_VERSION}-cloudrun"
    )


# Readiness probe endpoint
@app.get("/ready")
async def readiness_check():
    """
    Readiness probe endpoint for Cloud Run.
    
    Checks if the service is ready to accept traffic by verifying:
    - Database connectivity (if applicable)
    - AI provider availability
    - Essential services status
    """
    try:
        # Check if blog writer is initialized
        if not blog_writer:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "reason": "Blog writer not initialized"}
            )
        
        # Check AI providers if enabled
        if blog_writer.enable_ai_enhancement and blog_writer.ai_generator:
            try:
                # Quick health check of AI providers
                provider_status = blog_writer.ai_generator.provider_manager.get_provider_status()
                active_providers = [p for p, status in provider_status.items() if status.get('available', False)]
                if not active_providers:
                    return JSONResponse(
                        status_code=503,
                        content={"status": "not_ready", "reason": "No AI providers available"}
                    )
            except Exception as e:
                # AI providers not critical for readiness, log but don't fail
                print(f"Warning: AI provider check failed: {e}")
        
        return {
            "status": "ready",
            "timestamp": time.time(),
            "services": {
                "blog_writer": "available",
                "seo_optimizer": "available",
                "keyword_analyzer": "available",
                "ai_enhancement": blog_writer.enable_ai_enhancement
            }
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "reason": str(e),
                "timestamp": time.time()
            }
        )


# Liveness probe endpoint
@app.get("/live")
async def liveness_check():
    """
    Liveness probe endpoint for Cloud Run.
    
    Simple check to verify the application is running and responsive.
    Should only fail if the application needs to be restarted.
    """
    return {
        "status": "alive",
        "timestamp": time.time(),
        "uptime": time.time() - startup_time if 'startup_time' in globals() else 0
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Blog Writer SDK API",
        "version": APP_VERSION,
        "environment": "cloud-run",
        "testing_mode": is_testing_mode(),
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
        "live": "/live",
        "endpoints": {
            "generate": "/api/v1/blog/generate",
            "analyze": "/api/v1/analyze",
            "keywords": "/api/v1/keywords",
            "batch": "/api/v1/batch",
            "metrics": "/api/v1/metrics",
            "platforms": {
                "webflow": "/api/v1/publish/webflow",
                "shopify": "/api/v1/publish/shopify",
                "wordpress": "/api/v1/publish/wordpress"
            },
            "media": {
                "cloudinary": "/api/v1/media/upload/cloudinary",
                "cloudflare": "/api/v1/media/upload/cloudflare"
            }
        }
    }


# Blog generation endpoints
@app.post("/api/v1/blog/generate", response_model=BlogGenerationResult)
async def generate_blog_v2(
    request: BlogGenerationRequest,
    background_tasks: BackgroundTasks,
    writer: BlogWriter = Depends(get_blog_writer)
):
    """
    Generate a complete blog post with SEO optimization (v2 endpoint).
    
    This endpoint creates a full blog post including:
    - SEO-optimized content structure
    - Meta tags and descriptions
    - Keyword optimization
    - Quality analysis and suggestions
    """
    return await generate_blog(request, background_tasks, writer)


@app.post("/api/v1/generate", response_model=BlogGenerationResult)
async def generate_blog(
    request: BlogGenerationRequest,
    background_tasks: BackgroundTasks,
    writer: BlogWriter = Depends(get_blog_writer)
):
    """
    Generate a complete blog post with SEO optimization.
    
    This endpoint creates a full blog post including:
    - SEO-optimized content structure
    - Meta tags and descriptions
    - Keyword optimization
    - Content quality analysis
    """
    try:
        # Convert API request to SDK request
        blog_request = BlogRequest(
            topic=request.topic,
            keywords=request.keywords,
            tone=request.tone,
            length=request.length,
            format=request.format,
            target_audience=request.target_audience,
            focus_keyword=request.focus_keyword,
            include_introduction=request.include_introduction,
            include_conclusion=request.include_conclusion,
            include_faq=request.include_faq,
            include_toc=request.include_toc,
            word_count_target=request.word_count_target,
            custom_instructions=request.custom_instructions,
        )
        
        # Generate blog post
        result = await writer.generate(blog_request)
        
        # Log generation for analytics (background task)
        background_tasks.add_task(
            log_generation,
            topic=request.topic,
            success=result.success,
            word_count=result.word_count,
            generation_time=result.generation_time_seconds
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Blog generation failed: {str(e)}"
        )


# Enhanced blog generation endpoint (Phase 1 & 2)
@app.post("/api/v1/blog/generate-enhanced", response_model=Union[EnhancedBlogGenerationResponse, CreateJobResponse])
async def generate_blog_enhanced(
    request: EnhancedBlogGenerationRequest,
    background_tasks: BackgroundTasks,
    async_mode: bool = Query(default=False, description="If true, creates async job via Cloud Tasks")
):
    """
    Generate high-quality blog content using multi-stage pipeline (Phase 1, 2 & 3).
    
    This endpoint uses:
    - Multi-stage generation pipeline (Research → Draft → Enhancement → SEO)
    - Google Custom Search for research and fact-checking
    - Readability optimization
    - SERP feature optimization
    - Citation integration
    - Phase 3: Multi-model consensus, Knowledge Graph, semantic keywords, quality scoring
    
    Query Parameters:
    - async_mode: If true, creates an async job via Cloud Tasks and returns job_id immediately
    
    Returns:
    - If async_mode=false: EnhancedBlogGenerationResponse (synchronous)
    - If async_mode=true: CreateJobResponse with job_id (asynchronous)
    
    Use GET /api/v1/blog/jobs/{job_id} to check status and retrieve results.
    """
    try:
        # Get global clients
        global google_custom_search_client, readability_analyzer, citation_generator, serp_analyzer
        global ai_generator, google_knowledge_graph_client, semantic_integrator, quality_scorer
        global intent_analyzer, few_shot_extractor, length_optimizer, dataforseo_client_global
        global blog_generation_jobs
        
        # Check if AI generator is available
        if ai_generator is None:
            raise HTTPException(
                status_code=503,
                detail="AI Content Generator is not initialized. Please configure AI provider credentials (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)"
            )
        
        # Handle async mode - create Cloud Tasks job
        if async_mode:
            job_id = str(uuid.uuid4())
            
            # Create job record
            job = BlogGenerationJob(
                job_id=job_id,
                status=JobStatus.PENDING,
                request=request.dict()
            )
            blog_generation_jobs[job_id] = job
            
            try:
                # Get Cloud Tasks service
                cloud_tasks_service = get_cloud_tasks_service()
                
                # Get worker URL (Cloud Run service URL)
                worker_url = os.getenv("CLOUD_RUN_WORKER_URL")
                if not worker_url:
                    # Fallback: Use the actual service URL (Cloud Run URLs have unique hashes)
                    # Default to the known dev service URL
                    service_base_url = os.getenv("CLOUD_RUN_SERVICE_URL", "https://blog-writer-api-dev-kq42l26tuq-od.a.run.app")
                    worker_url = f"{service_base_url}/api/v1/blog/worker"
                
                # Create Cloud Task
                task_name = cloud_tasks_service.create_blog_generation_task(
                    request_data={
                        "job_id": job_id,
                        "request": request.dict()
                    },
                    worker_url=worker_url
                )
                
                # Update job with task name
                job.task_name = task_name
                job.status = JobStatus.QUEUED
                job.queued_at = datetime.utcnow()
                
                logger.info(f"Created async blog generation job: {job_id}, task: {task_name}")
                
                # Estimate completion time (4 minutes average)
                estimated_time = 240  # 4 minutes in seconds
                
                return CreateJobResponse(
                    job_id=job_id,
                    status=JobStatus.QUEUED,
                    message="Blog generation job queued successfully",
                    estimated_completion_time=estimated_time
                )
                
            except Exception as e:
                logger.error(f"Failed to create Cloud Task: {e}", exc_info=True)
                # Update job status
                job.status = JobStatus.FAILED
                job.error_message = f"Failed to queue job: {str(e)}"
                job.completed_at = datetime.utcnow()
                
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create async job: {str(e)}"
                )
        
        # Create progress callback for streaming updates
        progress_updates = []
        async def progress_callback(update):
            """Store progress updates for response."""
            progress_updates.append(update.dict())
        
        # Initialize pipeline with Phase 3 components and additional enhancements
        pipeline = MultiStageGenerationPipeline(
            ai_generator=ai_generator,
            google_search=google_custom_search_client if request.use_google_search else None,
            readability_analyzer=readability_analyzer,
            knowledge_graph=google_knowledge_graph_client if request.use_knowledge_graph else None,
            semantic_integrator=semantic_integrator if request.use_semantic_keywords else None,
            quality_scorer=quality_scorer if request.use_quality_scoring else None,
            intent_analyzer=intent_analyzer,  # Always enabled for better content
            few_shot_extractor=few_shot_extractor if request.use_google_search else None,
            length_optimizer=length_optimizer if request.use_google_search else None,
            use_consensus=request.use_consensus_generation,
            dataforseo_client=dataforseo_client_global,  # Add DataForSEO Labs integration
            progress_callback=progress_callback  # Add progress callback
        )
        
        # Determine template type
        template = None
        if request.template_type:
            try:
                template = PromptTemplate(request.template_type)
            except ValueError:
                template = PromptTemplate.EXPERT_AUTHORITY
        
        # Prepare additional context
        additional_context = {}
        if request.target_audience:
            additional_context["target_audience"] = request.target_audience
        if request.custom_instructions:
            additional_context["custom_instructions"] = request.custom_instructions
        
        # Add product research requirements if enabled
        if request.include_product_research:
            additional_context["product_research_requirements"] = {
                "include_brands": request.include_brands,
                "include_models": request.include_models,
                "include_prices": request.include_prices,
                "include_features": request.include_features,
                "include_reviews": request.include_reviews,
                "include_pros_cons": request.include_pros_cons,
                "include_product_table": request.include_product_table,
                "include_comparison_section": request.include_comparison_section,
                "include_buying_guide": request.include_buying_guide,
                "include_faq_section": request.include_faq_section,
                "research_depth": request.research_depth
            }
            # Force Google Search for product research
            if not request.use_google_search:
                logger.info("Product research enabled, forcing Google Search")
                # Note: We can't modify request.use_google_search here, but we can ensure search is used
                # The pipeline will use google_search if available
        
        # SERP optimization if enabled
        serp_features = []
        if request.use_serp_optimization and request.keywords:
            try:
                serp_analysis = await serp_analyzer.analyze_serp_features(
                    request.keywords[0]
                )
                serp_features = [f.type for f in serp_analysis.features]
                additional_context["serp_features"] = serp_features
            except Exception as e:
                logger.warning(f"SERP analysis failed: {e}")
        
        # Generate using multi-stage pipeline
        pipeline_result = await pipeline.generate(
            topic=request.topic,
            keywords=request.keywords,
            tone=request.tone,
            length=request.length,
            template=template,
            additional_context=additional_context
        )
        
        # Image generation has been moved to a separate endpoint
        # Frontend should call /api/v1/images/generate separately after blog generation
        final_content = pipeline_result.final_content
        
        # Add citations if enabled
        citations = []
        if request.use_citations and google_custom_search_client:
            try:
                citation_result = await citation_generator.generate_citations(
                    final_content,
                    request.topic,
                    request.keywords
                )
                citations = [
                    {
                        "text": c.text[:100],
                        "url": c.source_url,
                        "title": c.source_title
                    }
                    for c in citation_result.citations
                ]
                # Integrate citations into content
                final_content = citation_generator.integrate_citations(
                    final_content,
                    citation_result.citations
                )
                # Add references section
                if citation_result.sources_used:
                    final_content += citation_generator.generate_references_section(
                        citation_result.sources_used
                    )
            except Exception as e:
                logger.warning(f"Citation generation failed: {e}")
        
        # Calculate SEO score (simplified)
        seo_score = min(100, pipeline_result.readability_score * 0.4 + 60)
        
        # Extract quality scores (Phase 3)
        quality_dimensions = {}
        if pipeline_result.quality_score is not None:
            quality_report = pipeline_result.seo_metadata.get("quality_report", {})
            quality_dimensions = quality_report.get("dimension_scores", {})
        
        # Extract semantic keywords (Phase 3)
        semantic_keywords = pipeline_result.seo_metadata.get("semantic_keywords", [])
        
        # Extract brand recommendations from context
        brand_recommendations = None
        if additional_context.get("brand_recommendations"):
            brand_recommendations = additional_context["brand_recommendations"].get("brands", [])
        
        # Extract content metadata for frontend processing (unified + remark + rehype support)
        content_metadata = extract_content_metadata(final_content)
        
        # Enhance SEO metadata with OG and Twitter tags
        enhanced_seo_metadata = pipeline_result.seo_metadata.copy()
        
        # Get featured image URL if available (from structured data)
        featured_image_url = None
        if pipeline_result.structured_data and pipeline_result.structured_data.get("image"):
            featured_image_url = pipeline_result.structured_data.get("image")
        
        # Generate canonical URL (should be set by frontend, but provide default)
        canonical_url = os.getenv("CANONICAL_BASE_URL", "https://your-domain.com")
        if pipeline_result.structured_data and pipeline_result.structured_data.get("mainEntityOfPage"):
            canonical_url = pipeline_result.structured_data.get("mainEntityOfPage", {}).get("@id", canonical_url)
        
        # Add OG tags
        enhanced_seo_metadata["og_tags"] = {
            "title": pipeline_result.meta_title or request.topic,
            "description": pipeline_result.meta_description or "",
            "image": featured_image_url,
            "url": canonical_url,
            "type": "article",
            "site_name": os.getenv("SITE_NAME", "Blog Writer")
        }
        
        # Add Twitter tags
        enhanced_seo_metadata["twitter_tags"] = {
            "card": "summary_large_image" if featured_image_url else "summary",
            "title": pipeline_result.meta_title or request.topic,
            "description": pipeline_result.meta_description or "",
            "image": featured_image_url
        }
        
        # Enhance structured_data to be schema-dts compatible
        enhanced_structured_data = pipeline_result.structured_data
        if enhanced_structured_data:
            # Ensure all required BlogPosting fields are present
            if "@context" not in enhanced_structured_data:
                enhanced_structured_data["@context"] = "https://schema.org"
            if "@type" not in enhanced_structured_data:
                enhanced_structured_data["@type"] = "BlogPosting"
            
            # Ensure required fields
            enhanced_structured_data["headline"] = enhanced_structured_data.get("headline") or pipeline_result.meta_title or request.topic
            enhanced_structured_data["description"] = enhanced_structured_data.get("description") or pipeline_result.meta_description or ""
            
            # Add datePublished and dateModified if not present
            if "datePublished" not in enhanced_structured_data:
                enhanced_structured_data["datePublished"] = datetime.now().isoformat()
            if "dateModified" not in enhanced_structured_data:
                enhanced_structured_data["dateModified"] = datetime.now().isoformat()
            
            # Add wordCount from content metadata
            if "wordCount" not in enhanced_structured_data:
                enhanced_structured_data["wordCount"] = content_metadata.get("word_count", 0)
            
            # Ensure mainEntityOfPage
            if "mainEntityOfPage" not in enhanced_structured_data:
                enhanced_structured_data["mainEntityOfPage"] = {
                    "@type": "WebPage",
                    "@id": canonical_url
                }
        
        # Prepare stage results for response
        stage_results_data = [
            {
                "stage": s.stage,
                "provider": s.provider_used,
                "tokens": s.tokens_used,
                "cost": s.cost
            }
            for s in pipeline_result.stage_results
        ]
        
        # Log generation
        background_tasks.add_task(
            log_generation,
            topic=request.topic,
            success=True,
            word_count=len(final_content.split()),
            generation_time=pipeline_result.generation_time
        )
        
        return EnhancedBlogGenerationResponse(
            title=pipeline_result.meta_title or request.topic,
            content=final_content,
            meta_title=pipeline_result.meta_title,
            meta_description=pipeline_result.meta_description,
            readability_score=pipeline_result.readability_score,
            seo_score=seo_score,
            stage_results=stage_results_data,
            citations=citations,
            total_tokens=pipeline_result.total_tokens,
            total_cost=pipeline_result.total_cost,
            generation_time=pipeline_result.generation_time,
            seo_metadata=enhanced_seo_metadata,
            internal_links=pipeline_result.seo_metadata.get("internal_links", []),
            quality_score=pipeline_result.quality_score,
            quality_dimensions=quality_dimensions,
            structured_data=enhanced_structured_data,
            semantic_keywords=semantic_keywords,
            content_metadata=content_metadata,
            generated_images=None,  # Image generation moved to separate endpoint
            brand_recommendations=brand_recommendations,
            success=True,
            warnings=[],  # Image generation warnings removed (use separate endpoint)
            progress_updates=progress_updates  # Include progress updates for frontend
        )
        
    except Exception as e:
        logger.error(f"Enhanced blog generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Enhanced blog generation failed: {str(e)}"
        )


# Worker endpoint for Cloud Tasks
@app.post("/api/v1/blog/worker")
async def blog_generation_worker(request: Dict[str, Any]):
    """
    Internal worker endpoint called by Cloud Tasks to process blog generation jobs.
    
    This endpoint:
    1. Receives job_id and request data from Cloud Tasks
    2. Updates job status to PROCESSING
    3. Executes the blog generation pipeline
    4. Updates job with result or error
    5. Marks job as COMPLETED or FAILED
    
    This endpoint should not be called directly by clients.
    """
    try:
        global blog_generation_jobs
        global google_custom_search_client, readability_analyzer, citation_generator, serp_analyzer
        global ai_generator, google_knowledge_graph_client, semantic_integrator, quality_scorer
        global intent_analyzer, few_shot_extractor, length_optimizer, dataforseo_client_global
        
        # Extract job_id and request data
        job_id = request.get("job_id")
        if not job_id:
            logger.error("Worker called without job_id")
            return JSONResponse(
                status_code=400,
                content={"error": "job_id is required"}
            )
        
        # Get job from storage
        if job_id not in blog_generation_jobs:
            logger.error(f"Job {job_id} not found")
            return JSONResponse(
                status_code=404,
                content={"error": f"Job {job_id} not found"}
            )
        
        job = blog_generation_jobs[job_id]
        
        # Update job status
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.utcnow()
        job.current_stage = "initialization"
        
        # Parse request
        request_data = request.get("request", {})
        blog_request = EnhancedBlogGenerationRequest(**request_data)
        
        try:
            # Create progress callback that updates job
            progress_updates = []
            async def progress_callback(update):
                """Update job progress."""
                progress_updates.append(update.dict())
                job.progress_updates = progress_updates
                
                # Update current stage and progress
                if "stage" in update:
                    job.current_stage = update.get("stage", "processing")
                if "progress_percentage" in update:
                    job.progress_percentage = update.get("progress_percentage", 0.0)
            
            # Initialize pipeline (same as synchronous endpoint)
            pipeline = MultiStageGenerationPipeline(
                ai_generator=ai_generator,
                google_search=google_custom_search_client if blog_request.use_google_search else None,
                readability_analyzer=readability_analyzer,
                knowledge_graph=google_knowledge_graph_client if blog_request.use_knowledge_graph else None,
                semantic_integrator=semantic_integrator if blog_request.use_semantic_keywords else None,
                quality_scorer=quality_scorer if blog_request.use_quality_scoring else None,
                intent_analyzer=intent_analyzer,
                few_shot_extractor=few_shot_extractor if blog_request.use_google_search else None,
                length_optimizer=length_optimizer if blog_request.use_google_search else None,
                use_consensus=blog_request.use_consensus_generation,
                dataforseo_client=dataforseo_client_global,
                progress_callback=progress_callback
            )
            
            # Determine template type
            template = None
            if blog_request.template_type:
                try:
                    template = PromptTemplate(blog_request.template_type)
                except ValueError:
                    template = PromptTemplate.EXPERT_AUTHORITY
            
            # Prepare additional context
            additional_context = {}
            if blog_request.target_audience:
                additional_context["target_audience"] = blog_request.target_audience
            if blog_request.custom_instructions:
                additional_context["custom_instructions"] = blog_request.custom_instructions
            
            # Add product research requirements if enabled
            if blog_request.include_product_research:
                additional_context["product_research_requirements"] = {
                    "include_brands": blog_request.include_brands,
                    "include_models": blog_request.include_models,
                    "include_prices": blog_request.include_prices,
                    "include_features": blog_request.include_features,
                    "include_reviews": blog_request.include_reviews,
                    "include_pros_cons": blog_request.include_pros_cons,
                    "include_product_table": blog_request.include_product_table,
                    "include_comparison_section": blog_request.include_comparison_section,
                    "include_buying_guide": blog_request.include_buying_guide,
                    "include_faq_section": blog_request.include_faq_section,
                    "research_depth": blog_request.research_depth
                }
            
            # SERP optimization if enabled
            serp_features = []
            if blog_request.use_serp_optimization and blog_request.keywords:
                try:
                    serp_analysis = await serp_analyzer.analyze_serp_features(
                        blog_request.keywords[0]
                    )
                    serp_features = [f.type for f in serp_analysis.features]
                    additional_context["serp_features"] = serp_features
                except Exception as e:
                    logger.warning(f"SERP analysis failed: {e}")
            
            # Generate using multi-stage pipeline
            pipeline_result = await pipeline.generate(
                topic=blog_request.topic,
                keywords=blog_request.keywords,
                tone=blog_request.tone,
                length=blog_request.length,
                template=template,
                additional_context=additional_context
            )
            
            # Image generation has been moved to a separate endpoint
            # Frontend should call /api/v1/images/generate separately after blog generation
            final_content = pipeline_result.final_content
            
            # Add citations if enabled
            citations = []
            if blog_request.use_citations and google_custom_search_client:
                try:
                    citation_result = await citation_generator.generate_citations(
                        final_content,
                        blog_request.topic,
                        blog_request.keywords
                    )
                    citations = [
                        {
                            "text": c.text[:100],
                            "url": c.source_url,
                            "title": c.source_title
                        }
                        for c in citation_result.citations
                    ]
                    final_content = citation_generator.integrate_citations(
                        final_content,
                        citation_result.citations
                    )
                    if citation_result.sources_used:
                        final_content += citation_generator.generate_references_section(
                            citation_result.sources_used
                        )
                except Exception as e:
                    logger.warning(f"Citation generation failed: {e}")
            
            # Calculate SEO score
            seo_score = min(100, pipeline_result.readability_score * 0.4 + 60)
            
            # Extract quality scores
            quality_dimensions = {}
            if pipeline_result.quality_score is not None:
                quality_report = pipeline_result.seo_metadata.get("quality_report", {})
                quality_dimensions = quality_report.get("dimension_scores", {})
            
            # Extract semantic keywords
            semantic_keywords = pipeline_result.seo_metadata.get("semantic_keywords", [])
            
            # Extract brand recommendations
            brand_recommendations = None
            if additional_context.get("brand_recommendations"):
                brand_recommendations = additional_context["brand_recommendations"].get("brands", [])
            
            # Extract content metadata
            content_metadata = extract_content_metadata(final_content)
            
            # Enhance SEO metadata
            enhanced_seo_metadata = pipeline_result.seo_metadata.copy()
            
            # Get featured image URL if available (from structured data)
            featured_image_url = None
            if pipeline_result.structured_data and pipeline_result.structured_data.get("image"):
                featured_image_url = pipeline_result.structured_data.get("image")
            
            # Generate canonical URL
            canonical_url = os.getenv("CANONICAL_BASE_URL", "https://your-domain.com")
            if pipeline_result.structured_data and pipeline_result.structured_data.get("mainEntityOfPage"):
                canonical_url = pipeline_result.structured_data.get("mainEntityOfPage", {}).get("@id", canonical_url)
            
            # Add OG tags
            enhanced_seo_metadata["og_tags"] = {
                "title": pipeline_result.meta_title or blog_request.topic,
                "description": pipeline_result.meta_description or "",
                "image": featured_image_url,
                "url": canonical_url,
                "type": "article",
                "site_name": os.getenv("SITE_NAME", "Blog Writer")
            }
            
            # Add Twitter tags
            enhanced_seo_metadata["twitter_tags"] = {
                "card": "summary_large_image" if featured_image_url else "summary",
                "title": pipeline_result.meta_title or blog_request.topic,
                "description": pipeline_result.meta_description or "",
                "image": featured_image_url
            }
            
            # Enhance structured_data
            enhanced_structured_data = pipeline_result.structured_data
            if enhanced_structured_data:
                if "@context" not in enhanced_structured_data:
                    enhanced_structured_data["@context"] = "https://schema.org"
                if "@type" not in enhanced_structured_data:
                    enhanced_structured_data["@type"] = "BlogPosting"
                enhanced_structured_data["headline"] = enhanced_structured_data.get("headline") or pipeline_result.meta_title or blog_request.topic
                enhanced_structured_data["description"] = enhanced_structured_data.get("description") or pipeline_result.meta_description or ""
                if "datePublished" not in enhanced_structured_data:
                    enhanced_structured_data["datePublished"] = datetime.now().isoformat()
                if "dateModified" not in enhanced_structured_data:
                    enhanced_structured_data["dateModified"] = datetime.now().isoformat()
                if "wordCount" not in enhanced_structured_data:
                    enhanced_structured_data["wordCount"] = content_metadata.get("word_count", 0)
                if "mainEntityOfPage" not in enhanced_structured_data:
                    enhanced_structured_data["mainEntityOfPage"] = {
                        "@type": "WebPage",
                        "@id": canonical_url
                    }
            
            # Prepare stage results
            stage_results_data = [
                {
                    "stage": s.stage,
                    "provider": s.provider_used,
                    "tokens": s.tokens_used,
                    "cost": s.cost
                }
                for s in pipeline_result.stage_results
            ]
            
            # Create response
            response = EnhancedBlogGenerationResponse(
                title=pipeline_result.meta_title or blog_request.topic,
                content=final_content,
                meta_title=pipeline_result.meta_title,
                meta_description=pipeline_result.meta_description,
                readability_score=pipeline_result.readability_score,
                seo_score=seo_score,
                stage_results=stage_results_data,
                citations=citations,
                total_tokens=pipeline_result.total_tokens,
                total_cost=pipeline_result.total_cost,
                generation_time=pipeline_result.generation_time,
                seo_metadata=enhanced_seo_metadata,
                internal_links=pipeline_result.seo_metadata.get("internal_links", []),
                quality_score=pipeline_result.quality_score,
                quality_dimensions=quality_dimensions,
                structured_data=enhanced_structured_data,
                semantic_keywords=semantic_keywords,
                content_metadata=content_metadata,
                generated_images=None,  # Image generation moved to separate endpoint
                brand_recommendations=brand_recommendations,
                success=True,
                warnings=[],  # Image generation warnings removed (use separate endpoint)
                progress_updates=progress_updates
            )
            
            # Update job with result
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.progress_percentage = 100.0
            job.current_stage = "completed"
            job.result = response.dict()
            
            logger.info(f"Blog generation job {job_id} completed successfully")
            
            return JSONResponse(
                status_code=200,
                content={"status": "success", "job_id": job_id}
            )
            
        except Exception as e:
            logger.error(f"Blog generation job {job_id} failed: {e}", exc_info=True)
            
            # Update job with error
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error_message = str(e)
            job.error_details = {
                "type": type(e).__name__,
                "message": str(e)
            }
            
            return JSONResponse(
                status_code=500,
                content={"status": "error", "job_id": job_id, "error": str(e)}
            )
            
    except Exception as e:
        logger.error(f"Worker endpoint error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# Job status endpoint
@app.get("/api/v1/blog/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get the status of an async blog generation job.
    
    Returns:
    - Job status (pending, queued, processing, completed, failed)
    - Progress percentage
    - Current stage
    - Result (if completed)
    - Error message (if failed)
    """
    global blog_generation_jobs
    
    if job_id not in blog_generation_jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found"
        )
    
    job = blog_generation_jobs[job_id]
    
    # Calculate estimated time remaining
    estimated_time_remaining = None
    if job.status == JobStatus.PROCESSING and job.started_at:
        elapsed = (datetime.utcnow() - job.started_at).total_seconds()
        # Average generation time is 240 seconds (4 minutes)
        estimated_time_remaining = max(0, int(240 - elapsed))
    
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress_percentage=job.progress_percentage,
        current_stage=job.current_stage,
        progress_updates=job.progress_updates,  # Include all progress updates for stage tracking
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        result=job.result,
        error_message=job.error_message,
        estimated_time_remaining=estimated_time_remaining
    )


# Content analysis endpoint
@app.post("/api/v1/analyze")
async def analyze_content(
    request: ContentAnalysisRequest,
    writer: BlogWriter = Depends(get_blog_writer)
):
    """
    Analyze existing content for SEO and quality metrics.
    
    This endpoint provides:
    - SEO score and recommendations
    - Readability analysis
    - Content quality metrics
    - Keyword density analysis
    """
    try:
        # Analyze the content
        result = await writer.analyze_existing_content(
            content=request.content,
            title=request.title or ""
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content analysis failed: {str(e)}"
        )


# Keyword analysis endpoint
@app.post("/api/v1/keywords/analyze")
async def analyze_keywords(
    keyword_request: KeywordAnalysisRequest,
    http_request: Request,
    writer: BlogWriter = Depends(get_blog_writer)
):
    """
    Analyze keywords for SEO potential and difficulty.
    
    If `max_suggestions_per_keyword` is provided (even if 0), automatically routes to enhanced analysis
    for better results with search volume, difficulty, and competition data.
    
    Returns analysis for each keyword including:
    - Estimated difficulty
    - Search volume (if enhanced analysis available)
    - Competition metrics
    - Related keywords
    - Long-tail variations
    - Recommendations
    """
    try:
        if not keyword_request.keywords:
            raise HTTPException(
                status_code=400,
                detail="No keywords provided. Please provide at least one keyword in the 'keywords' array."
            )
        
        # Apply testing mode limits
        limited_keywords = apply_keyword_limits(keyword_request.keywords)
        if is_testing_mode():
            logger.info(f"🧪 TESTING MODE: Limited keywords from {len(keyword_request.keywords)} to {len(limited_keywords)}")
        
        # If max_suggestions_per_keyword is provided (even if 0), use enhanced analysis for better results
        if keyword_request.max_suggestions_per_keyword is not None:
            # Apply testing mode limits to suggestions
            max_suggestions = apply_suggestions_limit(
                max(5, min(keyword_request.max_suggestions_per_keyword, 150)) if keyword_request.max_suggestions_per_keyword > 0 else 20
            )
            # Convert to EnhancedKeywordAnalysisRequest format
            enhanced_request = EnhancedKeywordAnalysisRequest(
                keywords=limited_keywords,
                location=keyword_request.location,
                language=keyword_request.language,
                search_type=keyword_request.search_type or "keyword_analysis",
                include_serp=False,
                max_suggestions_per_keyword=max_suggestions
            )
            # Route to enhanced endpoint for better results
            enhanced_response = await analyze_keywords_enhanced(enhanced_request, http_request)
            return enhanced_response
        
        # Standard analysis - but prefer enhanced if available
        # Apply testing mode limits to keywords
        limited_keywords = apply_keyword_limits(keyword_request.keywords)
        analysis_mode = "standard"
        if enhanced_analyzer:
            try:
                results = await enhanced_analyzer.analyze_keywords_comprehensive(
                    keywords=limited_keywords,
                    tenant_id=os.getenv("TENANT_ID", "default")
                )
                analysis_mode = "enhanced"
                # Convert to expected format
                keyword_analysis = {}
                for kw, analysis in results.items():
                    # Ensure search_volume and cpc are always numeric (never None)
                    search_volume = analysis.search_volume if analysis.search_volume is not None else 0
                    cpc_value = analysis.cpc if analysis.cpc is not None else 0.0
                    competition_value = analysis.competition if analysis.competition is not None else 0.0
                    
                    # Get difficulty_score from analysis object (stored as attribute)
                    difficulty_score = getattr(analysis, 'difficulty_score', None)
                    
                    # If difficulty_score not available, calculate from difficulty enum
                    if difficulty_score is None:
                        difficulty_enum = analysis.difficulty.value if hasattr(analysis.difficulty, "value") else str(analysis.difficulty)
                        # Map enum to approximate numeric score
                        enum_to_score = {
                            "VERY_EASY": 10.0,
                            "EASY": 30.0,
                            "MEDIUM": 50.0,
                            "HARD": 70.0,
                            "VERY_HARD": 90.0
                        }
                        difficulty_score = enum_to_score.get(difficulty_enum, 50.0)
                    
                    keyword_analysis[kw] = {
                        "difficulty": analysis.difficulty.value if hasattr(analysis.difficulty, "value") else str(analysis.difficulty),
                        "difficulty_score": float(difficulty_score) if difficulty_score is not None else 50.0,  # Numeric score for gauge
                        "search_volume": search_volume,  # Always numeric
                        "global_search_volume": analysis.global_search_volume or 0,
                        "search_volume_by_country": analysis.search_volume_by_country,
                        "monthly_searches": analysis.monthly_searches,
                        "competition": competition_value,
                        "cpc": cpc_value,  # Always numeric
                        "cpc_currency": analysis.cpc_currency,
                        "cps": analysis.cps,
                        "clicks": analysis.clicks,
                        "recommended": analysis.recommended,
                        "reason": analysis.reason,
                        "related_keywords": analysis.related_keywords[:10],
                        "long_tail_keywords": analysis.long_tail_keywords[:10],
                        "trend_score": analysis.trend_score,
                        "traffic_potential": analysis.traffic_potential,
                        "parent_topic": analysis.parent_topic,
                        "serp_features": analysis.serp_features,
                        "serp_feature_counts": analysis.serp_feature_counts,
                        "primary_intent": analysis.primary_intent,
                        "intent_probabilities": analysis.intent_probabilities,
                        "also_rank_for": analysis.also_rank_for,
                        "also_talk_about": analysis.also_talk_about,
                        "top_competitors": analysis.top_competitors,
                        "first_seen": analysis.first_seen,
                        "last_updated": analysis.last_updated,
                    }
                response_payload = {"keyword_analysis": keyword_analysis}
                return response_payload
            except Exception as e:
                logger.warning(f"Enhanced analysis failed, falling back to standard: {e}")
        
        # Fallback to standard analysis
        results: Dict[str, Dict[str, Any]] = {}
        for keyword in keyword_request.keywords:
            analysis = await writer.keyword_analyzer.analyze_keyword(keyword)
            
            # Normalize analysis to plain dict with numeric defaults
            analysis_dict = analysis.model_dump()
            difficulty_value = analysis.difficulty.value if hasattr(analysis.difficulty, "value") else str(analysis.difficulty)
            
            # Calculate difficulty_score from difficulty enum for fallback
            difficulty_enum = difficulty_value
            enum_to_score = {
                "VERY_EASY": 10.0,
                "EASY": 30.0,
                "MEDIUM": 50.0,
                "HARD": 70.0,
                "VERY_HARD": 90.0
            }
            difficulty_score = enum_to_score.get(difficulty_enum, 50.0)
            
            results[keyword] = {
                "difficulty": difficulty_value,
                "difficulty_score": difficulty_score,  # Numeric score for gauge
                "search_volume": analysis_dict.get("search_volume") or 0,
                "global_search_volume": analysis_dict.get("global_search_volume") or 0,
                "search_volume_by_country": analysis_dict.get("search_volume_by_country") or {},
                "monthly_searches": analysis_dict.get("monthly_searches") or [],
                "competition": analysis_dict.get("competition") or 0.0,
                "cpc": analysis_dict.get("cpc") or 0.0,
                "trend_score": analysis_dict.get("trend_score") or 0.0,
                "traffic_potential": analysis_dict.get("traffic_potential"),
                "parent_topic": analysis_dict.get("parent_topic"),
                "serp_features": analysis_dict.get("serp_features") or [],
                "serp_feature_counts": analysis_dict.get("serp_feature_counts") or {},
                "primary_intent": analysis_dict.get("primary_intent"),
                "intent_probabilities": analysis_dict.get("intent_probabilities") or {},
                "also_rank_for": analysis_dict.get("also_rank_for") or [],
                "also_talk_about": analysis_dict.get("also_talk_about") or [],
                "top_competitors": analysis_dict.get("top_competitors") or [],
                "first_seen": analysis_dict.get("first_seen"),
                "last_updated": analysis_dict.get("last_updated"),
                "recommended": analysis_dict.get("recommended", False),
                "reason": analysis_dict.get("reason"),
                "related_keywords": analysis_dict.get("related_keywords", []),
                "long_tail_keywords": analysis_dict.get("long_tail_keywords", []),
            }
        
        response_payload = {"keyword_analysis": results}
        return response_payload
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Keyword analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Keyword analysis failed: {str(e)}"
        )


async def detect_location_from_ip(request: Request) -> Optional[str]:
    """
    Detect location from client IP address using geolocation service.
    
    Returns country name in DataForSEO format (e.g., "United States", "United Kingdom")
    Falls back to None if detection fails.
    """
    try:
        # Get client IP
        client_ip = request.client.host if request.client else None
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            client_ip = forwarded_for.split(',')[0].strip()
        
        if not client_ip or client_ip in ['127.0.0.1', 'localhost', '::1']:
            return None
        
        # Use free geolocation API (ip-api.com - no API key required)
        # Note: httpx is imported at module level
        import httpx
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"http://ip-api.com/json/{client_ip}?fields=country")
            if response.status_code == 200:
                data = response.json()
                country = data.get('country')
                if country:
                    # Map common country names to DataForSEO format
                    country_mapping = {
                        'United States': 'United States',
                        'United Kingdom': 'United Kingdom',
                        'Canada': 'Canada',
                        'Australia': 'Australia',
                        'Germany': 'Germany',
                        'France': 'France',
                        'Spain': 'Spain',
                        'Italy': 'Italy',
                        'Netherlands': 'Netherlands',
                        'Sweden': 'Sweden',
                        'Norway': 'Norway',
                        'Denmark': 'Denmark',
                        'Finland': 'Finland',
                        'Poland': 'Poland',
                        'Brazil': 'Brazil',
                        'Mexico': 'Mexico',
                        'India': 'India',
                        'Japan': 'Japan',
                        'South Korea': 'South Korea',
                        'China': 'China',
                        'Singapore': 'Singapore',
                    }
                    return country_mapping.get(country, country)
    except Exception as e:
        logger.debug(f"IP-based location detection failed: {e}")
    
    return None


async def _build_keyword_discovery(
    seed_keyword: str,
    location: str,
    language: str,
    tenant_id: str,
    df_client
) -> Dict[str, Any]:
    """
    Build enhanced keyword discovery data (matching/related terms, SERP context).
    """
    discovery: Dict[str, Any] = {
        "matching_terms": [],
        "questions": [],
        "related_terms": [],
    }
    
    try:
        tasks = await asyncio.gather(
            df_client.get_related_keywords(
                keyword=seed_keyword,
                location_name=location,
                language_code=language,
                tenant_id=tenant_id,
                depth=2,
                limit=150
            ),
            df_client.get_keyword_ideas(
                keywords=[seed_keyword],
                location_name=location,
                language_code=language,
                tenant_id=tenant_id,
                limit=200
            ),
            df_client.get_serp_analysis(
                keyword=seed_keyword,
                location_name=location,
                language_code=language,
                tenant_id=tenant_id,
                depth=20
            ),
            return_exceptions=True
        )
    except Exception as e:
        logger.warning(f"Keyword discovery tasks failed to start: {e}")
        return discovery
    
    related_resp, ideas_resp, serp_analysis_raw = tasks
    
    if not isinstance(related_resp, Exception):
        matching_terms = _extract_keywords_from_related_response(related_resp)
        discovery["matching_terms"] = matching_terms
        discovery["questions"] = [
            term for term in matching_terms if _looks_like_question(term.get("keyword", ""))
        ][:50]
    else:
        logger.warning(f"Related keywords task failed: {related_resp}")
    
    if not isinstance(ideas_resp, Exception):
        discovery["related_terms"] = _extract_keywords_from_ideas_response(ideas_resp)
    else:
        logger.warning(f"Keyword ideas task failed: {ideas_resp}")
    
    if not isinstance(serp_analysis_raw, Exception):
        discovery["serp_analysis"] = _summarize_serp_analysis(serp_analysis_raw)
        logger.info(f"SERP analysis completed for keyword: {seed_keyword}")
    else:
        logger.warning(f"SERP analysis failed: {serp_analysis_raw}")
        discovery["serp_analysis"] = {}
    
    return discovery


def _extract_keywords_from_related_response(response: Any, limit: int = 200) -> List[Dict[str, Any]]:
    keywords: List[Dict[str, Any]] = []
    if not response:
        return keywords
    
    items = []
    if isinstance(response, dict) and "tasks" in response:
        for task in response.get("tasks", []):
            result_data = task.get("result")
            if result_data is None:
                continue
            if isinstance(result_data, list):
                for result in result_data:
                    if isinstance(result, dict):
                        items.extend(result.get("items", []))
            elif isinstance(result_data, dict):
                items.extend(result_data.get("items", []))
    elif isinstance(response, list):
        items = response
    
    for item in items:
        normalized = _normalize_keyword_record(item)
        if normalized:
            keywords.append(normalized)
            if len(keywords) >= limit:
                break
    return keywords


def _extract_keywords_from_ideas_response(response: Any, limit: int = 200) -> List[Dict[str, Any]]:
    if isinstance(response, list):
        records = response
    elif isinstance(response, dict) and "tasks" in response:
        records = []
        for task in response.get("tasks", []):
            result_data = task.get("result")
            if result_data is None:
                continue
            if isinstance(result_data, list):
                records.extend(result_data)
            elif isinstance(result_data, dict):
                records.append(result_data)
    else:
        return []
    
    keywords: List[Dict[str, Any]] = []
    for item in records:
        normalized = _normalize_keyword_record(item)
        if normalized:
            keywords.append(normalized)
        if len(keywords) >= limit:
            break
    return keywords


def _normalize_keyword_record(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(item, dict):
        return None
    keyword = item.get("keyword") or item.get("text")
    keyword_data = item.get("keyword_data", {})
    keyword_info = keyword_data.get("keyword_info", {})
    
    if not keyword:
        keyword = keyword_data.get("keyword")
    if not keyword:
        return None
    
    search_volume = keyword_info.get("search_volume", item.get("search_volume", 0))
    keyword_difficulty = keyword_info.get("keyword_difficulty", item.get("keyword_difficulty"))
    cpc = keyword_info.get("cpc", item.get("cpc", 0.0))
    competition = keyword_info.get("competition", item.get("competition", 0.0))
    
    intent_info = keyword_info.get("search_intent_info", keyword_data.get("search_intent_info", {}))
    intent = intent_info.get("main_intent") or keyword_info.get("search_intent") or item.get("search_intent")
    
    return {
        "keyword": keyword,
        "search_volume": search_volume or 0,
        "keyword_difficulty": keyword_difficulty or 0,
        "cpc": cpc or 0.0,
        "competition": competition or 0.0,
        "parent_topic": keyword_info.get("parent_topic"),
        "intent": intent,
    }


def _looks_like_question(keyword: str) -> bool:
    keyword_lower = keyword.lower()
    question_prefixes = ("how", "what", "when", "where", "why", "who", "can", "does", "is", "are", "should")
    return "?" in keyword or keyword_lower.startswith(question_prefixes)


def _summarize_serp_analysis(raw: Any) -> Dict[str, Any]:
    """
    Process SERP analysis response, returning complete SERP data.
    Handles both dict and string responses, returns full SERP analysis data.
    """
    if not raw:
        return {}
    # Handle string responses (error messages or raw text)
    if isinstance(raw, str):
        logger.warning(f"SERP analysis returned string instead of dict: {raw[:100]}")
        return {}
    if not isinstance(raw, dict):
        logger.warning(f"SERP analysis returned unexpected type: {type(raw)}")
        return {}
    
    # Return full SERP analysis data (not just a summary)
    # This includes all organic results, PAA questions, featured snippets, etc.
    serp_data = {
        "keyword": raw.get("keyword"),
        "organic_results": raw.get("organic_results", []),
        "people_also_ask": raw.get("people_also_ask", []),
        "featured_snippet": raw.get("featured_snippet"),
        "video_results": raw.get("video_results", []),
        "image_results": raw.get("image_results", []),
        "related_searches": raw.get("related_searches", []),
        "top_domains": raw.get("top_domains", []),
        "competition_level": raw.get("competition_level", "medium"),
        "content_gaps": raw.get("content_gaps", []),
        "serp_features": raw.get("serp_features", {
            "has_featured_snippet": False,
            "has_people_also_ask": False,
            "has_videos": False,
            "has_images": False
        })
    }
    return serp_data


# Enhanced keyword analysis endpoint using DataForSEO (if configured)
@app.post("/api/v1/keywords/enhanced")
async def analyze_keywords_enhanced(
    request: EnhancedKeywordAnalysisRequest,
    http_request: Request
):
    """
    Enhanced keyword analysis leveraging DataForSEO when available.
    Includes keyword clustering and parent topic extraction.
    Falls back gracefully if credentials are not configured.
    
    Location Detection:
    - If `location` is specified in request, it will be used
    - If `location` is not specified (or is default "United States"), the API will attempt
      to detect location from the client's IP address
    - Falls back to "United States" if IP detection fails or is unavailable
    """
    try:
        # Detect location from IP if not explicitly specified
        detected_location = None
        if not request.location or request.location == "United States":
            if http_request:
                detected_location = await detect_location_from_ip(http_request)
                if detected_location:
                    logger.info(f"Detected location from IP: {detected_location}")
        
        # Use detected location or fall back to request location or default
        effective_location = detected_location or request.location or "United States"
        from src.blog_writer_sdk.seo.keyword_clustering import KeywordClustering
        
        # Apply testing mode limits
        limited_keywords = apply_keyword_limits(request.keywords)
        max_suggestions = apply_suggestions_limit(request.max_suggestions_per_keyword)
        limits = get_testing_limits() if is_testing_mode() else {}
        max_total = limits.get("max_total_keywords", 200) if is_testing_mode() else 200
        
        if is_testing_mode():
            logger.info(f"🧪 TESTING MODE: Keyword limits - {len(limited_keywords)} primary, {max_suggestions} suggestions/keyword, {max_total} total max")
        
        if not enhanced_analyzer:
            raise HTTPException(status_code=503, detail="Enhanced analyzer not available")
        results = await enhanced_analyzer.analyze_keywords_comprehensive(
            keywords=limited_keywords,
            tenant_id=os.getenv("TENANT_ID", "default")
        )
        
        # Get additional keyword suggestions using DataForSEO if available
        all_keywords = list(limited_keywords)
        if enhanced_analyzer and enhanced_analyzer._df_client:
            try:
                tenant_id = os.getenv("TENANT_ID", "default")
                await enhanced_analyzer._df_client.initialize_credentials(tenant_id)
                
                # Get suggestions for each seed keyword (apply testing limits)
                max_seed_keywords = limits.get("max_keywords", 5) if is_testing_mode() else 5
                for seed_keyword in limited_keywords[:max_seed_keywords]:
                    if len(all_keywords) >= max_total:
                        break
                    
                    try:
                        df_suggestions = await enhanced_analyzer._df_client.get_keyword_suggestions(
                            seed_keyword=seed_keyword,
                            location_name=effective_location,
                            language_code=request.language or "en",
                            tenant_id=tenant_id,
                            limit=max_suggestions
                        )
                        
                        # Add new keywords that aren't already in the list (apply testing limits)
                        for suggestion in df_suggestions:
                            if len(all_keywords) >= max_total:
                                break
                            kw = suggestion.get("keyword", "").strip()
                            if kw and kw not in all_keywords:
                                all_keywords.append(kw)
                    except Exception as e:
                        logger.warning(f"Failed to get suggestions for {seed_keyword}: {e}")
                        continue
            except Exception as e:
                logger.warning(f"DataForSEO suggestions failed: {e}")
        
        # Analyze all keywords (original + suggestions)
        if len(all_keywords) > len(request.keywords):
            # Analyze additional keywords
            additional_results = await enhanced_analyzer.analyze_keywords_comprehensive(
                keywords=all_keywords[len(request.keywords):],
                tenant_id=os.getenv("TENANT_ID", "default")
            )
            # Merge results
            results.update(additional_results)
        
        # Cluster keywords by parent topics
        # Use global knowledge graph client if available
        kg_client = None
        try:
            kg_client = google_knowledge_graph_client if 'google_knowledge_graph_client' in globals() else None
        except:
            pass
        
        clustering = KeywordClustering(knowledge_graph_client=kg_client)
        try:
            # Apply testing mode clustering limits
            max_clusters, max_keywords_per_cluster = apply_clustering_limits()
            clustering_result = clustering.cluster_keywords(
                keywords=all_keywords,
                min_cluster_size=1,  # Allow single keywords to form clusters
                max_clusters=max_clusters,
                max_keywords_per_cluster=max_keywords_per_cluster
            )
            # Log clustering results for debugging
            logger.info(f"Clustering result: {clustering_result.cluster_count} clusters from {clustering_result.total_keywords} keywords")
            logger.info(f"Clusters: {[c.parent_topic for c in clustering_result.clusters[:5]]}")
        except Exception as e:
            logger.warning(f"Clustering failed: {e}, continuing without clustering")
            # Create a fallback clustering result
            from src.blog_writer_sdk.seo.keyword_clustering import ClusteringResult, KeywordCluster
            clustering_result = ClusteringResult(
                clusters=[KeywordCluster(
                    parent_topic=kw,
                    keywords=[kw],
                    cluster_score=0.5,
                    dominant_words=kw.split()[:3],
                    category_type="topic"
                ) for kw in all_keywords[:50]],
                unclustered=all_keywords[50:] if len(all_keywords) > 50 else [],
                total_keywords=len(all_keywords),
                cluster_count=min(len(all_keywords), 50)
            )
        
        # Get AI optimization data for all keywords (critical for AI-optimized content)
        ai_optimization_data = {}
        if enhanced_analyzer and enhanced_analyzer._df_client:
            try:
                tenant_id = os.getenv("TENANT_ID", "default")
                await enhanced_analyzer._df_client.initialize_credentials(tenant_id)
                ai_optimization_data = await enhanced_analyzer._df_client.get_ai_search_volume(
                    keywords=list(results.keys()),
                    location_name=effective_location,
                    language_code=request.language or "en",
                    tenant_id=tenant_id
                )
            except Exception as e:
                logger.warning(f"Failed to get AI optimization data: {e}")
                # Continue without AI data
        
        # Get related keywords and keyword ideas (questions/topics) for primary keywords
        related_keywords_data = {}
        keyword_ideas_data = {}
        if enhanced_analyzer and enhanced_analyzer._df_client:
            try:
                tenant_id = os.getenv("TENANT_ID", "default")
                await enhanced_analyzer._df_client.initialize_credentials(tenant_id)
                
                # Get related keywords (graph-based) and keyword ideas for primary keywords only
                max_primary = min(len(limited_keywords), 5)  # Limit to 5 primary keywords to avoid too many API calls
                for primary_keyword in limited_keywords[:max_primary]:
                    try:
                        # Get related keywords (graph traversal)
                        related_response = await enhanced_analyzer._df_client.get_related_keywords(
                            keyword=primary_keyword,
                            location_name=effective_location,
                            language_code=request.language or "en",
                            tenant_id=tenant_id,
                            depth=1,  # Start with depth 1 for speed
                            limit=20  # Limit to top 20 related keywords
                        )
                        # Parse related keywords response
                        related_keywords_list = []
                        if isinstance(related_response, dict) and related_response.get("tasks"):
                            tasks_list = related_response.get("tasks", [])
                            if tasks_list and len(tasks_list) > 0:
                                first_task = tasks_list[0]
                                # Check task status_code first (20000 = success)
                                task_status_code = first_task.get("status_code")
                                if task_status_code == 20000:
                                    result = first_task.get("result")
                                    if result and isinstance(result, list):
                                        for item in result[:20]:  # Limit to 20
                                            if not isinstance(item, dict):
                                                continue
                                            # Extract keyword from multiple possible locations
                                            keyword_text = item.get("keyword") or ""
                                            kw_data = item.get("keyword_data", {})
                                            keyword_info = kw_data.get("keyword_info", {}) if kw_data else {}
                                            
                                            if not keyword_text:
                                                keyword_text = keyword_info.get("keyword", "")
                                            
                                            if not keyword_text:
                                                continue
                                            
                                            related_keywords_list.append({
                                                "keyword": keyword_text,
                                                "search_volume": keyword_info.get("search_volume", 0) or item.get("search_volume", 0) or 0,
                                                "cpc": keyword_info.get("cpc", 0.0) or item.get("cpc", 0.0) or 0.0,
                                                "competition": keyword_info.get("competition", 0.0) or item.get("competition", 0.0) or 0.0,
                                                "difficulty_score": keyword_info.get("keyword_difficulty", 50.0) or item.get("keyword_difficulty", 50.0) or 50.0,
                                            })
                                else:
                                    logger.debug(f"Related keywords task has error status_code: {task_status_code}, message: {first_task.get('status_message')}")
                        related_keywords_data[primary_keyword] = related_keywords_list
                    except Exception as e:
                        logger.warning(f"Failed to get related keywords for {primary_keyword}: {e}")
                        related_keywords_data[primary_keyword] = []
                    
                    try:
                        # Get keyword ideas (includes questions and topics)
                        ideas_response = await enhanced_analyzer._df_client.get_keyword_ideas(
                            keywords=[primary_keyword],
                            location_name=effective_location,
                            language_code=request.language or "en",
                            tenant_id=tenant_id,
                            limit=50  # Limit to 50 ideas per keyword
                        )
                        # Parse keyword ideas response (returns list directly)
                        ideas_list = []
                        questions_list = []
                        topics_list = []
                        
                        # Parse keyword ideas response - handle both list and dict formats
                        if isinstance(ideas_response, list):
                            # Direct list format
                            for item in ideas_response[:50]:  # Limit to 50
                                if not isinstance(item, dict):
                                    continue
                                keyword_text = item.get("keyword", "") or item.get("text", "")
                                keyword_info = item.get("keyword_info", {})
                                keyword_data = item.get("keyword_data", {})
                                if not keyword_text and keyword_data:
                                    keyword_info_from_data = keyword_data.get("keyword_info", {})
                                    keyword_text = keyword_info_from_data.get("keyword", "")
                                
                                if not keyword_text:
                                    continue
                                
                                idea_item = {
                                    "keyword": keyword_text,
                                    "search_volume": keyword_info.get("search_volume", 0) or item.get("search_volume", 0) or 0,
                                    "cpc": keyword_info.get("cpc", 0.0) or item.get("cpc", 0.0) or 0.0,
                                    "competition": keyword_info.get("competition", 0.0) or item.get("competition", 0.0) or 0.0,
                                    "difficulty_score": keyword_info.get("keyword_difficulty", 50.0) or item.get("keyword_difficulty", 50.0) or 50.0,
                                }
                                ideas_list.append(idea_item)
                                
                                # Categorize as question or topic
                                keyword_lower = keyword_text.lower()
                                if any(q_word in keyword_lower for q_word in ["how", "what", "why", "when", "where", "who", "does", "can", "should", "is", "are", "?"]):
                                    questions_list.append(idea_item)
                                else:
                                    topics_list.append(idea_item)
                        elif isinstance(ideas_response, dict) and ideas_response.get("tasks"):
                            # Handle task-based response format
                            for task in ideas_response.get("tasks", []):
                                # Check task status_code first (20000 = success)
                                task_status_code = task.get("status_code")
                                if task_status_code != 20000:
                                    logger.debug(f"Keyword ideas task has error status_code: {task_status_code}, message: {task.get('status_message')}")
                                    continue
                                
                                result = task.get("result", [])
                                if not result or not isinstance(result, list):
                                    continue
                                
                                for item in result[:50]:
                                    if not isinstance(item, dict):
                                        continue
                                    keyword_text = item.get("keyword", "") or item.get("text", "")
                                    keyword_data = item.get("keyword_data", {})
                                    keyword_info = keyword_data.get("keyword_info", {}) if keyword_data else item.get("keyword_info", {})
                                    
                                    if not keyword_text:
                                        keyword_text = keyword_info.get("keyword", "")
                                    
                                    if not keyword_text:
                                        continue
                                    
                                    idea_item = {
                                        "keyword": keyword_text,
                                        "search_volume": keyword_info.get("search_volume", 0) or item.get("search_volume", 0) or 0,
                                        "cpc": keyword_info.get("cpc", 0.0) or item.get("cpc", 0.0) or 0.0,
                                        "competition": keyword_info.get("competition", 0.0) or item.get("competition", 0.0) or 0.0,
                                        "difficulty_score": keyword_info.get("keyword_difficulty", 50.0) or item.get("keyword_difficulty", 50.0) or 50.0,
                                    }
                                    ideas_list.append(idea_item)
                                    
                                    keyword_lower = keyword_text.lower()
                                    if any(q_word in keyword_lower for q_word in ["how", "what", "why", "when", "where", "who", "does", "can", "should", "is", "are", "?"]):
                                        questions_list.append(idea_item)
                                    else:
                                        topics_list.append(idea_item)
                        
                        keyword_ideas_data[primary_keyword] = {
                            "all_ideas": ideas_list,
                            "questions": questions_list,
                            "topics": topics_list,
                        }
                    except Exception as e:
                        logger.warning(f"Failed to get keyword ideas for {primary_keyword}: {e}")
                        keyword_ideas_data[primary_keyword] = {
                            "all_ideas": [],
                            "questions": [],
                            "topics": [],
                        }
            except Exception as e:
                logger.warning(f"Failed to get related keywords and ideas: {e}")
        
        # Shape into a simple dict for API response with parent topics
        out = {}
        for k, v in results.items():
            # Find parent topic for this keyword
            parent_topic = None
            category_type = None
            cluster_score = None
            
            for cluster in clustering_result.clusters:
                if k in cluster.keywords:
                    parent_topic = cluster.parent_topic
                    category_type = cluster.category_type
                    cluster_score = cluster.cluster_score
                    break
            
            # If not found in cluster, extract from keyword itself
            if not parent_topic:
                parent_topic = clustering._extract_parent_topic_from_keyword(k)
                category_type = clustering._classify_keyword_type(k)
                cluster_score = 0.5
            
            # Ensure search_volume and cpc are always numeric (never None)
            search_volume = v.search_volume if v.search_volume is not None else 0
            cpc_value = v.cpc if v.cpc is not None else 0.0
            competition_value = v.competition if v.competition is not None else 0.0
            trend_score_value = v.trend_score if v.trend_score is not None else 0.0
            
            # Get AI optimization metrics
            ai_metrics = ai_optimization_data.get(k, {})
            ai_search_volume = ai_metrics.get("ai_search_volume", 0) or 0
            ai_trend = ai_metrics.get("ai_trend", 0.0) or 0.0
            ai_monthly_searches = ai_metrics.get("ai_monthly_searches", [])
            
            # Get difficulty_score from analysis object (stored as attribute, may not be in model)
            # Use getattr with try/except to handle Pydantic strictness
            try:
                difficulty_score = getattr(v, 'difficulty_score', None)
            except (AttributeError, ValueError):
                difficulty_score = None
            
            if difficulty_score is None:
                # Calculate from difficulty enum if not available
                difficulty_enum = v.difficulty.value if hasattr(v.difficulty, "value") else str(v.difficulty)
                enum_to_score = {
                    "VERY_EASY": 10.0,
                    "EASY": 30.0,
                    "MEDIUM": 50.0,
                    "HARD": 70.0,
                    "VERY_HARD": 90.0
                }
                difficulty_score = enum_to_score.get(difficulty_enum, 50.0)
            
            # Get related keywords and ideas for this keyword if available
            related_keywords_enhanced = related_keywords_data.get(k, [])
            keyword_ideas_enhanced = keyword_ideas_data.get(k, {
                "all_ideas": [],
                "questions": [],
                "topics": [],
            })
            
            out[k] = {
                "search_volume": search_volume,  # Always numeric
                "global_search_volume": v.global_search_volume or 0,
                "search_volume_by_country": v.search_volume_by_country,
                "monthly_searches": v.monthly_searches,
                "difficulty": v.difficulty.value if hasattr(v.difficulty, "value") else str(v.difficulty),
                "difficulty_score": float(difficulty_score) if difficulty_score is not None else 50.0,  # Numeric score for gauge
                "competition": competition_value,
                "cpc": cpc_value,  # Always numeric
                "cpc_currency": v.cpc_currency,
                "cps": v.cps,
                "clicks": v.clicks,
                "trend_score": trend_score_value,
                "recommended": v.recommended,
                "reason": v.reason,
                "related_keywords": v.related_keywords,  # Basic related keywords from content analysis
                "related_keywords_enhanced": related_keywords_enhanced,  # Graph-based related keywords from DataForSEO
                "long_tail_keywords": v.long_tail_keywords,
                "questions": keyword_ideas_enhanced.get("questions", []),  # Question-type keywords
                "topics": keyword_ideas_enhanced.get("topics", []),  # Topic-type keywords
                "keyword_ideas": keyword_ideas_enhanced.get("all_ideas", []),  # All keyword ideas
                "parent_topic": parent_topic,
                "category_type": category_type,
                "cluster_score": cluster_score,
                # AI Optimization metrics (critical for AI-optimized content)
                "ai_search_volume": ai_search_volume,
                "ai_trend": ai_trend,
                "ai_monthly_searches": ai_monthly_searches,
                "traffic_potential": v.traffic_potential,
                "serp_features": v.serp_features,
                "serp_feature_counts": v.serp_feature_counts,
                "primary_intent": v.primary_intent,
                "intent_probabilities": v.intent_probabilities,
                "also_rank_for": v.also_rank_for,
                "also_talk_about": v.also_talk_about,
                "top_competitors": v.top_competitors,
                "first_seen": v.first_seen,
                "last_updated": v.last_updated,
            }
        
        # Ensure clusters are always returned, even if empty
        clusters_list = [
            {
                "parent_topic": c.parent_topic,
                "keywords": c.keywords,
                "cluster_score": c.cluster_score,
                "category_type": c.category_type,
                "keyword_count": len(c.keywords)
            }
            for c in clustering_result.clusters
        ]
        
        # If no clusters found, create single-keyword clusters from all keywords
        if not clusters_list and all_keywords:
            logger.warning(f"No clusters found for {len(all_keywords)} keywords, creating single-keyword clusters")
            for kw in all_keywords[:50]:  # Limit to first 50 to avoid huge responses
                parent_topic = clustering._extract_parent_topic_from_keyword(kw)
                clusters_list.append({
                    "parent_topic": parent_topic,
                    "keywords": [kw],
                    "cluster_score": 0.5,
                    "category_type": clustering._classify_keyword_type(kw),
                    "keyword_count": 1
                })
        
        discovery_data = {}
        serp_analysis_summary = {}
        if enhanced_analyzer and enhanced_analyzer._df_client and request.keywords:
            try:
                tenant_id_env = os.getenv("TENANT_ID", "default")
                # Ensure credentials are initialized
                await enhanced_analyzer._df_client.initialize_credentials(tenant_id_env)
                
                if not enhanced_analyzer._df_client.is_configured:
                    logger.warning("DataForSEO credentials not configured, skipping SERP analysis and discovery")
                else:
                    enrichment = await _build_keyword_discovery(
                        seed_keyword=request.keywords[0],
                        location=effective_location,
                        language=request.language or "en",
                        tenant_id=tenant_id_env,
                        df_client=enhanced_analyzer._df_client
                    )
                    serp_analysis_summary = enrichment.pop("serp_analysis", {})
                    discovery_data = enrichment
                    logger.info(f"SERP analysis and discovery data retrieved for keyword: {request.keywords[0]}")
            except Exception as e:
                logger.warning(f"Keyword discovery enrichment failed: {e}", exc_info=True)
        else:
            if not enhanced_analyzer:
                logger.debug("Enhanced analyzer not available")
            elif not enhanced_analyzer._df_client:
                logger.debug("DataForSEO client not initialized in enhanced analyzer")
            elif not request.keywords:
                logger.debug("No keywords provided for discovery")
        
        response_payload = {
            "enhanced_analysis": out,
            "total_keywords": len(all_keywords),
            "original_keywords": request.keywords,
            "suggested_keywords": all_keywords[len(request.keywords):] if len(all_keywords) > len(request.keywords) else [],
            "clusters": clusters_list,
            "cluster_summary": {
                "total_keywords": clustering_result.total_keywords if clustering_result else len(all_keywords),
                "cluster_count": len(clusters_list),
                "unclustered_count": len(clustering_result.unclustered) if clustering_result else 0
            },
            "location": {
                "used": effective_location,
                "detected_from_ip": detected_location is not None,
                "specified": request.location is not None and request.location != "United States"
            },
            "discovery": discovery_data,
            "serp_analysis": serp_analysis_summary
        }
        
        return response_payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced keyword analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Enhanced keyword analysis failed: {str(e)}"
        )


# Streaming version of enhanced keyword analysis
@app.post("/api/v1/keywords/enhanced/stream")
async def analyze_keywords_enhanced_stream(
    request: EnhancedKeywordAnalysisRequest,
    http_request: Request
):
    """
    Streaming version of enhanced keyword analysis.
    
    Returns Server-Sent Events (SSE) stream showing progress through each stage:
    - initializing: Starting search
    - detecting_location: Detecting user location
    - analyzing_keywords: Analyzing primary keywords
    - getting_suggestions: Fetching keyword suggestions
    - analyzing_suggestions: Analyzing suggested keywords
    - clustering_keywords: Clustering keywords by topic
    - getting_ai_data: Getting AI optimization metrics
    - getting_related_keywords: Finding related keywords
    - getting_keyword_ideas: Getting keyword ideas (questions/topics)
    - analyzing_serp: Analyzing SERP features (if requested)
    - building_discovery: Building discovery data
    - completed: Final results
    
    Frontend can listen to these events to show real-time progress.
    
    Example:
    ```typescript
    const response = await fetch('/api/v1/keywords/enhanced/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keywords: ['seo'], location: 'United States' })
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      const lines = chunk.split('\\n');
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const update = JSON.parse(line.slice(6));
          console.log(`Stage: ${update.stage}, Progress: ${update.progress}%`);
        }
      }
    }
    ```
    """
    async def generate_stream():
        try:
            # Stage 1: Initializing
            yield await stream_stage_update(
                KeywordSearchStage.INITIALIZING,
                5.0,
                message="Initializing keyword search..."
            )
            
            # Stage 2: Detecting location
            detected_location = None
            if not request.location or request.location == "United States":
                yield await stream_stage_update(
                    KeywordSearchStage.DETECTING_LOCATION,
                    10.0,
                    message="Detecting location from IP..."
                )
                if http_request:
                    detected_location = await detect_location_from_ip(http_request)
                    if detected_location:
                        yield await stream_stage_update(
                            KeywordSearchStage.DETECTING_LOCATION,
                            15.0,
                            data={"detected_location": detected_location},
                            message=f"Detected location: {detected_location}"
                        )
            
            effective_location = detected_location or request.location or "United States"
            
            # Stage 3: Analyzing keywords
            yield await stream_stage_update(
                KeywordSearchStage.ANALYZING_KEYWORDS,
                20.0,
                data={"keywords": request.keywords, "location": effective_location},
                message=f"Analyzing {len(request.keywords)} keywords..."
            )
            
            if not enhanced_analyzer:
                raise HTTPException(status_code=503, detail="Enhanced analyzer not available")
            
            # Apply limits
            limited_keywords = apply_keyword_limits(request.keywords)
            max_suggestions = apply_suggestions_limit(request.max_suggestions_per_keyword)
            limits = get_testing_limits() if is_testing_mode() else {}
            max_total = limits.get("max_total_keywords", 200) if is_testing_mode() else 200
            
            # Analyze primary keywords
            results = await enhanced_analyzer.analyze_keywords_comprehensive(
                keywords=limited_keywords,
                tenant_id=os.getenv("TENANT_ID", "default")
            )
            
            yield await stream_stage_update(
                KeywordSearchStage.ANALYZING_KEYWORDS,
                30.0,
                data={"keywords_analyzed": len(results)},
                message=f"Analyzed {len(results)} keywords"
            )
            
            # Stage 4: Getting suggestions
            all_keywords = list(limited_keywords)
            if enhanced_analyzer and enhanced_analyzer._df_client:
                yield await stream_stage_update(
                    KeywordSearchStage.GETTING_SUGGESTIONS,
                    40.0,
                    message="Getting keyword suggestions from DataForSEO..."
                )
                
                try:
                    tenant_id = os.getenv("TENANT_ID", "default")
                    await enhanced_analyzer._df_client.initialize_credentials(tenant_id)
                    
                    max_seed_keywords = limits.get("max_keywords", 5) if is_testing_mode() else 5
                    for idx, seed_keyword in enumerate(limited_keywords[:max_seed_keywords]):
                        if len(all_keywords) >= max_total:
                            break
                        
                        yield await stream_stage_update(
                            KeywordSearchStage.GETTING_SUGGESTIONS,
                            40.0 + (idx + 1) * 5.0 / max_seed_keywords,
                            data={"current_keyword": seed_keyword, "suggestions_found": len(all_keywords) - len(limited_keywords)},
                            message=f"Getting suggestions for '{seed_keyword}'..."
                        )
                        
                        try:
                            df_suggestions = await enhanced_analyzer._df_client.get_keyword_suggestions(
                                seed_keyword=seed_keyword,
                                location_name=effective_location,
                                language_code=request.language or "en",
                                tenant_id=tenant_id,
                                limit=max_suggestions
                            )
                            
                            for suggestion in df_suggestions:
                                if len(all_keywords) >= max_total:
                                    break
                                kw = suggestion.get("keyword", "").strip()
                                if kw and kw not in all_keywords:
                                    all_keywords.append(kw)
                        except Exception as e:
                            logger.warning(f"Failed to get suggestions for {seed_keyword}: {e}")
                            continue
                except Exception as e:
                    logger.warning(f"DataForSEO suggestions failed: {e}")
            
            # Stage 5: Analyzing suggestions
            if len(all_keywords) > len(request.keywords):
                yield await stream_stage_update(
                    KeywordSearchStage.ANALYZING_SUGGESTIONS,
                    50.0,
                    data={"suggestions_to_analyze": len(all_keywords) - len(request.keywords)},
                    message=f"Analyzing {len(all_keywords) - len(request.keywords)} suggested keywords..."
                )
                
                additional_results = await enhanced_analyzer.analyze_keywords_comprehensive(
                    keywords=all_keywords[len(request.keywords):],
                    tenant_id=os.getenv("TENANT_ID", "default")
                )
                results.update(additional_results)
                
                yield await stream_stage_update(
                    KeywordSearchStage.ANALYZING_SUGGESTIONS,
                    55.0,
                    data={"total_keywords_analyzed": len(results)},
                    message="Completed analyzing suggestions"
                )
            
            # Stage 6: Clustering
            yield await stream_stage_update(
                KeywordSearchStage.CLUSTERING_KEYWORDS,
                60.0,
                message="Clustering keywords by topic..."
            )
            
            from src.blog_writer_sdk.seo.keyword_clustering import KeywordClustering
            kg_client = None
            try:
                kg_client = google_knowledge_graph_client if 'google_knowledge_graph_client' in globals() else None
            except:
                pass
            
            clustering = KeywordClustering(knowledge_graph_client=kg_client)
            try:
                max_clusters, max_keywords_per_cluster = apply_clustering_limits()
                clustering_result = clustering.cluster_keywords(
                    keywords=all_keywords,
                    min_cluster_size=1,
                    max_clusters=max_clusters,
                    max_keywords_per_cluster=max_keywords_per_cluster
                )
                
                yield await stream_stage_update(
                    KeywordSearchStage.CLUSTERING_KEYWORDS,
                    65.0,
                    data={"clusters_found": clustering_result.cluster_count, "total_keywords": clustering_result.total_keywords},
                    message=f"Found {clustering_result.cluster_count} keyword clusters"
                )
            except Exception as e:
                logger.warning(f"Clustering failed: {e}")
                from src.blog_writer_sdk.seo.keyword_clustering import ClusteringResult, KeywordCluster
                clustering_result = ClusteringResult(
                    clusters=[KeywordCluster(
                        parent_topic=kw,
                        keywords=[kw],
                        cluster_score=0.5,
                        dominant_words=kw.split()[:3],
                        category_type="topic"
                    ) for kw in all_keywords[:50]],
                    unclustered=all_keywords[50:] if len(all_keywords) > 50 else [],
                    total_keywords=len(all_keywords),
                    cluster_count=min(len(all_keywords), 50)
                )
            
            # Stage 7: Getting AI data
            yield await stream_stage_update(
                KeywordSearchStage.GETTING_AI_DATA,
                70.0,
                message="Getting AI optimization metrics..."
            )
            
            ai_optimization_data = {}
            if enhanced_analyzer and enhanced_analyzer._df_client:
                try:
                    tenant_id = os.getenv("TENANT_ID", "default")
                    await enhanced_analyzer._df_client.initialize_credentials(tenant_id)
                    ai_optimization_data = await enhanced_analyzer._df_client.get_ai_search_volume(
                        keywords=list(results.keys()),
                        location_name=effective_location,
                        language_code=request.language or "en",
                        tenant_id=tenant_id
                    )
                    
                    yield await stream_stage_update(
                        KeywordSearchStage.GETTING_AI_DATA,
                        75.0,
                        data={"ai_metrics_count": len(ai_optimization_data)},
                        message=f"Retrieved AI metrics for {len(ai_optimization_data)} keywords"
                    )
                except Exception as e:
                    logger.warning(f"Failed to get AI optimization data: {e}")
            
            # Stage 8: Getting related keywords
            related_keywords_data = {}
            if enhanced_analyzer and enhanced_analyzer._df_client:
                yield await stream_stage_update(
                    KeywordSearchStage.GETTING_RELATED_KEYWORDS,
                    80.0,
                    message="Finding related keywords..."
                )
                
                try:
                    tenant_id = os.getenv("TENANT_ID", "default")
                    await enhanced_analyzer._df_client.initialize_credentials(tenant_id)
                    
                    max_primary = min(len(limited_keywords), 5)
                    for idx, primary_keyword in enumerate(limited_keywords[:max_primary]):
                        yield await stream_stage_update(
                            KeywordSearchStage.GETTING_RELATED_KEYWORDS,
                            80.0 + (idx + 1) * 2.0 / max_primary,
                            data={"current_keyword": primary_keyword},
                            message=f"Finding related keywords for '{primary_keyword}'..."
                        )
                        
                        try:
                            related_response = await enhanced_analyzer._df_client.get_related_keywords(
                                keyword=primary_keyword,
                                location_name=effective_location,
                                language_code=request.language or "en",
                                tenant_id=tenant_id,
                                depth=1,
                                limit=20
                            )
                            
                            related_keywords_list = []
                            if isinstance(related_response, dict) and related_response.get("tasks"):
                                tasks_list = related_response.get("tasks", [])
                                if tasks_list and len(tasks_list) > 0:
                                    first_task = tasks_list[0]
                                    task_status_code = first_task.get("status_code")
                                    if task_status_code == 20000:
                                        result = first_task.get("result")
                                        if result and isinstance(result, list):
                                            for item in result[:20]:
                                                if not isinstance(item, dict):
                                                    continue
                                                keyword_text = item.get("keyword") or ""
                                                kw_data = item.get("keyword_data", {})
                                                keyword_info = kw_data.get("keyword_info", {}) if kw_data else {}
                                                
                                                if not keyword_text:
                                                    keyword_text = keyword_info.get("keyword", "")
                                                
                                                if keyword_text:
                                                    related_keywords_list.append({
                                                        "keyword": keyword_text,
                                                        "search_volume": keyword_info.get("search_volume", 0) or item.get("search_volume", 0) or 0,
                                                        "cpc": keyword_info.get("cpc", 0.0) or item.get("cpc", 0.0) or 0.0,
                                                        "competition": keyword_info.get("competition", 0.0) or item.get("competition", 0.0) or 0.0,
                                                        "difficulty_score": keyword_info.get("keyword_difficulty", 50.0) or item.get("keyword_difficulty", 50.0) or 50.0,
                                                    })
                            related_keywords_data[primary_keyword] = related_keywords_list
                        except Exception as e:
                            logger.warning(f"Failed to get related keywords for {primary_keyword}: {e}")
                            related_keywords_data[primary_keyword] = []
                except Exception as e:
                    logger.warning(f"Failed to get related keywords: {e}")
            
            # Stage 9: Getting keyword ideas
            keyword_ideas_data = {}
            if enhanced_analyzer and enhanced_analyzer._df_client:
                yield await stream_stage_update(
                    KeywordSearchStage.GETTING_KEYWORD_IDEAS,
                    85.0,
                    message="Getting keyword ideas (questions and topics)..."
                )
                
                try:
                    tenant_id = os.getenv("TENANT_ID", "default")
                    await enhanced_analyzer._df_client.initialize_credentials(tenant_id)
                    
                    max_primary = min(len(limited_keywords), 5)
                    for idx, primary_keyword in enumerate(limited_keywords[:max_primary]):
                        yield await stream_stage_update(
                            KeywordSearchStage.GETTING_KEYWORD_IDEAS,
                            85.0 + (idx + 1) * 3.0 / max_primary,
                            data={"current_keyword": primary_keyword},
                            message=f"Getting ideas for '{primary_keyword}'..."
                        )
                        
                        try:
                            ideas_response = await enhanced_analyzer._df_client.get_keyword_ideas(
                                keywords=[primary_keyword],
                                location_name=effective_location,
                                language_code=request.language or "en",
                                tenant_id=tenant_id,
                                limit=50
                            )
                            
                            ideas_list = []
                            questions_list = []
                            topics_list = []
                            
                            if isinstance(ideas_response, list):
                                for item in ideas_response[:50]:
                                    if not isinstance(item, dict):
                                        continue
                                    keyword_text = item.get("keyword", "") or item.get("text", "")
                                    keyword_info = item.get("keyword_info", {})
                                    keyword_data = item.get("keyword_data", {})
                                    if not keyword_text and keyword_data:
                                        keyword_info_from_data = keyword_data.get("keyword_info", {})
                                        keyword_text = keyword_info_from_data.get("keyword", "")
                                    
                                    if keyword_text:
                                        idea_item = {
                                            "keyword": keyword_text,
                                            "search_volume": keyword_info.get("search_volume", 0) or item.get("search_volume", 0) or 0,
                                            "cpc": keyword_info.get("cpc", 0.0) or item.get("cpc", 0.0) or 0.0,
                                            "competition": keyword_info.get("competition", 0.0) or item.get("competition", 0.0) or 0.0,
                                            "difficulty_score": keyword_info.get("keyword_difficulty", 50.0) or item.get("keyword_difficulty", 50.0) or 50.0,
                                        }
                                        ideas_list.append(idea_item)
                                        
                                        keyword_lower = keyword_text.lower()
                                        if any(q_word in keyword_lower for q_word in ["how", "what", "why", "when", "where", "who", "does", "can", "should", "is", "are", "?"]):
                                            questions_list.append(idea_item)
                                        else:
                                            topics_list.append(idea_item)
                            
                            keyword_ideas_data[primary_keyword] = {
                                "all_ideas": ideas_list,
                                "questions": questions_list,
                                "topics": topics_list,
                            }
                        except Exception as e:
                            logger.warning(f"Failed to get keyword ideas for {primary_keyword}: {e}")
                            keyword_ideas_data[primary_keyword] = {
                                "all_ideas": [],
                                "questions": [],
                                "topics": [],
                            }
                except Exception as e:
                    logger.warning(f"Failed to get keyword ideas: {e}")
            
            # Stage 10: SERP analysis (if requested)
            serp_analysis_summary = {}
            discovery_data = {}
            if request.include_serp and enhanced_analyzer and enhanced_analyzer._df_client and request.keywords:
                yield await stream_stage_update(
                    KeywordSearchStage.ANALYZING_SERP,
                    92.0,
                    data={"keyword": request.keywords[0]},
                    message=f"Analyzing SERP for '{request.keywords[0]}'..."
                )
                
                try:
                    tenant_id_env = os.getenv("TENANT_ID", "default")
                    await enhanced_analyzer._df_client.initialize_credentials(tenant_id_env)
                    
                    if enhanced_analyzer._df_client.is_configured:
                        enrichment = await _build_keyword_discovery(
                            seed_keyword=request.keywords[0],
                            location=effective_location,
                            language=request.language or "en",
                            tenant_id=tenant_id_env,
                            df_client=enhanced_analyzer._df_client
                        )
                        serp_analysis_summary = enrichment.pop("serp_analysis", {})
                        discovery_data = enrichment
                        
                        yield await stream_stage_update(
                            KeywordSearchStage.ANALYZING_SERP,
                            95.0,
                            data={"serp_features_found": len(serp_analysis_summary.get("serp_features", {}))},
                            message="SERP analysis completed"
                        )
                except Exception as e:
                    logger.warning(f"SERP analysis failed: {e}")
            
            # Stage 11: Building final response
            yield await stream_stage_update(
                KeywordSearchStage.BUILDING_DISCOVERY,
                98.0,
                message="Building final results..."
            )
            
            # Build response (same logic as non-streaming endpoint)
            from src.blog_writer_sdk.seo.keyword_clustering import KeywordClustering
            clustering = KeywordClustering(knowledge_graph_client=kg_client)
            
            out = {}
            for k, v in results.items():
                parent_topic = None
                category_type = None
                cluster_score = None
                
                for cluster in clustering_result.clusters:
                    if k in cluster.keywords:
                        parent_topic = cluster.parent_topic
                        category_type = cluster.category_type
                        cluster_score = cluster.cluster_score
                        break
                
                if not parent_topic:
                    parent_topic = clustering._extract_parent_topic_from_keyword(k)
                    category_type = clustering._classify_keyword_type(k)
                    cluster_score = 0.5
                
                search_volume = v.search_volume if v.search_volume is not None else 0
                cpc_value = v.cpc if v.cpc is not None else 0.0
                competition_value = v.competition if v.competition is not None else 0.0
                trend_score_value = v.trend_score if v.trend_score is not None else 0.0
                
                ai_metrics = ai_optimization_data.get(k, {})
                ai_search_volume = ai_metrics.get("ai_search_volume", 0) or 0
                ai_trend = ai_metrics.get("ai_trend", 0.0) or 0.0
                ai_monthly_searches = ai_metrics.get("ai_monthly_searches", [])
                
                try:
                    difficulty_score = getattr(v, 'difficulty_score', None)
                except (AttributeError, ValueError):
                    difficulty_score = None
                
                if difficulty_score is None:
                    difficulty_enum = v.difficulty.value if hasattr(v.difficulty, "value") else str(v.difficulty)
                    enum_to_score = {
                        "VERY_EASY": 10.0,
                        "EASY": 30.0,
                        "MEDIUM": 50.0,
                        "HARD": 70.0,
                        "VERY_HARD": 90.0
                    }
                    difficulty_score = enum_to_score.get(difficulty_enum, 50.0)
                
                related_keywords_enhanced = related_keywords_data.get(k, [])
                keyword_ideas_enhanced = keyword_ideas_data.get(k, {
                    "all_ideas": [],
                    "questions": [],
                    "topics": [],
                })
                
                out[k] = {
                    "search_volume": search_volume,
                    "global_search_volume": v.global_search_volume or 0,
                    "search_volume_by_country": v.search_volume_by_country,
                    "monthly_searches": v.monthly_searches,
                    "difficulty": v.difficulty.value if hasattr(v.difficulty, "value") else str(v.difficulty),
                    "difficulty_score": float(difficulty_score) if difficulty_score is not None else 50.0,
                    "competition": competition_value,
                    "cpc": cpc_value,
                    "cpc_currency": v.cpc_currency,
                    "cps": v.cps,
                    "clicks": v.clicks,
                    "trend_score": trend_score_value,
                    "recommended": v.recommended,
                    "reason": v.reason,
                    "related_keywords": v.related_keywords,
                    "related_keywords_enhanced": related_keywords_enhanced,
                    "long_tail_keywords": v.long_tail_keywords,
                    "questions": keyword_ideas_enhanced.get("questions", []),
                    "topics": keyword_ideas_enhanced.get("topics", []),
                    "keyword_ideas": keyword_ideas_enhanced.get("all_ideas", []),
                    "parent_topic": parent_topic,
                    "category_type": category_type,
                    "cluster_score": cluster_score,
                    "ai_search_volume": ai_search_volume,
                    "ai_trend": ai_trend,
                    "ai_monthly_searches": ai_monthly_searches,
                    "traffic_potential": v.traffic_potential,
                    "serp_features": v.serp_features,
                    "serp_feature_counts": v.serp_feature_counts,
                    "primary_intent": v.primary_intent,
                    "intent_probabilities": v.intent_probabilities,
                    "also_rank_for": v.also_rank_for,
                    "also_talk_about": v.also_talk_about,
                    "top_competitors": v.top_competitors,
                    "first_seen": v.first_seen,
                    "last_updated": v.last_updated,
                }
            
            clusters_list = [
                {
                    "parent_topic": c.parent_topic,
                    "keywords": c.keywords,
                    "cluster_score": c.cluster_score,
                    "category_type": c.category_type,
                    "keyword_count": len(c.keywords)
                }
                for c in clustering_result.clusters
            ]
            
            if not clusters_list and all_keywords:
                for kw in all_keywords[:50]:
                    parent_topic = clustering._extract_parent_topic_from_keyword(kw)
                    clusters_list.append({
                        "parent_topic": parent_topic,
                        "keywords": [kw],
                        "cluster_score": 0.5,
                        "category_type": clustering._classify_keyword_type(kw),
                        "keyword_count": 1
                    })
            
            final_result = {
                "enhanced_analysis": out,
                "total_keywords": len(all_keywords),
                "original_keywords": request.keywords,
                "suggested_keywords": all_keywords[len(request.keywords):] if len(all_keywords) > len(request.keywords) else [],
                "clusters": clusters_list,
                "cluster_summary": {
                    "total_keywords": clustering_result.total_keywords if clustering_result else len(all_keywords),
                    "cluster_count": len(clusters_list),
                    "unclustered_count": len(clustering_result.unclustered) if clustering_result else 0
                },
                "location": {
                    "used": effective_location,
                    "detected_from_ip": detected_location is not None,
                    "specified": request.location is not None and request.location != "United States"
                },
                "discovery": discovery_data,
                "serp_analysis": serp_analysis_summary
            }
            
            # Stage 12: Completed - ALWAYS send final result
            # Log the final result to help debug
            logger.info(f"Sending final result in stream: {len(final_result.get('enhanced_analysis', {}))} keywords analyzed")
            
            completed_message = await stream_stage_update(
                KeywordSearchStage.COMPLETED,
                100.0,
                data={"result": final_result},
                message="Search completed successfully"
            )
            yield completed_message
            
            # Ensure stream is flushed and properly closed
            # Send an explicit end marker for frontend to detect
            yield f"data: {json.dumps({'type': 'end', 'stage': 'completed'})}\n\n"
            
        except HTTPException as http_ex:
            # For HTTP exceptions, send error but don't raise (to keep stream open)
            logger.error(f"Streaming keyword analysis HTTP error: {http_ex.detail}")
            yield await stream_stage_update(
                KeywordSearchStage.ERROR,
                0.0,
                data={"error": http_ex.detail, "status_code": http_ex.status_code},
                message=f"Search failed: {http_ex.detail}"
            )
            yield "\n"
        except Exception as e:
            logger.error(f"Streaming keyword analysis failed: {e}", exc_info=True)
            # Try to send partial results if available
            try:
                partial_result = {
                    "enhanced_analysis": {},
                    "total_keywords": 0,
                    "original_keywords": request.keywords,
                    "suggested_keywords": [],
                    "clusters": [],
                    "cluster_summary": {
                        "total_keywords": 0,
                        "cluster_count": 0,
                        "unclustered_count": 0
                    },
                    "location": {
                        "used": effective_location if 'effective_location' in locals() else request.location or "United States",
                        "detected_from_ip": detected_location is not None if 'detected_location' in locals() else False,
                        "specified": request.location is not None and request.location != "United States"
                    },
                    "discovery": {},
                    "serp_analysis": {},
                    "error": str(e)
                }
                
                # Send error with partial results if we have any data
                error_message = await stream_stage_update(
                    KeywordSearchStage.ERROR,
                    0.0,
                    data={"error": str(e), "partial_result": partial_result},
                    message=f"Search failed: {str(e)}"
                )
                yield error_message
            except:
                # If even partial result fails, send minimal error
                error_message = await stream_stage_update(
                    KeywordSearchStage.ERROR,
                    0.0,
                    data={"error": str(e)},
                    message=f"Search failed: {str(e)}"
                )
                yield error_message
            yield f"data: {json.dumps({'type': 'end', 'stage': 'error'})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@app.post("/api/v1/keywords/ai-optimization")
async def analyze_keywords_ai_optimization(
    request: EnhancedKeywordAnalysisRequest
):
    """
    Analyze keywords specifically for AI optimization.
    
    This endpoint focuses on AI search volume data, which is critical for creating
    content that appears in AI LLM responses (ChatGPT, Claude, Gemini, etc.).
    
    Returns:
    - ai_search_volume: Current month's estimated volume in AI queries
    - ai_monthly_searches: Historical trend over past 12 months
    - ai_trend: Trend score indicating if AI volume is increasing/decreasing
    - Comparison with traditional search volume
    - AI optimization recommendations
    """
    try:
        if not enhanced_analyzer or not enhanced_analyzer._df_client:
            raise HTTPException(status_code=503, detail="Enhanced analyzer with DataForSEO not available")
        
        tenant_id = os.getenv("TENANT_ID", "default")
        await enhanced_analyzer._df_client.initialize_credentials(tenant_id)
        
        # Get AI optimization data
        ai_data = await enhanced_analyzer._df_client.get_ai_search_volume(
            keywords=request.keywords,
            location_name=request.location or "United States",
            language_code=request.language or "en",
            tenant_id=tenant_id
        )
        
        # Get traditional search volume for comparison
        traditional_data = await enhanced_analyzer._df_client.get_search_volume_data(
            keywords=request.keywords,
            location_name=request.location or "United States",
            language_code=request.language or "en",
            tenant_id=tenant_id
        )
        
        # Build comprehensive AI optimization analysis
        ai_analysis = {}
        for keyword in request.keywords:
            ai_metrics = ai_data.get(keyword, {})
            traditional_metrics = traditional_data.get(keyword, {})
            
            ai_search_volume = ai_metrics.get("ai_search_volume", 0) or 0
            traditional_search_volume = traditional_metrics.get("search_volume", 0) or 0
            ai_trend = ai_metrics.get("ai_trend", 0.0) or 0.0
            ai_monthly_searches = ai_metrics.get("ai_monthly_searches", [])
            
            # Calculate AI optimization score (0-100)
            # Higher score = better for AI optimization
            ai_score = 0
            if ai_search_volume > 0:
                # Base score from AI volume (log scale)
                ai_score += min(50, math.log10(ai_search_volume + 1) * 10)
            
            # Trend bonus (positive trend = higher score)
            if ai_trend > 0:
                ai_score += min(25, ai_trend * 25)
            
            # Volume growth bonus
            if ai_monthly_searches and len(ai_monthly_searches) >= 2:
                recent_avg = sum(m.get("search_volume", 0) for m in ai_monthly_searches[-3:]) / 3
                older_avg = sum(m.get("search_volume", 0) for m in ai_monthly_searches[:3]) / 3
                if older_avg > 0:
                    growth = (recent_avg - older_avg) / older_avg
                    ai_score += min(25, growth * 25)
            
            # Determine AI optimization recommendation
            ai_recommended = ai_score >= 40
            if ai_score >= 70:
                ai_reason = "Excellent AI visibility - high volume and positive trend"
            elif ai_score >= 50:
                ai_reason = "Good AI visibility - moderate volume with growth potential"
            elif ai_score >= 30:
                ai_reason = "Moderate AI visibility - consider optimizing for AI search"
            else:
                ai_reason = "Low AI visibility - focus on traditional SEO or emerging AI trends"
            
            ai_analysis[keyword] = {
                "ai_search_volume": ai_search_volume,
                "traditional_search_volume": traditional_search_volume,
                "ai_trend": ai_trend,
                "ai_monthly_searches": ai_monthly_searches,
                "ai_optimization_score": min(100, max(0, int(ai_score))),
                "ai_recommended": ai_recommended,
                "ai_reason": ai_reason,
                "comparison": {
                    "ai_to_traditional_ratio": round(ai_search_volume / traditional_search_volume, 3) if traditional_search_volume > 0 else 0.0,
                    "ai_growth_trend": "increasing" if ai_trend > 0.1 else "decreasing" if ai_trend < -0.1 else "stable"
                }
            }
        
        return {
            "ai_optimization_analysis": ai_analysis,
            "total_keywords": len(request.keywords),
            "location": request.location or "United States",
            "language": request.language or "en",
            "summary": {
                "keywords_with_ai_volume": sum(1 for k, v in ai_analysis.items() if v["ai_search_volume"] > 0),
                "average_ai_score": sum(v["ai_optimization_score"] for v in ai_analysis.values()) / len(ai_analysis) if ai_analysis else 0,
                "recommended_keywords": [k for k, v in ai_analysis.items() if v["ai_recommended"]]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI optimization analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"AI optimization analysis failed: {str(e)}"
        )


@app.post("/api/v1/keywords/difficulty")
async def analyze_keyword_difficulty(
    request: KeywordDifficultyRequest
):
    """
    Analyze keyword difficulty with multi-factor analysis.
    
    Provides:
    - Domain authority requirements
    - Backlink requirements
    - Content length needs
    - Competition level
    - Time-to-rank estimates
    - Ranking probability over time
    """
    try:
        global keyword_difficulty_analyzer
        if not keyword_difficulty_analyzer:
            raise HTTPException(status_code=503, detail="Difficulty analyzer not available")
        
        analysis = await keyword_difficulty_analyzer.analyze_difficulty(
            keyword=request.keyword,
            search_volume=request.search_volume,
            difficulty=request.difficulty,
            competition=request.competition,
            location=request.location,
            language=request.language
        )
        
        return {
            "keyword": request.keyword,
            "overall_difficulty": analysis.overall_difficulty,
            "domain_authority_required": analysis.factors.domain_authority_required,
            "backlink_requirements": analysis.factors.backlink_requirements.value,
            "content_length_needed": analysis.factors.content_length_needed,
            "competition_level": analysis.factors.competition_level.value,
            "time_to_rank": analysis.factors.time_to_rank,
            "ranking_probability": analysis.factors.ranking_probability,
            "recommendations": analysis.recommendations,
            "metadata": analysis.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Difficulty analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Difficulty analysis failed: {str(e)}"
        )


@app.get("/api/v1/quota/{organization_id}")
async def get_quota_info(organization_id: str):
    """
    Get quota information for an organization.
    
    Returns:
    - Monthly, daily, and hourly limits
    - Current usage
    - Remaining quota
    - Warnings if approaching limits
    """
    try:
        global quota_manager
        if not quota_manager:
            raise HTTPException(status_code=503, detail="Quota manager not available")
        
        quota_info = await quota_manager.get_quota_info(organization_id)
        if not quota_info:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        return quota_info.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quota info retrieval failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Quota info retrieval failed: {str(e)}"
        )


@app.post("/api/v1/quota/{organization_id}/set-limits")
async def set_quota_limits(
    organization_id: str,
    request: SetQuotaLimitsRequest
):
    """
    Set custom quota limits for an organization.
    
    Only updates provided limits, leaves others unchanged.
    """
    try:
        global quota_manager
        if not quota_manager:
            raise HTTPException(status_code=503, detail="Quota manager not available")
        
        await quota_manager.set_quota_limits(
            organization_id=organization_id,
            monthly_limit=request.monthly_limit,
            daily_limit=request.daily_limit,
            hourly_limit=request.hourly_limit
        )
        
        return {"message": "Quota limits updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quota limit update failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Quota limit update failed: {str(e)}"
        )

# Topic recommendation endpoint
@app.post("/api/v1/topics/recommend")
async def recommend_topics(
    request: TopicRecommendationRequest
):
    """
    Recommend high-ranking blog topics based on seed keywords.
    
    Uses:
    - DataForSEO for keyword metrics (search volume, difficulty, competition)
    - Google Custom Search for content gap analysis
    - Claude AI (3.5 Sonnet) for intelligent topic generation
    
    Returns topics with ranking scores, opportunity scores, and content gap analysis.
    """
    try:
        global topic_recommender, ai_generator
        
        if not topic_recommender:
            raise HTTPException(
                status_code=503,
                detail="Topic recommendation engine not available"
            )
        
        # Get recommendations
        result = await topic_recommender.recommend_topics(
            seed_keywords=request.seed_keywords,
            location=request.location or "United States",
            language=request.language or "en",
            max_topics=request.max_topics,
            min_search_volume=request.min_search_volume,
            max_difficulty=request.max_difficulty,
            include_ai_suggestions=request.include_ai_suggestions
        )
        
        # Convert to response format
        return {
            "recommended_topics": [
                {
                    "topic": t.topic,
                    "primary_keyword": t.primary_keyword,
                    "search_volume": t.search_volume,
                    "difficulty": t.difficulty,
                    "competition": t.competition,
                    "cpc": t.cpc,
                    "ranking_score": t.ranking_score,
                    "opportunity_score": t.opportunity_score,
                    "related_keywords": t.related_keywords,
                    "content_gaps": t.content_gaps,
                    "estimated_traffic": t.estimated_traffic,
                    "reason": t.reason
                }
                for t in result.recommended_topics
            ],
            "high_priority_topics": [
                {
                    "topic": t.topic,
                    "primary_keyword": t.primary_keyword,
                    "ranking_score": t.ranking_score,
                    "search_volume": t.search_volume,
                    "difficulty": t.difficulty,
                    "reason": t.reason
                }
                for t in result.high_priority_topics
            ],
            "trending_topics": [
                {
                    "topic": t.topic,
                    "primary_keyword": t.primary_keyword,
                    "search_volume": t.search_volume,
                    "difficulty": t.difficulty,
                    "reason": t.reason
                }
                for t in result.trending_topics
            ],
            "low_competition_topics": [
                {
                    "topic": t.topic,
                    "primary_keyword": t.primary_keyword,
                    "difficulty": t.difficulty,
                    "competition": t.competition,
                    "reason": t.reason
                }
                for t in result.low_competition_topics
            ],
            "total_opportunities": result.total_opportunities,
            "analysis_date": result.analysis_date
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Topic recommendation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Topic recommendation failed: {str(e)}"
        )

# Extract keywords from content endpoint
@app.post("/api/v1/keywords/extract")
async def extract_keywords(
    request: KeywordExtractionRequest,
    writer: BlogWriter = Depends(get_blog_writer)
):
    """
    Extract potential keywords from existing content with clustering.
    
    Uses advanced NLP techniques to identify:
    - High-value keywords
    - Relevant phrases
    - Content themes
    - Parent topics (clustered keywords)
    
    Returns keywords grouped by parent topics for better organization.
    """
    try:
        from src.blog_writer_sdk.seo.keyword_clustering import KeywordClustering
        
        keywords = await writer.keyword_analyzer.extract_keywords_from_content(
            content=request.content,
            max_keywords=request.max_keywords,
            max_ngram=request.max_ngram,
            dedup_lim=request.dedup_lim
        )
        
        # Cluster keywords by parent topics
        # Use global knowledge graph client if available
        kg_client = None
        try:
            kg_client = google_knowledge_graph_client if 'google_knowledge_graph_client' in globals() else None
        except:
            pass
        
        clustering = KeywordClustering(knowledge_graph_client=kg_client)
        clustering_result = clustering.cluster_keywords(
            keywords=keywords,
            min_cluster_size=1,  # Allow single keywords to have parent topics
            max_clusters=None  # No limit
        )
        
        # Build response with parent topics
        keywords_with_topics = []
        for cluster in clustering_result.clusters:
            for keyword in cluster.keywords:
                keywords_with_topics.append({
                    "keyword": keyword,
                    "parent_topic": cluster.parent_topic,
                    "cluster_score": cluster.cluster_score,
                    "category_type": cluster.category_type
                })
        
        # Add unclustered keywords with extracted parent topics
        for keyword in clustering_result.unclustered:
            parent_topic = clustering._extract_parent_topic_from_keyword(keyword)
            keywords_with_topics.append({
                "keyword": keyword,
                "parent_topic": parent_topic,
                "cluster_score": 0.5,
                "category_type": clustering._classify_keyword_type(keyword)
            })
        
        return {
            "extracted_keywords": keywords,
            "keywords_with_topics": keywords_with_topics,
            "clusters": [
                {
                    "parent_topic": c.parent_topic,
                    "keywords": c.keywords,
                    "cluster_score": c.cluster_score,
                    "category_type": c.category_type,
                    "keyword_count": len(c.keywords)
                }
                for c in clustering_result.clusters
            ],
            "cluster_summary": {
                "total_keywords": clustering_result.total_keywords,
                "cluster_count": clustering_result.cluster_count,
                "unclustered_count": len(clustering_result.unclustered)
            }
        }
        
    except Exception as e:
        logger.error(f"Keyword extraction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Keyword extraction failed: {str(e)}"
        )


# Keyword suggestions endpoint
@app.post("/api/v1/keywords/suggest")
async def suggest_keywords(
    request: KeywordSuggestionRequest,
    writer: BlogWriter = Depends(get_blog_writer)
):
    """
    Get keyword variations and suggestions.
    
    Provides:
    - Related keywords
    - Long-tail variations
    - Question-based keywords
    - Semantic variations
    """
    try:
        suggestions = await writer.keyword_analyzer.suggest_keyword_variations(request.keyword)
        
        return {"keyword_suggestions": suggestions}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Keyword suggestion failed: {str(e)}"
        )


# Content optimization endpoint
@app.post("/api/v1/optimize")
async def optimize_content(
    request: ContentOptimizationRequest,
    writer: BlogWriter = Depends(get_blog_writer)
):
    """
    Optimize existing content for better SEO.
    
    Improvements include:
    - Keyword distribution optimization
    - Heading structure enhancement
    - Internal linking suggestions
    - Meta tag generation
    """
    try:
        # Optimize keyword distribution
        optimized_content = await writer.seo_optimizer.optimize_keyword_distribution(
            content=request.content,
            keywords=request.keywords,
            focus_keyword=request.focus_keyword
        )
        
        # Optimize heading structure
        optimized_content = await writer.seo_optimizer.optimize_heading_structure(
            optimized_content
        )
        
        # Add internal linking suggestions
        optimized_content = await writer.seo_optimizer.add_internal_linking_suggestions(
            optimized_content
        )
        
        return {
            "optimized_content": optimized_content,
            "original_length": len(request.content.split()),
            "optimized_length": len(optimized_content.split()),
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content optimization failed: {str(e)}"
        )


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=f"HTTP {exc.status_code}",
            message=exc.detail,
            timestamp=time.time()
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            message="An unexpected error occurred",
            timestamp=time.time()
        ).dict()
    )


# Background tasks
async def log_generation(topic: str, success: bool, word_count: int, generation_time: float):
    """Log blog generation for analytics."""
    # Use structured cloud logging
    log_blog_generation(
        topic=topic,
        success=success,
        word_count=word_count,
        generation_time=generation_time,
        seo_optimization_enabled=blog_writer.enable_seo_optimization if blog_writer else False,
        ai_enhancement_enabled=blog_writer.enable_ai_enhancement if blog_writer else False
    )


# Configuration endpoint (for debugging)
@app.get("/api/v1/config")
async def get_config():
    """Get current API configuration."""
    config = {
        "seo_optimization_enabled": blog_writer.enable_seo_optimization,
        "quality_analysis_enabled": blog_writer.enable_quality_analysis,
        "enhanced_keyword_analysis_enabled": isinstance(blog_writer.keyword_analyzer, EnhancedKeywordAnalyzer),
        "ai_enhancement_enabled": blog_writer.enable_ai_enhancement,
        "default_tone": blog_writer.default_tone.value,
        "default_length": blog_writer.default_length.value,
        "supported_tones": [tone.value for tone in ContentTone],
        "supported_lengths": [length.value for length in ContentLength],
        "supported_formats": [format.value for format in ContentFormat],
    }
    
    # Add AI provider information if available
    if blog_writer.ai_generator:
        try:
            provider_status = blog_writer.ai_generator.provider_manager.get_provider_status()
            config["ai_providers"] = provider_status
            config["ai_generation_stats"] = blog_writer.ai_generator.get_generation_stats()
        except Exception as e:
            config["ai_providers_error"] = str(e)
    
    # LiteLLM router removed
    config["litellm_router"] = {"enabled": False, "message": "LiteLLM removed from project"}
    
    return config


# AI health check endpoint
@app.get("/api/v1/ai/health")
async def ai_health_check():
    """Check the health of AI providers."""
    if not blog_writer.ai_generator:
        return {
            "ai_enabled": False,
            "message": "AI content generation is not enabled"
        }
    
    try:
        health_results = await blog_writer.ai_generator.get_provider_health()
        return {
            "ai_enabled": True,
            "providers": health_results,
            "generation_stats": blog_writer.ai_generator.get_generation_stats()
        }
    except Exception as e:
        return {
            "ai_enabled": True,
            "error": str(e),
            "message": "Failed to check AI provider health"
        }


# Blog Writer Abstraction Layer endpoints
class AbstractionBlogGenerationRequest(BaseModel):
    """Request model for abstraction layer blog generation."""
    topic: str = Field(..., min_length=3, max_length=200, description="Main topic for the blog post")
    keywords: List[str] = Field(default_factory=list, max_items=20, description="Target SEO keywords")
    target_audience: Optional[str] = Field(None, max_length=200, description="Target audience description")
    content_strategy: ContentStrategy = Field(default=ContentStrategy.SEO_OPTIMIZED, description="Content generation strategy")
    tone: ContentTone = Field(default=ContentTone.PROFESSIONAL, description="Writing tone")
    length: ContentLength = Field(default=ContentLength.MEDIUM, description="Target content length")
    format: ContentFormat = Field(default=ContentFormat.HTML, description="Output format")
    quality_target: ContentQuality = Field(default=ContentQuality.GOOD, description="Target content quality")
    preferred_provider: Optional[str] = Field(None, description="Preferred AI provider")
    additional_context: Optional[Dict[str, Any]] = Field(None, description="Additional context for generation")
    seo_requirements: Optional[Dict[str, Any]] = Field(None, description="SEO-specific requirements")


class AbstractionBlogGenerationResult(BaseModel):
    """Response model for abstraction layer blog generation."""
    title: str = Field(..., description="Generated blog title")
    content: str = Field(..., description="Generated blog content")
    meta_description: str = Field(..., description="SEO meta description")
    introduction: str = Field(..., description="Blog introduction")
    conclusion: str = Field(..., description="Blog conclusion")
    faq_section: Optional[str] = Field(None, description="FAQ section if generated")
    seo_score: Optional[float] = Field(None, description="SEO optimization score")
    readability_score: Optional[float] = Field(None, description="Content readability score")
    quality_score: Optional[float] = Field(None, description="Overall content quality score")
    provider_used: str = Field(..., description="AI provider used for generation")
    generation_time: Optional[float] = Field(None, description="Time taken for generation")
    cost: Optional[float] = Field(None, description="Cost of generation")
    tokens_used: Optional[int] = Field(None, description="Tokens used for generation")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


# Global abstraction layer instance
abstraction_writer: Optional[BlogWriterAbstraction] = None


def get_abstraction_writer() -> BlogWriterAbstraction:
    """Get or create the abstraction layer blog writer."""
    global abstraction_writer
    if abstraction_writer is None:
        # Create abstraction writer with default configuration
        abstraction_writer = BlogWriterFactory.create_seo_focused_writer()
    return abstraction_writer


@app.post("/api/v1/abstraction/blog/generate", response_model=AbstractionBlogGenerationResult)
async def generate_blog_with_abstraction(
    request: AbstractionBlogGenerationRequest,
    background_tasks: BackgroundTasks,
    writer: BlogWriterAbstraction = Depends(get_abstraction_writer)
):
    """
    Generate a blog post using the new abstraction layer.
    
    This endpoint provides advanced blog generation with:
    - Multiple content strategies (SEO, Engagement, Conversion)
    - Quality assurance and optimization
    - Provider management and fallback
    - Comprehensive analytics and monitoring
    """
    try:
        # Convert API request to abstraction layer request
        abstraction_request = AbstractionBlogRequest(
            topic=request.topic,
            keywords=request.keywords,
            target_audience=request.target_audience,
            content_strategy=request.content_strategy,
            tone=request.tone,
            length=request.length,
            format=request.format,
            quality_target=request.quality_target,
            preferred_provider=request.preferred_provider,
            additional_context=request.additional_context,
            seo_requirements=request.seo_requirements
        )
        
        # Generate blog using abstraction layer
        result = await writer.generate_blog(abstraction_request)
        
        # Convert result to API response
        return AbstractionBlogGenerationResult(
            title=result.title,
            content=result.content,
            meta_description=result.meta_description,
            introduction=result.introduction,
            conclusion=result.conclusion,
            faq_section=result.faq_section,
            seo_score=result.seo_score,
            readability_score=result.readability_score,
            quality_score=result.quality_score,
            provider_used=result.provider_used,
            generation_time=result.generation_time,
            cost=result.cost,
            tokens_used=result.tokens_used,
            metadata=result.metadata
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Blog generation failed: {str(e)}"
        )


@app.get("/api/v1/abstraction/strategies")
async def get_content_strategies():
    """Get available content generation strategies."""
    return {
        "strategies": [
            {
                "name": strategy.value,
                "description": f"Content strategy focused on {strategy.value.replace('_', ' ')}"
            }
            for strategy in ContentStrategy
        ]
    }


# Unified Blog Generation Endpoint (Routes to specific handlers)
@app.post("/api/v1/blog/generate-unified")
async def generate_blog_unified(
    request: UnifiedBlogRequest,
    background_tasks: BackgroundTasks,
    writer: BlogWriter = Depends(get_blog_writer)
):
    """
    Unified blog generation endpoint that routes to specific handlers based on blog_type.
    
    This endpoint provides a single interface for all blog generation types:
    - standard: Basic blog posts with SEO optimization
    - enhanced: High-quality multi-stage blog generation with research and citations
    - local_business: Comprehensive blogs about local businesses with reviews
    - abstraction: Strategy-based blog generation (SEO, Engagement, Conversion)
    
    The endpoint routes internally to the appropriate handler while maintaining
    backward compatibility with existing endpoints.
    
    **Benefits:**
    - Single endpoint for all blog types
    - Consistent API design
    - Type-safe with conditional fields
    - Easier frontend integration
    
    **Example Request:**
    ```json
    {
      "blog_type": "local_business",
      "topic": "best plumbers in Miami",
      "location": "Miami, FL",
      "max_businesses": 10,
      "tone": "professional",
      "length": "long"
    }
    ```
    """
    try:
        # Route to appropriate handler based on blog_type
        if request.blog_type == BlogType.STANDARD:
            # Convert to BlogGenerationRequest
            standard_request = BlogGenerationRequest(
                topic=request.topic,
                keywords=request.keywords,
                tone=request.tone,
                length=request.length,
                format=request.format,
                target_audience=request.target_audience,
                focus_keyword=request.focus_keyword,
                include_introduction=request.include_introduction,
                include_conclusion=request.include_conclusion,
                include_faq=request.include_faq,
                include_toc=request.include_toc,
                word_count_target=request.word_count_target,
                custom_instructions=request.custom_instructions,
            )
            return await generate_blog(standard_request, background_tasks, writer)
        
        elif request.blog_type == BlogType.ENHANCED:
            # Convert to EnhancedBlogGenerationRequest
            enhanced_request = EnhancedBlogGenerationRequest(
                topic=request.topic,
                keywords=request.keywords if request.keywords else [request.topic],
                tone=request.tone,
                length=request.length,
                use_google_search=request.use_google_search,
                use_fact_checking=request.use_fact_checking,
                use_citations=request.use_citations,
                use_serp_optimization=request.use_serp_optimization,
                use_consensus_generation=request.use_consensus_generation,
                use_knowledge_graph=request.use_knowledge_graph,
                use_semantic_keywords=request.use_semantic_keywords,
                use_quality_scoring=request.use_quality_scoring,
                target_audience=request.target_audience,
                custom_instructions=request.custom_instructions,
                template_type=request.template_type,
            )
            return await generate_blog_enhanced(
                enhanced_request,
                background_tasks,
                async_mode=request.async_mode
            )
        
        elif request.blog_type == BlogType.LOCAL_BUSINESS:
            # Validate required fields
            if not request.location:
                raise HTTPException(
                    status_code=400,
                    detail="'location' is required for local_business blog type"
                )
            
            # Convert to LocalBusinessBlogRequest
            local_business_request = LocalBusinessBlogRequest(
                topic=request.topic,
                location=request.location,
                max_businesses=request.max_businesses,
                max_reviews_per_business=request.max_reviews_per_business,
                tone=request.tone,
                length=request.length,
                format=request.format,
                include_business_details=request.include_business_details,
                include_review_sentiment=request.include_review_sentiment,
                use_google=request.use_google,
                custom_instructions=request.custom_instructions,
            )
            return await generate_local_business_blog(
                local_business_request,
                background_tasks,
                writer
            )
        
        elif request.blog_type == BlogType.ABSTRACTION:
            # Convert to AbstractionBlogGenerationRequest
            # Parse content_strategy string to enum if provided
            content_strategy_enum = ContentStrategy.SEO_OPTIMIZED
            if request.content_strategy:
                try:
                    content_strategy_enum = ContentStrategy(request.content_strategy)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid content_strategy: {request.content_strategy}, using default")
            
            # Parse quality_target string to enum if provided
            quality_target_enum = ContentQuality.GOOD
            if request.quality_target:
                try:
                    quality_target_enum = ContentQuality(request.quality_target)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid quality_target: {request.quality_target}, using default")
            
            abstraction_request = AbstractionBlogGenerationRequest(
                topic=request.topic,
                keywords=request.keywords if request.keywords else [request.topic],
                target_audience=request.target_audience,
                content_strategy=content_strategy_enum,
                tone=request.tone,
                length=request.length,
                format=request.format,
                quality_target=quality_target_enum,
                preferred_provider=request.preferred_provider,
                additional_context={"custom_instructions": request.custom_instructions} if request.custom_instructions else None,
                seo_requirements=request.seo_requirements,
            )
            abstraction_writer = get_abstraction_writer()
            return await generate_blog_with_abstraction(
                abstraction_request,
                background_tasks,
                abstraction_writer
            )
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported blog_type: {request.blog_type}. Supported types: standard, enhanced, local_business, abstraction"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unified blog generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Blog generation failed: {str(e)}"
        )


# Local Business Blog Generation Endpoint
@app.post("/api/v1/blog/generate-local-business", response_model=LocalBusinessBlogResponse)
async def generate_local_business_blog(
    request: LocalBusinessBlogRequest,
    background_tasks: BackgroundTasks,
    writer: BlogWriter = Depends(get_blog_writer)
):
    """
    Generate a comprehensive blog post about local businesses.
    
    This endpoint:
    1. Uses SERP analysis to find top businesses in the specified location
    2. Fetches reviews from Google Places
    3. Aggregates review data and business information
    4. Generates comprehensive blog content using AI pipeline
    
    Features:
    - Business discovery from SERP results
    - Google Places review aggregation
    - Business details extraction (hours, contact, services)
    - Review sentiment analysis
    - SEO-optimized content generation
    """
    import time
    start_time = time.time()
    
    try:
        # Initialize review aggregation service
        google_client = GoogleReviewsClient()
        review_service = ReviewAggregationService(
            google_client=google_client if request.use_google else None
        )
        
        # Step 1: Use SERP analysis to find businesses
        logger.info(f"Finding businesses for topic: {request.topic} in {request.location}")
        
        # Get SERP analysis using DataForSEO
        businesses_found = []
        serp_businesses = []
        
        if dataforseo_client_global and dataforseo_client_global.is_configured:
            try:
                tenant_id = os.getenv("TENANT_ID", "default")
                serp_data = await dataforseo_client_global.get_serp_analysis(
                    keyword=request.topic,
                    location_name=request.location,
                    language_code="en",
                    tenant_id=tenant_id,
                    depth=20
                )
                
                # Extract businesses from organic results
                organic_results = serp_data.get("organic_results", [])
                for result in organic_results[:request.max_businesses]:
                    # Try to extract business name and URL
                    title = result.get("title", "")
                    url = result.get("url", "")
                    domain = result.get("domain", "")
                    
                    # Check if this looks like a business listing (Google Maps, etc.)
                    if "google.com/maps" in domain.lower() or "maps.google.com" in domain.lower():
                        # Extract Google Place ID if possible
                        place_id = None
                        if "place_id=" in url:
                            place_id = url.split("place_id=")[1].split("&")[0]
                        
                        serp_businesses.append({
                            "name": title,
                            "google_place_id": place_id,
                            "url": url,
                            "source": "serp_google"
                        })
                    else:
                        # Generic business from SERP
                        serp_businesses.append({
                            "name": title,
                            "url": url,
                            "source": "serp_organic"
                        })
                
                logger.info(f"Found {len(serp_businesses)} businesses from SERP analysis")
            
            except Exception as e:
                logger.warning(f"SERP analysis failed: {e}, falling back to direct search")
        
        # Step 2: Search for businesses using Google Places if SERP didn't find enough
        if len(serp_businesses) < request.max_businesses:
            # Search Google Places
            if request.use_google and google_client.is_configured:
                try:
                    google_results = await google_client.search_businesses(
                        query=request.topic,
                        location=request.location,
                        limit=request.max_businesses
                    )
                    
                    for place in google_results.get("places", []):
                        place_id = place.get("place_id")
                        # Avoid duplicates
                        if not any(b.get("google_place_id") == place_id for b in serp_businesses):
                            serp_businesses.append({
                                "name": place.get("name", ""),
                                "google_place_id": place_id,
                                "address": place.get("formatted_address"),
                                "rating": place.get("rating"),
                                "review_count": place.get("user_ratings_total", 0),
                                "source": "google_search"
                            })
                except Exception as e:
                    logger.warning(f"Google Places search failed: {e}")
        
        # Limit to max_businesses
        serp_businesses = serp_businesses[:request.max_businesses]
        
        if not serp_businesses:
            raise HTTPException(
                status_code=404,
                detail=f"No businesses found for '{request.topic}' in {request.location}"
            )
        
        # Step 3: Aggregate reviews for each business
        logger.info(f"Aggregating reviews for {len(serp_businesses)} businesses")
        
        review_summaries = await review_service.aggregate_multiple_businesses(
            businesses=serp_businesses,
            max_reviews_per_business=request.max_reviews_per_business
        )
        
        # Step 4: Build business info list
        businesses_info = []
        total_reviews = 0
        
        for i, business_data in enumerate(serp_businesses):
            review_summary = review_summaries[i] if i < len(review_summaries) else None
            
            business_info = BusinessInfo(
                name=business_data.get("name", "Unknown Business"),
                google_place_id=business_data.get("google_place_id"),
                address=business_data.get("address"),
                phone=business_data.get("phone"),
                website=business_data.get("url"),
                rating=business_data.get("rating") or (review_summary.average_rating if review_summary else None),
                review_count=business_data.get("review_count") or (review_summary.total_reviews if review_summary else 0),
                categories=business_data.get("categories", [])
            )
            
            businesses_info.append(business_info)
            if review_summary:
                total_reviews += review_summary.total_reviews
        
        # Step 5: Generate blog content using AI pipeline
        logger.info("Generating blog content with AI")
        
        # Build context from reviews and business data
        review_context = []
        for i, review_summary in enumerate(review_summaries):
            if review_summary and review_summary.reviews:
                top_reviews = review_service.get_top_reviews(review_summary, limit=5, min_rating=3.0)
                business_name = businesses_info[i].name
                
                review_texts = "\n".join([
                    f"- {r.text[:200]}... (Rating: {r.rating}/5)" 
                    for r in top_reviews[:3]
                ])
                
                review_context.append(f"""
Business: {business_name}
Rating: {review_summary.average_rating:.1f}/5 ({review_summary.total_reviews} reviews)
Top Reviews:
{review_texts}
""")
        
        # Create blog request
        blog_request = BlogRequest(
            topic=f"{request.topic}: Comprehensive Guide to Top Businesses",
            keywords=[request.topic, f"{request.topic.split(' in ')[0]} in {request.location}"],
            tone=request.tone,
            length=request.length,
            format=request.format,
            custom_instructions=f"""
Generate a comprehensive blog post about {request.topic} in {request.location}.

Include detailed information about each business:
{chr(10).join(review_context)}

Focus on:
- Business quality and reputation based on reviews
- Services offered and specialties
- Customer experiences and testimonials
- Location and contact information
- What makes each business stand out

Make the content engaging, informative, and SEO-optimized.
{request.custom_instructions if request.custom_instructions else ''}
"""
        )
        
        # Generate blog
        blog_result = await writer.generate(blog_request)
        
        if not blog_result.success:
            raise HTTPException(
                status_code=500,
                detail=f"Blog generation failed: {blog_result.error_message}"
            )
        
        generation_time = time.time() - start_time
        
        # Build response
        response = LocalBusinessBlogResponse(
            title=blog_result.blog_post.title,
            content=blog_result.blog_post.content,
            businesses=businesses_info,
            total_reviews_aggregated=total_reviews,
            generation_time_seconds=generation_time,
            metadata={
                "sources_used": list(set([b.get("source", "unknown") for b in serp_businesses])),
                "review_sources": [s.value for s in review_summaries[0].sources] if review_summaries and review_summaries[0].sources else [],
                "seo_score": blog_result.seo_score,
                "word_count": blog_result.word_count,
            }
        )
        
        # Log generation
        background_tasks.add_task(
            log_generation,
            topic=request.topic,
            success=True,
            word_count=blog_result.word_count,
            generation_time=generation_time
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Local business blog generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Local business blog generation failed: {str(e)}"
        )


@app.get("/api/v1/abstraction/quality-levels")
async def get_quality_levels():
    """Get available content quality levels."""
    return {
        "quality_levels": [
            {
                "name": quality.value,
                "description": f"Content quality level: {quality.value.replace('_', ' ')}"
            }
            for quality in ContentQuality
        ]
    }


@app.get("/api/v1/abstraction/presets")
async def get_blog_writer_presets():
    """Get available blog writer presets."""
    return {
        "presets": [
            {
                "name": preset.value,
                "description": f"Blog writer preset: {preset.value.replace('_', ' ')}"
            }
            for preset in BlogWriterPreset
        ]
    }


@app.get("/api/v1/abstraction/status")
async def get_abstraction_status(writer: BlogWriterAbstraction = Depends(get_abstraction_writer)):
    """Get abstraction layer status and statistics."""
    try:
        provider_status = await writer.get_ai_provider_status()
        generation_stats = writer.get_generation_statistics()
        
        return {
            "status": "operational",
            "provider_status": provider_status,
            "generation_statistics": generation_stats,
            "features": {
                "content_strategies": len(ContentStrategy),
                "quality_levels": len(ContentQuality),
                "presets": len(BlogWriterPreset),
                "optimization_strategies": True,
                "quality_assurance": True,
                "batch_generation": True,
                "provider_fallback": True
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to get abstraction layer status"
        }


# LiteLLM endpoints removed - using direct AI provider integrations

class BatchGenerationRequest(BaseModel):
    """Request model for batch blog generation."""
    requests: List[BlogGenerationRequest] = Field(..., min_length=1, max_length=100, description="List of blog generation requests")
    job_id: Optional[str] = Field(None, description="Optional custom job ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional job metadata")


# ===== NEW V1.0 ENDPOINTS =====

# Batch Processing Endpoints
@app.post("/api/v1/batch/generate")
async def create_batch_generation(request: BatchGenerationRequest):
    """Create a batch blog generation job."""
    if not batch_processor:
        raise HTTPException(status_code=503, detail="Batch processor not available")
    
    try:
        # Convert requests to BlogRequest objects
        blog_requests = []
        for req in request.requests:
            blog_request = BlogRequest(
                topic=req.topic,
                keywords=req.keywords,
                tone=req.tone,
                length=req.length,
                format=req.format,
                target_audience=req.target_audience,
                focus_keyword=req.focus_keyword,
                include_introduction=req.include_introduction,
                include_conclusion=req.include_conclusion,
                include_faq=req.include_faq,
                include_toc=req.include_toc,
                word_count_target=req.word_count_target,
                custom_instructions=req.custom_instructions
            )
            blog_requests.append(blog_request)
        
        # Create batch job
        job = batch_processor.create_batch_job(
            requests=blog_requests,
            job_id=request.job_id,
            metadata=request.metadata
        )
        
        # Start processing in background
        asyncio.create_task(batch_processor.process_batch(job.id))
        
        return {
            "success": True,
            "job_id": job.id,
            "total_items": job.total_items,
            "status": job.status.value,
            "message": f"Batch job created with {job.total_items} items"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create batch job: {str(e)}")


@app.get("/api/v1/batch/{job_id}/status")
async def get_batch_status(job_id: str):
    """Get status of a batch job."""
    if not batch_processor:
        raise HTTPException(status_code=503, detail="Batch processor not available")
    
    status = batch_processor.get_batch_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Batch job not found")
    
    return status


@app.get("/api/v1/batch/{job_id}/stream")
async def stream_batch_results(job_id: str):
    """Stream batch results as they complete."""
    if not batch_processor:
        raise HTTPException(status_code=503, detail="Batch processor not available")
    
    async def generate_stream():
        try:
            async for item in batch_processor.process_batch_stream(job_id):
                yield f"data: {item.to_dict()}\n\n"
        except Exception as e:
            yield f"data: {{'error': '{str(e)}'}}\n\n"
    
    return StreamingResponse(generate_stream(), media_type="text/plain")


@app.get("/api/v1/batch")
async def list_batch_jobs():
    """List all batch jobs."""
    if not batch_processor:
        raise HTTPException(status_code=503, detail="Batch processor not available")
    
    return {
        "jobs": batch_processor.list_batch_jobs(),
        "statistics": batch_processor.get_batch_statistics()
    }


@app.delete("/api/v1/batch/{job_id}")
async def delete_batch_job(job_id: str):
    """Delete a batch job."""
    if not batch_processor:
        raise HTTPException(status_code=503, detail="Batch processor not available")
    
    success = batch_processor.delete_batch_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Batch job not found")
    
    return {"success": True, "message": "Batch job deleted"}


# Monitoring and Metrics Endpoints
@app.get("/api/v1/metrics")
async def get_metrics():
    """Get comprehensive system metrics."""
    metrics_collector = get_metrics_collector()
    if not metrics_collector:
        raise HTTPException(status_code=503, detail="Metrics collector not available")
    
    return metrics_collector.get_metrics_summary()


@app.get("/api/v1/health/detailed")
async def get_detailed_health():
    """Get detailed health status with system metrics."""
    metrics_collector = get_metrics_collector()
    if not metrics_collector:
        return {"status": "unknown", "message": "Metrics collector not available"}
    
    return metrics_collector.get_health_status()


@app.get("/api/v1/cache/stats")
async def get_cache_stats():
    """Get cache statistics."""
    cache_manager = get_cache_manager()
    if not cache_manager:
        return {"status": "unavailable", "message": "Cache manager not initialized"}
    
    return await cache_manager.get_stats()


@app.delete("/api/v1/cache/clear")
async def clear_cache(pattern: Optional[str] = None):
    """Clear cache entries."""
    cache_manager = get_cache_manager()
    if not cache_manager:
        raise HTTPException(status_code=503, detail="Cache manager not available")
    
    if pattern:
        count = await cache_manager.clear_pattern(pattern)
        return {"success": True, "cleared_items": count, "pattern": pattern}
    else:
        # Clear all cache
        count = await cache_manager.clear_pattern("blogwriter:*")
        return {"success": True, "cleared_items": count, "message": "All cache cleared"}


# Cloud Run specific monitoring endpoint
@app.get("/api/v1/cloudrun/status")
async def cloudrun_status():
    """
    Cloud Run specific status endpoint.
    
    Provides detailed information about the Cloud Run instance including:
    - Container metadata
    - Resource usage
    - Environment information
    - Service configuration
    """
    import psutil
    
    try:
        # Get system information
        memory_info = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        disk_usage = psutil.disk_usage('/')
        
        # Get Cloud Run specific environment variables
        cloud_run_env = {
            "service": os.getenv("K_SERVICE", "unknown"),
            "revision": os.getenv("K_REVISION", "unknown"),
            "configuration": os.getenv("K_CONFIGURATION", "unknown"),
            "port": os.getenv("PORT", "8000"),
            "project_id": os.getenv("GOOGLE_CLOUD_PROJECT", "unknown"),
            "region": os.getenv("GOOGLE_CLOUD_REGION", "unknown")
        }
        
        # Get application status
        app_status = {
            "uptime_seconds": time.time() - startup_time,
            "version": f"{APP_VERSION}-cloudrun",
            "python_version": os.sys.version,
            "environment": "production" if not os.getenv("DEBUG", "false").lower() == "true" else "development"
        }
        
        # Get service capabilities
        capabilities = {
            "ai_enhancement": blog_writer.enable_ai_enhancement if blog_writer else False,
            "seo_optimization": blog_writer.enable_seo_optimization if blog_writer else False,
            "quality_analysis": blog_writer.enable_quality_analysis if blog_writer else False,
            "enhanced_keyword_analysis": isinstance(blog_writer.keyword_analyzer, EnhancedKeywordAnalyzer) if blog_writer else False,
            "batch_processing": batch_processor is not None,
            "caching": get_cache_manager() is not None,
            "metrics": get_metrics_collector() is not None
        }
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "cloud_run": cloud_run_env,
            "application": app_status,
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total_gb": round(memory_info.total / (1024**3), 2),
                    "available_gb": round(memory_info.available / (1024**3), 2),
                    "used_percent": memory_info.percent
                },
                "disk": {
                    "total_gb": round(disk_usage.total / (1024**3), 2),
                    "free_gb": round(disk_usage.free / (1024**3), 2),
                    "used_percent": round((disk_usage.used / disk_usage.total) * 100, 1)
                }
            },
            "capabilities": capabilities
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }
        )


# Platform Publishing Endpoints

@app.post("/api/v1/publish/webflow")
async def publish_to_webflow(request: PlatformPublishRequest):
    """Publish blog content to Webflow."""
    try:
        # Initialize Webflow client
        webflow_client = WebflowClient()
        webflow_publisher = WebflowPublisher(webflow_client)
        
        # Prepare media files if provided
        media_files = []
        if request.media_files:
            for media_file in request.media_files:
                # Decode base64 media data
                media_data = base64.b64decode(media_file["data"])
                media_files.append({
                    "data": media_data,
                    "filename": media_file["filename"],
                    "alt_text": media_file.get("alt_text")
                })
        
        # Publish with media
        result = await webflow_publisher.publish_with_media(
            blog_result=request.blog_result,
            media_files=media_files,
            publish=request.publish
        )
        
        return {
            "success": True,
            "platform": "webflow",
            "result": result,
            "message": "Successfully published to Webflow"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish to Webflow: {str(e)}")


@app.post("/api/v1/publish/shopify")
async def publish_to_shopify(request: PlatformPublishRequest):
    """Publish blog content to Shopify with product recommendations."""
    try:
        # Initialize Shopify client
        shopify_client = ShopifyClient()
        shopify_publisher = ShopifyPublisher(shopify_client)
        
        # Publish with product recommendations
        result = await shopify_publisher.publish_with_recommendations(
            blog_result=request.blog_result,
            categories=request.categories,
            publish=request.publish,
            include_products=True
        )
        
        return {
            "success": True,
            "platform": "shopify",
            "result": result,
            "message": "Successfully published to Shopify with product recommendations"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish to Shopify: {str(e)}")


@app.post("/api/v1/publish/wordpress")
async def publish_to_wordpress(request: PlatformPublishRequest):
    """Publish blog content to WordPress."""
    try:
        if not WORDPRESS_AVAILABLE:
            raise HTTPException(status_code=501, detail="WordPress integration is not available in this deployment")
        # Initialize WordPress client
        wordpress_client = WordPressClient()
        wordpress_publisher = WordPressPublisher(wordpress_client)
        
        # Prepare media files if provided
        media_files = []
        if request.media_files:
            for media_file in request.media_files:
                # Decode base64 media data
                media_data = base64.b64decode(media_file["data"])
                media_files.append({
                    "data": media_data,
                    "filename": media_file["filename"],
                    "alt_text": media_file.get("alt_text"),
                    "caption": media_file.get("caption")
                })
        
        # Publish with media
        result = await wordpress_publisher.publish_with_media(
            blog_result=request.blog_result,
            media_files=media_files,
            categories=request.categories,
            publish=request.publish
        )
        
        return {
            "success": True,
            "platform": "wordpress",
            "result": result,
            "message": "Successfully published to WordPress"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish to WordPress: {str(e)}")


# Media Storage Endpoints

@app.post("/api/v1/media/upload/cloudinary")
async def upload_to_cloudinary(request: MediaUploadRequest):
    """Upload media to Cloudinary."""
    try:
        # Initialize Cloudinary storage
        cloudinary_storage = CloudinaryStorage()
        
        # Decode base64 media data
        media_data = base64.b64decode(request.media_data)
        
        # Upload media
        result = await cloudinary_storage.upload_media(
            media_data=media_data,
            filename=request.filename,
            folder=request.folder,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "provider": "cloudinary",
            "result": result,
            "message": "Successfully uploaded to Cloudinary"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to Cloudinary: {str(e)}")


@app.post("/api/v1/media/upload/cloudflare")
async def upload_to_cloudflare(request: MediaUploadRequest):
    """Upload media to Cloudflare R2."""
    try:
        # Initialize Cloudflare R2 storage
        cloudflare_storage = CloudflareR2Storage()
        
        # Decode base64 media data
        media_data = base64.b64decode(request.media_data)
        
        # Upload media
        result = await cloudflare_storage.upload_media(
            media_data=media_data,
            filename=request.filename,
            folder=request.folder,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "provider": "cloudflare-r2",
            "result": result,
            "message": "Successfully uploaded to Cloudflare R2"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to Cloudflare R2: {str(e)}")


@app.get("/api/v1/platforms/webflow/collections")
async def get_webflow_collections():
    """Get available Webflow collections."""
    try:
        webflow_client = WebflowClient()
        collections = await webflow_client.get_collections()
        
        return {
            "success": True,
            "platform": "webflow",
            "collections": collections
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Webflow collections: {str(e)}")


@app.get("/api/v1/platforms/shopify/blogs")
async def get_shopify_blogs():
    """Get available Shopify blogs."""
    try:
        shopify_client = ShopifyClient()
        blogs = await shopify_client.get_blogs()
        
        return {
            "success": True,
            "platform": "shopify",
            "blogs": blogs
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Shopify blogs: {str(e)}")


@app.get("/api/v1/platforms/wordpress/categories")
async def get_wordpress_categories():
    """Get available WordPress categories."""
    try:
        if not WORDPRESS_AVAILABLE:
            raise HTTPException(status_code=501, detail="WordPress integration is not available in this deployment")
        wordpress_client = WordPressClient()
        categories = await wordpress_client.get_categories()
        
        return {
            "success": True,
            "platform": "wordpress",
            "categories": categories
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get WordPress categories: {str(e)}")


# Credential Management Endpoints
# Credential endpoints not implemented yet - DataForSEOCredentials class not available
# @app.post("/api/v1/tenants/{tenant_id}/credentials/dataforseo", response_model=Dict[str, str], tags=["Credential Management"])
# async def create_or_update_dataforseo_credentials(tenant_id: str, credentials: DataForSEOCredentials):
#     if not dataforseo_credential_service:
#         raise HTTPException(status_code=500, detail="DataforSEO Credential Service not initialized.")
#     
#     success = await dataforseo_credential_service.store_credentials(
#         tenant_id, "dataforseo", credentials.model_dump()
#     )
#     if success:
#         return {"message": "DataforSEO credentials stored successfully."}
#     raise HTTPException(status_code=500, detail="Failed to store DataforSEO credentials.")

# @app.get("/api/v1/tenants/{tenant_id}/credentials/dataforseo/status", response_model=TenantCredentialStatus, tags=["Credential Management"])
# async def get_dataforseo_credentials_status(tenant_id: str):
#     if not dataforseo_credential_service:
#         raise HTTPException(status_code=500, detail="DataforSEO Credential Service not initialized.")
#     
#     # Retrieve status from the database
#     result = supabase_client.table("tenant_credentials").select(
#         "provider", "is_active", "test_status"
#     ).eq("tenant_id", tenant_id).eq("provider", "dataforseo").single().execute()
#
#     if not result.data:
#         raise HTTPException(status_code=404, detail="DataforSEO credentials not found for this tenant.")
#     
#     return TenantCredentialStatus(
#         provider=result.data["provider"],
#         is_active=result.data["is_active"],
#         test_status=result.data["test_status"]
#     )

# @app.post("/api/v1/tenants/{tenant_id}/credentials/dataforseo/test", response_model=Dict[str, str], tags=["Credential Management"])
# async def test_dataforseo_credentials(tenant_id: str):
#     if not dataforseo_credential_service:
#         raise HTTPException(status_code=500, detail="DataforSEO Credential Service not initialized.")
#     
#     test_result = await dataforseo_credential_service.test_credentials(tenant_id, "dataforseo")
#     if test_result["status"] == "success":
#         return {"message": test_result["message"]}
#     raise HTTPException(status_code=500, detail=test_result["error"])

# @app.delete("/api/v1/tenants/{tenant_id}/credentials/dataforseo", response_model=Dict[str, str], tags=["Credential Management"])
# async def delete_dataforseo_credentials(tenant_id: str):
#     if not dataforseo_credential_service:
#         raise HTTPException(status_code=500, detail="DataforSEO Credential Service not initialized.")
#     
#     success = await dataforseo_credential_service.delete_credentials(tenant_id, "dataforseo")
#     if success:
#         return {"message": "DataforSEO credentials deleted successfully."}
#     raise HTTPException(status_code=500, detail="Failed to delete DataforSEO credentials.")


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    print(f"🚀 Starting Blog Writer SDK API on {host}:{port}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )
