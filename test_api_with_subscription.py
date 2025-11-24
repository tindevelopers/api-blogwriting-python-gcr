#!/usr/bin/env python3
"""Test DataForSEO API endpoints with updated subscription."""

import json
import base64
import subprocess

# API credentials
api_key = "developer@tin.info"
api_secret = "725ec88e0af0c905"
credentials = f"{api_key}:{api_secret}"
encoded = base64.b64encode(credentials.encode()).decode()

base_url = "https://api.dataforseo.com/v3"

print("="*80)
print("Testing DataForSEO API Endpoints with Updated Subscription")
print("="*80)
print()

# Test 1: LLM Mentions (should work now)
print("Test 1: LLM Mentions Endpoint")
print("-" * 80)
print("Endpoint: ai_optimization/llm_mentions/search/live")
print()

payload_llm = [{
    "target": [{"keyword": "chatgpt"}],
    "location_name": "United States",
    "language_code": "en",
    "platform": "chat_gpt",
    "limit": 10
}]

try:
    result = subprocess.run(
        ['curl', '-s', '-X', 'POST', f'{base_url}/ai_optimization/llm_mentions/search/live',
         '-H', f'Authorization: Basic {encoded}',
         '-H', 'Content-Type: application/json',
         '-d', json.dumps(payload_llm),
         '--max-time', '30'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        print(f"Status: {data.get('status_code')} - {data.get('status_message')}")
        
        if data.get('tasks') and len(data['tasks']) > 0:
            task = data['tasks'][0]
            task_status = task.get('status_code')
            task_msg = task.get('status_message')
            
            print(f"Task Status: {task_status} - {task_msg}")
            
            if task_status == 20000:
                print("✅✅✅ SUCCESS! LLM Mentions endpoint works!")
                result_data = task.get('result')
                if result_data and len(result_data) > 0:
                    first = result_data[0]
                    print(f"\nResult structure:")
                    print(f"  Keys: {list(first.keys())}")
                    
                    if 'aggregated_metrics' in first:
                        metrics = first['aggregated_metrics']
                        print(f"\nAggregated Metrics:")
                        print(f"  AI Search Volume: {metrics.get('ai_search_volume', 'N/A')}")
                        print(f"  Mentions Count: {metrics.get('mentions_count', 'N/A')}")
                    
                    if 'items' in first:
                        items = first['items']
                        print(f"\nTop Pages: {len(items)}")
                        if items:
                            print(f"  First page: {items[0].get('title', 'N/A')[:60]}")
                            print(f"  URL: {items[0].get('url', 'N/A')[:80]}")
                            print(f"  Mentions: {items[0].get('mentions_count', 'N/A')}")
                    
                    print(f"\nFull first result (first 1500 chars):")
                    print(json.dumps(first, indent=2, default=str)[:1500])
            elif task_status == 40204:
                print("⚠️ Still needs subscription activation")
            else:
                print(f"❌ Error: {task_msg}")
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("="*80)
print("Test 2: AI Search Volume Endpoints")
print("="*80)
print()

# Test AI Search Volume endpoints
endpoints_to_test = [
    "ai_optimization/keyword_data/live",
    "ai_optimization/ai_keyword_data/live",
    "keywords_data/ai_optimization/search_volume/live",  # Original (known wrong)
]

payload_sv = [{
    "keywords": ["chatgpt"],
    "location_name": "United States",
    "language_code": "en"
}]

for endpoint in endpoints_to_test:
    print(f"Testing: {endpoint}")
    print("-" * 80)
    
    try:
        result = subprocess.run(
            ['curl', '-s', '-X', 'POST', f'{base_url}/{endpoint}',
             '-H', f'Authorization: Basic {encoded}',
             '-H', 'Content-Type: application/json',
             '-d', json.dumps(payload_sv),
             '--max-time', '30'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            
            if data.get('tasks') and len(data['tasks']) > 0:
                task = data['tasks'][0]
                task_status = task.get('status_code')
                task_msg = task.get('status_message')
                
                print(f"Status: {task_status} - {task_msg}")
                
                if task_status == 20000:
                    print("✅✅✅ SUCCESS! This endpoint works!")
                    result_data = task.get('result')
                    if result_data:
                        print(f"Result count: {len(result_data) if isinstance(result_data, list) else 'N/A'}")
                        if result_data and len(result_data) > 0:
                            first = result_data[0]
                            print(f"\nFirst result keys: {list(first.keys())}")
                            
                            # Check for keyword_data structure
                            if 'keyword_data' in first:
                                keyword_data = first['keyword_data']
                                print(f"keyword_data keys: {list(keyword_data.keys())}")
                                if 'keyword_info' in keyword_data:
                                    keyword_info = keyword_data['keyword_info']
                                    print(f"keyword_info keys: {list(keyword_info.keys())}")
                                    print(f"AI Search Volume: {keyword_info.get('ai_search_volume', 'N/A')}")
                            
                            print(f"\nFull first result (first 1000 chars):")
                            print(json.dumps(first, indent=2, default=str)[:1000])
                elif task_status == 40204:
                    print("⚠️ Path correct but needs subscription")
                elif task_status == 40402:
                    print("❌ Invalid Path")
                else:
                    print(f"Error: {task_msg}")
            else:
                print(f"Status: {data.get('status_code')} - {data.get('status_message')}")
        else:
            print(f"❌ curl error: {result.stderr[:100]}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()

print("="*80)
print("Summary")
print("="*80)

