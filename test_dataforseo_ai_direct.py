#!/usr/bin/env python3
"""Test DataForSEO AI Optimization endpoints directly to inspect response structure."""

import os
import json
import base64
import httpx
import asyncio

async def test_ai_search_volume():
    """Test AI Search Volume endpoint."""
    print("="*80)
    print("Testing AI Search Volume Endpoint")
    print("="*80)
    
    api_key = os.getenv("DATAFORSEO_API_KEY", "").strip()
    api_secret = os.getenv("DATAFORSEO_API_SECRET", "").strip()
    
    if not api_key or not api_secret:
        print("❌ DATAFORSEO_API_KEY and DATAFORSEO_API_SECRET must be set")
        return None
    
    base_url = "https://api.dataforseo.com/v3"
    credentials = f"{api_key}:{api_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/json"
    }
    
    payload = [{
        "keywords": ["chatgpt", "artificial intelligence", "machine learning"],
        "location_name": "United States",
        "language_code": "en"
    }]
    
    url = f"{base_url}/keywords_data/ai_optimization/search_volume/live"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            print(f"\n✅ HTTP Status: {response.status_code}")
            print(f"\nResponse Structure:")
            print(f"  - Status Code: {data.get('status_code')}")
            print(f"  - Status Message: {data.get('status_message')}")
            print(f"  - Tasks Count: {data.get('tasks_count')}")
            
            tasks = data.get("tasks", [])
            if tasks:
                task = tasks[0]
                print(f"\nTask Structure:")
                print(f"  - Task Status Code: {task.get('status_code')}")
                print(f"  - Task Status Message: {task.get('status_message')}")
                
                result = task.get("result", [])
                print(f"  - Result Count: {len(result)}")
                
                if result:
                    print(f"\nFirst Result Item Structure:")
                    first_item = result[0]
                    print(f"  - Keys: {list(first_item.keys())}")
                    
                    # Check for keyword
                    keyword = first_item.get("keyword", "N/A")
                    print(f"  - Keyword: {keyword}")
                    
                    # Check for keyword_data structure
                    keyword_data = first_item.get("keyword_data", {})
                    if keyword_data:
                        print(f"  - keyword_data keys: {list(keyword_data.keys())}")
                        keyword_info = keyword_data.get("keyword_info", {})
                        if keyword_info:
                            print(f"  - keyword_info keys: {list(keyword_info.keys())}")
                            print(f"  - ai_search_volume: {keyword_info.get('ai_search_volume', 'N/A')}")
                            print(f"  - monthly_searches: {len(keyword_info.get('monthly_searches', []))} items")
                    
                    # Check direct fields
                    if "ai_search_volume" in first_item:
                        print(f"  - Direct ai_search_volume: {first_item.get('ai_search_volume')}")
                    
                    print(f"\nFull First Item:")
                    print(json.dumps(first_item, indent=2, default=str)[:1000])
            
            return data
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_llm_mentions():
    """Test LLM Mentions endpoint."""
    print("\n\n" + "="*80)
    print("Testing LLM Mentions Endpoint")
    print("="*80)
    
    api_key = os.getenv("DATAFORSEO_API_KEY", "").strip()
    api_secret = os.getenv("DATAFORSEO_API_SECRET", "").strip()
    
    if not api_key or not api_secret:
        print("❌ DATAFORSEO_API_KEY and DATAFORSEO_API_SECRET must be set")
        return None
    
    base_url = "https://api.dataforseo.com/v3"
    credentials = f"{api_key}:{api_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/json"
    }
    
    payload = [{
        "target": [{"keyword": "chatgpt"}],
        "location_name": "United States",
        "language_code": "en",
        "platform": "chat_gpt",
        "limit": 10
    }]
    
    url = f"{base_url}/ai_optimization/llm_mentions/search/live"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            print(f"\n✅ HTTP Status: {response.status_code}")
            print(f"\nResponse Structure:")
            print(f"  - Status Code: {data.get('status_code')}")
            print(f"  - Status Message: {data.get('status_message')}")
            print(f"  - Tasks Count: {data.get('tasks_count')}")
            
            tasks = data.get("tasks", [])
            if tasks:
                task = tasks[0]
                print(f"\nTask Structure:")
                print(f"  - Task Status Code: {task.get('status_code')}")
                print(f"  - Task Status Message: {task.get('status_message')}")
                
                result = task.get("result", [])
                print(f"  - Result Count: {len(result)}")
                
                if result:
                    print(f"\nFirst Result Item Structure:")
                    first_item = result[0]
                    print(f"  - Keys: {list(first_item.keys())}")
                    
                    # Check for aggregated_metrics
                    aggregated_metrics = first_item.get("aggregated_metrics", {})
                    if aggregated_metrics:
                        print(f"  - aggregated_metrics keys: {list(aggregated_metrics.keys())}")
                        print(f"  - ai_search_volume: {aggregated_metrics.get('ai_search_volume', 'N/A')}")
                        print(f"  - mentions_count: {aggregated_metrics.get('mentions_count', 'N/A')}")
                    
                    # Check for items (top pages)
                    items = first_item.get("items", [])
                    print(f"  - items (top pages) count: {len(items)}")
                    
                    if items:
                        print(f"\nFirst Top Page:")
                        first_page = items[0]
                        print(f"  - Keys: {list(first_page.keys())}")
                        print(f"  - URL: {first_page.get('url', 'N/A')[:80]}")
                        print(f"  - Title: {first_page.get('title', 'N/A')[:60]}")
                        print(f"  - Mentions: {first_page.get('mentions_count', 'N/A')}")
                    
                    print(f"\nFull First Item (first 1500 chars):")
                    print(json.dumps(first_item, indent=2, default=str)[:1500])
            
            return data
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("DATAFORSEO AI OPTIMIZATION ENDPOINTS DIRECT TEST")
    print("="*80)
    
    # Check if credentials are available
    api_key = os.getenv("DATAFORSEO_API_KEY", "").strip()
    api_secret = os.getenv("DATAFORSEO_API_SECRET", "").strip()
    
    if not api_key or not api_secret:
        print("\n⚠️  DATAFORSEO_API_KEY and DATAFORSEO_API_SECRET not found in environment")
        print("   These need to be set to test the API directly.")
        print("   The API is being called from Cloud Run, but we can't test locally without credentials.")
        return
    
    # Test AI Search Volume
    ai_volume_data = await test_ai_search_volume()
    
    # Test LLM Mentions
    llm_mentions_data = await test_llm_mentions()
    
    # Summary
    print("\n\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    if ai_volume_data:
        tasks = ai_volume_data.get("tasks", [])
        if tasks and tasks[0].get("result"):
            result = tasks[0]["result"]
            print(f"\n✅ AI Search Volume: Got {len(result)} results")
            if result:
                first = result[0]
                keyword_data = first.get("keyword_data", {})
                keyword_info = keyword_data.get("keyword_info", {}) if keyword_data else {}
                ai_vol = keyword_info.get("ai_search_volume", 0)
                print(f"   First keyword AI volume: {ai_vol:,}")
        else:
            print(f"\n⚠️  AI Search Volume: No results returned")
    
    if llm_mentions_data:
        tasks = llm_mentions_data.get("tasks", [])
        if tasks and tasks[0].get("result"):
            result = tasks[0]["result"]
            print(f"\n✅ LLM Mentions: Got {len(result)} results")
            if result:
                first = result[0]
                metrics = first.get("aggregated_metrics", {})
                mentions = metrics.get("mentions_count", 0)
                items = first.get("items", [])
                print(f"   Mentions count: {mentions:,}")
                print(f"   Top pages: {len(items)}")
        else:
            print(f"\n⚠️  LLM Mentions: No results returned")

if __name__ == "__main__":
    asyncio.run(main())

