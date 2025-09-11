"""
FastAPI application for the Blog Writer SDK.

This module provides a REST API wrapper around the Blog Writer SDK,
enabling web-based access to all blog generation and optimization features.
"""

import os
import time
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
    yield
    # Shutdown
    print("📝 Blog Writer SDK API shutting down...")


# Create FastAPI application
app = FastAPI(
    title="Blog Writer SDK API",
    description="A powerful REST API for AI-driven blog writing with advanced SEO optimization",
    version="0.1.0",
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

# Global blog writer instance
enhanced_analyzer = create_enhanced_keyword_analyzer()
ai_generator = create_ai_content_generator()
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


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=time.time(),
        version="0.1.0-railway-deploy"
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Blog Writer SDK API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "generate": "/api/v1/generate",
            "analyze": "/api/v1/analyze",
            "keywords": "/api/v1/keywords",
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
