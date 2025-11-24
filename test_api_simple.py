#!/usr/bin/env python3
import json
import base64
import subprocess
import sys

api_key = "developer@tin.info"
api_secret = "725ec88e0af0c905"
encoded = base64.b64encode(f"{api_key}:{api_secret}".encode()).decode()
base_url = "https://api.dataforseo.com/v3"

print("="*80)
print("Testing DataForSEO API Endpoints")
print("="*80)

# Test LLM Mentions
print("\n1. Testing LLM Mentions:")
print("-" * 80)
payload = json.dumps([{"target": [{"keyword": "chatgpt"}], "location_name": "United States", "language_code": "en", "platform": "chat_gpt", "limit": 10}])
result = subprocess.run(['curl', '-s', '-X', 'POST', f'{base_url}/ai_optimization/llm_mentions/search/live', '-H', f'Authorization: Basic {encoded}', '-H', 'Content-Type: application/json', '-d', payload], capture_output=True, text=True)
if result.returncode == 0:
    data = json.loads(result.stdout)
    if data.get('tasks'):
        task = data['tasks'][0]
        status = task.get('status_code')
        print(f"Status: {status} - {task.get('status_message')}")
        if status == 20000:
            print("✅ SUCCESS! LLM Mentions works!")
            r = task.get('result', [])
            if r and len(r) > 0:
                m = r[0].get('aggregated_metrics', {})
                print(f"AI Search Volume: {m.get('ai_search_volume', 0)}")
                print(f"Mentions Count: {m.get('mentions_count', 0)}")
                print(f"Top Pages: {len(r[0].get('items', []))}")
        elif status == 40204:
            print("⚠️ Needs subscription")
        else:
            print(f"Error: {task.get('status_message')}")

# Test AI Search Volume paths
paths = ["ai_optimization/keyword_data/live", "ai_optimization/ai_keyword_data/live"]
payload_sv = json.dumps([{"keywords": ["chatgpt"], "location_name": "United States", "language_code": "en"}])

for i, path in enumerate(paths, 2):
    print(f"\n{i}. Testing: {path}")
    print("-" * 80)
    result = subprocess.run(['curl', '-s', '-X', 'POST', f'{base_url}/{path}', '-H', f'Authorization: Basic {encoded}', '-H', 'Content-Type: application/json', '-d', payload_sv], capture_output=True, text=True)
    if result.returncode == 0:
        data = json.loads(result.stdout)
        if data.get('tasks'):
            task = data['tasks'][0]
            status = task.get('status_code')
            print(f"Status: {status} - {task.get('status_message')}")
            if status == 20000:
                print("✅✅✅ SUCCESS! This endpoint works!")
                r = task.get('result', [])
                if r and len(r) > 0:
                    print(f"Result keys: {list(r[0].keys())}")
                    kd = r[0].get('keyword_data', {})
                    if kd:
                        ki = kd.get('keyword_info', {})
                        if ki:
                            print(f"AI Search Volume: {ki.get('ai_search_volume', 'N/A')}")
            elif status == 40204:
                print("⚠️ Path correct but needs subscription")
            elif status == 40402:
                print("❌ Invalid Path")
            else:
                print(f"Error: {task.get('status_message')}")

print("\n" + "="*80)
print("Done!")

