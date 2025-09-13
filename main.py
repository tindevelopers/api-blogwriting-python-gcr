"""
FastAPI application for the Blog Writer SDK.

This module provides a REST API wrapper around the Blog Writer SDK,
enabling web-based access to all blog generation and optimization features.
"""

import os
import time
import logging
import asyncio
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

# Track startup time for uptime calculation
startup_time = time.time()

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
from src.blog_writer_sdk.ai.litellm_router import LiteLLMRouterProvider, TaskType, TaskComplexity
from src.blog_writer_sdk.middleware.rate_limiter import rate_limit_middleware
from src.blog_writer_sdk.cache.redis_cache import initialize_cache, get_cache_manager
from src.blog_writer_sdk.monitoring.metrics import initialize_metrics, get_metrics_collector, monitor_performance
from src.blog_writer_sdk.batch.batch_processor import BatchProcessor


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
    keywords: List[str] = Field(..., max_length=50, description="Keywords to analyze")
    location: Optional[str] = Field("United States", description="Location for keyword analysis")
    language: Optional[str] = Field("en", description="Language code for analysis")


class KeywordExtractionRequest(BaseModel):
    """Request model for keyword extraction API."""
    content: str = Field(..., min_length=100, description="Content to extract keywords from")
    max_keywords: int = Field(default=20, ge=5, le=50, description="Maximum keywords to extract")


class KeywordSuggestionRequest(BaseModel):
    """Request model for keyword suggestions."""
    keyword: str = Field(..., min_length=2, max_length=100, description="Base keyword for suggestions")


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
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    # Startup
    print("🚀 Blog Writer SDK API starting up...")
    
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
    
    # Initialize batch processor
    global batch_processor
    blog_writer = get_blog_writer()
    batch_processor = BatchProcessor(
        blog_writer=blog_writer,
        max_concurrent=int(os.getenv("BATCH_MAX_CONCURRENT", "5")),
        max_retries=int(os.getenv("BATCH_MAX_RETRIES", "2"))
    )
    print("✅ Batch processor initialized")
    
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
    description="A powerful REST API for AI-driven blog writing with advanced SEO optimization, intelligent routing, and enterprise features",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js development
        "http://localhost:3001",  # Alternative Next.js port
        "https://*.vercel.app",   # Vercel deployments
        "https://*.netlify.app",  # Netlify deployments
        # Add your production domains here
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.middleware("http")(rate_limit_middleware)

# Global variables
batch_processor: Optional[BatchProcessor] = None

# Initialize enhanced keyword analyzer if DataForSEO credentials are available
def create_enhanced_keyword_analyzer() -> Optional[EnhancedKeywordAnalyzer]:
    """Create enhanced keyword analyzer with DataForSEO integration if configured."""
    dataforseo_api_key = os.getenv("DATAFORSEO_API_KEY")
    dataforseo_api_secret = os.getenv("DATAFORSEO_API_SECRET")
    
    if dataforseo_api_key and dataforseo_api_secret:
        try:
            # Use the enhanced keyword analyzer with DataForSEO integration
            return EnhancedKeywordAnalyzer(use_dataforseo=True, location="United States")
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


def create_litellm_router() -> Optional[LiteLLMRouterProvider]:
    """Create LiteLLM router for intelligent AI provider routing."""
    try:
        # Check if any AI provider is configured
        openai_key = os.getenv("OPENAI_API_KEY")
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not any([openai_key, deepseek_key, anthropic_key]):
            logging.info("No AI provider keys found, LiteLLM router disabled")
            return None
        
        # Get config path
        config_path = os.getenv("LITELLM_CONFIG_PATH", "litellm_config.yaml")
        
        # Create LiteLLM router
        router = LiteLLMRouterProvider(
            config_path=config_path,
            enable_cost_tracking=True,
            enable_caching=True,
            debug=os.getenv("DEBUG", "false").lower() == "true"
        )
        
        logging.info(f"✅ LiteLLM Router initialized with config: {config_path}")
        return router
        
    except Exception as e:
        logging.error(f"❌ Failed to initialize LiteLLM Router: {e}")
        return None


# Global instances
enhanced_analyzer = create_enhanced_keyword_analyzer()
ai_generator = create_ai_content_generator()
litellm_router = create_litellm_router()
blog_writer = BlogWriter(
    enable_seo_optimization=True,
    enable_quality_analysis=True,
    enhanced_keyword_analyzer=enhanced_analyzer,
    ai_content_generator=ai_generator,
    enable_ai_enhancement=ai_generator is not None,
)


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
        version="1.0.0-cloudrun"
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
        "version": "1.0.0",
        "environment": "cloud-run",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
        "live": "/live",
        "endpoints": {
            "generate": "/api/v1/generate",
            "analyze": "/api/v1/analyze",
            "keywords": "/api/v1/keywords",
            "batch": "/api/v1/batch",
            "metrics": "/api/v1/metrics"
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
    
    Returns analysis for each keyword including:
    - Estimated difficulty
    - Related keywords
    - Long-tail variations
    - Recommendations
    """
    try:
        if not request.keywords:
            raise HTTPException(status_code=400, detail="No keywords provided")
        
        results = {}
        for keyword in request.keywords:
            analysis = await writer.keyword_analyzer.analyze_keyword(keyword)
            results[keyword] = analysis
        
        return {"keyword_analysis": results}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Keyword analysis failed: {str(e)}"
        )


# Extract keywords from content endpoint
@app.post("/api/v1/keywords/extract")
async def extract_keywords(
    request: KeywordExtractionRequest,
    writer: BlogWriter = Depends(get_blog_writer)
):
    """
    Extract potential keywords from existing content.
    
    Uses advanced NLP techniques to identify:
    - High-value keywords
    - Relevant phrases
    - Content themes
    """
    try:
        keywords = await writer.keyword_analyzer.extract_keywords_from_content(
            content=request.content,
            max_keywords=request.max_keywords
        )
        
        return {"extracted_keywords": keywords}
        
    except Exception as e:
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
            "original_length": len(content.split()),
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
    # This could be enhanced to log to a database or analytics service
    print(f"📊 Generation Log: Topic='{topic}', Success={success}, Words={word_count}, Time={generation_time:.2f}s")


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
    
    # Add LiteLLM router information if available
    if litellm_router:
        try:
            config["litellm_router"] = {
                "enabled": True,
                "available_models": litellm_router.get_available_models(),
                "cost_tracking": litellm_router.enable_cost_tracking,
                "cost_summary": litellm_router.get_cost_summary()
            }
        except Exception as e:
            config["litellm_router_error"] = str(e)
    else:
        config["litellm_router"] = {"enabled": False}
    
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


# LiteLLM Router Endpoints
@app.get("/api/v1/litellm/health")
async def litellm_health_check():
    """Check health of all LiteLLM router providers."""
    if not litellm_router:
        return {
            "status": "disabled",
            "message": "LiteLLM router not initialized"
        }
    
    try:
        health_status = await litellm_router.health_check()
        return health_status
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to check LiteLLM router health"
        }


@app.get("/api/v1/litellm/models")
async def get_available_models():
    """Get list of available models in LiteLLM router."""
    if not litellm_router:
        return {
            "models": [],
            "message": "LiteLLM router not initialized"
        }
    
    try:
        models = litellm_router.get_available_models()
        return {
            "models": models,
            "count": len(models)
        }
    except Exception as e:
        return {
            "models": [],
            "error": str(e),
            "message": "Failed to get available models"
        }


@app.get("/api/v1/litellm/costs")
async def get_cost_summary():
    """Get cost tracking summary from LiteLLM router."""
    if not litellm_router:
        return {
            "cost_summary": {},
            "message": "LiteLLM router not initialized"
        }
    
    try:
        cost_summary = litellm_router.get_cost_summary()
        return cost_summary
    except Exception as e:
        return {
            "cost_summary": {},
            "error": str(e),
            "message": "Failed to get cost summary"
        }


class LiteLLMGenerationRequest(BaseModel):
    """Request model for LiteLLM content generation."""
    prompt: str = Field(..., min_length=10, description="Content generation prompt")
    task_type: str = Field(default="simple_completion", description="Task type for optimal routing")
    complexity: str = Field(default="medium", description="Task complexity level")
    max_tokens: Optional[int] = Field(default=4096, ge=1, le=8192, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")


class BatchGenerationRequest(BaseModel):
    """Request model for batch blog generation."""
    requests: List[BlogGenerationRequest] = Field(..., min_length=1, max_length=100, description="List of blog generation requests")
    job_id: Optional[str] = Field(None, description="Optional custom job ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional job metadata")


@app.post("/api/v1/litellm/generate")
async def generate_with_litellm(request: LiteLLMGenerationRequest):
    """Generate content using LiteLLM router with intelligent model selection."""
    if not litellm_router:
        raise HTTPException(
            status_code=503,
            detail="LiteLLM router not available"
        )
    
    try:
        # Map string values to enums
        task_type_map = {
            "blog_generation": TaskType.BLOG_GENERATION,
            "seo_analysis": TaskType.SEO_ANALYSIS,
            "keyword_extraction": TaskType.KEYWORD_EXTRACTION,
            "content_formatting": TaskType.CONTENT_FORMATTING,
            "image_analysis": TaskType.IMAGE_ANALYSIS,
            "simple_completion": TaskType.SIMPLE_COMPLETION
        }
        
        complexity_map = {
            "low": TaskComplexity.LOW,
            "medium": TaskComplexity.MEDIUM,
            "high": TaskComplexity.HIGH
        }
        
        task_type = task_type_map.get(request.task_type, TaskType.SIMPLE_COMPLETION)
        complexity = complexity_map.get(request.complexity, TaskComplexity.MEDIUM)
        
        # Generate content using LiteLLM router
        response = await litellm_router.generate_content(
            prompt=request.prompt,
            task_type=task_type,
            complexity=complexity,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        return {
            "success": True,
            "content": response.content,
            "model_used": response.model,
            "usage": response.usage,
            "metadata": response.metadata
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content generation failed: {str(e)}"
        )


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
            "version": "1.0.0-cloudrun",
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
