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
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

# Track startup time for uptime calculation
startup_time = time.time()

# Deployment trigger - updated timestamp
deployment_version = "2025-11-12-001"
APP_VERSION = os.getenv("APP_VERSION", "1.2.1")

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from src.blog_writer_sdk import BlogWriter
from src.blog_writer_sdk.models.blog_models import (
    BlogRequest,
    BlogGenerationResult,
    ContentTone,
    ContentLength,
    ContentFormat,
)
from src.blog_writer_sdk.seo.enhanced_keyword_analyzer import EnhancedKeywordAnalyzer
from src.blog_writer_sdk.ai.ai_content_generator import AIContentGenerator
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
# Credential services not implemented yet - using direct environment variables
# from src.blog_writer_sdk.services.credential_service import TenantCredentialService
# from src.blog_writer_sdk.services.dataforseo_credential_service import DataForSEOCredentialService
# from src.blog_writer_sdk.models.credential_models import DataForSEOCredentials, TenantCredentialStatus
from src.blog_writer_sdk.integrations.dataforseo_integration import DataForSEOClient, EnhancedKeywordAnalyzer

# Global DataForSEO client for Phase 3 semantic integration
dataforseo_client_global = None
from src.blog_writer_sdk.integrations import (
    WebflowClient, WebflowPublisher,
    ShopifyClient, ShopifyPublisher,
    CloudinaryStorage, CloudflareR2Storage, MediaStorageManager
)
try:
    # Optional: WordPress not installed in this repo currently
    from src.blog_writer_sdk.integrations.wordpress_integration import WordPressClient, WordPressPublisher  # type: ignore
    WORDPRESS_AVAILABLE = True
except Exception:
    WORDPRESS_AVAILABLE = False

from google.cloud import secretmanager
from supabase import create_client, Client
from src.blog_writer_sdk.batch.batch_processor import BatchProcessor
from src.blog_writer_sdk.api.ai_provider_management import router as ai_provider_router, initialize_from_env
from src.blog_writer_sdk.api.image_generation import router as image_generation_router, initialize_image_providers_from_env
from src.blog_writer_sdk.api.integration_management import router as integrations_router
from src.blog_writer_sdk.models.enhanced_blog_models import (
    EnhancedBlogGenerationRequest,
    EnhancedBlogGenerationResponse
)
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
    text: Optional[str] = Field(None, description="Optional text content (ignored if keywords provided)")
    max_suggestions_per_keyword: Optional[int] = Field(None, description="Optional: if provided, routes to enhanced analysis")
    
    class Config:
        extra = "ignore"  # Ignore extra fields to be more flexible with frontend requests

class EnhancedKeywordAnalysisRequest(BaseModel):
    """Request model for enhanced keyword analysis with DataForSEO."""
    keywords: List[str] = Field(..., max_length=200, description="Keywords to analyze (up to 200 for comprehensive research)")
    location: Optional[str] = Field("United States", description="Location for keyword analysis")
    language: Optional[str] = Field("en", description="Language code for analysis")
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


# Application lifespan management
def load_env_from_secrets():
    """Load environment variables from mounted secrets file."""
    secrets_file = "/secrets/env"
    if os.path.exists(secrets_file):
        print("📁 Loading environment variables from mounted secrets...")
        with open(secrets_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✅ Environment variables loaded from secrets")
    else:
        print("⚠️ No secrets file found at /secrets/env, using system environment variables")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    # Startup
    print("🚀 Blog Writer SDK API starting up...")
    
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
    supabase_key = os.getenv("SUPABASE_KEY")
    if supabase_url and supabase_key:
        global supabase_client
        supabase_client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client initialized.")
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
    enhanced_keyword_analyzer = EnhancedKeywordAnalyzer(
        use_dataforseo=True, # Assuming we always want to use DataforSEO if available
        credential_service=dataforseo_credential_service
    )
    
    # Initialize DataForSEO client for semantic integration (Phase 3)
    # Note: DataForSEO client will be initialized synchronously when needed
    dataforseo_client_global = None  # Will be initialized on first use if credentials available
    
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
    - **Multi-Provider Support**: OpenAI, Anthropic, Azure OpenAI with automatic fallback
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
    
    # Check for Azure OpenAI configuration
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    if azure_api_key and azure_endpoint:
        ai_config['providers']['azure_openai'] = {
            'api_key': azure_api_key,
            'azure_endpoint': azure_endpoint,
            'api_version': os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            'default_model': os.getenv("AZURE_OPENAI_DEFAULT_MODEL", "gpt-4o-mini"),
            'enabled': True,
            'priority': 2
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
@app.post("/api/v1/blog/generate-enhanced", response_model=EnhancedBlogGenerationResponse)
async def generate_blog_enhanced(
    request: EnhancedBlogGenerationRequest,
    background_tasks: BackgroundTasks
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
    
    Returns significantly higher-quality content optimized for ranking.
    """
    try:
        # Get global clients
        global google_custom_search_client, readability_analyzer, citation_generator, serp_analyzer
        global ai_generator, google_knowledge_graph_client, semantic_integrator, quality_scorer
        global intent_analyzer, few_shot_extractor, length_optimizer
        
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
            use_consensus=request.use_consensus_generation
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
        
        # Generate images if this is a product-related topic
        generated_images = []
        if request.use_google_search:  # Only if Google Search is enabled (indicates research was done)
            try:
                from src.blog_writer_sdk.api.image_generation import image_provider_manager
                from src.blog_writer_sdk.models.image_models import ImageGenerationRequest, ImageStyle, ImageAspectRatio, ImageQuality
                
                # Check if topic suggests product content
                product_indicators = ["best", "top", "review", "compare", "guide"]
                is_product_topic = any(indicator in request.topic.lower() for indicator in product_indicators)
                
                if is_product_topic and image_provider_manager and image_provider_manager.providers:
                    logger.info("Generating images for product blog post")
                    
                    # Generate featured image
                    try:
                        featured_image_request = ImageGenerationRequest(
                            prompt=f"Professional product photography: {request.topic}. High quality, clean background, professional lighting",
                            style=ImageStyle.PHOTOGRAPHIC,
                            aspect_ratio=ImageAspectRatio.SIXTEEN_NINE,
                            quality=ImageQuality.HIGH
                        )
                        featured_image_response = await image_provider_manager.generate_image(featured_image_request)
                        if featured_image_response.success and featured_image_response.images:
                            generated_images.append({
                                "type": "featured",
                                "prompt": featured_image_request.prompt,
                                "image_url": featured_image_response.images[0].get("image_url") or featured_image_response.images[0].get("image_data"),
                                "alt_text": f"Featured image for {request.topic}"
                            })
                            logger.info("Featured image generated successfully")
                    except Exception as e:
                        logger.warning(f"Featured image generation failed: {e}")
                    
                    # Generate section images (if brand recommendations exist)
                    if additional_context.get("brand_recommendations"):
                        brands = additional_context["brand_recommendations"].get("brands", [])[:3]
                        for brand in brands:
                            try:
                                brand_image_request = ImageGenerationRequest(
                                    prompt=f"Professional product image: {brand} {request.keywords[0] if request.keywords else ''}. Clean, professional, product photography style",
                                    style=ImageStyle.PHOTOGRAPHIC,
                                    aspect_ratio=ImageAspectRatio.FOUR_THREE,
                                    quality=ImageQuality.STANDARD
                                )
                                brand_image_response = await image_provider_manager.generate_image(brand_image_request)
                                if brand_image_response.success and brand_image_response.images:
                                    generated_images.append({
                                        "type": "product",
                                        "brand": brand,
                                        "prompt": brand_image_request.prompt,
                                        "image_url": brand_image_response.images[0].get("image_url") or brand_image_response.images[0].get("image_data"),
                                        "alt_text": f"{brand} product image"
                                    })
                            except Exception as e:
                                logger.warning(f"Brand image generation failed for {brand}: {e}")
            except Exception as e:
                logger.warning(f"Image generation integration failed: {e}")
        
        # Add citations if enabled
        citations = []
        final_content = pipeline_result.final_content
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
            seo_metadata=pipeline_result.seo_metadata,
            internal_links=pipeline_result.seo_metadata.get("internal_links", []),
            quality_score=pipeline_result.quality_score,
            quality_dimensions=quality_dimensions,
            structured_data=pipeline_result.structured_data,
            semantic_keywords=semantic_keywords,
            generated_images=generated_images if generated_images else None,
            brand_recommendations=brand_recommendations,
            success=True,
            warnings=[]
        )
        
    except Exception as e:
        logger.error(f"Enhanced blog generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Enhanced blog generation failed: {str(e)}"
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
    request: KeywordAnalysisRequest,
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
        if not request.keywords:
            raise HTTPException(
                status_code=400,
                detail="No keywords provided. Please provide at least one keyword in the 'keywords' array."
            )
        
        # If max_suggestions_per_keyword is provided (even if 0), use enhanced analysis for better results
        if request.max_suggestions_per_keyword is not None:
            # Convert to EnhancedKeywordAnalysisRequest format
            enhanced_request = EnhancedKeywordAnalysisRequest(
                keywords=request.keywords,
                location=request.location,
                language=request.language,
                include_serp=False,
                max_suggestions_per_keyword=max(5, min(request.max_suggestions_per_keyword, 150)) if request.max_suggestions_per_keyword > 0 else 20
            )
            # Route to enhanced endpoint for better results
            return await analyze_keywords_enhanced(enhanced_request)
        
        # Standard analysis - but prefer enhanced if available
        if enhanced_analyzer:
            try:
                results = await enhanced_analyzer.analyze_keywords_comprehensive(
                    keywords=request.keywords,
                    tenant_id=os.getenv("TENANT_ID", "default")
                )
                # Convert to expected format
                keyword_analysis = {}
                for kw, analysis in results.items():
                    # Ensure search_volume and cpc are always numeric (never None)
                    search_volume = analysis.search_volume if analysis.search_volume is not None else 0
                    cpc_value = analysis.cpc if analysis.cpc is not None else 0.0
                    competition_value = analysis.competition if analysis.competition is not None else 0.0
                    
                    keyword_analysis[kw] = {
                        "difficulty": analysis.difficulty.value if hasattr(analysis.difficulty, "value") else str(analysis.difficulty),
                        "search_volume": search_volume,  # Always numeric
                        "competition": competition_value,
                        "cpc": cpc_value,  # Always numeric
                        "recommended": analysis.recommended,
                        "reason": analysis.reason,
                        "related_keywords": analysis.related_keywords[:10],
                        "long_tail_keywords": analysis.long_tail_keywords[:10]
                    }
                return {"keyword_analysis": keyword_analysis}
            except Exception as e:
                logger.warning(f"Enhanced analysis failed, falling back to standard: {e}")
        
        # Fallback to standard analysis
        results = {}
        for keyword in request.keywords:
            analysis = await writer.keyword_analyzer.analyze_keyword(keyword)
            results[keyword] = analysis
        
        return {"keyword_analysis": results}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Keyword analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Keyword analysis failed: {str(e)}"
        )


# Enhanced keyword analysis endpoint using DataForSEO (if configured)
@app.post("/api/v1/keywords/enhanced")
async def analyze_keywords_enhanced(
    request: EnhancedKeywordAnalysisRequest
):
    """
    Enhanced keyword analysis leveraging DataForSEO when available.
    Includes keyword clustering and parent topic extraction.
    Falls back gracefully if credentials are not configured.
    """
    try:
        from src.blog_writer_sdk.seo.keyword_clustering import KeywordClustering
        
        if not enhanced_analyzer:
            raise HTTPException(status_code=503, detail="Enhanced analyzer not available")
        results = await enhanced_analyzer.analyze_keywords_comprehensive(
            keywords=request.keywords,
            tenant_id=os.getenv("TENANT_ID", "default")
        )
        
        # Get additional keyword suggestions using DataForSEO if available
        all_keywords = list(request.keywords)
        if enhanced_analyzer and enhanced_analyzer._df_client:
            try:
                tenant_id = os.getenv("TENANT_ID", "default")
                await enhanced_analyzer._df_client.initialize_credentials(tenant_id)
                
                # Get suggestions for each seed keyword
                for seed_keyword in request.keywords[:5]:  # Limit to top 5 seed keywords to avoid too many API calls
                    if len(all_keywords) >= 200:  # Max limit
                        break
                    
                    try:
                        df_suggestions = await enhanced_analyzer._df_client.get_keyword_suggestions(
                            seed_keyword=seed_keyword,
                            location_name=request.location or "United States",
                            language_code=request.language or "en",
                            tenant_id=tenant_id,
                            limit=min(request.max_suggestions_per_keyword, 150)
                        )
                        
                        # Add new keywords that aren't already in the list
                        for suggestion in df_suggestions:
                            kw = suggestion.get("keyword", "").strip()
                            if kw and kw not in all_keywords and len(all_keywords) < 200:
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
        clustering_result = clustering.cluster_keywords(
            keywords=all_keywords,
            min_cluster_size=1,  # Allow single keywords to form clusters
            max_clusters=None
        )
        
        # Log clustering results for debugging
        logger.info(f"Clustering result: {clustering_result.cluster_count} clusters from {clustering_result.total_keywords} keywords")
        logger.info(f"Clusters: {[c.parent_topic for c in clustering_result.clusters[:5]]}")
        
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
            
            out[k] = {
                "search_volume": search_volume,  # Always numeric
                "difficulty": v.difficulty.value if hasattr(v.difficulty, "value") else str(v.difficulty),
                "competition": competition_value,
                "cpc": cpc_value,  # Always numeric
                "trend_score": trend_score_value,
                "recommended": v.recommended,
                "reason": v.reason,
                "related_keywords": v.related_keywords,
                "long_tail_keywords": v.long_tail_keywords,
                "parent_topic": parent_topic,
                "category_type": category_type,
                "cluster_score": cluster_score
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
        
        return {
            "enhanced_analysis": out,
            "total_keywords": len(all_keywords),
            "original_keywords": request.keywords,
            "suggested_keywords": all_keywords[len(request.keywords):] if len(all_keywords) > len(request.keywords) else [],
            "clusters": clusters_list,
            "cluster_summary": {
                "total_keywords": clustering_result.total_keywords if clustering_result else len(all_keywords),
                "cluster_count": len(clusters_list),
                "unclustered_count": len(clustering_result.unclustered) if clustering_result else 0
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced keyword analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Enhanced keyword analysis failed: {str(e)}"
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
