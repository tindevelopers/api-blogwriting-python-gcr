# Blog Writer Abstraction Layer Guide

This guide explains how to use the new Blog Writer abstraction layer, which provides a high-level, intelligent interface for content generation with advanced features like strategy-based optimization, quality assurance, and provider management.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Core Components](#core-components)
4. [Content Strategies](#content-strategies)
5. [Factory Patterns](#factory-patterns)
6. [Quality Assurance](#quality-assurance)
7. [API Integration](#api-integration)
8. [Advanced Usage](#advanced-usage)
9. [Examples](#examples)

## Overview

The Blog Writer abstraction layer provides:

- **Intelligent Content Generation**: Multiple strategies for different content goals
- **Quality Assurance**: Automatic content optimization and quality scoring
- **Provider Management**: Multi-provider support with automatic fallback
- **Factory Patterns**: Easy configuration with presets and builders
- **Comprehensive Analytics**: Detailed statistics and monitoring
- **Batch Processing**: Concurrent blog generation for efficiency

## Quick Start

### Basic Usage

```python
from src.blog_writer_sdk.ai import BlogWriterFactory, BlogGenerationRequest, ContentStrategy

# Create a blog writer
blog_writer = BlogWriterFactory.create_seo_focused_writer()

# Create a request
request = BlogGenerationRequest(
    topic="Python Web Development Best Practices",
    keywords=["python", "web development", "best practices"],
    content_strategy=ContentStrategy.SEO_OPTIMIZED
)

# Generate blog
result = await blog_writer.generate_blog(request)
print(f"Title: {result.title}")
print(f"Quality Score: {result.quality_score}")
```

### Using Presets

```python
from src.blog_writer_sdk.ai import BlogWriterFactory

# Different presets for different needs
seo_writer = BlogWriterFactory.create_seo_focused_writer()
engagement_writer = BlogWriterFactory.create_engagement_focused_writer()
conversion_writer = BlogWriterFactory.create_conversion_focused_writer()
technical_writer = BlogWriterFactory.create_technical_writer()
```

## Core Components

### 1. BlogWriterAbstraction

The main class that orchestrates blog generation with advanced features.

```python
from src.blog_writer_sdk.ai import BlogWriterAbstraction

blog_writer = BlogWriterAbstraction(
    ai_generator=ai_generator,
    keyword_analyzer=keyword_analyzer,
    content_analyzer=content_analyzer
)
```

### 2. BlogGenerationRequest

Request model for blog generation with comprehensive options.

```python
from src.blog_writer_sdk.ai import BlogGenerationRequest, ContentStrategy, ContentQuality

request = BlogGenerationRequest(
    topic="Your Blog Topic",
    keywords=["keyword1", "keyword2"],
    target_audience="Your target audience",
    content_strategy=ContentStrategy.SEO_OPTIMIZED,
    quality_target=ContentQuality.EXCELLENT,
    additional_context={"industry": "technology"}
)
```

### 3. BlogGenerationResult

Comprehensive result with quality metrics and analytics.

```python
result = await blog_writer.generate_blog(request)

print(f"Title: {result.title}")
print(f"Content: {result.content}")
print(f"SEO Score: {result.seo_score}")
print(f"Quality Score: {result.quality_score}")
print(f"Cost: ${result.cost}")
print(f"Provider Used: {result.provider_used}")
```

## Content Strategies

### Available Strategies

1. **SEO_OPTIMIZED**: Focus on search engine optimization
2. **ENGAGEMENT_FOCUSED**: Maximize reader engagement
3. **CONVERSION_OPTIMIZED**: Optimize for conversions
4. **EDUCATIONAL**: Educational content approach
5. **PROMOTIONAL**: Promotional content strategy
6. **TECHNICAL**: Technical documentation style
7. **CREATIVE**: Creative and artistic content

### Strategy Usage

```python
from src.blog_writer_sdk.ai import ContentStrategy

# SEO-focused content
seo_request = BlogGenerationRequest(
    topic="Digital Marketing Trends",
    keywords=["digital marketing", "trends", "2024"],
    content_strategy=ContentStrategy.SEO_OPTIMIZED
)

# Engagement-focused content
engagement_request = BlogGenerationRequest(
    topic="Personal Productivity Tips",
    keywords=["productivity", "tips", "personal"],
    content_strategy=ContentStrategy.ENGAGEMENT_FOCUSED
)

# Conversion-focused content
conversion_request = BlogGenerationRequest(
    topic="Why Choose Our Product",
    keywords=["product", "benefits", "features"],
    content_strategy=ContentStrategy.CONVERSION_OPTIMIZED
)
```

## Factory Patterns

### BlogWriterFactory

Create blog writers with predefined configurations.

```python
from src.blog_writer_sdk.ai import BlogWriterFactory, BlogWriterPreset

# Using presets
seo_writer = BlogWriterFactory.create_seo_focused_writer()
engagement_writer = BlogWriterFactory.create_engagement_focused_writer()
conversion_writer = BlogWriterFactory.create_conversion_focused_writer()
technical_writer = BlogWriterFactory.create_technical_writer()
creative_writer = BlogWriterFactory.create_creative_writer()
enterprise_writer = BlogWriterFactory.create_enterprise_writer()
startup_writer = BlogWriterFactory.create_startup_writer()
minimal_writer = BlogWriterFactory.create_minimal_writer()

# Custom configuration
custom_writer = BlogWriterFactory.create_custom_writer(
    providers=["openai", "anthropic"],
    strategy=ContentStrategy.SEO_OPTIMIZED,
    quality=ContentQuality.EXCELLENT
)
```

### BlogWriterBuilder

Fluent interface for custom blog writer configuration.

```python
from src.blog_writer_sdk.ai import BlogWriterBuilder, BlogWriterPreset, ContentStrategy, ContentQuality

custom_writer = (BlogWriterBuilder()
                .with_preset(BlogWriterPreset.ENTERPRISE_WRITER)
                .with_providers("openai", "anthropic")
                .with_strategy(ContentStrategy.SEO_OPTIMIZED)
                .with_quality(ContentQuality.PUBLICATION_READY)
                .with_keyword_analysis(True)
                .with_content_optimization(True)
                .with_quality_assurance(True)
                .build())
```

## Quality Assurance

### Content Quality Levels

1. **DRAFT**: Basic quality for initial drafts
2. **GOOD**: Good quality for most use cases
3. **EXCELLENT**: High quality for professional content
4. **PUBLICATION_READY**: Publication-ready quality

### Quality Assessment

```python
# Assess existing content
quality_metrics = await blog_writer.assess_content_quality(
    content="Your existing content",
    keywords=["keyword1", "keyword2"],
    target_quality=ContentQuality.EXCELLENT
)

print(f"Readability Score: {quality_metrics['readability_score']}")
print(f"SEO Score: {quality_metrics['seo_score']}")
print(f"Overall Quality: {quality_metrics['overall_quality']}")
```

### Content Optimization

```python
# Optimize existing content
optimized_content = await blog_writer.optimize_existing_content(
    content="Your content to optimize",
    keywords=["keyword1", "keyword2"],
    strategy=ContentStrategy.SEO_OPTIMIZED
)
```

## API Integration

### New API Endpoints

The abstraction layer adds new API endpoints:

- `POST /api/v1/abstraction/blog/generate` - Generate blog with abstraction layer
- `GET /api/v1/abstraction/strategies` - Get available content strategies
- `GET /api/v1/abstraction/quality-levels` - Get available quality levels
- `GET /api/v1/abstraction/presets` - Get available presets
- `GET /api/v1/abstraction/status` - Get abstraction layer status

### API Usage Example

```bash
# Generate blog with abstraction layer
curl -X POST "http://localhost:8000/api/v1/abstraction/blog/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AI in Web Development",
    "keywords": ["AI", "web development", "automation"],
    "content_strategy": "seo_optimized",
    "quality_target": "excellent"
  }'

# Get available strategies
curl "http://localhost:8000/api/v1/abstraction/strategies"

# Get abstraction layer status
curl "http://localhost:8000/api/v1/abstraction/status"
```

## Advanced Usage

### Batch Generation

```python
# Generate multiple blogs concurrently
requests = [
    BlogGenerationRequest(topic="Topic 1", keywords=["keyword1"]),
    BlogGenerationRequest(topic="Topic 2", keywords=["keyword2"]),
    BlogGenerationRequest(topic="Topic 3", keywords=["keyword3"])
]

results = await blog_writer.generate_blog_batch(requests, max_concurrent=3)
```

### Provider Management

```python
# Check provider status
provider_status = await blog_writer.get_ai_provider_status()
print(f"OpenAI Status: {provider_status['openai']['status']}")

# Get generation statistics
stats = blog_writer.get_generation_statistics()
print(f"Total Blogs: {stats['total_blogs_generated']}")
print(f"Success Rate: {stats['success_rate']:.2%}")
print(f"Average Cost: ${stats['average_cost_per_blog']:.4f}")
```

### Custom Optimization Strategies

```python
from src.blog_writer_sdk.ai import ContentOptimizationStrategy

class CustomOptimizationStrategy(ContentOptimizationStrategy):
    async def optimize_content(self, content, keywords, target_audience=None):
        # Implement custom optimization logic
        return optimized_content

# Use custom strategy
blog_writer.optimization_strategies[ContentStrategy.CUSTOM] = CustomOptimizationStrategy()
```

## Examples

### Complete Example

```python
import asyncio
from src.blog_writer_sdk.ai import (
    BlogWriterFactory,
    BlogGenerationRequest,
    ContentStrategy,
    ContentQuality,
    ContentTone,
    ContentLength
)

async def main():
    # Create blog writer
    blog_writer = BlogWriterFactory.create_seo_focused_writer()
    
    # Create request
    request = BlogGenerationRequest(
        topic="Python Web Development Best Practices",
        keywords=["python", "web development", "best practices", "fastapi"],
        target_audience="Python developers",
        content_strategy=ContentStrategy.SEO_OPTIMIZED,
        tone=ContentTone.PROFESSIONAL,
        length=ContentLength.MEDIUM,
        quality_target=ContentQuality.EXCELLENT,
        additional_context={
            "industry": "technology",
            "experience_level": "intermediate"
        }
    )
    
    # Generate blog
    result = await blog_writer.generate_blog(request)
    
    # Display results
    print("🎉 Blog Generated Successfully!")
    print(f"📝 Title: {result.title}")
    print(f"📊 Quality Score: {result.quality_score:.2f}")
    print(f"🔍 SEO Score: {result.seo_score:.2f}")
    print(f"📖 Readability Score: {result.readability_score:.2f}")
    print(f"🔧 Provider Used: {result.provider_used}")
    print(f"💰 Cost: ${result.cost:.4f}")
    print(f"⏱️ Generation Time: {result.generation_time:.2f}s")
    print(f"🔤 Tokens Used: {result.tokens_used}")
    
    return result

# Run the example
if __name__ == "__main__":
    asyncio.run(main())
```

### Multiple Strategies Example

```python
async def compare_strategies():
    blog_writer = BlogWriterFactory.create_seo_focused_writer()
    
    strategies = [
        ContentStrategy.SEO_OPTIMIZED,
        ContentStrategy.ENGAGEMENT_FOCUSED,
        ContentStrategy.CONVERSION_OPTIMIZED
    ]
    
    for strategy in strategies:
        request = BlogGenerationRequest(
            topic="Remote Work Productivity",
            keywords=["remote work", "productivity", "tips"],
            content_strategy=strategy,
            quality_target=ContentQuality.GOOD
        )
        
        result = await blog_writer.generate_blog(request)
        print(f"{strategy.value}: Quality {result.quality_score:.2f}, Cost ${result.cost:.4f}")
```

## Best Practices

1. **Choose the Right Strategy**: Select content strategy based on your goals
2. **Set Appropriate Quality**: Balance quality requirements with cost
3. **Use Batch Generation**: For multiple blogs, use batch generation for efficiency
4. **Monitor Statistics**: Track generation statistics for optimization
5. **Provider Fallback**: Let the system handle provider fallback automatically
6. **Quality Assessment**: Use quality assessment for existing content
7. **Custom Context**: Provide additional context for better results

## Troubleshooting

### Common Issues

1. **No AI Providers Available**: Ensure API keys are configured
2. **Low Quality Scores**: Try different strategies or increase quality target
3. **High Costs**: Use shorter content lengths or different providers
4. **Generation Failures**: Check provider status and API limits

### Debug Information

```python
# Get detailed status
status = await blog_writer.get_ai_provider_status()
print("Provider Status:", status)

# Get generation statistics
stats = blog_writer.get_generation_statistics()
print("Generation Stats:", stats)
```

This abstraction layer provides a powerful, flexible interface for blog generation with advanced features and comprehensive quality assurance. Use it to create high-quality, optimized content efficiently and cost-effectively.
