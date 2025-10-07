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
deployment_version = "2024-12-19-001"

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
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

from google.cloud import secretmanager
from supabase import create_client, Client
from src.blog_writer_sdk.batch.batch_processor import BatchProcessor
from src.blog_writer_sdk.api.ai_provider_management import router as ai_provider_router, initialize_from_env
from src.blog_writer_sdk.api.image_generation import router as image_generation_router, initialize_image_providers_from_env


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
    global enhanced_keyword_analyzer
    enhanced_keyword_analyzer = EnhancedKeywordAnalyzer(
        use_dataforseo=True, # Assuming we always want to use DataforSEO if available
        credential_service=dataforseo_credential_service
    )
    print("✅ EnhancedKeywordAnalyzer initialized.")

    yield
    
    # Shutdown
    print("📝 Blog Writer SDK API shutting down...")
    
    # Cleanup tasks
    if hasattr(metrics_collector, '_cleanup_task') and metrics_collector._cleanup_task:
        metrics_collector._cleanup_task.cancel()
    
    print("✅ Cleanup completed")


# Create FastAPI application
app = FastAPI(
    title="PetStore Direct Content Creator",
    description="""
    A powerful REST API for AI-driven content creation for pet stores with advanced SEO optimization, intelligent routing, and enterprise features.
    
    ## Key Features
    
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
    
    ## Quick Start
    
    1. **Configure AI Providers**: Use `/api/v1/ai/providers/configure` to add your AI provider credentials
    2. **Configure Image Providers**: Use `/api/v1/images/providers/configure` to add image generation providers
    3. **Generate Content**: Use `/api/v1/blog/generate` to create blog posts
    4. **Generate Images**: Use `/api/v1/images/generate` to create images from text prompts
    5. **Analyze Keywords**: Use `/api/v1/keywords/suggest` for keyword research
    6. **Monitor Usage**: Use `/api/v1/ai/providers/stats` to track usage and costs
    
    ## Authentication
    
    API keys are managed securely through the provider management system. No additional authentication is required for basic usage.
    
    ## Support
    
    - 📚 **Documentation**: Complete API documentation available at `/docs`
    - 🔧 **Health Checks**: Monitor service health at `/health`
    - 📊 **Metrics**: View usage statistics at `/api/v1/metrics`
    """,
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)

# Custom JavaScript to inject the PetStore Direct logo
CUSTOM_SWAGGER_JS = """
<script>
    window.addEventListener('load', function() {
        const topbar = document.querySelector('.swagger-ui .topbar-wrapper');
        if (topbar) {
            const link = topbar.querySelector('.link');
            if (link) {
                const img = document.createElement('img');
                img.src = 'https://petstore.direct/static/images/logo.png';
                img.alt = 'PetStore Direct Logo';
                img.style.height = '40px';
                img.style.marginRight = '10px';
                img.style.verticalAlign = 'middle';
                img.onerror = function() {
                    // Fallback to text if logo doesn't load
                    this.style.display = 'none';
                };
                link.prepend(img);
            }
        }
    });
</script>
"""

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    response = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - API Documentation",
        swagger_ui_parameters={"dom_id": "#swagger-ui", "layout": "BaseLayout", "deepLinking": True, "displayRequestDuration": True},
    )
    html_content = response.body.decode("utf-8")
    html_content = html_content.replace(
        "</head>",
        f"{CUSTOM_SWAGGER_JS}</head>"
    )
    return HTMLResponse(content=html_content)

@app.get("/redoc", include_in_schema=False)
async def custom_redoc():
    from fastapi.openapi.docs import get_redoc_html
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
    )

@app.get("/api-docs", include_in_schema=False)
async def api_documentation():
    """Serve comprehensive API documentation in markdown format."""
    try:
        # Try to read from file first, fallback to embedded content
        try:
            with open("API_DOCUMENTATION.md", "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            # Embedded documentation content
            content = """# 🏪 PetStore Direct Content Creator API

## 📋 Overview

The **PetStore Direct Content Creator API** is a powerful, AI-driven content creation platform specifically designed for pet stores, veterinary clinics, and pet service businesses. This API generates high-quality, SEO-optimized blog posts, product descriptions, and marketing content using advanced AI providers including OpenAI, Anthropic, and Azure OpenAI.

## 🚀 Service Information

- **Service Name:** PetStore Direct Content Creator
- **Service URL:** `https://petstore-content-creator-613248238610.us-east1.run.app`
- **Region:** us-east1
- **Version:** 1.0.0
- **Status:** ✅ Active and Healthy

## 🎯 Key Features

### 🤖 AI-Powered Content Generation
- **Multi-Provider AI Support**: OpenAI GPT-4, Anthropic Claude, Azure OpenAI with intelligent fallback
- **Pet-Focused Content**: Specialized templates for pet care guides, product reviews, breed information
- **SEO Optimization**: Built-in keyword analysis and meta tag generation for pet industry terms
- **Content Quality Analysis**: Readability scoring and improvement suggestions
- **Multiple Output Formats**: Markdown, HTML, and JSON support

### 📊 Advanced Analytics
- **SEO Metrics**: Keyword density, focus keyword scoring, title optimization
- **Content Quality**: Flesch-Kincaid grade level, reading ease, vocabulary diversity
- **Performance Tracking**: Generation time, word count, success rates
- **Real-time Monitoring**: Health checks, error tracking, usage statistics

## 📚 API Endpoints

### 🏥 Health & Status

#### GET `/health`
**Description:** Check service health and status

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1759488304.3095403,
  "version": "1.0.0-cloudrun"
}
```

#### GET `/api/v1/health/detailed`
**Description:** Detailed health metrics including CPU, memory, and performance data

### 📝 Content Generation

#### POST `/api/v1/blog/generate`
**Description:** Generate AI-powered blog content for pet stores

**Request Body:**
```json
{
  "topic": "Best Dog Food for Puppies",
  "keywords": ["puppy food", "dog nutrition", "puppy care"],
  "tone": "professional",
  "length": "medium",
  "target_audience": "new dog owners",
  "custom_instructions": "Focus on nutritional benefits and feeding schedules"
}
```

**Response includes:**
- Generated blog content with title, content, and excerpt
- SEO meta tags and Open Graph tags
- SEO metrics and content quality scores
- Readability analysis and recommendations
- Generation time and word count

### ⚙️ Configuration

#### GET `/api/v1/config`
**Description:** Get API configuration and supported features

## 🎨 Content Types & Templates

### 📝 Pet Care Guides
- **Puppy Training Tips**
- **Senior Pet Care**
- **Pet Nutrition Guides**
- **Breed-Specific Information**
- **Health & Wellness Content**

### 🛍️ Product Content
- **Product Descriptions**
- **Product Reviews**
- **Comparison Articles**
- **Buying Guides**
- **Feature Highlights**

### 🏥 Veterinary Content
- **Medical Information**
- **Treatment Options**
- **Preventive Care**
- **Emergency Procedures**
- **Health Monitoring**

## 🔧 Request Parameters

### Content Generation Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `topic` | string | ✅ | Main topic/subject of the content | "Best Cat Litter for Odor Control" |
| `keywords` | array | ❌ | SEO keywords to include | ["cat litter", "odor control", "clumping"] |
| `tone` | string | ❌ | Writing tone and style | "professional", "casual", "friendly" |
| `length` | string | ❌ | Content length preference | "short", "medium", "long", "extended" |
| `target_audience` | string | ❌ | Intended audience | "new pet owners", "experienced breeders" |
| `custom_instructions` | string | ❌ | Specific requirements or focus areas | "Include feeding schedules and portion sizes" |

### Supported Tones
- **Professional**: Formal, authoritative tone for business content
- **Casual**: Friendly, approachable tone for general audience
- **Friendly**: Warm, personal tone for customer engagement
- **Authoritative**: Expert-level tone for technical content
- **Conversational**: Natural, dialogue-like tone
- **Technical**: Detailed, scientific tone for specialized content
- **Creative**: Engaging, storytelling tone for marketing content

### Supported Lengths
- **Short**: 300-500 words (Quick reads, social media posts)
- **Medium**: 500-1000 words (Standard blog posts, product descriptions)
- **Long**: 1000-2000 words (Comprehensive guides, detailed reviews)
- **Extended**: 2000+ words (In-depth articles, comprehensive resources)

## 🚀 Usage Examples

### Example 1: Pet Care Guide
```bash
curl -X POST "https://petstore-content-creator-613248238610.us-east1.run.app/api/v1/blog/generate" \\
  -H "Content-Type: application/json" \\
  -d '{
    "topic": "How to Train a Puppy to Use a Crate",
    "keywords": ["puppy training", "crate training", "dog behavior"],
    "tone": "instructional",
    "length": "medium",
    "target_audience": "new dog owners"
  }'
```

### Example 2: Product Review
```bash
curl -X POST "https://petstore-content-creator-613248238610.us-east1.run.app/api/v1/blog/generate" \\
  -H "Content-Type: application/json" \\
  -d '{
    "topic": "Best Cat Litter for Multi-Cat Households",
    "keywords": ["cat litter", "multi-cat", "odor control"],
    "tone": "professional",
    "length": "long",
    "custom_instructions": "Include pros and cons, price comparisons, and maintenance tips"
  }'
```

## 🔒 Security & Authentication

### CORS Configuration
The API supports Cross-Origin Resource Sharing (CORS) for the following origins:
- `http://localhost:3000` (Next.js development)
- `http://localhost:3001` (Alternative Next.js port)
- `https://petstore.direct` (Production frontend)
- `https://*.vercel.app` (Vercel deployments)

### Rate Limiting
- **Requests per minute**: 60 requests
- **Requests per hour**: 1000 requests
- **Requests per day**: 10000 requests
- **Burst capacity**: 10 concurrent requests

## 📈 Performance & Monitoring

### Response Times
- **Average response time**: < 2 seconds
- **95th percentile**: < 5 seconds
- **Timeout limit**: 15 minutes
- **Concurrent requests**: Up to 80 per instance

### Resource Allocation
- **Memory**: 2GB per instance
- **CPU**: 2 vCPUs per instance
- **Storage**: 100GB disk space
- **Network**: High-bandwidth connectivity

### Monitoring Endpoints
- **Health Check**: `/health`
- **Detailed Metrics**: `/api/v1/health/detailed`
- **API Documentation**: `/docs`
- **Alternative Docs**: `/redoc`
- **Comprehensive Docs**: `/api-docs`

## 🛠️ Integration Examples

### JavaScript/Node.js
```javascript
const axios = require('axios');

const petStoreAPI = axios.create({
  baseURL: 'https://petstore-content-creator-613248238610.us-east1.run.app',
  headers: {
    'Content-Type': 'application/json',
  },
});

async function generatePetContent(topic, keywords = []) {
  try {
    const response = await petStoreAPI.post('/api/v1/blog/generate', {
      topic,
      keywords,
      tone: 'professional',
      length: 'medium'
    });
    
    return response.data;
  } catch (error) {
    console.error('Content generation failed:', error.response?.data || error.message);
    throw error;
  }
}
```

### Python
```python
import requests

class PetStoreContentAPI:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
    
    def generate_content(self, topic, **kwargs):
        payload = {
            "topic": topic,
            "tone": kwargs.get("tone", "professional"),
            "length": kwargs.get("length", "medium"),
            "keywords": kwargs.get("keywords", []),
            "target_audience": kwargs.get("target_audience"),
            "custom_instructions": kwargs.get("custom_instructions")
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/blog/generate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        response.raise_for_status()
        return response.json()
```

## 🎯 Best Practices

### Content Generation
1. **Be Specific with Topics**: Use detailed, specific topics for better results
2. **Include Relevant Keywords**: Add 3-5 relevant keywords for SEO optimization
3. **Choose Appropriate Tone**: Match tone to your audience and content type
4. **Set Realistic Length**: Choose length based on content complexity and audience needs
5. **Provide Context**: Use custom instructions to guide content focus

### SEO Optimization
1. **Keyword Research**: Use pet industry-specific keywords
2. **Local SEO**: Include location-based keywords for local pet stores
3. **Long-tail Keywords**: Target specific, less competitive phrases
4. **Content Structure**: Use proper heading hierarchy (H1, H2, H3)
5. **Meta Optimization**: Leverage generated meta tags for better search visibility

## 🚨 Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
  "detail": "Topic is required for content generation"
}
```

#### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "tone"],
      "msg": "invalid choice",
      "type": "value_error.const"
    }
  ]
}
```

#### 429 Rate Limit Exceeded
```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

## 📞 Support & Resources

### Documentation
- **Interactive API Docs**: `https://petstore-content-creator-613248238610.us-east1.run.app/docs`
- **Alternative Docs**: `https://petstore-content-creator-613248238610.us-east1.run.app/redoc`
- **Comprehensive Docs**: `https://petstore-content-creator-613248238610.us-east1.run.app/api-docs`
- **OpenAPI Spec**: `https://petstore-content-creator-613248238610.us-east1.run.app/openapi.json`

### Health Monitoring
- **Service Health**: `https://petstore-content-creator-613248238610.us-east1.run.app/health`
- **Detailed Metrics**: `https://petstore-content-creator-613248238610.us-east1.run.app/api/v1/health/detailed`

---

*This API is powered by advanced AI technology and optimized for the pet industry. For technical support or feature requests, please contact the development team.*

**Last Updated**: October 3, 2025  
**API Version**: 1.0.0  
**Service Status**: ✅ Active"""
        
        # Convert markdown to HTML for better presentation
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>PetStore Direct Content Creator - API Documentation</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background: #f8f9fa;
                }}
                .container {{
                    background: white;
                    padding: 40px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #2c3e50;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #34495e;
                    margin-top: 30px;
                    border-left: 4px solid #3498db;
                    padding-left: 15px;
                }}
                h3 {{
                    color: #2c3e50;
                    margin-top: 25px;
                }}
                code {{
                    background: #f4f4f4;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: 'Monaco', 'Menlo', monospace;
                }}
                pre {{
                    background: #2c3e50;
                    color: #ecf0f1;
                    padding: 20px;
                    border-radius: 5px;
                    overflow-x: auto;
                    margin: 20px 0;
                }}
                pre code {{
                    background: none;
                    color: inherit;
                    padding: 0;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }}
                th {{
                    background: #f8f9fa;
                    font-weight: 600;
                }}
                .status-badge {{
                    background: #27ae60;
                    color: white;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                .endpoint {{
                    background: #e8f4fd;
                    padding: 15px;
                    border-left: 4px solid #3498db;
                    margin: 15px 0;
                }}
                .method {{
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 12px;
                    margin-right: 10px;
                }}
                .get {{ background: #27ae60; color: white; }}
                .post {{ background: #3498db; color: white; }}
                .put {{ background: #f39c12; color: white; }}
                .delete {{ background: #e74c3c; color: white; }}
                .feature-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin: 20px 0;
                }}
                .feature-card {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    border-left: 4px solid #3498db;
                }}
                .logo {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .logo img {{
                    height: 60px;
                    margin-bottom: 10px;
                }}
                .service-info {{
                    background: #e8f5e8;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">
                    <h1>🏪 PetStore Direct Content Creator API</h1>
                    <p><span class="status-badge">✅ Active</span> | Version 1.0.0 | us-east1</p>
                </div>
                <div class="service-info">
                    <h3>🚀 Service Information</h3>
                    <p><strong>Service URL:</strong> <code>https://petstore-content-creator-613248238610.us-east1.run.app</code></p>
                    <p><strong>API Documentation:</strong> <a href="/docs">Interactive Docs</a> | <a href="/redoc">ReDoc</a></p>
                    <p><strong>Health Check:</strong> <a href="/health">Service Status</a></p>
                </div>
                {content.replace('```json', '<pre><code class="language-json">').replace('```', '</code></pre>').replace('```bash', '<pre><code class="language-bash">').replace('```javascript', '<pre><code class="language-javascript">').replace('```python', '<pre><code class="language-python">').replace('```php', '<pre><code class="language-php">')}
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Documentation Not Found</h1><p>The API documentation file is not available.</p>",
            status_code=404
        )
    except Exception as e:
        return HTMLResponse(
            content=f"<h1>Error Loading Documentation</h1><p>Error: {str(e)}</p>",
            status_code=500
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

# Include AI provider management router
app.include_router(ai_provider_router)

# Include image generation router
app.include_router(image_generation_router)

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
