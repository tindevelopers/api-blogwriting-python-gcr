#!/usr/bin/env python3
"""Test DataForSEO SERP API to inspect actual response structure."""

import os
import json
import base64
import httpx
import asyncio

async def test_serp_api_response():
    """Test DataForSEO SERP API directly to see response structure."""
    
    # Get credentials
    api_key = os.getenv("DATAFORSEO_API_KEY", "").strip()
    api_secret = os.getenv("DATAFORSEO_API_SECRET", "").strip()
    
    if not api_key or not api_secret:
        print("❌ DATAFORSEO_API_KEY and DATAFORSEO_API_SECRET must be set")
        print("   Set them in your environment or .env file")
        return
    
    base_url = "https://api.dataforseo.com/v3"
    credentials = f"{api_key}:{api_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/json"
    }
    
    print("="*80)
    print("Testing DataForSEO SERP Organic Live Advanced API")
    print("="*80)
    print()
    
    # Test SERP Organic endpoint (same as used in code)
    payload = [{
        "keyword": "plumbers in miami",
        "location_name": "United States",
        "language_code": "en",
        "depth": 10,
        "people_also_ask_click_depth": 2
    }]
    
    url = f"{base_url}/serp/google/organic/live/advanced"
    
    try:
        print(f"📡 Calling: {url}")
        print(f"📦 Payload: {json.dumps(payload, indent=2)}")
        print()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            print(f"✅ HTTP Status: {response.status_code}")
            print(f"📊 Response Type: {type(data)}")
            print()
            
            if isinstance(data, dict):
                print("="*80)
                print("RESPONSE STRUCTURE ANALYSIS")
                print("="*80)
                print()
                
                print(f"Top-level keys: {list(data.keys())}")
                print(f"Status Code: {data.get('status_code')}")
                print(f"Status Message: {data.get('status_message')}")
                print(f"Tasks Count: {data.get('tasks_count')}")
                print(f"Tasks Error: {data.get('tasks_error')}")
                print()
                
                tasks = data.get("tasks")
                print(f"Tasks Type: {type(tasks)}")
                print(f"Tasks is None: {tasks is None}")
                
                if isinstance(tasks, list) and len(tasks) > 0:
                    print(f"Tasks Length: {len(tasks)}")
                    first_task = tasks[0]
                    print(f"\nFirst Task Type: {type(first_task)}")
                    
                    if isinstance(first_task, dict):
                        print(f"First Task Keys: {list(first_task.keys())}")
                        print(f"Task Status Code: {first_task.get('status_code')}")
                        print(f"Task Status Message: {first_task.get('status_message')}")
                        print()
                        
                        result = first_task.get("result")
                        print(f"Result Type: {type(result)}")
                        print(f"Result is None: {result is None}")
                        
                        if result is None:
                            print("⚠️  RESULT IS NONE - This explains empty arrays!")
                        elif isinstance(result, list):
                            print(f"Result Length: {len(result)}")
                            if len(result) > 0:
                                print(f"First Result Item Type: {type(result[0])}")
                                if isinstance(result[0], dict):
                                    print(f"First Result Item Keys: {list(result[0].keys())[:20]}")
                                    if "items" in result[0]:
                                        items = result[0]["items"]
                                        print(f"Items Type: {type(items)}")
                                        print(f"Items Length: {len(items) if isinstance(items, list) else 'N/A'}")
                                        if isinstance(items, list) and len(items) > 0:
                                            print(f"First Item Type: {type(items[0])}")
                                            if isinstance(items[0], dict):
                                                print(f"First Item Keys: {list(items[0].keys())[:15]}")
                                                print(f"First Item Type Field: {items[0].get('type', 'N/A')}")
                        elif isinstance(result, dict):
                            print(f"Result Keys: {list(result.keys())[:20]}")
                            if "items" in result:
                                items = result["items"]
                                print(f"Items Type: {type(items)}")
                                print(f"Items Length: {len(items) if isinstance(items, list) else 'N/A'}")
                                if isinstance(items, list) and len(items) > 0:
                                    print(f"First Item Type: {type(items[0])}")
                                    if isinstance(items[0], dict):
                                        print(f"First Item Keys: {list(items[0].keys())[:15]}")
                                        print(f"First Item Type Field: {items[0].get('type', 'N/A')}")
                
                print()
                print("="*80)
                print("FULL RESPONSE (first 3000 chars)")
                print("="*80)
                response_str = json.dumps(data, indent=2, default=str)
                print(response_str[:3000])
                if len(response_str) > 3000:
                    print(f"\n... (truncated, total length: {len(response_str)} chars)")
                    print("\n💡 Tip: Check if 'result' is None or empty")
                    print("💡 Tip: Check if 'items' array exists and has data")
            else:
                print(f"\n⚠️  Unexpected response type: {type(data)}")
                print(f"Response: {str(data)[:500]}")
                
    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text[:500]}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_serp_api_response())

