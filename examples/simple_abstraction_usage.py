"""
Simple Blog Writer Abstraction Layer Usage

This example shows the simplest way to use the new Blog Writer abstraction layer.
Perfect for getting started quickly.
"""

import asyncio
import os
from src.blog_writer_sdk.ai import (
    BlogWriterFactory,
    BlogGenerationRequest,
    ContentStrategy,
    ContentQuality,
    ContentTone,
    ContentLength
)


async def simple_blog_generation():
    """Generate a simple blog post using the abstraction layer."""
    
    # Create a blog writer (easiest way)
    blog_writer = BlogWriterFactory.create_seo_focused_writer()
    
    # Create a simple request
    request = BlogGenerationRequest(
        topic="Getting Started with Python Programming",
        keywords=["python", "programming", "beginner", "tutorial"],
        content_strategy=ContentStrategy.SEO_OPTIMIZED,
        tone=ContentTone.FRIENDLY,
        length=ContentLength.MEDIUM,
        quality_target=ContentQuality.GOOD
    )
    
    # Generate the blog
    result = await blog_writer.generate_blog(request)
    
    # Display results
    print("🎉 Blog Generated Successfully!")
    print(f"📝 Title: {result.title}")
    print(f"📊 Quality Score: {result.quality_score:.2f}")
    print(f"💰 Cost: ${result.cost:.4f}")
    print(f"⏱️ Time: {result.generation_time:.2f}s")
    
    return result


async def main():
    """Main function to run the example."""
    print("🚀 Simple Blog Writer Abstraction Example")
    print("=" * 50)
    
    try:
        result = await simple_blog_generation()
        print("\n✅ Example completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("💡 Make sure you have set up your AI provider API keys!")


if __name__ == "__main__":
    asyncio.run(main())
