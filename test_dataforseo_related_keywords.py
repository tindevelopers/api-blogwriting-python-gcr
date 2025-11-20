#!/usr/bin/env python3
"""Test DataForSEO related_keywords endpoint directly with different payloads."""

import os
import json
import base64
import httpx
import asyncio

async def test_related_keywords(payload_name: str, payload: list):
    """Test DataForSEO related_keywords endpoint with a specific payload."""
    
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
    
    endpoint = "dataforseo_labs/google/related_keywords/live"
    url = f"{base_url}/{endpoint}"
    
    print(f"\n{'='*80}")
    print(f"Testing: {payload_name}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"{'='*80}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()
            
            data = response.json()
            
            print(f"✅ HTTP Status: {response.status_code}")
            print(f"Status Code: {data.get('status_code')}")
            print(f"Status Message: {data.get('status_message')}")
            print(f"Tasks Error: {data.get('tasks_error', 0)}")
            
            if data.get("tasks"):
                tasks = data.get("tasks", [])
                if tasks and len(tasks) > 0:
                    task = tasks[0]
                    task_status = task.get("status_code")
                    task_message = task.get("status_message")
                    result_count = task.get("result_count", 0)
                    
                    print(f"\nTask Status Code: {task_status}")
                    print(f"Task Status Message: {task_message}")
                    print(f"Result Count: {result_count}")
                    
                    if task_status == 20000 and result_count > 0:
                        print(f"✅ SUCCESS! Found {result_count} results")
                        if task.get("result") and len(task["result"]) > 0:
                            first_result = task["result"][0]
                            if isinstance(first_result, dict):
                                print(f"First result keys: {list(first_result.keys())[:10]}")
                    elif task_status != 20000:
                        print(f"❌ ERROR: {task_message}")
                        print(f"Task data sent: {json.dumps(task.get('data', {}), indent=2)}")
                else:
                    print("⚠️ No tasks in response")
            else:
                print("⚠️ No 'tasks' key in response")
                print(f"Response keys: {list(data.keys())}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        if hasattr(e, 'response') and e.response:
            try:
                error_data = e.response.json()
                print(f"Error response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error response text: {e.response.text}")

async def main():
    """Test different payload configurations."""
    
    test_cases = [
        # Test 1: Minimal - keyword and depth only
        ("Minimal (keyword + depth)", [{
            "keyword": "pet grooming",
            "depth": 1
        }]),
        
        # Test 2: keyword + location_name
        ("Keyword + location_name", [{
            "keyword": "pet grooming",
            "location_name": "United States",
            "depth": 1
        }]),
        
        # Test 3: keyword + location_code
        ("Keyword + location_code", [{
            "keyword": "pet grooming",
            "location_code": 2840,  # US location code
            "depth": 1
        }]),
        
        # Test 4: keyword + location_name + limit (no depth)
        ("Keyword + location_name + limit (no depth)", [{
            "keyword": "pet grooming",
            "location_name": "United States",
            "limit": 5
        }]),
        
        # Test 5: keyword only (no location, no depth)
        ("Keyword only", [{
            "keyword": "pet grooming"
        }]),
    ]
    
    print("Testing DataForSEO related_keywords endpoint with different payloads...")
    print("="*80)
    
    for payload_name, payload in test_cases:
        await test_related_keywords(payload_name, payload)
        await asyncio.sleep(1)  # Small delay between requests
    
    print(f"\n{'='*80}")
    print("Testing complete!")

if __name__ == "__main__":
    asyncio.run(main())
