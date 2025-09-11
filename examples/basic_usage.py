"""
Basic usage example for the Blog Writer SDK.

This script demonstrates how to use the SDK to generate
and analyze blog content.
"""

import asyncio
from src.blog_writer_sdk import BlogWriter
from src.blog_writer_sdk.models.blog_models import (
    BlogRequest,
    ContentTone,
    ContentLength,
)


async def main():
    """Main example function."""
    print("🚀 Blog Writer SDK - Basic Usage Example")
    print("=" * 50)
    
    # Initialize the blog writer
    writer = BlogWriter(
        enable_seo_optimization=True,
        enable_quality_analysis=True,
    )
    
    # Example 1: Generate a blog post
    print("\n📝 Example 1: Generating a blog post")
    print("-" * 30)
    
    request = BlogRequest(
        topic="The Future of Remote Work",
        keywords=["remote work", "digital nomad", "work from home", "productivity"],
        tone=ContentTone.PROFESSIONAL,
        length=ContentLength.MEDIUM,
        focus_keyword="remote work",
        include_faq=True,
        include_toc=True,
    )
    
    result = await writer.generate(request)
    
    if result.success:
        print(f"✅ Blog post generated successfully!")
        print(f"📊 Title: {result.blog_post.title}")
        print(f"📊 Word count: {result.word_count}")
        print(f"📊 SEO score: {result.seo_score:.1f}/100")
        print(f"📊 Readability score: {result.readability_score:.1f}/100")
        print(f"⏱️  Generation time: {result.generation_time_seconds:.2f} seconds")
        
        if result.suggestions:
            print(f"\n💡 Suggestions:")
            for suggestion in result.suggestions[:3]:  # Show first 3 suggestions
                print(f"   • {suggestion}")
        
        # Show excerpt of the content
        content_preview = result.blog_post.content[:200] + "..."
        print(f"\n📄 Content preview:\n{content_preview}")
        
    else:
        print(f"❌ Generation failed: {result.error_message}")
    
    # Example 2: Analyze existing content
    print("\n\n🔍 Example 2: Analyzing existing content")
    print("-" * 30)
    
    sample_content = """
    # The Benefits of Remote Work
    
    Remote work has become increasingly popular in recent years.
    Many companies are now offering flexible work arrangements
    to attract and retain top talent.
    
    ## Increased Productivity
    
    Studies show that remote workers are often more productive
    than their office-based counterparts. This is due to fewer
    distractions and the ability to work in a comfortable environment.
    
    ## Better Work-Life Balance
    
    Remote work allows employees to better balance their personal
    and professional lives. This leads to higher job satisfaction
    and reduced burnout.
    """
    
    analysis_result = await writer.analyze_existing_content(
        content=sample_content,
        title="The Benefits of Remote Work"
    )
    
    if analysis_result.success:
        print(f"✅ Content analyzed successfully!")
        print(f"📊 SEO score: {analysis_result.seo_score:.1f}/100")
        print(f"📊 Readability score: {analysis_result.readability_score:.1f}/100")
        print(f"📊 Word count: {analysis_result.word_count}")
        
        if analysis_result.suggestions:
            print(f"\n💡 Improvement suggestions:")
            for suggestion in analysis_result.suggestions[:3]:
                print(f"   • {suggestion}")
    else:
        print(f"❌ Analysis failed: {analysis_result.error_message}")
    
    # Example 3: Keyword analysis
    print("\n\n🔑 Example 3: Keyword analysis")
    print("-" * 30)
    
    keywords_to_analyze = ["remote work", "digital transformation", "productivity tools"]
    
    for keyword in keywords_to_analyze:
        analysis = await writer.keyword_analyzer.analyze_keyword(keyword)
        print(f"📈 Keyword: '{keyword}'")
        print(f"   Difficulty: {analysis.difficulty.value}")
        print(f"   Recommended: {'Yes' if analysis.recommended else 'No'}")
        if analysis.reason:
            print(f"   Reason: {analysis.reason}")
        print()
    
    # Example 4: Extract keywords from content
    print("\n🎯 Example 4: Extract keywords from content")
    print("-" * 30)
    
    extracted_keywords = await writer.keyword_analyzer.extract_keywords_from_content(
        sample_content, max_keywords=10
    )
    
    print("📝 Extracted keywords:")
    for i, keyword in enumerate(extracted_keywords[:5], 1):
        print(f"   {i}. {keyword}")
    
    print(f"\n🎉 Example completed successfully!")
    print("💡 Try modifying the parameters to see different results.")


if __name__ == "__main__":
    asyncio.run(main())
