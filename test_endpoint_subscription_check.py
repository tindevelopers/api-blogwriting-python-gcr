#!/usr/bin/env python3
"""
Test the correct DataForSEO AI Search Volume endpoint to check subscription status.
"""
import json
import requests
import base64

# API credentials
USERNAME = "developer@tin.info"
PASSWORD = "725ec88e0af0c905"
AUTH_HEADER = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
BASE_URL = "https://api.dataforseo.com/v3"

# Correct endpoint path from documentation
ENDPOINT = "ai_optimization/ai_keyword_data/keywords_search_volume/live"

def test_endpoint():
    """Test the endpoint and check subscription status."""
    url = f"{BASE_URL}/{ENDPOINT}"
    
    payload = [{
        "keywords": ["chatgpt"],
        "language_code": "en",
        "location_name": "United States"
    }]
    
    headers = {
        "Authorization": f"Basic {AUTH_HEADER}",
        "Content-Type": "application/json"
    }
    
    print("="*80)
    print("Testing DataForSEO AI Search Volume Endpoint")
    print("="*80)
    print(f"Endpoint: {ENDPOINT}")
    print(f"URL: {url}")
    print(f"Keyword: chatgpt")
    print("="*80)
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"\nHTTP Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return
        
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            print(f"Response: {response.text[:500]}")
            return
        
        # Check response
        status_code = data.get("status_code")
        status_message = data.get("status_message", "")
        
        print(f"\nResponse Status Code: {status_code}")
        print(f"Response Status Message: {status_message}")
        
        if data.get("tasks") and len(data["tasks"]) > 0:
            task = data["tasks"][0]
            task_status = task.get("status_code")
            task_message = task.get("status_message", "")
            
            print(f"\nTask Status Code: {task_status}")
            print(f"Task Status Message: {task_message}")
            
            print("\n" + "="*80)
            
            if task_status == 20000:
                print("✅✅✅ SUCCESS! Endpoint works and returns data!")
                print("   Subscription: ✅ ACTIVE")
                
                result_data = task.get("result", [])
                if result_data and len(result_data) > 0:
                    first_result = result_data[0]
                    
                    # Extract AI search volume
                    ai_vol = None
                    if "keyword_data" in first_result:
                        keyword_data = first_result.get("keyword_data", {})
                        keyword_info = keyword_data.get("keyword_info", {})
                        ai_vol = keyword_info.get("ai_search_volume", None)
                    
                    if ai_vol:
                        print(f"\n✅ AI Search Volume: {ai_vol}")
                    else:
                        print("\n⚠️  No AI search volume found in response")
                    
                    print("\nSample result structure:")
                    print(json.dumps(first_result, indent=2, default=str)[:1000])
                
            elif task_status == 40204:
                print("✅ Path is CORRECT!")
                print("❌ Subscription: NOT ACTIVE")
                print(f"\nMessage: {task_message}")
                print("\nAction Required:")
                print("   - Visit DataForSEO Plans and Subscriptions")
                print("   - Activate AI Optimization subscription")
                print("   - Then the endpoint will return data")
                
            elif task_status == 40402:
                print("❌ Invalid Path (40402)")
                print("   The endpoint path is incorrect")
                
            elif task_status == 40400:
                print("❌ Not Found (40400)")
                print("   The endpoint doesn't exist")
                
            else:
                print(f"⚠️  Unexpected status: {task_status}")
                print(f"   Message: {task_message}")
        else:
            print("\n⚠️  No tasks in response")
            print(f"Full response: {json.dumps(data, indent=2, default=str)[:500]}")
        
        print("\n" + "="*80)
        
    except requests.exceptions.Timeout:
        print("\n❌ Request timeout")
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request error: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_endpoint()

