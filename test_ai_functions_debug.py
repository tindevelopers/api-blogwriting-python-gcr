#!/usr/bin/env python3
"""
Debug test to check if DataForSEO AI functions are actually returning data.
Tests with various keywords to see which ones have data.
"""

import json
import subprocess
import sys

BASE_URL = "https://blog-writer-api-dev-kq42l26tuq-od.a.run.app"

def test_keyword(keyword, test_name):
    """Test a keyword and return results."""
    print(f"\n{'='*80}")
    print(f"Testing: {test_name}")
    print(f"Keyword: {keyword}")
    print(f"{'='*80}")
    
    payload = {
        "target": keyword,
        "target_type": "keyword",
        "location": "United States",
        "language": "en",
        "platform": "chat_gpt",
        "limit": 10
    }
    
    try:
        result = subprocess.run(
            ['curl', '-s', '-X', 'POST', 
             f'{BASE_URL}/api/v1/keywords/ai-mentions',
             '-H', 'Content-Type: application/json',
             '-d', json.dumps(payload),
             '--max-time', '60'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            mentions = data.get('llm_mentions', {})
            
            print(f"\nResults:")
            print(f"  - AI Search Volume: {mentions.get('ai_search_volume', 0):,}")
            print(f"  - Mentions Count: {mentions.get('mentions_count', 0):,}")
            print(f"  - Top Pages: {len(mentions.get('top_pages', []))}")
            print(f"  - Top Domains: {len(mentions.get('top_domains', []))}")
            print(f"  - Topics: {len(mentions.get('topics', []))}")
            
            # Show first few top pages if available
            top_pages = mentions.get('top_pages', [])
            if top_pages:
                print(f"\n  Top Pages (first 3):")
                for i, page in enumerate(top_pages[:3], 1):
                    print(f"    {i}. {page.get('title', 'N/A')[:60]}")
                    print(f"       URL: {page.get('url', 'N/A')[:80]}")
                    print(f"       Mentions: {page.get('mentions', 0)}")
            
            return {
                'keyword': keyword,
                'ai_search_volume': mentions.get('ai_search_volume', 0),
                'mentions_count': mentions.get('mentions_count', 0),
                'has_data': mentions.get('ai_search_volume', 0) > 0 or mentions.get('mentions_count', 0) > 0
            }
        else:
            print(f"❌ Error: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def main():
    """Test multiple keywords to find ones with data."""
    print("\n" + "="*80)
    print("DATAFORSEO AI FUNCTIONS DEBUG TEST")
    print("="*80)
    print(f"\nTesting various keywords to find which ones have AI search volume/mentions data")
    
    # Test keywords that should have high AI search volume
    test_keywords = [
        ("chatgpt", "ChatGPT (AI tool)"),
        ("openai", "OpenAI (company)"),
        ("artificial intelligence", "AI (general term)"),
        ("machine learning", "Machine Learning"),
        ("python programming", "Python (programming)"),
        ("javascript", "JavaScript"),
        ("web development", "Web Development"),
        ("seo", "SEO"),
        ("digital marketing", "Digital Marketing"),
        ("google", "Google (company)"),
        ("apple", "Apple (company)"),
        ("microsoft", "Microsoft (company)"),
    ]
    
    results = []
    for keyword, name in test_keywords:
        result = test_keyword(keyword, name)
        if result:
            results.append(result)
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    keywords_with_data = [r for r in results if r['has_data']]
    keywords_without_data = [r for r in results if not r['has_data']]
    
    print(f"\n✅ Keywords WITH data: {len(keywords_with_data)}")
    for r in keywords_with_data:
        print(f"  - {r['keyword']}: AI Volume={r['ai_search_volume']:,}, Mentions={r['mentions_count']:,}")
    
    print(f"\n❌ Keywords WITHOUT data: {len(keywords_without_data)}")
    for r in keywords_without_data[:5]:  # Show first 5
        print(f"  - {r['keyword']}")
    
    if len(keywords_without_data) > 5:
        print(f"  ... and {len(keywords_without_data) - 5} more")
    
    if keywords_with_data:
        print(f"\n✅ SUCCESS: Found {len(keywords_with_data)} keywords with AI data!")
        print(f"   The API is working - some keywords just don't have data.")
    else:
        print(f"\n⚠️  WARNING: No keywords returned data.")
        print(f"   This could indicate:")
        print(f"   1. DataForSEO API credentials not configured")
        print(f"   2. API endpoint returning errors (check logs)")
        print(f"   3. DataForSEO doesn't have data for these keywords")
    
    return 0 if keywords_with_data else 1

if __name__ == "__main__":
    sys.exit(main())

