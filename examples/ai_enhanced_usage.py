"""
Example demonstrating AI-enhanced blog content generation.

This example shows how to use the BlogWriter SDK with AI providers
for enhanced content generation capabilities.
"""

import asyncio
import os
from dotenv import load_dotenv

from src.blog_writer_sdk import BlogWriter
from src.blog_writer_sdk.models.blog_models import (
    BlogRequest, 
    ContentTone, 
    ContentLength,
    ContentFormat
)
from src.blog_writer_sdk.ai.ai_content_generator import AIContentGenerator, ContentTemplate

# Load environment variables
load_dotenv()


async def main():
    """Demonstrate AI-enhanced blog generation."""
    
    # Configure AI providers
    ai_config = {
        'providers': {}
    }
    
    # Add OpenAI if available
    if os.getenv("OPENAI_API_KEY"):
        ai_config['providers']['openai'] = {
            'api_key': os.getenv("OPENAI_API_KEY"),
            'organization': os.getenv("OPENAI_ORGANIZATION"),
            'default_model': os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini"),
            'enabled': True,
            'priority': 1
        }
        print("✅ OpenAI provider configured")
    
    # Add Anthropic if available
    if os.getenv("ANTHROPIC_API_KEY"):
        ai_config['providers']['anthropic'] = {
            'api_key': os.getenv("ANTHROPIC_API_KEY"),
            'default_model': os.getenv("ANTHROPIC_DEFAULT_MODEL", "claude-3-5-haiku-20241022"),
            'enabled': True,
            'priority': 2
        }
        print("✅ Anthropic provider configured")
    
    if not ai_config['providers']:
        print("❌ No AI providers configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY")
        print("💡 Falling back to traditional content generation")
        ai_generator = None
    else:
        # Initialize AI content generator
        ai_generator = AIContentGenerator(config=ai_config)
        print(f"🤖 AI Content Generator initialized with {len(ai_config['providers'])} providers")
    
    # Initialize BlogWriter with AI enhancement
    blog_writer = BlogWriter(
        default_tone=ContentTone.PROFESSIONAL,
        default_length=ContentLength.MEDIUM,
        enable_seo_optimization=True,
        enable_quality_analysis=True,
        ai_content_generator=ai_generator,
        enable_ai_enhancement=ai_generator is not None,
    )
    
    print(f"\n📝 BlogWriter initialized with AI enhancement: {blog_writer.enable_ai_enhancement}")
    
    # Example 1: Generate a how-to guide
    print("\n" + "="*60)
    print("🎯 Example 1: AI-Enhanced How-To Guide")
    print("="*60)
    
    how_to_request = BlogRequest(
        topic="How to Build a Python REST API with FastAPI",
        keywords=[
            "FastAPI tutorial",
            "Python REST API",
            "web development",
            "API documentation",
            "async Python"
        ],
        tone=ContentTone.INSTRUCTIONAL,
        length=ContentLength.LONG,
        target_audience="Python developers",
        custom_instructions="Include code examples and best practices. Focus on practical implementation.",
        include_faq=True,
        include_toc=True
    )
    
    try:
        result = await blog_writer.generate(how_to_request)
        
        print(f"✅ Generated blog post: '{result.blog_post.title}'")
        print(f"📊 Word count: {result.blog_post.word_count}")
        print(f"⏱️ Generation time: {result.generation_time:.2f}s")
        print(f"🎯 SEO score: {result.seo_analysis.overall_score}/100")
        
        if blog_writer.enable_ai_enhancement:
            print(f"🤖 AI-enhanced generation used")
        
        # Show first 200 characters of content
        content_preview = result.blog_post.content[:200] + "..." if len(result.blog_post.content) > 200 else result.blog_post.content
        print(f"\n📄 Content preview:\n{content_preview}")
        
    except Exception as e:
        print(f"❌ Error generating how-to guide: {e}")
    
    # Example 2: Generate a comparison article
    print("\n" + "="*60)
    print("🎯 Example 2: AI-Enhanced Comparison Article")
    print("="*60)
    
    comparison_request = BlogRequest(
        topic="FastAPI vs Django vs Flask: Python Web Framework Comparison",
        keywords=[
            "FastAPI vs Django",
            "Python web frameworks",
            "Flask comparison",
            "web development",
            "framework performance"
        ],
        tone=ContentTone.ANALYTICAL,
        length=ContentLength.EXTENDED,
        target_audience="Web developers choosing a Python framework",
        custom_instructions="Create detailed comparison with pros/cons, performance metrics, and use case recommendations.",
        include_faq=True,
        include_toc=True
    )
    
    try:
        result = await blog_writer.generate(comparison_request)
        
        print(f"✅ Generated comparison: '{result.blog_post.title}'")
        print(f"📊 Word count: {result.blog_post.word_count}")
        print(f"⏱️ Generation time: {result.generation_time:.2f}s")
        print(f"🎯 SEO score: {result.seo_analysis.overall_score}/100")
        
        # Show meta description
        print(f"\n🏷️ Meta description: {result.blog_post.meta_description}")
        
    except Exception as e:
        print(f"❌ Error generating comparison article: {e}")
    
    # Example 3: Test individual AI components
    if ai_generator:
        print("\n" + "="*60)
        print("🎯 Example 3: Individual AI Component Testing")
        print("="*60)
        
        try:
            # Test title generation
            print("\n🏷️ Testing AI title generation...")
            title_response = await ai_generator.generate_title(
                topic="Python Machine Learning for Beginners",
                content="This comprehensive guide covers the fundamentals of machine learning using Python...",
                keywords=["Python machine learning", "ML tutorial", "beginner guide"],
                tone=ContentTone.FRIENDLY
            )
            print(f"Generated title: {title_response.content}")
            print(f"Provider used: {title_response.provider}")
            print(f"Tokens used: {title_response.tokens_used}")
            print(f"Cost: ${title_response.cost:.6f}")
            
            # Test FAQ generation
            print("\n❓ Testing AI FAQ generation...")
            faq_response = await ai_generator.generate_faq_section(
                topic="Python Machine Learning for Beginners",
                keywords=["Python machine learning", "ML tutorial", "scikit-learn"],
                num_questions=3
            )
            print(f"Generated FAQ (first 300 chars): {faq_response.content[:300]}...")
            print(f"Provider used: {faq_response.provider}")
            
            # Show generation statistics
            print("\n📊 AI Generation Statistics:")
            stats = ai_generator.get_generation_stats()
            for key, value in stats.items():
                print(f"  {key}: {value}")
            
        except Exception as e:
            print(f"❌ Error testing AI components: {e}")
    
    # Example 4: Provider health check
    if ai_generator:
        print("\n" + "="*60)
        print("🎯 Example 4: AI Provider Health Check")
        print("="*60)
        
        try:
            health_results = await ai_generator.get_provider_health()
            
            for provider_name, health_info in health_results.items():
                status_emoji = "✅" if health_info["status"] == "healthy" else "❌"
                print(f"{status_emoji} {provider_name}: {health_info['status']}")
                
                if "api_key_valid" in health_info:
                    key_emoji = "🔑" if health_info["api_key_valid"] else "🚫"
                    print(f"  {key_emoji} API Key Valid: {health_info['api_key_valid']}")
                
                if "rate_limits" in health_info:
                    print(f"  📊 Rate Limits: {health_info['rate_limits']}")
        
        except Exception as e:
            print(f"❌ Error checking provider health: {e}")
    
    print("\n" + "="*60)
    print("🎉 AI-Enhanced Blog Generation Demo Complete!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
