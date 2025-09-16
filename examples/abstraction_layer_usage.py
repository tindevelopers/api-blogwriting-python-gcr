"""
Blog Writer Abstraction Layer Usage Examples

This file demonstrates how to use the new Blog Writer abstraction layer
with different strategies, presets, and advanced features.
"""

import asyncio
import os
from typing import List, Dict, Any

from src.blog_writer_sdk.ai import (
    BlogWriterAbstraction,
    BlogWriterFactory,
    BlogWriterPreset,
    BlogWriterBuilder,
    BlogGenerationRequest,
    ContentStrategy,
    ContentQuality,
    ContentTone,
    ContentLength,
    ContentFormat,
    ContentTemplate
)


async def example_basic_usage():
    """Example of basic blog generation using the abstraction layer."""
    print("🚀 Basic Blog Generation Example")
    print("=" * 50)
    
    # Create a blog writer using the factory
    blog_writer = BlogWriterFactory.create_seo_focused_writer()
    
    # Create a blog generation request
    request = BlogGenerationRequest(
        topic="Python Web Development Best Practices",
        keywords=["python", "web development", "best practices", "fastapi", "django"],
        target_audience="Python developers",
        content_strategy=ContentStrategy.SEO_OPTIMIZED,
        tone=ContentTone.PROFESSIONAL,
        length=ContentLength.MEDIUM,
        format=ContentFormat.HTML,
        template=ContentTemplate.HOW_TO_GUIDE,
        quality_target=ContentQuality.EXCELLENT
    )
    
    # Generate the blog
    result = await blog_writer.generate_blog(request)
    
    print(f"✅ Blog Generated Successfully!")
    print(f"📝 Title: {result.title}")
    print(f"📊 Quality Score: {result.quality_score}")
    print(f"🔧 Provider Used: {result.provider_used}")
    print(f"💰 Cost: ${result.cost:.4f}")
    print(f"⏱️ Generation Time: {result.generation_time:.2f}s")
    print(f"🔤 Tokens Used: {result.tokens_used}")
    
    return result


async def example_factory_presets():
    """Example of using different factory presets."""
    print("\n🏭 Factory Presets Example")
    print("=" * 50)
    
    # Create different types of blog writers
    seo_writer = BlogWriterFactory.create_seo_focused_writer()
    engagement_writer = BlogWriterFactory.create_engagement_focused_writer()
    conversion_writer = BlogWriterFactory.create_conversion_focused_writer()
    technical_writer = BlogWriterFactory.create_technical_writer()
    creative_writer = BlogWriterFactory.create_creative_writer()
    
    # Test each writer with the same topic
    topic = "AI-Powered Content Creation"
    keywords = ["AI", "content creation", "automation", "blog writing"]
    
    writers = [
        ("SEO Focused", seo_writer, ContentStrategy.SEO_OPTIMIZED),
        ("Engagement Focused", engagement_writer, ContentStrategy.ENGAGEMENT_FOCUSED),
        ("Conversion Focused", conversion_writer, ContentStrategy.CONVERSION_OPTIMIZED),
        ("Technical Writer", technical_writer, ContentStrategy.TECHNICAL),
        ("Creative Writer", creative_writer, ContentStrategy.CREATIVE)
    ]
    
    for name, writer, strategy in writers:
        print(f"\n📝 Testing {name} Writer...")
        
        request = BlogGenerationRequest(
            topic=topic,
            keywords=keywords,
            content_strategy=strategy,
            tone=ContentTone.PROFESSIONAL,
            length=ContentLength.SHORT,
            quality_target=ContentQuality.GOOD
        )
        
        try:
            result = await writer.generate_blog(request)
            print(f"✅ {name}: Quality Score {result.quality_score:.2f}, Cost ${result.cost:.4f}")
        except Exception as e:
            print(f"❌ {name}: Error - {str(e)}")


async def example_builder_pattern():
    """Example of using the builder pattern for custom configuration."""
    print("\n🔨 Builder Pattern Example")
    print("=" * 50)
    
    # Create a custom blog writer using the builder pattern
    custom_writer = (BlogWriterBuilder()
                    .with_preset(BlogWriterPreset.ENTERPRISE_WRITER)
                    .with_providers("openai", "anthropic")
                    .with_strategy(ContentStrategy.SEO_OPTIMIZED)
                    .with_quality(ContentQuality.PUBLICATION_READY)
                    .with_keyword_analysis(True)
                    .with_content_optimization(True)
                    .with_quality_assurance(True)
                    .with_dataforseo({
                        "api_key": os.getenv("DATAFORSEO_API_KEY"),
                        "enable_enhanced_analysis": True
                    })
                    .build())
    
    # Generate a high-quality blog
    request = BlogGenerationRequest(
        topic="Enterprise API Security Best Practices",
        keywords=["API security", "enterprise", "best practices", "authentication", "authorization"],
        target_audience="Enterprise developers and security teams",
        content_strategy=ContentStrategy.SEO_OPTIMIZED,
        tone=ContentTone.AUTHORITATIVE,
        length=ContentLength.LONG,
        quality_target=ContentQuality.PUBLICATION_READY,
        additional_context={
            "industry": "technology",
            "compliance": ["SOC2", "GDPR", "HIPAA"],
            "audience_level": "expert"
        }
    )
    
    result = await custom_writer.generate_blog(request)
    
    print(f"✅ Custom Enterprise Blog Generated!")
    print(f"📝 Title: {result.title}")
    print(f"📊 SEO Score: {result.seo_score}")
    print(f"📖 Readability Score: {result.readability_score}")
    print(f"⭐ Overall Quality: {result.quality_score}")
    print(f"🔧 Provider: {result.provider_used}")
    
    return result


async def example_batch_generation():
    """Example of batch blog generation."""
    print("\n📦 Batch Generation Example")
    print("=" * 50)
    
    # Create a blog writer
    blog_writer = BlogWriterFactory.create_startup_writer()
    
    # Create multiple blog requests
    requests = [
        BlogGenerationRequest(
            topic="Getting Started with Python",
            keywords=["python", "beginner", "tutorial", "programming"],
            content_strategy=ContentStrategy.EDUCATIONAL,
            tone=ContentTone.FRIENDLY,
            length=ContentLength.MEDIUM,
            quality_target=ContentQuality.GOOD
        ),
        BlogGenerationRequest(
            topic="Advanced Python Techniques",
            keywords=["python", "advanced", "techniques", "optimization"],
            content_strategy=ContentStrategy.TECHNICAL,
            tone=ContentTone.PROFESSIONAL,
            length=ContentLength.LONG,
            quality_target=ContentQuality.EXCELLENT
        ),
        BlogGenerationRequest(
            topic="Python for Data Science",
            keywords=["python", "data science", "pandas", "numpy", "machine learning"],
            content_strategy=ContentStrategy.SEO_OPTIMIZED,
            tone=ContentTone.PROFESSIONAL,
            length=ContentLength.MEDIUM,
            quality_target=ContentQuality.GOOD
        )
    ]
    
    # Generate all blogs concurrently
    results = await blog_writer.generate_blog_batch(requests, max_concurrent=2)
    
    print(f"✅ Generated {len(results)} blogs in batch!")
    
    total_cost = sum(result.cost or 0 for result in results)
    total_tokens = sum(result.tokens_used or 0 for result in results)
    avg_quality = sum(result.quality_score or 0 for result in results) / len(results)
    
    print(f"💰 Total Cost: ${total_cost:.4f}")
    print(f"🔤 Total Tokens: {total_tokens}")
    print(f"⭐ Average Quality: {avg_quality:.2f}")
    
    for i, result in enumerate(results, 1):
        print(f"📝 Blog {i}: {result.title} (Quality: {result.quality_score:.2f})")
    
    return results


async def example_content_optimization():
    """Example of content optimization strategies."""
    print("\n🎯 Content Optimization Example")
    print("=" * 50)
    
    # Create a blog writer
    blog_writer = BlogWriterFactory.create_engagement_focused_writer()
    
    # Generate initial content
    request = BlogGenerationRequest(
        topic="Remote Work Productivity Tips",
        keywords=["remote work", "productivity", "tips", "work from home"],
        content_strategy=ContentStrategy.ENGAGEMENT_FOCUSED,
        tone=ContentTone.CONVERSATIONAL,
        length=ContentLength.MEDIUM,
        quality_target=ContentQuality.GOOD
    )
    
    result = await blog_writer.generate_blog(request)
    
    print(f"✅ Initial Content Generated")
    print(f"📊 Initial Quality Score: {result.quality_score}")
    
    # Optimize the content using different strategies
    content = result.content
    keywords = request.keywords
    
    # SEO Optimization
    seo_optimized = await blog_writer.optimize_existing_content(
        content, keywords, ContentStrategy.SEO_OPTIMIZED
    )
    
    # Engagement Optimization
    engagement_optimized = await blog_writer.optimize_existing_content(
        content, keywords, ContentStrategy.ENGAGEMENT_FOCUSED
    )
    
    # Conversion Optimization
    conversion_optimized = await blog_writer.optimize_existing_content(
        content, keywords, ContentStrategy.CONVERSION_OPTIMIZED
    )
    
    print(f"🎯 Content optimization completed!")
    print(f"📝 Original length: {len(content)} characters")
    print(f"🔍 SEO optimized length: {len(seo_optimized)} characters")
    print(f"💬 Engagement optimized length: {len(engagement_optimized)} characters")
    print(f"💰 Conversion optimized length: {len(conversion_optimized)} characters")
    
    return {
        "original": content,
        "seo_optimized": seo_optimized,
        "engagement_optimized": engagement_optimized,
        "conversion_optimized": conversion_optimized
    }


async def example_quality_assessment():
    """Example of content quality assessment."""
    print("\n📊 Quality Assessment Example")
    print("=" * 50)
    
    # Create a blog writer
    blog_writer = BlogWriterFactory.create_enterprise_writer()
    
    # Sample content to assess
    sample_content = """
    # Python Web Development: A Comprehensive Guide
    
    Python has become one of the most popular programming languages for web development.
    With frameworks like Django and FastAPI, developers can build robust, scalable web applications.
    
    ## Why Choose Python for Web Development?
    
    Python offers several advantages for web development:
    - Easy to learn and read
    - Extensive library ecosystem
    - Strong community support
    - Excellent frameworks
    
    ## Popular Python Web Frameworks
    
    ### Django
    Django is a high-level web framework that encourages rapid development and clean design.
    
    ### FastAPI
    FastAPI is a modern, fast web framework for building APIs with Python 3.7+.
    
    ## Best Practices
    
    When developing web applications with Python, consider these best practices:
    1. Use virtual environments
    2. Follow PEP 8 style guidelines
    3. Write comprehensive tests
    4. Use proper error handling
    """
    
    keywords = ["python", "web development", "django", "fastapi", "best practices"]
    
    # Assess content quality
    quality_metrics = await blog_writer.assess_content_quality(
        sample_content, keywords, ContentQuality.EXCELLENT
    )
    
    print(f"📊 Quality Assessment Results:")
    print(f"📖 Readability Score: {quality_metrics.get('readability_score', 0):.2f}")
    print(f"🔍 SEO Score: {quality_metrics.get('seo_score', 0):.2f}")
    print(f"💬 Engagement Score: {quality_metrics.get('engagement_score', 0):.2f}")
    print(f"⭐ Overall Quality: {quality_metrics.get('overall_quality', 0):.2f}")
    
    recommendations = quality_metrics.get('recommendations', [])
    if recommendations:
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    
    return quality_metrics


async def example_provider_management():
    """Example of AI provider management and monitoring."""
    print("\n🔧 Provider Management Example")
    print("=" * 50)
    
    # Create a blog writer with multiple providers
    blog_writer = BlogWriterFactory.create_custom_writer(
        providers=["openai", "anthropic"],
        strategy=ContentStrategy.SEO_OPTIMIZED,
        quality=ContentQuality.GOOD
    )
    
    # Check provider status
    provider_status = await blog_writer.get_ai_provider_status()
    
    print("🔧 AI Provider Status:")
    for provider_name, status in provider_status.items():
        print(f"   {provider_name}: {status.get('status', 'unknown')}")
        if 'rate_limits' in status:
            print(f"      Rate Limits: {status['rate_limits']}")
    
    # Get generation statistics
    stats = blog_writer.get_generation_statistics()
    
    print(f"\n📊 Generation Statistics:")
    print(f"   Total Blogs Generated: {stats['total_blogs_generated']}")
    print(f"   Success Rate: {stats.get('success_rate', 0):.2%}")
    print(f"   Average Cost per Blog: ${stats.get('average_cost_per_blog', 0):.4f}")
    print(f"   Average Tokens per Blog: {stats.get('average_tokens_per_blog', 0):.0f}")
    print(f"   Average Quality Score: {stats.get('average_quality_score', 0):.2f}")
    
    if stats.get('strategy_usage'):
        print(f"\n🎯 Strategy Usage:")
        for strategy, count in stats['strategy_usage'].items():
            print(f"   {strategy}: {count} times")
    
    if stats.get('provider_usage'):
        print(f"\n🔧 Provider Usage:")
        for provider, count in stats['provider_usage'].items():
            print(f"   {provider}: {count} times")
    
    return provider_status, stats


async def main():
    """Run all examples."""
    print("🚀 Blog Writer Abstraction Layer Examples")
    print("=" * 60)
    
    try:
        # Run all examples
        await example_basic_usage()
        await example_factory_presets()
        await example_builder_pattern()
        await example_batch_generation()
        await example_content_optimization()
        await example_quality_assessment()
        await example_provider_management()
        
        print("\n🎉 All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Set up environment variables for testing
    os.environ.setdefault("OPENAI_API_KEY", "your-openai-key-here")
    os.environ.setdefault("ANTHROPIC_API_KEY", "your-anthropic-key-here")
    
    # Run the examples
    asyncio.run(main())
