"""
Example usage of the Blog Writer SDK with DataForSEO integration.

This script demonstrates how to use real SEO data from DataForSEO
to enhance keyword analysis and content strategy.
"""

import asyncio
from src.blog_writer_sdk.integrations.dataforseo_integration import (
    DataForSEOClient,
    EnhancedKeywordAnalyzer
)


async def main():
    """Demonstrate DataForSEO integration capabilities."""
    print("🔍 Blog Writer SDK - DataForSEO Integration Example")
    print("=" * 60)
    
    # Initialize enhanced keyword analyzer
    analyzer = EnhancedKeywordAnalyzer(
        use_dataforseo=True,
        location="United States"
    )
    
    # Example keywords to analyze
    keywords = [
        "content marketing",
        "SEO optimization", 
        "blog writing tools",
        "AI content creation",
        "digital marketing strategy"
    ]
    
    print(f"\n📊 Analyzing {len(keywords)} keywords with enhanced metrics...")
    print("-" * 50)
    
    # Perform comprehensive keyword analysis
    results = await analyzer.analyze_keywords_comprehensive(keywords)
    
    # Display results
    for keyword, analysis in results.items():
        print(f"\n🔑 Keyword: '{keyword}'")
        print(f"   📈 Search Volume: {analysis.search_volume:,}" if analysis.search_volume else "   📈 Search Volume: Not available")
        print(f"   🎯 Difficulty: {analysis.difficulty.value}")
        print(f"   💰 Competition: {analysis.competition:.2f}")
        print(f"   💵 CPC: ${analysis.cpc:.2f}" if analysis.cpc else "   💵 CPC: Not available")
        print(f"   📊 Trend Score: {analysis.trend_score:.2f}")
        print(f"   ✅ Recommended: {'Yes' if analysis.recommended else 'No'}")
        print(f"   💡 Reason: {analysis.reason}")
        
        if analysis.related_keywords:
            print(f"   🔗 Related: {', '.join(analysis.related_keywords[:3])}")
    
    # Generate content strategy
    print(f"\n🎯 Generating Content Strategy...")
    print("-" * 50)
    
    competitor_domains = ["contentmarketinginstitute.com", "hubspot.com", "moz.com"]
    
    strategy = await analyzer.get_content_strategy(
        primary_keywords=keywords[:3],  # Use top 3 keywords
        competitor_domains=competitor_domains
    )
    
    print(f"\n📋 Content Strategy Recommendations:")
    
    if strategy["primary_keywords"]:
        print(f"\n🎯 Primary Keywords (High Priority):")
        for item in strategy["primary_keywords"]:
            print(f"   • {item['keyword']} - {item['reason']}")
    
    if strategy["supporting_keywords"]:
        print(f"\n🔧 Supporting Keywords (Medium Priority):")
        for item in strategy["supporting_keywords"]:
            print(f"   • {item['keyword']} - {item['reason']}")
    
    # Demonstrate DataForSEO client directly
    print(f"\n🔬 Direct DataForSEO Analysis...")
    print("-" * 50)
    
    dataforseo_client = DataForSEOClient(location="United States")
    
    # Get search volume data
    search_data = await dataforseo_client.get_search_volume_data(keywords[:3])
    print(f"\n📊 Search Volume Analysis:")
    for keyword, data in search_data.items():
        volume = data.get("search_volume", "N/A")
        competition = data.get("competition", 0)
        print(f"   • {keyword}: {volume:,} searches/month, {competition:.1%} competition" if isinstance(volume, int) else f"   • {keyword}: {volume} searches/month, {competition:.1%} competition")
    
    # Get keyword difficulty
    difficulty_data = await dataforseo_client.get_keyword_difficulty(keywords[:3])
    print(f"\n🎯 Keyword Difficulty Scores:")
    for keyword, difficulty in difficulty_data.items():
        print(f"   • {keyword}: {difficulty:.0f}/100 difficulty")
    
    # Analyze competitor keywords
    print(f"\n🕵️ Competitor Analysis...")
    competitor_keywords = await dataforseo_client.get_competitor_keywords(
        domain="hubspot.com",
        limit=10
    )
    
    if competitor_keywords:
        print(f"   Top competitor keywords:")
        for kw_data in competitor_keywords[:5]:
            print(f"   • {kw_data.get('keyword', 'N/A')}")
    else:
        print("   No competitor data available (requires DataForSEO API)")
    
    # Content gap analysis
    print(f"\n🔍 Content Gap Analysis...")
    gaps = await dataforseo_client.analyze_content_gaps(
        primary_keyword="content marketing",
        competitor_domains=competitor_domains[:2]
    )
    
    print(f"   Identified {len(gaps.get('opportunities', []))} content opportunities")
    print(f"   Found {len(gaps.get('missing_keywords', []))} missing keyword targets")
    
    print(f"\n✨ Analysis Complete!")
    print(f"\n💡 Next Steps:")
    print(f"   1. Set up DataForSEO API credentials for real data")
    print(f"   2. Integrate MCP DataForSEO tools for live metrics")
    print(f"   3. Use insights to create targeted content")
    print(f"   4. Monitor keyword performance over time")


async def demonstrate_mcp_integration():
    """
    Demonstrate how to integrate with MCP DataForSEO tools.
    
    This shows the structure for real API integration.
    """
    print(f"\n🔌 MCP DataForSEO Integration Structure")
    print("-" * 50)
    
    # Example of how MCP tool integration would work
    example_keywords = ["content marketing", "SEO tools"]
    
    print(f"📋 To get real data, you would use MCP tools like:")
    print(f"")
    print(f"   # Search Volume Data")
    print(f"   mcp_dataforseo_keywords_data_google_ads_search_volume(")
    print(f"       keywords={example_keywords},")
    print(f"       language_code='en',")
    print(f"       location_name='United States'")
    print(f"   )")
    print(f"")
    print(f"   # Keyword Difficulty")
    print(f"   mcp_dataforseo_dataforseo_labs_bulk_keyword_difficulty(")
    print(f"       keywords={example_keywords},")
    print(f"       language_code='en',")
    print(f"       location_name='United States'")
    print(f"   )")
    print(f"")
    print(f"   # SERP Analysis")
    print(f"   mcp_dataforseo_serp_organic_live_advanced(")
    print(f"       keyword='content marketing',")
    print(f"       language_code='en',")
    print(f"       location_name='United States',")
    print(f"       depth=10")
    print(f"   )")
    print(f"")
    print(f"   # Competitor Keywords")
    print(f"   mcp_dataforseo_dataforseo_labs_google_ranked_keywords(")
    print(f"       target='hubspot.com',")
    print(f"       language_code='en',")
    print(f"       location_name='United States',")
    print(f"       limit=50")
    print(f"   )")
    
    print(f"\n🔧 Integration Benefits:")
    print(f"   ✅ Real search volume data")
    print(f"   ✅ Accurate keyword difficulty scores")
    print(f"   ✅ Live SERP analysis")
    print(f"   ✅ Competitor keyword research")
    print(f"   ✅ Trend analysis and forecasting")
    print(f"   ✅ Content gap identification")


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(demonstrate_mcp_integration())
