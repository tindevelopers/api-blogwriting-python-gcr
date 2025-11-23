#!/usr/bin/env python3
"""Test different DataForSEO AI optimization endpoint paths to find the correct one."""

import json
import base64
import subprocess

# API credentials
api_key = "developer@tin.info"
api_secret = "725ec88e0af0c905"
credentials = f"{api_key}:{api_secret}"
encoded = base64.b64encode(credentials.encode()).decode()

base_url = "https://api.dataforseo.com/v3"

# Test different endpoint paths based on DataForSEO API patterns
endpoints_to_test = [
    "ai_optimization/keyword_data/live",
    "ai_optimization/ai_keyword_data/live", 
    "ai_optimization/keyword_data/search_volume/live",
    "ai_optimization/ai_keyword_data/search_volume/live",
    "ai_optimization/search_volume/live",
    "keywords_data/ai_optimization/search_volume/live",  # Current (wrong)
]

payload = [{
    "keywords": ["chatgpt"],
    "location_name": "United States",
    "language_code": "en"
}]

print("="*80)
print("Testing DataForSEO AI Keyword Data Endpoints")
print("="*80)
print()

results = []

for endpoint in endpoints_to_test:
    url = f"{base_url}/{endpoint}"
    print(f"Testing: {endpoint}")
    
    try:
        result = subprocess.run(
            ['curl', '-s', '-X', 'POST', url,
             '-H', f'Authorization: Basic {encoded}',
             '-H', 'Content-Type: application/json',
             '-d', json.dumps(payload),
             '--max-time', '10'],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                status = data.get('status_code')
                
                if data.get('tasks') and len(data['tasks']) > 0:
                    task = data['tasks'][0]
                    task_status = task.get('status_code')
                    task_msg = task.get('status_message')
                    
                    result_info = {
                        'endpoint': endpoint,
                        'status': task_status,
                        'message': task_msg
                    }
                    
                    if task_status == 20000:
                        print(f"  ✅✅✅ SUCCESS! Endpoint works!")
                        result_data = task.get('result')
                        if result_data:
                            print(f"  Result count: {len(result_data) if isinstance(result_data, list) else 'N/A'}")
                            if result_data and len(result_data) > 0:
                                print(f"  First result keys: {list(result_data[0].keys()) if isinstance(result_data[0], dict) else 'N/A'}")
                        result_info['success'] = True
                    elif task_status == 40204:
                        print(f"  ✅ Path CORRECT (needs subscription) - Status: {task_status}")
                        result_info['correct_path'] = True
                    elif task_status == 40402:
                        print(f"  ❌ Invalid Path - Status: {task_status}")
                    else:
                        print(f"  Status: {task_status} - {task_msg}")
                    
                    results.append(result_info)
                else:
                    print(f"  Status: {status} - {data.get('status_message')}")
                    results.append({
                        'endpoint': endpoint,
                        'status': status,
                        'message': data.get('status_message')
                    })
            except json.JSONDecodeError:
                print(f"  ❌ Invalid JSON response")
        else:
            print(f"  ❌ curl error: {result.stderr[:100]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    print()

print("="*80)
print("SUMMARY")
print("="*80)
print()

correct_paths = [r for r in results if r.get('correct_path') or r.get('success')]
invalid_paths = [r for r in results if r.get('status') == 40402]

if correct_paths:
    print("✅ Found correct endpoint paths:")
    for r in correct_paths:
        print(f"  - {r['endpoint']} (Status: {r['status']})")
else:
    print("❌ No correct endpoint paths found")
    print("\nAll tested paths returned errors.")
    print("The AI search volume endpoint might:")
    print("  1. Not exist yet in DataForSEO API")
    print("  2. Be under a different API category")
    print("  3. Require different parameters or structure")

if invalid_paths:
    print(f"\n❌ Invalid paths ({len(invalid_paths)}):")
    for r in invalid_paths:
        print(f"  - {r['endpoint']}")

print("\n" + "="*80)
print("Next Steps:")
print("1. Check DataForSEO API documentation: https://docs.dataforseo.com/v3/ai_optimization-overview/")
print("2. Look for 'AI Keyword Data API' endpoint path")
print("3. Verify if endpoint exists or if search volume is part of another endpoint")

