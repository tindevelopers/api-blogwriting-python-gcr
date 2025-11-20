#!/usr/bin/env python3
"""Test DataForSEO endpoints directly via HTTP to inspect response structure."""

import os
import json
import base64
import httpx
import asyncio

async def test_dataforseo_endpoint():
    """Test DataForSEO API directly."""
    
    # Get credentials
    api_key = os.getenv("DATAFORSEO_API_KEY", "").strip()
    api_secret = os.getenv("DATAFORSEO_API_SECRET", "").strip()
    
    if not api_key or not api_secret:
        print("❌ DATAFORSEO_API_KEY and DATAFORSEO_API_SECRET must be set")
        return
    
    base_url = "https://api.dataforseo.com/v3"
    credentials = f"{api_key}:{api_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/json"
    }
    
    # Test Related Keywords
    print("="*80)
    print("Testing Related Keywords Endpoint")
    print("="*80)
    
    payload = [{
        "keyword": "pet grooming",
        "depth": 1,
        "location_name": "United States",
        "language_code": "en",
        "limit": 5
    }]
    
    url = f"{base_url}/dataforseo_labs/google/related_keywords/live"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            print(f"\n✅ HTTP Status: {response.status_code}")
            print(f"\nResponse Type: {type(data)}")
            print(f"Response Keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
            
            if isinstance(data, dict):
                print(f"\nStatus Code: {data.get('status_code')}")
                print(f"Status Message: {data.get('status_message')}")
                print(f"Tasks Count: {data.get('tasks_count')}")
                print(f"Tasks Error: {data.get('tasks_error')}")
                
                tasks = data.get("tasks")
                print(f"\nTasks Type: {type(tasks)}")
                print(f"Tasks is None: {tasks is None}")
                
                if isinstance(tasks, list) and len(tasks) > 0:
                    first_task = tasks[0]
                    print(f"\nFirst Task Type: {type(first_task)}")
                    print(f"First Task is None: {first_task is None}")
                    
                    if isinstance(first_task, dict):
                        print(f"\nFirst Task Keys: {list(first_task.keys())}")
                        print(f"Task Status Code: {first_task.get('status_code')}")
                        print(f"Task Status Message: {first_task.get('status_message')}")
                        
                        result = first_task.get("result")
                        print(f"\nResult Type: {type(result)}")
                        print(f"Result is None: {result is None}")
                        print(f"Result Length: {len(result) if isinstance(result, list) else 'N/A'}")
                        
                        if isinstance(result, list) and len(result) > 0:
                            print(f"\nFirst Result Item Keys: {list(result[0].keys()) if isinstance(result[0], dict) else 'N/A'}")
                
                print("\n" + "="*80)
                print("FULL RESPONSE:")
                print("="*80)
                print(json.dumps(data, indent=2, default=str))
            else:
                print(f"\nResponse: {data}")
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test Keyword Ideas
    print("\n\n" + "="*80)
    print("Testing Keyword Ideas Endpoint")
    print("="*80)
    
    payload = [{
        "keywords": ["pet grooming"],
        "location_name": "United States",
        "language_code": "en",
        "limit": 10
    }]
    
    url = f"{base_url}/dataforseo_labs/google/keyword_ideas/live"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            print(f"\n✅ HTTP Status: {response.status_code}")
            print(f"\nResponse Type: {type(data)}")
            print(f"Response Keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
            
            if isinstance(data, dict):
                print(f"\nStatus Code: {data.get('status_code')}")
                print(f"Status Message: {data.get('status_message')}")
                print(f"Tasks Count: {data.get('tasks_count')}")
                print(f"Tasks Error: {data.get('tasks_error')}")
                
                tasks = data.get("tasks")
                if isinstance(tasks, list) and len(tasks) > 0:
                    first_task = tasks[0]
                    if isinstance(first_task, dict):
                        print(f"\nFirst Task Keys: {list(first_task.keys())}")
                        print(f"Task Status Code: {first_task.get('status_code')}")
                        print(f"Task Status Message: {first_task.get('status_message')}")
                        
                        result = first_task.get("result")
                        print(f"\nResult Type: {type(result)}")
                        print(f"Result Length: {len(result) if isinstance(result, list) else 'N/A'}")
                
                print("\n" + "="*80)
                print("FULL RESPONSE (first 2000 chars):")
                print("="*80)
                response_str = json.dumps(data, indent=2, default=str)
                print(response_str[:2000])
                if len(response_str) > 2000:
                    print(f"\n... (truncated, total length: {len(response_str)} chars)")
            else:
                print(f"\nResponse: {data}")
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_dataforseo_endpoint())

